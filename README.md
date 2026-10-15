# Appointment Manager

A small web app for managing clinic appointments: create, view, edit, delete, search and filter.
All sample data is **fictional**.

## Tech stack and why

| Part | Choice | Reason |
|------|--------|--------|
| Backend | Python 3 + Flask | Small, readable, easy to run and review |
| Database | SQLite (standard library `sqlite3`) | Zero setup; file-based; fine for this scope |
| Frontend | Plain HTML, CSS, JavaScript | No build step; the app is one page |
| Tests | pytest | Simple API tests using Flask's test client |

## Run it

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python seed.py                  # optional: adds 6 fictional appointments
python run.py                   # open http://127.0.0.1:5000
```

## Run the tests

```bash
python -m pytest -v
```

Tests use a temporary database, so they never touch your real data.

## Features

- **Create / Edit** an appointment in a dialog (patient name, date and time, doctor, type, status)
- **View** all appointments, sorted by date and time
- **Delete** with a confirmation step
- **Search** by patient name, and **filter** by doctor, type, status and date range (filters combine)
- Validation on both client (quick feedback) and server (authoritative)
- **Double-booking protection:** a doctor cannot have two non-cancelled appointments at the same time (HTTP 409)
- **No past bookings:** a *Scheduled* appointment must be in the future. Past dates are still allowed for records that already happened (Completed, No-show, Cancelled)

## Project structure

```
app/
  __init__.py     app factory
  db.py           SQLite connection + schema
  validation.py   input validation (pure functions, unit tested)
  routes.py       REST API and the page route
  static/         index.html, styles.css, app.js
tests/            validation tests + API tests
seed.py           fictional sample data
run.py            dev server entry point
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/appointments?search=&doctor=&type=&status=&date_from=&date_to=` | List (all filters optional) |
| GET | `/api/appointments/<id>` | One appointment |
| POST | `/api/appointments` | Create (201, or 400 / 409) |
| PUT | `/api/appointments/<id>` | Update (200, or 400 / 404 / 409) |
| DELETE | `/api/appointments/<id>` | Delete (204, or 404) |
| GET | `/api/meta` | Doctors, types and statuses for the dropdowns |

Appointment JSON:

```json
{ "id": 1, "patient_name": "Sample Patient One", "appointment_time": "2026-11-05T14:30",
  "doctor": "Dr. Amal Perera", "appointment_type": "Consultation", "status": "Scheduled" }
```

## Design decisions

- **Validation is separate from routes** so it can be unit tested without HTTP.
- **Parameterised SQL everywhere**; user input is never concatenated into queries
  (there is a test for an injection attempt).
- **Dates stored as ISO text** (`YYYY-MM-DDTHH:MM`): sorts correctly as text, no timezone handling needed for a single clinic.
- **Doctors, types and statuses live in one place** (`validation.py`) and are served to the UI via `/api/meta`, so the UI and server cannot drift apart.
- **Frontend escapes all text** before inserting it into the page, so a patient name can't inject HTML.

## How I used AI

I used Claude to generate the first version of the code, then reviewed it myself.

**What I asked AI to do:** scaffold the Flask app, write the REST API, build the UI, and draft tests.

**What I checked and corrected:**
- First test run had one failing test because the frontend file didn't exist yet. I confirmed the failure was genuine, added the page, and re-ran: 26/26 pass.
- Checked every SQL statement for injection risk. Filter column names are hard-coded; only values are user-supplied and bound as parameters.
- Checked that editing an appointment without changing its time is not flagged as a double-booking (needed an `ignore_id`).
- Checked that a cancelled slot can be rebooked.
- Manually tried the UI: create, edit, delete, each filter, empty state, validation errors.
- Spotted myself that appointments could be scheduled in the past, and added a rule: Scheduled must be in the future, other statuses may be in the past. I also rewrote the tests to use dates relative to today, because hard-coded dates would start failing once they passed.

## Known limitations / next steps

- No login or user roles (a real clinic system would need authentication and audit logging)
- Doctors are a fixed list, not a managed table
- No pagination (fine for a small dataset)
- No UI-level automated tests (e.g. Playwright)
