"""
app/routers/vapi_webhook.py
---------------------------
Webhook handler specifically formatted for Vapi.ai tool-calls.
Implements POST /vapi/register-patient.

References:
  - Vapi Tool-Calls Webhook Protocol:
    Request shape:
      {"message": {"type": "tool-calls", "toolCalls": [{"id": "...", "function": {"name": "register_patient", "arguments": {...}}}]}}
    Response shape:
      {"results": [{"toolCallId": "...", "result": "..."}]}
"""

import json
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas import PatientCreate
from app.services.patient_service import create_patient_record

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi"])


def _extract_validation_message(exc: ValidationError) -> str:
    """Extract a user-friendly single sentence from a Pydantic ValidationError."""
    errors = exc.errors()
    if not errors:
        return "Invalid registration data provided."

    first_err = errors[0]
    loc = [str(item) for item in first_err.get("loc", []) if item != "body"]
    field_name = ".".join(loc) if loc else "field"
    msg = first_err.get("msg", "Invalid value")

    if msg.startswith("Value error, "):
        msg = msg[len("Value error, "):]

    if msg.lower() == "field required":
        return f"{field_name} is required."
    elif field_name and field_name.lower() in msg.lower():
        return msg
    elif field_name and field_name != "field":
        return f"{field_name}: {msg}"
    else:
        return msg


@router.post(
    "/register-patient",
    summary="Vapi Tool Call Webhook: Register Patient",
    status_code=status.HTTP_200_OK,
)
async def vapi_register_patient(
    request: Request,
    x_vapi_secret: str | None = Header(default=None, alias="x-vapi-secret"),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Handles Vapi.ai tool calls for register_patient.
    - Authenticates via X-Vapi-Secret header when configured.
    - Extracts arguments from the Vapi envelope.
    - Validates with PatientCreate.
    - Persists the record via create_patient_record.
    - Always returns the Vapi results array envelope:
      {"results": [{"toolCallId": "<id>", "result": "<spoken message>"}]}
    """
    settings = get_settings()

    # 1. Secret header authentication (strictly enforced)
    expected_secret = (settings.VAPI_WEBHOOK_SECRET or "").strip()
    auth_header = request.headers.get("authorization", "")
    bearer_token = auth_header.replace("Bearer ", "").replace("bearer ", "").strip()
    provided_secret = (x_vapi_secret or "").strip() or bearer_token

    if not expected_secret or not provided_secret or provided_secret != expected_secret:
        logger.warning("Vapi webhook unauthorized: invalid or missing secret header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: invalid or missing X-Vapi-Secret or Authorization header.",
        )

    # 2. Parse request JSON body
    try:
        body = await request.json()
    except Exception as e:
        logger.error("Failed to parse JSON body from Vapi request: %s", e)
        return {
            "results": [
                {
                    "toolCallId": "unknown",
                    "result": "Registration failed: Invalid JSON request body.",
                }
            ]
        }

    # 3. Locate toolCall and arguments from Vapi's nested envelope
    # Typical Vapi envelope:
    # {"message": {"type": "tool-calls", "toolCalls": [{"id": "...", "function": {"arguments": {...}}}]}}
    message = body.get("message", {}) if isinstance(body.get("message"), dict) else {}
    tool_calls = (
        message.get("toolCalls")
        or message.get("toolCallList")
        or body.get("toolCalls")
        or []
    )

    tool_call_id = "unknown"
    raw_args: Any = {}

    if isinstance(tool_calls, list) and len(tool_calls) > 0:
        tool_call = tool_calls[0]
        if isinstance(tool_call, dict):
            tool_call_id = tool_call.get("id") or tool_call.get("toolCallId") or "unknown"
            func = tool_call.get("function", {})
            if isinstance(func, dict):
                raw_args = func.get("arguments", {})
    elif isinstance(body, dict) and "arguments" in body:
        # Fallback if arguments are sent at root
        tool_call_id = body.get("toolCallId") or body.get("id") or "unknown"
        raw_args = body.get("arguments", {})
    else:
        logger.warning("Vapi tool-call payload missing toolCalls: %s", body)
        return {
            "results": [
                {
                    "toolCallId": "unknown",
                    "result": "Registration failed: No toolCalls found in request.",
                }
            ]
        }

    # If arguments were serialized as a JSON string by the LLM, deserialize them
    if isinstance(raw_args, str):
        try:
            raw_args = json.loads(raw_args)
        except Exception:
            raw_args = {}

    if not isinstance(raw_args, dict):
        raw_args = {}

    logger.info(
        "Processing Vapi register_patient tool call: toolCallId=%s, fields=%s",
        tool_call_id,
        list(raw_args.keys()),
    )

    # 4. Validate arguments using PatientCreate schema
    try:
        patient_data = PatientCreate(**raw_args)
    except ValidationError as val_err:
        friendly_error = _extract_validation_message(val_err)
        logger.warning(
            "Vapi tool call validation failed for toolCallId=%s: %s",
            tool_call_id,
            friendly_error,
        )
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": f"Registration failed: {friendly_error}",
                }
            ]
        }

    # 5. Persist patient record
    try:
        patient = await create_patient_record(db, patient_data)
        success_message = (
            f"Patient {patient.first_name} {patient.last_name} has been successfully "
            f"registered with ID {patient.id}."
        )
        logger.info(
            "Vapi register_patient succeeded: patient_id=%s, toolCallId=%s",
            patient.id,
            tool_call_id,
        )
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": success_message,
                }
            ]
        }
    except Exception as db_err:
        logger.exception("Database error while creating patient via Vapi webhook: %s", db_err)
        return {
            "results": [
                {
                    "toolCallId": tool_call_id,
                    "result": (
                        "Registration failed due to an internal server error. "
                        "Please ask the caller to try again later."
                    ),
                }
            ]
        }
