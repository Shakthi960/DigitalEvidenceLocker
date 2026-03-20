from flask import Flask, render_template, request, redirect, session, send_file, flash
import os
import hashlib
import time
import sqlite3

from blockchain import Blockchain
from database import *
from docx import Document

DELETE_PASSWORD = "court@delete"

app = Flask(__name__)
app.secret_key = "evidence_locker_secret"

blockchain = Blockchain()

UPLOAD_FOLDER = "evidence_storage"
REPORT_FOLDER = "forensic_reports"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)

init_db()

# ---------------- USERS ----------------

USERS = {
    "police": {"password": "123", "role": "Police"},
    "forensic": {"password": "123", "role": "Forensic"},
    "court": {"password": "123", "role": "Court"}
}

# ---------------- HASH FUNCTION ----------------

def generate_hash(filepath):

    ext = os.path.splitext(filepath)[1].lower()
    sha256 = hashlib.sha256()

    try:

        if ext == ".docx":

            doc = Document(filepath)

            text = ""

            for para in doc.paragraphs:
                text += para.text

            sha256.update(text.encode("utf-8"))

        elif ext == ".txt":

            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                sha256.update(content.encode("utf-8"))

        else:

            with open(filepath, "rb") as f:

                while True:
                    chunk = f.read(4096)

                    if not chunk:
                        break

                    sha256.update(chunk)

    except Exception:

        with open(filepath, "rb") as f:

            while True:
                chunk = f.read(4096)

                if not chunk:
                    break

                sha256.update(chunk)

    return sha256.hexdigest()


# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if username in USERS and USERS[username]["password"] == password:

            session["username"] = username
            session["role"] = USERS[username]["role"]

            return redirect("/dashboard")

        flash("Invalid username or password!", "danger")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "username" not in session:
        return redirect("/")

    role = session["role"]

    if role == "Police":
        evidence_data = fetch_all_evidence()
    else:
        evidence_data = fetch_role_evidence(role)

    return render_template("dashboard.html", role=role, evidence=evidence_data)


# ---------------- HISTORY ----------------

@app.route("/history")
def history():

    if "username" not in session:
        return redirect("/")

    evidence_data = fetch_all_evidence()

    return render_template("history.html", evidence=evidence_data)


# ---------------- UPLOAD EVIDENCE ----------------

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "username" not in session:
        return redirect("/")

    if session["role"] != "Police":

        flash("Only Police can upload evidence!", "danger")
        return redirect("/dashboard")

    if request.method == "POST":

        file = request.files["file"]

        case_id = request.form["case_id"].strip()
        evidence_id = request.form["evidence_id"].strip()

        if file.filename == "":
            flash("Please select a file!", "danger")
            return redirect("/upload")

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
            "status": "Uploaded",
            "current_role": "Police",
            "forensic_remarks": "-",
            "court_remarks": "-",
            "forensic_report": "-",
            "timestamp": timestamp
        }

        insert_evidence(data)

        insert_custody(evidence_id, "Evidence Uploaded", session["username"], "Police", timestamp)

        blockchain.add_block({
            "evidence_id": evidence_id,
            "action": "Uploaded",
            "role": "Police",
            "timestamp": timestamp
        })

        flash("Evidence Uploaded Successfully!", "success")

        return redirect("/dashboard")

    return render_template("upload.html")


# ---------------- TRANSFER ----------------

@app.route("/transfer/<evidence_id>/<next_role>")
def transfer(evidence_id, next_role):

    if "username" not in session:
        return redirect("/")

    role = session["role"]

    if role not in ["Police", "Forensic"]:

        flash("You cannot transfer evidence!", "danger")
        return redirect("/dashboard")

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    update_status(evidence_id, f"Transferred to {next_role}", next_role)

    insert_custody(evidence_id, f"Transferred to {next_role}", session["username"], role, timestamp)

    blockchain.add_block({
        "evidence_id": evidence_id,
        "action": "Transferred",
        "to": next_role,
        "by": session["username"],
        "timestamp": timestamp
    })

    flash(f"Evidence transferred to {next_role}!", "success")

    return redirect("/dashboard")


# ---------------- DOWNLOAD ----------------

@app.route("/download/<evidence_id>")
def download(evidence_id):

    if "username" not in session:
        return redirect("/")

    evidence = fetch_single_evidence(evidence_id)

    if not evidence:

        flash("Evidence not found!", "danger")
        return redirect("/dashboard")

    return send_file(evidence[4], as_attachment=True)


# ---------------- VERIFY + REPORT ----------------

@app.route("/verify/<evidence_id>", methods=["GET", "POST"])
def verify(evidence_id):

    if "username" not in session:
        return redirect("/")

    role = session["role"]

    evidence = fetch_single_evidence(evidence_id)

    if not evidence:
        flash("Evidence not found!", "danger")
        return redirect("/dashboard")

    if evidence[8] != role:
        flash("This evidence is not assigned to you!", "danger")
        return redirect("/dashboard")

    if request.method == "POST":

        file = request.files["file"]
        report_file = request.files.get("report")

        remarks = request.form.get("remarks", "").strip()

        # -------- Save forensic report --------

        if role == "Forensic" and report_file and report_file.filename != "":

            report_path = os.path.join(REPORT_FOLDER, evidence_id + "_" + report_file.filename)

            report_file.save(report_path)

            conn = sqlite3.connect("evidence.db")
            cur = conn.cursor()

            cur.execute(
                "UPDATE evidence SET forensic_report=? WHERE evidence_id=?",
                (report_path, evidence_id)
            )

            conn.commit()
            conn.close()

        # -------- Verify evidence --------

        temp_path = "temp_" + file.filename
        file.save(temp_path)

        new_hash = generate_hash(temp_path)

        os.remove(temp_path)

        old_hash = fetch_hash(evidence_id)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        if old_hash == new_hash:

            result = "Verified"

            if role == "Forensic":

                update_forensic_remarks(evidence_id, remarks or "Verified by Forensic")
                update_status(evidence_id, "Forensic Verified", "Forensic")

            elif role == "Court":

                update_court_remarks(evidence_id, remarks or "Approved by Court")
                update_status(evidence_id, "Court Approved", "Completed")

            insert_custody(evidence_id, f"Verified by {role}", session["username"], role, timestamp)

            flash("Evidence Verified Successfully!", "success")

        else:

            result = "Tampered"

            update_status(evidence_id, "Tampered", role)

            insert_custody(evidence_id, "Tampering Detected", session["username"], role, timestamp)

            flash("Tampering Detected!", "danger")

        blockchain.add_block({
            "evidence_id": evidence_id,
            "action": result,
            "performed_by": session["username"],
            "role": role,
            "timestamp": timestamp
        })

        return redirect("/dashboard")

    return render_template("verify.html", evidence=evidence, role=role)


# ---------------- DELETE (COURT ONLY) ----------------

@app.route("/delete/<evidence_id>", methods=["POST"])
def delete_evidence(evidence_id):

    if "username" not in session:
        return redirect("/")

    if session["role"] != "Court":
        flash("Only court can delete records!", "danger")
        return redirect("/dashboard")

    password = request.form.get("delete_password")

    if password != DELETE_PASSWORD:
        flash("Invalid deletion password!", "danger")
        return redirect("/dashboard")

    conn = sqlite3.connect("evidence.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM evidence WHERE evidence_id=?", (evidence_id,))
    cur.execute("DELETE FROM custody WHERE evidence_id=?", (evidence_id,))

    conn.commit()
    conn.close()

    flash("Evidence deleted successfully!", "success")

    return redirect("/dashboard")


# ---------------- CHAIN ----------------

@app.route("/chain/<evidence_id>")
def chain(evidence_id):

    if "username" not in session:
        return redirect("/")

    history = fetch_custody(evidence_id)

    return render_template("chain.html", history=history, evidence_id=evidence_id)


# ---------------- BLOCKCHAIN VIEW ----------------

@app.route("/blockchain")
def view_blockchain():

    if "username" not in session:
        return redirect("/")

    chain_data = blockchain.get_chain()

    return render_template("blockchain.html", chain=chain_data)


# ---------------- DOWNLOAD REPORT ----------------

@app.route("/report/<evidence_id>")
def download_report(evidence_id):

    if "username" not in session:
        return redirect("/")

    evidence = fetch_single_evidence(evidence_id)

    if not evidence:
        flash("Report not found!", "danger")
        return redirect("/dashboard")

    report_path = evidence[11]

    if report_path == "-" or not os.path.exists(report_path):
        flash("No forensic report available!", "danger")
        return redirect("/dashboard")

    return send_file(report_path, as_attachment=True)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)