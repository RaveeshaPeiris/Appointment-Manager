"""SQLite helpers. One connection per request, stored on flask.g."""
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS appointments (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name     TEXT NOT NULL,
    appointment_time TEXT NOT NULL,          -- ISO format: YYYY-MM-DDTHH:MM
    doctor           TEXT NOT NULL,
    appointment_type TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'Scheduled'
);
CREATE INDEX IF NOT EXISTS idx_appt_time ON appointments(appointment_time);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    get_db().executescript(SCHEMA)
    get_db().commit()


def init_app(app):
    app.teardown_appcontext(close_db)
