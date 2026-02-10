import sqlite3

DB_NAME = "evidence.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE,
            case_id TEXT,
            filename TEXT,
            file_path TEXT,
            file_hash TEXT,
            uploaded_by TEXT,
            role TEXT,
            timestamp TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS custody (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT,
            action TEXT,
            performed_by TEXT,
            role TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

def insert_evidence(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO evidence (evidence_id, case_id, filename, file_path, file_hash, uploaded_by, role, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["evidence_id"], data["case_id"], data["filename"],
        data["file_path"], data["file_hash"], data["uploaded_by"],
        data["role"], data["timestamp"]
    ))

    conn.commit()
    conn.close()

def insert_custody(evidence_id, action, performed_by, role, timestamp):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO custody (evidence_id, action, performed_by, role, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (evidence_id, action, performed_by, role, timestamp))

    conn.commit()
    conn.close()

def fetch_all_evidence():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT * FROM evidence")
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_custody(evidence_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT action, performed_by, role, timestamp FROM custody WHERE evidence_id=?", (evidence_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_hash(evidence_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT file_hash FROM evidence WHERE evidence_id=?", (evidence_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
