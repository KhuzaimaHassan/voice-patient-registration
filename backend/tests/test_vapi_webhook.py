"""
tests/test_vapi_webhook.py
--------------------------
Tests for the Vapi tool-call webhook endpoint:
  POST /vapi/register-patient
"""

import pytest
from httpx import AsyncClient

from app.config import get_settings


@pytest.fixture
def auth_headers():
    settings = get_settings()
    if settings.VAPI_WEBHOOK_SECRET:
        return {"x-vapi-secret": settings.VAPI_WEBHOOK_SECRET}
    return {}


@pytest.mark.asyncio
async def test_vapi_register_patient_success(client: AsyncClient, auth_headers: dict):
    """
    Vapi tool-call with valid arguments should create a patient in DB
    and return the exact Vapi results array shape.
    """
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_vapi_test_001",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Vapi",
                            "last_name": "Caller",
                            "date_of_birth": "1994-07-22",
                            "sex": "female",
                            "phone_number": "+15125550144",
                            "address_line_1": "100 Webhook Lane",
                            "city": "Austin",
                            "state": "TX",
                            "zip_code": "78701",
                        },
                    },
                }
            ],
        }
    }

    resp = await client.post("/vapi/register-patient", json=vapi_payload, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert "results" in body
    assert len(body["results"]) == 1
    item = body["results"][0]
    assert item["toolCallId"] == "call_vapi_test_001"
    assert "Patient Vapi Caller has been successfully registered with ID" in item["result"]


@pytest.mark.asyncio
async def test_vapi_register_patient_validation_failure(client: AsyncClient, auth_headers: dict):
    """
    Vapi tool-call with invalid phone number must return 200 with a friendly
    error in the results array (never raw 422).
    """
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_vapi_test_002",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "Invalid",
                            "last_name": "Phone",
                            "date_of_birth": "1990-01-01",
                            "sex": "male",
                            "phone_number": "not-e164",
                            "address_line_1": "123 Main St",
                            "city": "Dallas",
                            "state": "TX",
                            "zip_code": "75001",
                        },
                    },
                }
            ],
        }
    }

    resp = await client.post("/vapi/register-patient", json=vapi_payload, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert "results" in body
    assert len(body["results"]) == 1
    item = body["results"][0]
    assert item["toolCallId"] == "call_vapi_test_002"
    assert "Registration failed:" in item["result"]
    assert "E.164" in item["result"]


@pytest.mark.asyncio
async def test_vapi_register_patient_missing_required(client: AsyncClient, auth_headers: dict):
    """
    Vapi tool-call missing a required field returns 200 with helpful field error.
    """
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_vapi_test_003",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {
                            "first_name": "MissingLastName",
                            # missing last_name, dob, etc.
                        },
                    },
                }
            ],
        }
    }

    resp = await client.post("/vapi/register-patient", json=vapi_payload, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    assert "results" in body
    item = body["results"][0]
    assert item["toolCallId"] == "call_vapi_test_003"
    assert "Registration failed: last_name is required." in item["result"]


@pytest.mark.asyncio
async def test_vapi_register_patient_secret_header(client: AsyncClient, monkeypatch):
    """
    If VAPI_WEBHOOK_SECRET is set, requests without matching X-Vapi-Secret
    header must be rejected with 401.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "VAPI_WEBHOOK_SECRET", "super-secret-key-123")

    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_vapi_test_004",
                    "type": "function",
                    "function": {
                        "name": "register_patient",
                        "arguments": {},
                    },
                }
            ],
        }
    }

    # Missing header -> 401
    resp_missing = await client.post("/vapi/register-patient", json=vapi_payload)
    assert resp_missing.status_code == 401

    # Wrong header -> 401
    resp_wrong = await client.post(
        "/vapi/register-patient",
        json=vapi_payload,
        headers={"x-vapi-secret": "wrong-secret"},
    )
    assert resp_wrong.status_code == 401

    # Correct header -> 200 (validation error handled inside)
    resp_correct = await client.post(
        "/vapi/register-patient",
        json=vapi_payload,
        headers={"x-vapi-secret": "super-secret-key-123"},
    )
    assert resp_correct.status_code == 200
