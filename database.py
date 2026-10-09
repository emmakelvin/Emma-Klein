import sqlite3
import os
import subprocess, sys
from datetime import date
DB_NAME = "jams.db"
UPLOAD_DIR = "uploads"

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Applicant','Admin'))
    );
    
    CREATE TABLE IF NOT EXISTS applicants(
        applicant_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id   INTEGER UNIQUE,
        phone      TEXT,
        address    TEXT,
        education  TEXT,
        experience TEXT,
        cv         TEXT,
        FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS jobs(
        job_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        title    TEXT NOT NULL,
        department  TEXT,
        description  TEXT,
        qualification  TEXT,
        experience  TEXT,
        location  TEXT,
        salary   TEXT,
        deadline  TEXT,
        status  TEXT DEFAULT 'Open'
    );
    
    CREATE TABLE IF NOT EXISTS applications(
        application_id  INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_id  INTEGER,
        job_id  INTEGER,
        application_date  DATE,
        status  TEXT DEFAULT 'Submitted',
        UNIQUE(applicant_id, job_id),
        FOREIGN KEY(applicant_id) REFERENCES applicants(applicant_id) ON DELETE CASCADE,
        FOREIGN KEY(job_id)  REFERENCES jobs(job_id) ON DELETE CASCADE
    );
    
    CREATE TABLE IF NOT EXISTS interviews(
        interview_id INTEGER PRIMARY KEY AUTOINCREMENT,
        application_id INTEGER UNIQUE,
        interview_date DATE,
        interview_time TIME,
        location  TEXT,
        result    TEXT,
        FOREIGN KEY(application_id) REFERENCES applications(application_id) ON DELETE CASCADE
    );
    """ )
    c.executescript('SELECT * FROM users')
    results = c.fetchall()
    print(results)
   

    # Migrate older schema if needed.
    cols = [row[1] for row in c.execute("PRAGMA table_info(jobs)")]
    if "qualification" not in cols and "qualifications" in cols:
        c.execute("ALTER TABLE jobs RENAME COLUMN qualifications TO qualification")
        conn.commit()

    # Seed default admin.
    c.execute("SELECT 1 FROM users WHERE role='Admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users(name, email, password, role) VALUES (?,?,?,?)",
                  ("System Admin", "admin@jams.com", "admin123", "Admin"))
        conn.commit()
    conn.close()
    
    #--------------user --------------
def create_applicant(name, email, phone, password, address):
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute("INSERT INTO users(name,email,password,role) VALUES (?,?,?,?)",
                  (name, email, password, "Applicant"))
        uid = c.lastrowid
        c.execute("""INSERT INTO applicants(user_id,phone,address)
                     VALUES (?,?,?)""", (uid, phone, address))
        conn.commit()
        return True, "Registration successful."
    except sqlite3.IntegrityError:
        return False, "Email already registered."
    finally:
        conn.close()

def authenticate(email, password):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT user_id,name,role FROM users WHERE email=? AND password=?",
              (email, password))
    row = c.fetchone(); conn.close()
    return row  # (user_id, name, role) or None

def get_applicant_by_user(user_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM applicants WHERE user_id=?", (user_id,))
    row = c.fetchone(); conn.close()
    return row

def update_applicant_profile(user_id, phone, address, education, experience):
    conn = get_conn(); c = conn.cursor()
    c.execute("""UPDATE applicants SET phone=?, address=?, education=?, experience=?
                 WHERE user_id=?""", (phone, address, education, experience, user_id))
    conn.commit(); conn.close()

def update_cv_path(user_id, path):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE applicants SET cv=? WHERE user_id=?", (path, user_id))
    conn.commit(); conn.close()
    
# ---------- JOBS ----------
def add_job(title, department, description, qualification, experience,
            location, salary, deadline):
    conn = get_conn(); c = conn.cursor()
    c.execute("""INSERT INTO jobs(title,department,description,qualification,
                 experience,location,salary,deadline,status)
                 VALUES (?,?,?,?,?,?,?,?,'Open')""",
              (title, department, description, qualification, experience,
               location, salary, deadline))
    conn.commit(); conn.close()

def update_job(job_id, title, department, description, qualification,
               experience, location, salary, deadline, status):
    conn = get_conn(); c = conn.cursor()
    c.execute("""UPDATE jobs SET title=?,department=?,description=?,qualification=?,
                 experience=?,location=?,salary=?,deadline=?,status=? WHERE job_id=?""",
              (title, department, description, qualification, experience,
               location, salary, deadline, status, job_id))
    conn.commit(); conn.close()

def delete_job(job_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM jobs WHERE job_id=?", (job_id,))
    conn.commit(); conn.close()

def list_jobs(search="", location="", department="", only_open=False):
    conn = get_conn(); c = conn.cursor()
    q = "SELECT * FROM jobs WHERE 1=1"
    params = []
    if search:
        q += " AND title LIKE ?"; params.append(f"%{search}%")
    if location:
        q += " AND location LIKE ?"; params.append(f"%{location}%")
    if department:
        q += " AND department LIKE ?"; params.append(f"%{department}%")
    if only_open:
        q += " AND status='Open'"
    q += " ORDER BY job_id DESC"
    c.execute(q, params)
    rows = c.fetchall(); conn.close()
    return rows

def get_job(job_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,))
    row = c.fetchone(); conn.close()
    return row

# ---------- APPLICATIONS ----------
def submit_application(applicant_id, job_id):
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute("""INSERT INTO applications(applicant_id,job_id,application_date,status)
                     VALUES (?,?,?, 'Submitted')""",
                  (applicant_id, job_id, date.today().isoformat()))
        conn.commit(); return True, "Application submitted."
    except sqlite3.IntegrityError:
        return False, "You already applied for this job."
    finally:
        conn.close()

def my_applications(applicant_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT a.application_id, j.title, j.department, j.location,
                        a.application_date, a.status
                 FROM applications a JOIN jobs j ON a.job_id=j.job_id
                 WHERE a.applicant_id=? ORDER BY a.application_id DESC""",
              (applicant_id,))
    rows = c.fetchall(); conn.close()
    return rows

def all_applications(status_filter=None):
    conn = get_conn(); c = conn.cursor()
    q = """SELECT a.application_id, u.name, u.email, j.title, j.department,
                  a.application_date, a.status, ap.cv, ap.applicant_id
           FROM applications a
           JOIN applicants ap ON a.applicant_id = ap.applicant_id
           JOIN users u       ON ap.user_id = u.user_id
           JOIN jobs  j       ON a.job_id = j.job_id"""
    params = []
    if status_filter:
        q += " WHERE a.status=?"; params.append(status_filter)
    q += " ORDER BY a.application_id DESC"
    c.execute(q, params)
    rows = c.fetchall(); conn.close()
    return rows

def update_application_status(app_id, status):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE applications SET status=? WHERE application_id=?", (status, app_id))
    conn.commit(); conn.close()

def get_application(app_id):
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT a.application_id, a.applicant_id, a.job_id, a.status,
                        u.name, u.email, j.title
                 FROM applications a
                 JOIN applicants ap ON a.applicant_id = ap.applicant_id
                 JOIN users u       ON ap.user_id = u.user_id
                 JOIN jobs  j       ON a.job_id = j.job_id
                 WHERE a.application_id=?""", (app_id,))
    row = c.fetchone(); conn.close()
    return row
'''
def get_full_application(app_id):
    """Return complete applicant + job + interview details for one application."""
    conn = get_conn(); c = conn.cursor()
    c.execute("""
              SELECT a.application_id,
              u.name, u.email, 
              ap.phone, ap.address, ap.education, ap.experince, ap.cv,
              j.title, j.department, j.location, j.salary, j.deadline,
              a.application_data, a.status,
              i.interview_date, i.interview_time, i.location, i.result
              FROM applications a
              JOIN applicants ap ON a.applicant_id = ap.applicant_id
              JOIN users u       ON ap.user_id = u.user_id
              JOIN jobs  j      ON a.job_id = j.job_id
              LEFT JOIN interviews i ON i.application-id = a.pplication_id
              WHERE a.application_id = ?
              """, (app_id,))
    row = c.fetchone()
    conn.close()
    return row

def open_file(path):
    """Open a file with the OS default application."""
    if not path or not os.path.exists(path):
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
        return True
    except Exception:
        return False'''

###########INTERVIEWS################
def schedule_interview(app_id, i_date, i_time, location):
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute("""INSERT INTO interviews(application_id,interview_date,
                     interview_time,location,result)
                     VALUES (?,?,?,?,'Pending')""",
                  (app_id, i_date, i_time, location))
        conn.commit(); return True, "Interview scheduled."
    except sqlite3.IntegrityError:
        c.execute("""UPDATE interviews SET interview_date=?, interview_time=?, location=?
                     WHERE application_id=?""",
                  (i_date, i_time, location, app_id))
        conn.commit(); return True, "Interview updated."
    finally:
        conn.close()

def list_interviews():
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT i.interview_id, u.name, j.title, i.interview_date,
                        i.interview_time, i.location, i.result, i.application_id
                 FROM interviews i
                 JOIN applications a ON i.application_id = a.application_id
                 JOIN applicants ap  ON a.applicant_id = ap.applicant_id
                 JOIN users u        ON ap.user_id = u.user_id
                 JOIN jobs j         ON a.job_id = j.job_id
                 ORDER BY i.interview_date DESC""")
    rows = c.fetchall(); conn.close()
    return rows

def record_interview_result(app_id, result):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE interviews SET result=? WHERE application_id=?", (result, app_id))
    conn.commit(); conn.close()
    
############### report ###############
def get_stats():
    conn = get_conn(); c = conn.cursor()
    stats = {}
    for key, q in {
        "jobs": "SELECT COUNT(*) FROM jobs",
        "applicants": "SELECT COUNT(*) FROM applicants",
        "applications": "SELECT COUNT(*) FROM applications",
        "shortlisted": "SELECT COUNT(*) FROM applications WHERE status='Shortlisted'",
        "rejected": "SELECT COUNT(*) FROM applications WHERE status='Rejected'",
        "accepted": "SELECT COUNT(*) FROM applications WHERE status='Accepted'",
        "interviews": "SELECT COUNT(*) FROM interviews",
    }.items():
        c.execute(q); stats[key] = c.fetchone()[0]
    conn.close()
    return stats


#conn = get_conn()
#c = conn.cursor()
#values = c.execute("SELECT * FROM users")
#conn.commit()
#print(values.fetchall())

print("Database initialized.")

