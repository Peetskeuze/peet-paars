import sqlite3
from pathlib import Path

DB_PATH = Path("peet_coach.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS profile (
        id INTEGER PRIMARY KEY,
        sex TEXT,
        age INTEGER,
        height INTEGER,
        current_weight REAL,
        target_weight REAL,
        weeks_to_goal INTEGER,
        kcal_target INTEGER
    )
    """)

    conn.commit()
    conn.close()


def save_profile(profile):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM profile")

    cur.execute("""
    INSERT INTO profile
    (sex, age, height, current_weight, target_weight, weeks_to_goal, kcal_target)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        profile.get("sex"),
        profile.get("age"),
        profile.get("height"),
        profile.get("current_weight"),
        profile.get("target_weight"),
        profile.get("weeks_to_goal"),
        profile.get("kcal_target"),
    ))

    conn.commit()
    conn.close()


def load_profile():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT sex, age, height, current_weight, target_weight, weeks_to_goal, kcal_target FROM profile LIMIT 1")

    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "sex": row[0],
        "age": row[1],
        "height": row[2],
        "current_weight": row[3],
        "target_weight": row[4],
        "weeks_to_goal": row[5],
        "kcal_target": row[6],
    }