from datetime import datetime

from app.validation import validate_appointment


def test_valid_data_has_no_errors(valid_payload):
    clean, errors = validate_appointment(valid_payload)
    assert errors == {}
    assert clean["patient_name"] == "Test Patient"


def test_name_is_trimmed(valid_payload):
    valid_payload["patient_name"] = "   Test Patient  "
    clean, _ = validate_appointment(valid_payload)
    assert clean["patient_name"] == "Test Patient"


def test_missing_fields_are_reported():
    _, errors = validate_appointment({})
    assert {"patient_name", "appointment_time", "doctor", "appointment_type"} <= set(errors)


def test_blank_name_rejected(valid_payload):
    valid_payload["patient_name"] = "   "
    assert "patient_name" in validate_appointment(valid_payload)[1]


def test_overlong_name_rejected(valid_payload):
    valid_payload["patient_name"] = "x" * 101
    assert "patient_name" in validate_appointment(valid_payload)[1]


def test_bad_datetime_rejected(valid_payload):
    for bad in ["tomorrow", "2026-13-40T10:00", "2026-11-05", ""]:
        valid_payload["appointment_time"] = bad
        assert "appointment_time" in validate_appointment(valid_payload)[1], bad


def test_unknown_doctor_type_status_rejected(valid_payload):
    valid_payload.update(doctor="Dr. Nobody", appointment_type="Magic", status="Maybe")
    errors = validate_appointment(valid_payload)[1]
    assert {"doctor", "appointment_type", "status"} <= set(errors)


def test_status_defaults_to_scheduled(valid_payload):
    del valid_payload["status"]
    clean, errors = validate_appointment(valid_payload)
    assert errors == {} and clean["status"] == "Scheduled"


def test_non_dict_body_rejected():
    assert "_" in validate_appointment(["not", "a", "dict"])[1]

FIXED_NOW = datetime(2026, 6, 1, 12, 0)


def test_past_scheduled_rejected(valid_payload):
    valid_payload["appointment_time"] = "2026-06-01T11:59"
    assert "appointment_time" in validate_appointment(valid_payload, now=FIXED_NOW)[1]


def test_future_scheduled_accepted(valid_payload):
    valid_payload["appointment_time"] = "2026-06-01T12:01"
    assert validate_appointment(valid_payload, now=FIXED_NOW)[1] == {}


def test_past_allowed_for_non_scheduled_statuses(valid_payload):
    valid_payload["appointment_time"] = "2026-05-01T09:00"
    for status in ["Completed", "No-show", "Cancelled"]:
        valid_payload["status"] = status
        assert validate_appointment(valid_payload, now=FIXED_NOW)[1] == {}, status
