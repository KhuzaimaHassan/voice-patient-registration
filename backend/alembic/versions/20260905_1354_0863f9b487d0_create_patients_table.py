"""create_patients_table

Revision ID: 0863f9b487d0
Revises: 
Create Date: 2026-09-05 13:54:51.702969
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0863f9b487d0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Create patients table
    # ------------------------------------------------------------------
    op.create_table(
        "patients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("sex", sa.String(length=20), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address_line_1", sa.String(length=255), nullable=False),
        sa.Column("address_line_2", sa.String(length=255), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("state", sa.CHAR(length=2), nullable=False),
        sa.Column("zip_code", sa.String(length=10), nullable=False),
        sa.Column("insurance_provider", sa.String(length=150), nullable=True),
        sa.Column("insurance_member_id", sa.String(length=100), nullable=True),
        sa.Column("preferred_language", sa.String(length=50), nullable=True, server_default="English"),
        sa.Column("emergency_contact_name", sa.String(length=200), nullable=True),
        sa.Column("emergency_contact_phone", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        # Table-level CHECK constraints
        sa.CheckConstraint(
            r"phone_number ~ '^\+[1-9]\d{7,14}$'",
            name="chk_phone_e164",
        ),
        sa.CheckConstraint(
            r"emergency_contact_phone IS NULL OR emergency_contact_phone ~ '^\+[1-9]\d{7,14}$'",
            name="chk_ec_phone_e164",
        ),
        sa.CheckConstraint(
            r"state ~ '^[A-Z]{2}$'",
            name="chk_state_code",
        ),
        sa.CheckConstraint(
            r"zip_code ~ '^\d{5}(-\d{4})?$'",
            name="chk_zip",
        ),
        sa.CheckConstraint(
            "date_of_birth < CURRENT_DATE AND date_of_birth > CURRENT_DATE - INTERVAL '150 years'",
            name="chk_dob",
        ),
    )

    # ------------------------------------------------------------------
    # Partial and standard indexes
    # ------------------------------------------------------------------
    op.create_index(
        "idx_patients_phone",
        "patients",
        ["phone_number"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_patients_last_name",
        "patients",
        ["last_name"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_patients_deleted_at",
        "patients",
        ["deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_patients_deleted_at", table_name="patients")
    op.drop_index("idx_patients_last_name", table_name="patients")
    op.drop_index("idx_patients_phone", table_name="patients")
    op.drop_table("patients")
