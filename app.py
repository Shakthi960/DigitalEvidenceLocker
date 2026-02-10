from flask import Flask, render_template, request, redirect, session, send_file
import os
import hashlib
import time
from blockchain import Blockchain
from database import init_db, insert_evidence, insert_custody, fetch_all_evidence, fetch_custody, fetch_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

blockchain = Blockchain()
UPLOAD_FOLDER = "evidence_storage"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()

# Dummy users
USERS = {
    "police": {"password": "123", "role": "Police"},
    "forensic": {"password": "123", "role": "Forensic"},
    "court": {"password": "123", "role": "Court"}
}

def generate_hash(filepath):
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USERS and USERS[username]["password"] == password:
            session["username"] = username
            session["role"] = USERS[username]["role"]
            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    return render_template("dashboard.html", role=session["role"])

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        return redirect("/")

    if request.method == "POST":
        file = request.files["file"]
        case_id = request.form["case_id"]
        evidence_id = request.form["evidence_id"]

        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, evidence_id + "_" + filename)
        file.save(filepath)

        file_hash = generate_hash(filepath)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        data = {
            "evidence_id": evidence_id,
            "case_id": case_id,
            "filename": filename,
            "file_path": filepath,
            "file_hash": file_hash,
            "uploaded_by": session["username"],
            "role": session["role"],
            "timestamp": timestamp
        }

        insert_evidence(data)

        insert_custody(evidence_id, "Uploaded Evidence", session["username"], session["role"], timestamp)

        blockchain.add_block({
            "evidence_id": evidence_id,
            "case_id": case_id,
            "file_hash": file_hash,
            "action": "Uploaded",
            "performed_by": session["username"],
            "role": session["role"],
            "timestamp": timestamp
        })

        return redirect("/evidence")

    return render_template("upload.html")

@app.route("/evidence")
def evidence():
    if "username" not in session:
        return redirect("/")
    all_data = fetch_all_evidence()
    return render_template("evidence_list.html", evidence=all_data)

@app.route("/download/<evidence_id>")
def download(evidence_id):
    all_data = fetch_all_evidence()
    for row in all_data:
        if row[1] == evidence_id:
            return send_file(row[4], as_attachment=True)
    return "File Not Found"

@app.route("/verify", methods=["GET", "POST"])
def verify():
    if "username" not in session:
        return redirect("/")

    if request.method == "POST":
        evidence_id = request.form["evidence_id"]
        file = request.files["file"]

        temp_path = os.path.join("temp_" + file.filename)
        file.save(temp_path)

        new_hash = generate_hash(temp_path)
        os.remove(temp_path)

        old_hash = fetch_hash(evidence_id)

        if old_hash == new_hash:
            result = "VALID - Evidence Not Tampered ✅"
        else:
            result = "TAMPERED - Evidence Modified ❌"

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        insert_custody(evidence_id, "Verified Evidence", session["username"], session["role"], timestamp)

        blockchain.add_block({
            "evidence_id": evidence_id,
            "action": "Verified",
            "performed_by": session["username"],
            "role": session["role"],
            "timestamp": timestamp,
            "result": result
        })

        return render_template("verify.html", result=result)

    return render_template("verify.html", result="")

@app.route("/chain/<evidence_id>")
def chain(evidence_id):
    history = fetch_custody(evidence_id)
    return render_template("chain.html", history=history, evidence_id=evidence_id)

@app.route("/blockchain")
def view_blockchain():
    return blockchain.get_chain()

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
