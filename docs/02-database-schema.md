# 02 · Database Schema

## Database: Supabase Postgres (free tier)

---

## Table: `patients`

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | UUID | NOT NULL | `gen_random_uuid()` | Primary key |
| `first_name` | VARCHAR(100) | NOT NULL | — | Required |
| `last_name` | VARCHAR(100) | NOT NULL | — | Required |
| `date_of_birth` | DATE | NOT NULL | — | Format: YYYY-MM-DD |
| `sex` | VARCHAR(20) | NOT NULL | — | Enum: male, female, other, prefer_not_to_say |
| `phone_number` | VARCHAR(20) | NOT NULL | — | E.164 format, e.g. +15551234567 |
| `email` | VARCHAR(255) | NULL | — | Optional |
| `address_line_1` | VARCHAR(255) | NOT NULL | — | Required |
| `address_line_2` | VARCHAR(255) | NULL | — | Optional (apt, suite) |
| `city` | VARCHAR(100) | NOT NULL | — | Required |
| `state` | CHAR(2) | NOT NULL | — | US state code, e.g. CA |
| `zip_code` | VARCHAR(10) | NOT NULL | — | 5 or 9 digit (ZIP+4) |
| `insurance_provider` | VARCHAR(150) | NULL | — | Optional |
| `insurance_member_id` | VARCHAR(100) | NULL | — | Optional |
| `preferred_language` | VARCHAR(50) | NULL | `'English'` | Optional, default English |
| `emergency_contact_name` | VARCHAR(200) | NULL | — | Optional |
| `emergency_contact_phone` | VARCHAR(20) | NULL | — | Optional, E.164 |
| `created_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | Auto-set on insert |
| `updated_at` | TIMESTAMPTZ | NOT NULL | `NOW()` | Auto-updated on change |
| `deleted_at` | TIMESTAMPTZ | NULL | — | Soft-delete; NULL = active |

---

## Constraints

```sql
-- Primary key
ALTER TABLE patients ADD CONSTRAINT patients_pkey PRIMARY KEY (id);

-- Phone number format check (E.164 basic)
ALTER TABLE patients ADD CONSTRAINT chk_phone_e164
  CHECK (phone_number ~ '^\+[1-9]\d{7,14}$');

-- Emergency contact phone format (when provided)
ALTER TABLE patients ADD CONSTRAINT chk_ec_phone_e164
  CHECK (
    emergency_contact_phone IS NULL OR
    emergency_contact_phone ~ '^\+[1-9]\d{7,14}$'
  );

-- State must be 2 uppercase letters
ALTER TABLE patients ADD CONSTRAINT chk_state_code
  CHECK (state ~ '^[A-Z]{2}$');

-- ZIP code format
ALTER TABLE patients ADD CONSTRAINT chk_zip
  CHECK (zip_code ~ '^\d{5}(-\d{4})?$');

-- DOB must be in the past and plausible (older than 0, younger than 150)
ALTER TABLE patients ADD CONSTRAINT chk_dob
  CHECK (date_of_birth < CURRENT_DATE AND date_of_birth > CURRENT_DATE - INTERVAL '150 years');
```

---

## Indexes

```sql
-- Fast lookup by phone number (used for duplicate detection)
CREATE INDEX idx_patients_phone ON patients(phone_number)
  WHERE deleted_at IS NULL;

-- Fast lookup by last name
CREATE INDEX idx_patients_last_name ON patients(last_name)
  WHERE deleted_at IS NULL;

-- Soft-delete filter
CREATE INDEX idx_patients_deleted_at ON patients(deleted_at);
```

---

## SQLAlchemy ORM Representation (pseudocode)

```python
class Patient(Base):
    __tablename__ = "patients"

    id                      = Column(UUID, primary_key=True, default=uuid4)
    first_name              = Column(String(100), nullable=False)
    last_name               = Column(String(100), nullable=False)
    date_of_birth           = Column(Date, nullable=False)
    sex                     = Column(String(20), nullable=False)
    phone_number            = Column(String(20), nullable=False)
    email                   = Column(String(255), nullable=True)
    address_line_1          = Column(String(255), nullable=False)
    address_line_2          = Column(String(255), nullable=True)
    city                    = Column(String(100), nullable=False)
    state                   = Column(CHAR(2), nullable=False)
    zip_code                = Column(String(10), nullable=False)
    insurance_provider      = Column(String(150), nullable=True)
    insurance_member_id     = Column(String(100), nullable=True)
    preferred_language      = Column(String(50), default="English")
    emergency_contact_name  = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    created_at              = Column(TIMESTAMPTZ, default=func.now())
    updated_at              = Column(TIMESTAMPTZ, default=func.now(), onupdate=func.now())
    deleted_at              = Column(TIMESTAMPTZ, nullable=True)
```

---

## Alembic Migration Strategy

1. `alembic init alembic` inside `/backend`.
2. Configure `alembic.ini` to read `DATABASE_URL` from environment.
3. First migration: `create_patients_table`.
4. Subsequent migrations: named descriptively, e.g. `add_insurance_fields`.
5. Apply on deploy: `alembic upgrade head` in Render start command.

---

## Soft Delete Pattern

- `DELETE /patients/:id` sets `deleted_at = NOW()` rather than removing the row.
- All queries filter `WHERE deleted_at IS NULL` by default.
- Hard delete never exposed via API; DBA-only operation.

---

## Data Retention Notes

- No automatic purge implemented in MVP.
- Future: cron job to hard-delete rows where `deleted_at < NOW() - INTERVAL '7 years'` (HIPAA retention guidance).
