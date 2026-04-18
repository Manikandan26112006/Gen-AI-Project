"""
Authentication module – secure login with role-based session payload.
Returns a dict with role, faculty_id, faculty_name, and department.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "database", "faculty.db")

engine = create_engine(f"sqlite:///{DB_PATH}")


def authenticate(username: str, password: str) -> dict | None:
    """
    Authenticate user and return session info dict, or None on failure.

    Returned dict keys:
        role        – Principal | HOD | Faculty | Admin
        username    – login username
        faculty_id  – int or None
        faculty_name– str or None
        department  – str or None  (HOD: their dept; Faculty: their dept)
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM users WHERE username = :u AND password = :p"),
            {"u": username, "p": password}
        ).mappings().fetchone()

    if row is None:
        return None

    session = {
        "role":         row["role"],
        "username":     row["username"],
        "faculty_id":   row["faculty_id"],
        "department":   row["department"],
        "faculty_name": None,
    }

    # Resolve faculty name for Faculty / HOD roles
    if row["faculty_id"] is not None:
        with engine.connect() as conn:
            frow = conn.execute(
                text("SELECT name FROM faculty WHERE faculty_id = :fid"),
                {"fid": row["faculty_id"]}
            ).mappings().fetchone()
        if frow:
            session["faculty_name"] = frow["name"]

    return session