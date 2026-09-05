"""
app/models.py
-------------
SQLAlchemy ORM model for the `patients` table.
Columns, types, nullability and defaults match docs/02-database-schema.md exactly.
DB-level constraints and indexes are declared here so Alembic can generate them.
"""

import uuid

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Date,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Patient(Base):
    """
    Represents one patient registration record.

    Soft-delete pattern: deleted_at IS NULL  →  active record.
    All API queries filter WHERE deleted_at IS NULL.
    Hard-delete is a DBA-only operation, never exposed via API.
    """

    __tablename__ = "patients"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        # server_default lets the DB generate the UUID too (belt-and-suspenders).
        server_default=func.gen_random_uuid(),
    )

    # ------------------------------------------------------------------
    # Required fields
    # ------------------------------------------------------------------
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[Date] = mapped_column(Date, nullable=False)
    sex: Mapped[str] = mapped_column(String(20), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    address_line_1: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)

    # ------------------------------------------------------------------
    # Optional fields
    # ------------------------------------------------------------------
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line_2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    insurance_provider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    insurance_member_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_language: Mapped[str | None] = mapped_column(
        String(50), nullable=True, server_default="English"
    )
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # ------------------------------------------------------------------
    # Audit timestamps
    # ------------------------------------------------------------------
    created_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[TIMESTAMP] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Soft-delete — NULL means active; set to NOW() on DELETE /patients/:id
    deleted_at: Mapped[TIMESTAMP | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        default=None,
    )

    # ------------------------------------------------------------------
    # Table-level constraints (from docs/02-database-schema.md)
    # ------------------------------------------------------------------
    __table_args__ = (
        # Phone number — basic E.164 format
        CheckConstraint(
            r"phone_number ~ '^\+[1-9]\d{7,14}$'",
            name="chk_phone_e164",
        ),
        # Emergency contact phone — E.164 or NULL
        CheckConstraint(
            r"emergency_contact_phone IS NULL OR emergency_contact_phone ~ '^\+[1-9]\d{7,14}$'",
            name="chk_ec_phone_e164",
        ),
        # State code — exactly 2 uppercase letters
        CheckConstraint(
            r"state ~ '^[A-Z]{2}$'",
            name="chk_state_code",
        ),
        # ZIP code — 5 digits or ZIP+4
        CheckConstraint(
            r"zip_code ~ '^\d{5}(-\d{4})?$'",
            name="chk_zip",
        ),
        # Date of birth — must be in the past, not more than 150 years ago
        CheckConstraint(
            "date_of_birth < CURRENT_DATE AND date_of_birth > CURRENT_DATE - INTERVAL '150 years'",
            name="chk_dob",
        ),
        # ------------------------------------------------------------------
        # Indexes (from docs/02-database-schema.md)
        # ------------------------------------------------------------------
        # Partial index on phone_number for active records (duplicate detection)
        Index(
            "idx_patients_phone",
            "phone_number",
            postgresql_where=Text("deleted_at IS NULL"),
        ),
        # Partial index on last_name for active records
        Index(
            "idx_patients_last_name",
            "last_name",
            postgresql_where=Text("deleted_at IS NULL"),
        ),
        # Full index on deleted_at for soft-delete filter scans
        Index(
            "idx_patients_deleted_at",
            "deleted_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Patient id={self.id} name={self.first_name} {self.last_name} "
            f"phone={self.phone_number}>"
        )
