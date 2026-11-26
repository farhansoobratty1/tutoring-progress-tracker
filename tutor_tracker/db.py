"""SQLite storage: students, topics and the scores recorded against them."""
import sqlite3
from datetime import date

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    year_group  TEXT NOT NULL,
    subject     TEXT NOT NULL,          -- matches a subject in questions.json, e.g. "GCSE Maths"
    target      INTEGER NOT NULL DEFAULT 70
);

CREATE TABLE IF NOT EXISTS scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    topic       TEXT NOT NULL,
    marks       REAL NOT NULL CHECK (marks >= 0),
    out_of      REAL NOT NULL CHECK (out_of > 0),
    taken_on    TEXT NOT NULL,          -- ISO date
    note        TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_scores_student ON scores(student_id, topic, taken_on);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    get_db().executescript(SCHEMA)


# --- queries -----------------------------------------------------------------

def list_students():
    return get_db().execute("SELECT * FROM students ORDER BY name").fetchall()


def get_student(student_id):
    return get_db().execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()


def add_student(name, year_group, subject, target=70):
    db = get_db()
    cur = db.execute(
        "INSERT INTO students (name, year_group, subject, target) VALUES (?, ?, ?, ?)",
        (name.strip(), year_group.strip(), subject, int(target)),
    )
    db.commit()
    return cur.lastrowid


def add_score(student_id, topic, marks, out_of, taken_on=None, note=""):
    if out_of <= 0 or marks < 0 or marks > out_of:
        raise ValueError("marks must be between 0 and out_of, and out_of must be positive")
    db = get_db()
    db.execute(
        "INSERT INTO scores (student_id, topic, marks, out_of, taken_on, note) VALUES (?, ?, ?, ?, ?, ?)",
        (student_id, topic, marks, out_of, taken_on or date.today().isoformat(), note.strip()),
    )
    db.commit()


def scores_for(student_id):
    """All of a student's scores, oldest first, with the percentage worked out."""
    rows = get_db().execute(
        "SELECT topic, marks, out_of, taken_on, note FROM scores WHERE student_id = ? ORDER BY taken_on, id",
        (student_id,),
    ).fetchall()
    return [
        {"topic": r["topic"], "percent": round(100 * r["marks"] / r["out_of"], 1),
         "marks": r["marks"], "out_of": r["out_of"], "taken_on": r["taken_on"], "note": r["note"]}
        for r in rows
    ]
