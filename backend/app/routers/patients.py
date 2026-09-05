"""
app/routers/patients.py
-----------------------
FastAPI REST router for patient registration CRUD operations.
Implements the 5 endpoints specified in docs/03-api-spec.md:
  - GET    /patients
  - GET    /patients/{id}
  - POST   /patients
  - PUT    /patients/{id}
  - DELETE /patients/{id}
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Patient
from app.schemas import (
    APIResponse,
    PatientCreate,
    PatientDeleteData,
    PatientResponse,
    PatientUpdate,
)
from app.services.patient_service import create_patient_record

router = APIRouter(prefix="/patients", tags=["patients"])


# ---------------------------------------------------------------------------
# GET /patients — list active patients with optional filtering & pagination
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=APIResponse,
    summary="List patients",
    status_code=status.HTTP_200_OK,
)
async def list_patients(
    phone: Optional[str] = Query(
        default=None,
        description="Exact E.164 phone number match",
        examples=["+15551234567"],
    ),
    last_name: Optional[str] = Query(
        default=None,
        description="Case-insensitive contains match for last name",
        examples=["Doe"],
    ),
    city: Optional[str] = Query(
        default=None,
        description="Case-insensitive exact match for city",
        examples=["Austin"],
    ),
    state: Optional[str] = Query(
        default=None,
        max_length=2,
        description="Exact 2-letter state code",
        examples=["TX"],
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Max results to return (1-200)",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Pagination offset",
    ),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    List all active patients (where deleted_at IS NULL) matching criteria.
    """
    stmt = select(Patient).where(Patient.deleted_at.is_(None))

    if phone is not None:
        stmt = stmt.where(Patient.phone_number == phone)

    if last_name is not None:
        stmt = stmt.where(Patient.last_name.ilike(f"%{last_name}%"))

    if city is not None:
        stmt = stmt.where(Patient.city.ilike(city))

    if state is not None:
        stmt = stmt.where(Patient.state == state.upper())

    stmt = stmt.order_by(Patient.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    patients = result.scalars().all()

    data = [PatientResponse.model_validate(p) for p in patients]
    return APIResponse(data=data, error=None)


# ---------------------------------------------------------------------------
# GET /patients/{id} — retrieve single patient by UUID
# ---------------------------------------------------------------------------

@router.get(
    "/{id}",
    response_model=APIResponse,
    summary="Get patient by ID",
    status_code=status.HTTP_200_OK,
)
async def get_patient(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Retrieve an active patient record by UUID.
    Returns 404 if not found or soft-deleted.
    """
    stmt = select(Patient).where(Patient.id == id, Patient.deleted_at.is_(None))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    return APIResponse(data=PatientResponse.model_validate(patient), error=None)


# ---------------------------------------------------------------------------
# POST /patients — create new patient record
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=APIResponse,
    summary="Create patient",
    status_code=status.HTTP_201_CREATED,
)
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Register a new patient record.
    Standard REST endpoint per docs/03-api-spec.md.
    """
    patient = await create_patient_record(db, payload)
    return APIResponse(data=PatientResponse.model_validate(patient), error=None)


# ---------------------------------------------------------------------------
# PUT /patients/{id} — update existing patient (partial update)
# ---------------------------------------------------------------------------

@router.put(
    "/{id}",
    response_model=APIResponse,
    summary="Update patient",
    status_code=status.HTTP_200_OK,
)
async def update_patient(
    id: uuid.UUID,
    payload: PatientUpdate,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Update fields of an active patient. Only provided fields are modified.
    Returns 404 if patient does not exist or has been soft-deleted.
    """
    stmt = select(Patient).where(Patient.id == id, Patient.deleted_at.is_(None))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    update_fields = payload.model_dump(exclude_unset=True)
    for field_name, value in update_fields.items():
        setattr(patient, field_name, value)

    patient.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(patient)

    return APIResponse(data=PatientResponse.model_validate(patient), error=None)


# ---------------------------------------------------------------------------
# DELETE /patients/{id} — soft-delete patient record
# ---------------------------------------------------------------------------

@router.delete(
    "/{id}",
    response_model=APIResponse,
    summary="Soft-delete patient",
    status_code=status.HTTP_200_OK,
)
async def delete_patient(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    """
    Soft-delete a patient by setting deleted_at to NOW().
    Returns 404 if not found or already deleted.
    """
    stmt = select(Patient).where(Patient.id == id, Patient.deleted_at.is_(None))
    result = await db.execute(stmt)
    patient = result.scalar_one_or_none()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found.",
        )

    patient.deleted_at = datetime.now(timezone.utc)
    await db.flush()

    return APIResponse(
        data=PatientDeleteData(deleted=True, id=patient.id),
        error=None,
    )
