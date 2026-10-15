from datetime import datetime, timedelta

import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()

def days_from_now(days, hour=10, minute=0):
    """Return an appointment-time string `days` from today (negative = past)."""
    d = datetime.now() + timedelta(days=days)
    return d.replace(hour=hour, minute=minute, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M")


@pytest.fixture
def valid_payload():
    return {
        "patient_name": "Test Patient",
        "appointment_time": days_from_now(30),
        "doctor": "Dr. Amal Perera",
        "appointment_type": "Consultation",
        "status": "Scheduled",
    }
