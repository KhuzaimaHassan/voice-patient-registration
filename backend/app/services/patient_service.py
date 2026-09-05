"""
app/services/patient_service.py
-------------------------------
Reusable business logic and database persistence for patients.
Decoupled from specific transport protocols (REST API vs Vapi webhook).
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient
from app.schemas import PatientCreate

logger = logging.getLogger(__name__)


async def create_patient_record(
    db: AsyncSession,
    patient_data: PatientCreate,
) -> Patient:
    """
    Persists a new patient record into Postgres.
    
    Args:
        db: Active asynchronous database session.
        patient_data: Validated PatientCreate Pydantic schema.

    Returns:
        The newly created and refreshed SQLAlchemy Patient model instance.
    """
    patient = Patient(**patient_data.model_dump())
    db.add(patient)
    await db.flush()
    await db.refresh(patient)
    logger.info("Created new patient record with ID: %s", patient.id)
    return patient
