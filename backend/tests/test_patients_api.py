"""
tests/test_patients_api.py
--------------------------
Integration tests for the /patients CRUD endpoints.
"""

import pytest
import uuid

@pytest.mark.asyncio
async def test_root_endpoint(client):
    res = await client.get("/")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["error"] is None
    assert res_json["data"]["status"] == "ok"
    assert res_json["data"]["health_check"] == "/health"

@pytest.mark.asyncio
async def test_health_check(client):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"data": {"status": "ok"}, "error": None}

@pytest.mark.asyncio
async def test_swagger_docs_endpoint(client):
    res = await client.get("/docs")
    assert res.status_code == 200

@pytest.mark.asyncio
async def test_unknown_route_returns_envelope_404(client):
    res = await client.get("/nonexistent-page")
    assert res.status_code == 404
    assert res.json() == {"data": None, "error": "Not Found"}

@pytest.mark.asyncio
async def test_patient_full_lifecycle(client):
    # 1. Create Patient
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1985-10-20",
        "sex": "male",
        "phone_number": "+15559876543",
        "email": "test.user@example.com",
        "address_line_1": "100 Test Blvd",
        "city": "Dallas",
        "state": "TX",
        "zip_code": "75001",
        "insurance_provider": "Cigna",
        "insurance_member_id": "CG12345",
        "preferred_language": "English"
    }
    res = await client.post("/patients", json=payload)
    assert res.status_code == 201
    res_json = res.json()
    assert res_json["error"] is None
    patient = res_json["data"]
    patient_id = patient["id"]
    assert patient["first_name"] == "Test"
    assert patient["last_name"] == "User"

    # 2. Get Patient by ID
    res = await client.get(f"/patients/{patient_id}")
    assert res.status_code == 200
    assert res.json()["data"]["id"] == patient_id

    # 3. Filter query
    res = await client.get("/patients?last_name=user")
    assert res.status_code == 200
    ids = [p["id"] for p in res.json()["data"]]
    assert patient_id in ids

    # 4. Partial update
    res = await client.put(f"/patients/{patient_id}", json={"city": "Plano"})
    assert res.status_code == 200
    assert res.json()["data"]["city"] == "Plano"
    assert res.json()["data"]["first_name"] == "Test"

    # 5. Empty update rejected
    res = await client.put(f"/patients/{patient_id}", json={})
    assert res.status_code == 422
    assert "Validation failed:" in res.json()["error"]

    # 6. Soft Delete
    res = await client.delete(f"/patients/{patient_id}")
    assert res.status_code == 200
    assert res.json() == {"data": {"deleted": True, "id": patient_id}, "error": None}

    # 7. Get deleted -> 404
    res = await client.get(f"/patients/{patient_id}")
    assert res.status_code == 404
    assert res.json() == {"data": None, "error": "Patient not found."}

    # 8. Excluded from query list
    res = await client.get("/patients?last_name=user")
    assert patient_id not in [p["id"] for p in res.json()["data"]]

@pytest.mark.asyncio
async def test_patient_validation_errors(client):
    # Missing required field
    res = await client.post("/patients", json={"first_name": "OnlyFirst"})
    assert res.status_code == 422
    assert res.json()["data"] is None
    assert "is required" in res.json()["error"]

    # Invalid state format
    bad_state = {
        "first_name": "Alice",
        "last_name": "Smith",
        "date_of_birth": "1995-01-01",
        "sex": "female",
        "phone_number": "+15551112233",
        "address_line_1": "1 Road",
        "city": "Town",
        "state": "California", # invalid length
        "zip_code": "90210"
    }
    res = await client.post("/patients", json=bad_state)
    assert res.status_code == 422
    assert "state" in res.json()["error"].lower()

    # Non-existent UUID
    random_id = str(uuid.uuid4())
    res = await client.get(f"/patients/{random_id}")
    assert res.status_code == 404
    assert res.json() == {"data": None, "error": "Patient not found."}
