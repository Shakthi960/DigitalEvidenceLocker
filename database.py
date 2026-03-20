import sqlite3

DB_NAME = "evidence.db"

# ---------------- INIT DB ----------------

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
        status TEXT,
        current_role TEXT,
        forensic_remarks TEXT,
        court_remarks TEXT,
        forensic_report TEXT,
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


# ---------------- INSERT EVIDENCE ----------------

def insert_evidence(data):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO evidence 
        (evidence_id, case_id, filename, file_path, file_hash, uploaded_by,
         status, current_role, forensic_remarks, court_remarks, forensic_report, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["evidence_id"],
        data["case_id"],
        data["filename"],
        data["file_path"],
        data["file_hash"],
        data["uploaded_by"],
        data["status"],
        data["current_role"],
        data["forensic_remarks"],
        data["court_remarks"],
        data["forensic_report"],
        data["timestamp"]
    ))

    conn.commit()
    conn.close()


# ---------------- UPDATE STATUS ----------------

def update_status(evidence_id, status, current_role):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        UPDATE evidence
        SET status=?, current_role=?
        WHERE evidence_id=?
    """, (status, current_role, evidence_id))

    conn.commit()
    conn.close()


# ---------------- UPDATE REMARKS ----------------

def update_forensic_remarks(evidence_id, remarks):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        UPDATE evidence
        SET forensic_remarks=?
        WHERE evidence_id=?
    """, (remarks, evidence_id))

    conn.commit()
    conn.close()


def update_court_remarks(evidence_id, remarks):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        UPDATE evidence
        SET court_remarks=?
        WHERE evidence_id=?
    """, (remarks, evidence_id))

    conn.commit()
    conn.close()


# ---------------- UPDATE FORENSIC REPORT ----------------

def update_forensic_report(evidence_id, report_path):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        UPDATE evidence
        SET forensic_report=?
        WHERE evidence_id=?
    """, (report_path, evidence_id))

    conn.commit()
    conn.close()


# ---------------- CUSTODY ----------------

def insert_custody(evidence_id, action, performed_by, role, timestamp):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO custody
        (evidence_id, action, performed_by, role, timestamp)
        VALUES (?, ?, ?, ?, ?)
    """, (evidence_id, action, performed_by, role, timestamp))

    conn.commit()
    conn.close()


# ---------------- FETCH FUNCTIONS ----------------

def fetch_all_evidence():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM evidence ORDER BY id DESC")

    rows = cur.fetchall()

    conn.close()

    return rows


def fetch_role_evidence(role):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM evidence
        WHERE current_role=?
        ORDER BY id DESC
    """, (role,))

    rows = cur.fetchall()

    conn.close()

    return rows


def fetch_single_evidence(evidence_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT * FROM evidence WHERE evidence_id=?", (evidence_id,))

    row = cur.fetchone()

    conn.close()

    return row


def fetch_custody(evidence_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT action, performed_by, role, timestamp
        FROM custody
        WHERE evidence_id=?
        ORDER BY id ASC
    """, (evidence_id,))

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