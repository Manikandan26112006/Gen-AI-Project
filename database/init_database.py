"""
Faculty Performance AI System – Database Initializer
Builds faculty, kpi, scores and users tables with realistic sample data.
9 Departments × 11 Faculty = 99 Faculty Members
Run once from the project root:
    python database/init_database.py
"""

import sys, os, random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from backend.score_calculator import calculate_score, classify_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "faculty.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
DEPARTMENTS = ["CSE", "ECE", "ME", "CIVIL", "EEE", "IT", "AIDS", "CSBS", "BME"]

DESIGNATIONS = ["Professor", "Associate Professor", "Assistant Professor"]

# Faculty names pool per department (11 per dept = 99 total)
FACULTY_NAMES = {
    "CSE": [
        "Dr. Arun Kumar", "Dr. Priya Vijayan", "Prof. Santhosh Babu",
        "Dr. Meena Krishnamurthy", "Dr. Kavitha Rajan", "Prof. Nikhil Sharma",
        "Dr. Sowmya Devi", "Prof. Harish Mohan", "Dr. Revathi Sundaram",
        "Prof. Ganesh Venkat", "Dr. Pooja Narayan",
    ],
    "ECE": [
        "Dr. Ramesh Nair", "Dr. Lakshmi Pradeep", "Prof. Arjun Menon",
        "Dr. Suresh Babu", "Prof. Nithya Krishnan", "Dr. Manoj Kumar",
        "Prof. Saravanan Pillai", "Dr. Jaya Lakshmi", "Prof. Dinesh Raman",
        "Dr. Asha Kumari", "Prof. Vignesh Selvam",
    ],
    "ME": [
        "Dr. Deepa Anand", "Prof. Karthik Rajan", "Dr. Sunita Varma",
        "Prof. Rajkumar Singh", "Dr. Bhavani Shankar", "Prof. Mohan Das",
        "Dr. Prema Kumari", "Prof. Aravind Swamy", "Dr. Geetha Rani",
        "Prof. Subramaniam Iyer", "Dr. Padma Priya",
    ],
    "CIVIL": [
        "Dr. Anand Pillai", "Prof. Divya Menon", "Dr. Sridhar Rao",
        "Prof. Vasanthi Devi", "Dr. Prakash Kumar", "Prof. Malathi Sundaram",
        "Dr. Kumaran Nair", "Prof. Indira Gandhi", "Dr. Balaji Raman",
        "Prof. Shanthi Priya", "Dr. Nagarajan Iyer",
    ],
    "EEE": [
        "Dr. Ravi Shankar", "Prof. Sheela Thomas", "Dr. Murali Krishnan",
        "Prof. Anitha Balan", "Dr. Vijay Kumar", "Prof. Saranya Devi",
        "Dr. Pandian Raju", "Prof. Kamala Rani", "Dr. Senthil Nathan",
        "Prof. Banu Priya", "Dr. Thirumal Selvam",
    ],
    "IT": [
        "Dr. Rajesh Kannan", "Prof. Anjali Menon", "Dr. Vikram Subramani",
        "Prof. Lavanya Rajan", "Dr. Sathish Kumar", "Prof. Deepika Nair",
        "Dr. Gopal Krishnan", "Prof. Meenakshi Amma", "Dr. Ashwin Ravi",
        "Prof. Sangeetha Devi", "Dr. Hari Prasad",
    ],
    "AIDS": [
        "Dr. Karthikeyan Murugan", "Prof. Swathi Reddy", "Dr. Naveen Raj",
        "Prof. Dhanalakshmi Pillai", "Dr. Akilesh Kumar", "Prof. Rekha Sharma",
        "Dr. Sivakumar Rangan", "Prof. Mythili Devi", "Dr. Prasanna Venkat",
        "Prof. Janani Krishnan", "Dr. Logesh Babu",
    ],
    "CSBS": [
        "Dr. Ramya Chandran", "Prof. Kishore Rajan", "Dr. Nandhini Priya",
        "Prof. Senthil Murugan", "Dr. Abinaya Devi", "Prof. Manikandan Iyer",
        "Dr. Thenmozhi Rani", "Prof. Arun Prasad", "Dr. Suganya Lakshmi",
        "Prof. Bharathi Kumari", "Dr. Velu Nachiyar",
    ],
    "BME": [
        "Dr. Gayathri Sundaram", "Prof. Raghu Raman", "Dr. Nirmala Devi",
        "Prof. Chandrasekhar Rao", "Dr. Vanitha Kumari", "Prof. Siva Prakash",
        "Dr. Usha Rani", "Prof. Mohanraj Kumar", "Dr. Kalaiselvi Devi",
        "Prof. Srinivasan Pillai", "Dr. Hema Malini",
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# 1.  FACULTY TABLE
# ─────────────────────────────────────────────────────────────────────────────
faculty_rows = []
fid = 1
for dept in DEPARTMENTS:
    names = FACULTY_NAMES[dept]
    for i, name in enumerate(names):
        # Cycle through designations: first few are Professors, etc.
        if i < 3:
            desig = "Professor"
        elif i < 6:
            desig = "Associate Professor"
        else:
            desig = "Assistant Professor"
        faculty_rows.append((fid, name, dept, desig, f"faculty{fid}"))
        fid += 1

faculty_df = pd.DataFrame(faculty_rows,
    columns=["faculty_id", "name", "department", "designation", "username"])

# ─────────────────────────────────────────────────────────────────────────────
# 2.  KPI & SCORE TABLE (Generated with Dynamic Unique Bins)
# ─────────────────────────────────────────────────────────────────────────────
random.seed(42)  # Reproducible

kpi_rows = []
score_rows = []

for dept in DEPARTMENTS:
    dept_faculty = faculty_df[faculty_df["department"] == dept]
    
    # 11 distinct unique scores per department:
    # 2 above 90%
    b1 = [round(random.uniform(91.0, 99.0), 1) for _ in range(2)]
    # 4 above 76% (76 - 90)
    b2 = [round(random.uniform(76.1, 89.9), 1) for _ in range(4)]
    # 3 mid-range above 45 (45 - 75)
    b3 = [round(random.uniform(45.1, 75.0), 1) for _ in range(3)]
    # 2 needs improvement (< 45)
    b4 = [round(random.uniform(32.0, 44.9), 1) for _ in range(2)]
    
    dept_scores = sorted(b1 + b2 + b3 + b4, reverse=True)
    
    for i, (_, frow) in enumerate(dept_faculty.iterrows()):
        fid = frow["faculty_id"]
        target_score = dept_scores[i]
        r = target_score / 100.0

        # Construct realistic KPI footprints mathematically mimicking the final score
        pub = round(15 * r)
        sci = round(10 * r)
        conf = round(10 * r)
        books = round(5 * r)
        fdp = round(8 * r)
        nptel = round(6 * r)
        ws = round(5 * r)
        ind = round(4 * r)
        cons = round(6 * r)
        fund = round(6 * r)
        pat = round(5 * r)
        inst = round(10 * r)
        fb = round(5.0 * r, 1)

        kpi_rows.append((fid, pub, sci, conf, books, fdp, nptel, ws, ind, cons, fund, pat, inst, fb, 2024))
        
        level = classify_score(target_score)
        score_rows.append({
            "faculty_id": fid,
            "performance_score": target_score,
            "performance_level": level,
            "year": 2024
        })

kpi_df = pd.DataFrame(kpi_rows, columns=[
    "faculty_id", "publications", "scie_scopus", "conferences", "books",
    "fdp_sttp", "nptel", "workshops_organized", "industrial_training",
    "consultancy_projects", "research_funding", "patents", "institutional_activities",
    "feedback_score", "year"
])

score_df = pd.DataFrame(score_rows)

# ─────────────────────────────────────────────────────────────────────────────
# 4.  USERS TABLE  (simple numbered usernames, all password = 1234)
# ─────────────────────────────────────────────────────────────────────────────
users_rows = [
    # Principal & Admin
    ("principal", "1234", "Principal", None, None),
    ("admin",     "1234", "Admin",     None, None),
]

# HODs – first faculty (Professor) in each department
hod_num = 1
for dept in DEPARTMENTS:
    dept_faculty = faculty_df[faculty_df["department"] == dept].iloc[0]
    users_rows.append((f"hod{hod_num}", "1234", "HOD", int(dept_faculty["faculty_id"]), dept))
    hod_num += 1

# Faculty logins
for _, frow in faculty_df.iterrows():
    users_rows.append((f"faculty{frow['faculty_id']}", "1234", "Faculty", int(frow["faculty_id"]), frow["department"]))

users_df = pd.DataFrame(users_rows,
    columns=["username", "password", "role", "faculty_id", "department"])

# ─────────────────────────────────────────────────────────────────────────────
# 5.  CERTIFICATES TABLE (create structure)
# ─────────────────────────────────────────────────────────────────────────────
# We create the table if it doesn't exist but don't populate it
cert_create_sql = """
CREATE TABLE IF NOT EXISTS certificates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER,
    faculty_name TEXT,
    category TEXT,
    content TEXT,
    file_path TEXT DEFAULT '',
    ai_analysis TEXT DEFAULT '',
    status TEXT DEFAULT 'Pending',
    admin_reason TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# ─────────────────────────────────────────────────────────────────────────────
# 6.  WRITE TO DB
# ─────────────────────────────────────────────────────────────────────────────
faculty_df.to_sql("faculty", engine, if_exists="replace", index=False)
kpi_df.to_sql("kpi",         engine, if_exists="replace", index=False)
score_df.to_sql("scores",    engine, if_exists="replace", index=False)
users_df.to_sql("users",     engine, if_exists="replace", index=False)

with engine.connect() as conn:
    conn.execute(text(cert_create_sql))
    conn.commit()

# ─────────────────────────────────────────────────────────────────────────────
# 7.  SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 60)
print("[OK] Database initialized successfully!")
print("=" * 60)
print(f"  Faculty   : {len(faculty_df)} records")
print(f"  KPI       : {len(kpi_df)} records")
print(f"  Scores    : {len(score_df)} records")
print(f"  Users     : {len(users_df)} records")
print(f"  Departments: {len(DEPARTMENTS)} → {', '.join(DEPARTMENTS)}")
print()
print("Faculty per Department:")
for dept in DEPARTMENTS:
    count = len(faculty_df[faculty_df["department"] == dept])
    print(f"  {dept:6} → {count} faculty")
print()
print("Login Credentials (ALL passwords = 1234):")
print("  Principal  → username: principal")
print("  Admin      → username: admin")
for i, dept in enumerate(DEPARTMENTS, 1):
    print(f"  HOD ({dept:5}) → username: hod{i}")
print(f"  Faculty    → username: faculty1 .. faculty{len(faculty_df)}")
print("=" * 60)