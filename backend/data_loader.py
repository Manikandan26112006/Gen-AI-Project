"""
Role-aware data loader.
Each function returns only the data the caller is authorised to see.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "faculty.db")

engine = create_engine(f"sqlite:///{DB_PATH}")

# ── base query (join faculty + kpi + scores) ─────────────────────────────────
_BASE_SQL = """
    SELECT
        f.faculty_id, f.name, f.department, f.designation,
        k.publications, k.scie_scopus, k.conferences, k.books,
        k.fdp_sttp, k.nptel, k.workshops_organized, k.industrial_training,
        k.consultancy_projects, k.research_funding, k.patents,
        k.institutional_activities, k.feedback_score, k.year,
        s.performance_score, s.performance_level
    FROM faculty f
    JOIN kpi     k ON f.faculty_id = k.faculty_id
    JOIN scores  s ON f.faculty_id = s.faculty_id
"""

def load_all_data() -> pd.DataFrame:
    """Principal / Admin – see everything."""
    return pd.read_sql(_BASE_SQL, engine)


def load_department_data(department: str) -> pd.DataFrame:
    """HOD – see only their department."""
    sql = _BASE_SQL + " WHERE f.department = :dept"
    return pd.read_sql(text(sql), engine, params={"dept": department})


def load_faculty_data(faculty_id: int) -> pd.DataFrame:
    """Faculty – see only their own row."""
    sql = _BASE_SQL + " WHERE f.faculty_id = :fid"
    return pd.read_sql(text(sql), engine, params={"fid": faculty_id})


def get_department_list() -> list:
    """Return all distinct departments."""
    df = pd.read_sql("SELECT DISTINCT department FROM faculty ORDER BY department", engine)
    return df["department"].tolist()


def get_faculty_list_for_dept(department: str) -> pd.DataFrame:
    """Return faculty names and IDs for a given department."""
    sql = "SELECT faculty_id, name FROM faculty WHERE department = :dept ORDER BY name"
    return pd.read_sql(text(sql), engine, params={"dept": department})