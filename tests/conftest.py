import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


@pytest.fixture
def valid_payload():
    return {
        "patient_name": "Test Patient",
        "appointment_time": "2026-11-05T14:30",
        "doctor": "Dr. Amal Perera",
        "appointment_type": "Consultation",
        "status": "Scheduled",
    }
