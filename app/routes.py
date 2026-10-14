"""REST API + the single HTML page."""
from flask import Blueprint, current_app, jsonify, request, send_from_directory

from .db import get_db
from .validation import (APPOINTMENT_TYPES, DOCTORS, STATUSES,
                         validate_appointment)

bp = Blueprint("appointments", __name__)

COLUMNS = "id, patient_name, appointment_time, doctor, appointment_type, status"


def _row_to_dict(row):
    return {k: row[k] for k in row.keys()}


def _error(message, status=400, fields=None):
    body = {"error": message}
    if fields:
        body["fields"] = fields
    return jsonify(body), status


def _doctor_is_busy(doctor, when, ignore_id=None):
    """A doctor can't have two active (non-cancelled) appointments at the same time."""
    sql = ("SELECT 1 FROM appointments WHERE doctor = ? AND appointment_time = ? "
           "AND status != 'Cancelled'")
    params = [doctor, when]
    if ignore_id is not None:
        sql += " AND id != ?"
        params.append(ignore_id)
    return get_db().execute(sql, params).fetchone() is not None


def _conflict():
    return _error("That doctor already has an appointment at this time.", 409,
                  {"appointment_time": "Doctor is already booked at this time."})


@bp.get("/")
def index():
    return send_from_directory(current_app.static_folder, "index.html")


@bp.get("/api/meta")
def meta():
    return jsonify(doctors=DOCTORS, types=APPOINTMENT_TYPES, statuses=STATUSES)


@bp.get("/api/appointments")
def list_appointments():
    """Optional filters: search, status, doctor, type, date_from, date_to."""
    clauses, params = [], []

    search = request.args.get("search", "").strip()
    if search:
        clauses.append("patient_name LIKE ?")
        params.append(f"%{search}%")
    for arg, column in (("status", "status"), ("doctor", "doctor"),
                        ("type", "appointment_type")):
        value = request.args.get(arg, "").strip()
        if value:
            clauses.append(f"{column} = ?")  # column names are hard-coded above, values are bound
            params.append(value)
    if request.args.get("date_from"):
        clauses.append("appointment_time >= ?")
        params.append(request.args["date_from"] + "T00:00")
    if request.args.get("date_to"):
        clauses.append("appointment_time <= ?")
        params.append(request.args["date_to"] + "T23:59")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = get_db().execute(
        f"SELECT {COLUMNS} FROM appointments {where} ORDER BY appointment_time ASC",
        params,
    ).fetchall()
    return jsonify([_row_to_dict(r) for r in rows])


@bp.get("/api/appointments/<int:appt_id>")
def get_appointment(appt_id):
    row = get_db().execute(
        f"SELECT {COLUMNS} FROM appointments WHERE id = ?", (appt_id,)
    ).fetchone()
    if row is None:
        return _error("Appointment not found.", 404)
    return jsonify(_row_to_dict(row))


@bp.post("/api/appointments")
def create_appointment():
    clean, errors = validate_appointment(request.get_json(silent=True))
    if errors:
        return _error("Validation failed.", 400, errors)
    if clean["status"] != "Cancelled" and _doctor_is_busy(clean["doctor"], clean["appointment_time"]):
        return _conflict()

    db = get_db()
    cur = db.execute(
        "INSERT INTO appointments (patient_name, appointment_time, doctor, appointment_type, status) "
        "VALUES (:patient_name, :appointment_time, :doctor, :appointment_type, :status)",
        clean,
    )
    db.commit()
    return jsonify({"id": cur.lastrowid, **clean}), 201


@bp.put("/api/appointments/<int:appt_id>")
def update_appointment(appt_id):
    db = get_db()
    if db.execute("SELECT 1 FROM appointments WHERE id = ?", (appt_id,)).fetchone() is None:
        return _error("Appointment not found.", 404)

    clean, errors = validate_appointment(request.get_json(silent=True))
    if errors:
        return _error("Validation failed.", 400, errors)
    if clean["status"] != "Cancelled" and _doctor_is_busy(
            clean["doctor"], clean["appointment_time"], ignore_id=appt_id):
        return _conflict()

    db.execute(
        "UPDATE appointments SET patient_name=:patient_name, appointment_time=:appointment_time, "
        "doctor=:doctor, appointment_type=:appointment_type, status=:status WHERE id=:id",
        {**clean, "id": appt_id},
    )
    db.commit()
    return jsonify({"id": appt_id, **clean})


@bp.delete("/api/appointments/<int:appt_id>")
def delete_appointment(appt_id):
    db = get_db()
    cur = db.execute("DELETE FROM appointments WHERE id = ?", (appt_id,))
    db.commit()
    if cur.rowcount == 0:
        return _error("Appointment not found.", 404)
    return "", 204
