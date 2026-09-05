"""
app/schemas.py
--------------
Pydantic v2 schemas for the patients API.

Three schemas:
  PatientCreate  — body for POST /patients  (required + optional fields)
  PatientUpdate  — body for PUT /patients/:id (all fields optional for partial update)
  PatientResponse — shape returned by all read endpoints

Field validators enforce the same rules as the DB CHECK constraints so the API
returns friendly 422 messages before the DB even sees the data.

Reference: docs/03-api-spec.md (required fields list), docs/02-database-schema.md (validation rules)
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Allowed values
# ---------------------------------------------------------------------------

SexEnum = Literal["male", "female", "other", "prefer_not_to_say"]

# ---------------------------------------------------------------------------
# Regex patterns (must match DB CHECK constraints exactly)
# ---------------------------------------------------------------------------

_PHONE_E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")
_STATE_RE = re.compile(r"^[A-Z]{2}$")
_ZIP_RE = re.compile(r"^\d{5}(-\d{4})?$")


# ---------------------------------------------------------------------------
# Reusable validator functions
# ---------------------------------------------------------------------------

def _validate_phone(value: str | None, field_name: str = "phone_number") -> str | None:
    """Validate E.164 phone number format. Returns value unchanged if valid."""
    if value is None:
        return value
    if not _PHONE_E164_RE.match(value):
        raise ValueError(
            f"{field_name} must be in E.164 format (e.g. +15551234567). "
            f"Received: {value!r}"
        )
    return value


def _validate_date_of_birth(value: date | None) -> date | None:
    """DOB must be in the past and no more than 150 years ago."""
    if value is None:
        return value
    today = date.today()
    if value >= today:
        raise ValueError("date_of_birth must be in the past.")
    cutoff = today.replace(year=today.year - 150)
    if value <= cutoff:
        raise ValueError("date_of_birth cannot be more than 150 years in the past.")
    return value


def _validate_state(value: str | None) -> str | None:
    """State must be exactly 2 uppercase letters (US state code)."""
    if value is None:
        return value
    if not _STATE_RE.match(value):
        raise ValueError(
            f"state must be a 2-letter uppercase US state code (e.g. TX). "
            f"Received: {value!r}"
        )
    return value


def _validate_zip(value: str | None) -> str | None:
    """ZIP code must be 5 digits, or 5+4 (ZIP+4) format."""
    if value is None:
        return value
    if not _ZIP_RE.match(value):
        raise ValueError(
            f"zip_code must be 5 digits or ZIP+4 format (e.g. 78701 or 78701-1234). "
            f"Received: {value!r}"
        )
    return value


# ---------------------------------------------------------------------------
# PatientCreate — POST /patients
# ---------------------------------------------------------------------------

class PatientCreate(BaseModel):
    """
    Fields sent by Vapi (via the register_patient tool call) or directly by API clients.
    Required fields match docs/03-api-spec.md → POST /patients → Required fields.
    """

    # Required
    first_name: str = Field(..., max_length=100, examples=["Jane"])
    last_name: str = Field(..., max_length=100, examples=["Doe"])
    date_of_birth: date = Field(..., examples=["1990-05-15"])
    sex: SexEnum = Field(..., examples=["female"])
    phone_number: str = Field(..., max_length=20, examples=["+15551234567"])
    address_line_1: str = Field(..., max_length=255, examples=["123 Main St"])
    city: str = Field(..., max_length=100, examples=["Austin"])
    state: str = Field(..., max_length=2, examples=["TX"])
    zip_code: str = Field(..., max_length=10, examples=["78701"])

    # Optional
    email: Optional[EmailStr] = Field(default=None, examples=["jane@example.com"])
    address_line_2: Optional[str] = Field(default=None, max_length=255, examples=["Apt 4B"])
    insurance_provider: Optional[str] = Field(default=None, max_length=150, examples=["BlueCross"])
    insurance_member_id: Optional[str] = Field(default=None, max_length=100, examples=["BC123456"])
    preferred_language: Optional[str] = Field(default="English", max_length=50, examples=["English"])
    emergency_contact_name: Optional[str] = Field(default=None, max_length=200, examples=["John Doe"])
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20, examples=["+15559876543"])

    # ------------------------------------------------------------------
    # Field-level validators
    # ------------------------------------------------------------------

    @field_validator("phone_number")
    @classmethod
    def phone_must_be_e164(cls, v: str) -> str:
        return _validate_phone(v, "phone_number")  # type: ignore[return-value]

    @field_validator("date_of_birth")
    @classmethod
    def dob_must_be_valid(cls, v: date) -> date:
        return _validate_date_of_birth(v)  # type: ignore[return-value]

    @field_validator("state")
    @classmethod
    def state_must_be_code(cls, v: str) -> str:
        return _validate_state(v)  # type: ignore[return-value]

    @field_validator("zip_code")
    @classmethod
    def zip_must_be_valid(cls, v: str) -> str:
        return _validate_zip(v)  # type: ignore[return-value]

    @field_validator("emergency_contact_phone")
    @classmethod
    def ec_phone_must_be_e164(cls, v: str | None) -> str | None:
        return _validate_phone(v, "emergency_contact_phone")


# ---------------------------------------------------------------------------
# PatientUpdate — PUT /patients/:id  (all fields optional for partial update)
# ---------------------------------------------------------------------------

class PatientUpdate(BaseModel):
    """
    All fields optional — send only what you want to change.
    Validators are identical to PatientCreate.
    """

    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    date_of_birth: Optional[date] = Field(default=None)
    sex: Optional[SexEnum] = Field(default=None)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    email: Optional[EmailStr] = Field(default=None)
    address_line_1: Optional[str] = Field(default=None, max_length=255)
    address_line_2: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=2)
    zip_code: Optional[str] = Field(default=None, max_length=10)
    insurance_provider: Optional[str] = Field(default=None, max_length=150)
    insurance_member_id: Optional[str] = Field(default=None, max_length=100)
    preferred_language: Optional[str] = Field(default=None, max_length=50)
    emergency_contact_name: Optional[str] = Field(default=None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("phone_number")
    @classmethod
    def phone_must_be_e164(cls, v: str | None) -> str | None:
        return _validate_phone(v, "phone_number")

    @field_validator("date_of_birth")
    @classmethod
    def dob_must_be_valid(cls, v: date | None) -> date | None:
        return _validate_date_of_birth(v)

    @field_validator("state")
    @classmethod
    def state_must_be_code(cls, v: str | None) -> str | None:
        return _validate_state(v)

    @field_validator("zip_code")
    @classmethod
    def zip_must_be_valid(cls, v: str | None) -> str | None:
        return _validate_zip(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def ec_phone_must_be_e164(cls, v: str | None) -> str | None:
        return _validate_phone(v, "emergency_contact_phone")

    @model_validator(mode="after")
    def at_least_one_field(self) -> "PatientUpdate":
        """Reject an empty update body (all None)."""
        non_none = {k for k, v in self.model_dump().items() if v is not None}
        if not non_none:
            raise ValueError("At least one field must be provided for an update.")
        return self


# ---------------------------------------------------------------------------
# PatientResponse — shape returned by GET /patients, GET /patients/:id, etc.
# ---------------------------------------------------------------------------

class PatientResponse(BaseModel):
    """
    Full patient record as returned by the API.
    deleted_at is excluded — soft-deleted records are never returned.
    Timestamps are serialised as ISO 8601 strings with timezone.
    """

    id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    email: Optional[str]
    address_line_1: str
    address_line_2: Optional[str]
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str]
    insurance_member_id: Optional[str]
    preferred_language: Optional[str]
    emergency_contact_name: Optional[str]
    emergency_contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# PatientDeleteData — payload for DELETE /patients/:id response
# ---------------------------------------------------------------------------

class PatientDeleteData(BaseModel):
    deleted: bool = True
    id: uuid.UUID


# ---------------------------------------------------------------------------
# API response envelope — used by all endpoints
# ---------------------------------------------------------------------------

class APIResponse(BaseModel):
    """
    Envelope: { "data": <T | null>, "error": <str | null> }
    Reference: docs/03-api-spec.md → Response Envelope
    """

    data: object = None
    error: Optional[str] = None

