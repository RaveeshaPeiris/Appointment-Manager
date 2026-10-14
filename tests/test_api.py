def create(client, payload, **overrides):
    return client.post("/api/appointments", json={**payload, **overrides})


def test_index_page_loads(client):
    assert client.get("/").status_code == 200


def test_create_and_get(client, valid_payload):
    res = create(client, valid_payload)
    assert res.status_code == 201
    new_id = res.get_json()["id"]
    got = client.get(f"/api/appointments/{new_id}")
    assert got.status_code == 200
    assert got.get_json()["patient_name"] == "Test Patient"


def test_create_invalid_returns_400_with_field_errors(client, valid_payload):
    res = create(client, valid_payload, patient_name="")
    assert res.status_code == 400
    assert "patient_name" in res.get_json()["fields"]


def test_create_without_json_returns_400(client):
    assert client.post("/api/appointments", data="nope").status_code == 400


def test_list_is_sorted_by_time(client, valid_payload):
    create(client, valid_payload, appointment_time="2026-11-06T10:00")
    create(client, valid_payload, appointment_time="2026-11-05T09:00")
    times = [a["appointment_time"] for a in client.get("/api/appointments").get_json()]
    assert times == sorted(times)


def test_update(client, valid_payload):
    new_id = create(client, valid_payload).get_json()["id"]
    res = client.put(f"/api/appointments/{new_id}", json={**valid_payload, "status": "Completed"})
    assert res.status_code == 200
    assert client.get(f"/api/appointments/{new_id}").get_json()["status"] == "Completed"


def test_update_missing_returns_404(client, valid_payload):
    assert client.put("/api/appointments/999", json=valid_payload).status_code == 404


def test_update_validates(client, valid_payload):
    new_id = create(client, valid_payload).get_json()["id"]
    res = client.put(f"/api/appointments/{new_id}", json={**valid_payload, "doctor": "Nobody"})
    assert res.status_code == 400


def test_delete(client, valid_payload):
    new_id = create(client, valid_payload).get_json()["id"]
    assert client.delete(f"/api/appointments/{new_id}").status_code == 204
    assert client.get(f"/api/appointments/{new_id}").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/api/appointments/999").status_code == 404


def test_double_booking_blocked(client, valid_payload):
    assert create(client, valid_payload).status_code == 201
    res = create(client, valid_payload, patient_name="Someone Else")
    assert res.status_code == 409


def test_same_time_different_doctor_allowed(client, valid_payload):
    create(client, valid_payload)
    assert create(client, valid_payload, doctor="Dr. Nimali Silva").status_code == 201


def test_cancelled_slot_can_be_rebooked(client, valid_payload):
    create(client, valid_payload, status="Cancelled")
    assert create(client, valid_payload).status_code == 201


def test_editing_without_changing_time_is_not_a_conflict(client, valid_payload):
    new_id = create(client, valid_payload).get_json()["id"]
    res = client.put(f"/api/appointments/{new_id}", json={**valid_payload, "patient_name": "Renamed"})
    assert res.status_code == 200


def test_search_and_filters(client, valid_payload):
    create(client, valid_payload, patient_name="Alice Example", appointment_time="2026-11-01T09:00")
    create(client, valid_payload, patient_name="Bob Sample", doctor="Dr. Nimali Silva",
           appointment_time="2026-11-10T09:00", status="Completed", appointment_type="Check-up")

    def names(query):
        return [a["patient_name"] for a in client.get(f"/api/appointments?{query}").get_json()]

    assert names("search=ali") == ["Alice Example"]
    assert names("status=Completed") == ["Bob Sample"]
    assert names("doctor=Dr. Nimali Silva") == ["Bob Sample"]
    assert names("type=Check-up") == ["Bob Sample"]
    assert names("date_from=2026-11-05") == ["Bob Sample"]
    assert names("date_to=2026-11-05") == ["Alice Example"]
    assert names("search=ali&status=Completed") == []


def test_sql_injection_attempt_is_harmless(client, valid_payload):
    create(client, valid_payload)
    res = client.get("/api/appointments?search=' OR '1'='1")
    assert res.status_code == 200 and res.get_json() == []


def test_meta_endpoint(client):
    data = client.get("/api/meta").get_json()
    assert {"doctors", "types", "statuses"} <= set(data)
