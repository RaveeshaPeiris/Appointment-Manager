"""Fill the database with FICTIONAL sample appointments: python seed.py"""
from datetime import datetime, timedelta

from app import create_app
from app.db import get_db

SAMPLES = [
    ("Sample Patient One", 1, 9, 0, "Dr. Amal Perera", "Consultation", "Scheduled"),
    ("Sample Patient Two", 1, 10, 30, "Dr. Nimali Silva", "Check-up", "Scheduled"),
    ("Sample Patient Three", 2, 14, 0, "Dr. Kasun Fernando", "Vaccination", "Scheduled"),
    ("Sample Patient Four", -3, 11, 0, "Dr. Amal Perera", "Follow-up", "Completed"),
    ("Sample Patient Five", -1, 15, 30, "Dr. Ishara Jayasuriya", "Lab Test", "No-show"),
    ("Sample Patient Six", 4, 8, 30, "Dr. Nimali Silva", "Consultation", "Cancelled"),
]

app = create_app()
with app.app_context():
    db = get_db()
    if db.execute("SELECT COUNT(*) FROM appointments").fetchone()[0] == 0:
        today = datetime.now().replace(second=0, microsecond=0)
        for name, days, hour, minute, doctor, kind, status in SAMPLES:
            when = (today + timedelta(days=days)).replace(hour=hour, minute=minute)
            db.execute(
                "INSERT INTO appointments (patient_name, appointment_time, doctor, appointment_type, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, when.strftime("%Y-%m-%dT%H:%M"), doctor, kind, status),
            )
        db.commit()
        print(f"Inserted {len(SAMPLES)} sample appointments.")
    else:
        print("Database already has data; nothing inserted.")
