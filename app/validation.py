"""Input validation, kept separate from routes so it is easy to unit test."""
from datetime import datetime

APPOINTMENT_TYPES = ["Consultation", "Follow-up", "Check-up", "Vaccination", "Lab Test"]
STATUSES = ["Scheduled", "Completed", "Cancelled", "No-show"]
DOCTORS = ["Dr. Amal Perera", "Dr. Nimali Silva", "Dr. Kasun Fernando", "Dr. Ishara Jayasuriya"]

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
MAX_NAME_LENGTH = 100


def validate_appointment(data, now=None):
    """Return (clean_data, errors). `errors` maps field name -> message.

    `now` can be passed in so tests don't depend on the real clock.
    """
    now = now or datetime.now()
    if not isinstance(data, dict):
        return {}, {"_": "Request body must be a JSON object."}

    errors = {}
    clean = {}

    name = str(data.get("patient_name", "")).strip()
    if not name:
        errors["patient_name"] = "Patient name is required."
    elif len(name) > MAX_NAME_LENGTH:
        errors["patient_name"] = f"Patient name must be {MAX_NAME_LENGTH} characters or fewer."
    clean["patient_name"] = name

    when = str(data.get("appointment_time", "")).strip()
    parsed_time = None
    try:
        parsed_time = datetime.strptime(when, DATETIME_FORMAT)
    except ValueError:
        errors["appointment_time"] = "Date and time must look like 2026-11-05T14:30."
    clean["appointment_time"] = when

    doctor = str(data.get("doctor", "")).strip()
    if not doctor:
        errors["doctor"] = "Doctor is required."
    elif doctor not in DOCTORS:
        errors["doctor"] = "Choose a doctor from the list."
    clean["doctor"] = doctor

    appt_type = str(data.get("appointment_type", "")).strip()
    if appt_type not in APPOINTMENT_TYPES:
        errors["appointment_type"] = f"Type must be one of: {', '.join(APPOINTMENT_TYPES)}."
    clean["appointment_type"] = appt_type

    status = str(data.get("status", "Scheduled")).strip() or "Scheduled"
    if status not in STATUSES:
        errors["status"] = f"Status must be one of: {', '.join(STATUSES)}."
    clean["status"] = status

        # Business rule: a still-"Scheduled" appointment must be in the future.
    # Past dates are fine for records that already happened (Completed, No-show, Cancelled).
    if (parsed_time and clean["status"] == "Scheduled" and parsed_time < now
            and "appointment_time" not in errors):
        errors["appointment_time"] = (
            "A scheduled appointment must be in the future. "
            "Pick a later time, or set the status to Completed, No-show or Cancelled."
        )

    return clean, errors
