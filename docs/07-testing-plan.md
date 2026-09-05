# 07 · Testing Plan

## Testing Layers

| Layer | Tool | What it covers |
|-------|------|----------------|
| Unit tests | pytest | Individual functions: validators, models, helpers |
| Integration tests | pytest + httpx (async) | API endpoints with a real test DB |
| Manual E2E tests | Phone call | Full voice flow end-to-end |
| Load / stress | Optional: locust | Concurrent registrations |

---

## Unit Test Cases

### Validators (pydantic / custom)

| Test ID | Input | Expected |
|---------|-------|----------|
| UT-01 | `phone_number = "+15551234567"` | Passes validation |
| UT-02 | `phone_number = "5551234567"` (no +) | Raises ValidationError |
| UT-03 | `phone_number = "+1555123"` (too short) | Raises ValidationError |
| UT-04 | `date_of_birth = "1990-05-15"` | Passes |
| UT-05 | `date_of_birth = "2099-01-01"` (future) | Raises ValidationError |
| UT-06 | `date_of_birth = "1800-01-01"` (>150 yrs) | Raises ValidationError |
| UT-07 | `state = "TX"` | Passes |
| UT-08 | `state = "Texas"` | Raises ValidationError (must be 2-char code) |
| UT-09 | `zip_code = "78701"` | Passes |
| UT-10 | `zip_code = "787"` | Raises ValidationError |
| UT-11 | `zip_code = "78701-1234"` | Passes (ZIP+4) |
| UT-12 | `sex = "female"` | Passes |
| UT-13 | `sex = "woman"` | Raises ValidationError |
| UT-14 | `email = "jane@example.com"` | Passes |
| UT-15 | `email = "not-an-email"` | Raises ValidationError |
| UT-16 | `email = None` | Passes (optional) |

---

## API Integration Test Cases

Requires test Postgres database (can use Supabase dev project or local Postgres).

### GET /health

| Test ID | Action | Expected |
|---------|--------|----------|
| IT-01 | GET /health | 200, `{ "data": { "status": "ok" } }` |

### POST /patients

| Test ID | Action | Expected |
|---------|--------|----------|
| IT-02 | POST with all required fields valid | 201, patient object returned |
| IT-03 | POST with missing `first_name` | 422, error message |
| IT-04 | POST with invalid `phone_number` | 422, error message |
| IT-05 | POST with invalid `date_of_birth` (future) | 422, error message |
| IT-06 | POST with all optional fields | 201, all fields in response |
| IT-07 | POST with null optional fields | 201, nulls in response |
| IT-08 | POST duplicate `phone_number` (bonus) | 409, existing patient in data |

### GET /patients

| Test ID | Action | Expected |
|---------|--------|----------|
| IT-09 | GET /patients (no filters) | 200, array of patients |
| IT-10 | GET /patients?phone=+15551234567 | 200, array with matching patient |
| IT-11 | GET /patients?last_name=doe | 200, case-insensitive match |
| IT-12 | GET /patients?state=TX | 200, only TX patients |
| IT-13 | GET /patients?limit=2 | 200, max 2 results |
| IT-14 | GET /patients?offset=100 | 200, empty array (beyond records) |
| IT-15 | GET /patients (deleted patient) | 200, deleted patient excluded |

### GET /patients/:id

| Test ID | Action | Expected |
|---------|--------|----------|
| IT-16 | GET /patients/{valid-uuid} | 200, patient object |
| IT-17 | GET /patients/{nonexistent-uuid} | 404, error message |
| IT-18 | GET /patients/{deleted-uuid} | 404, error message |

### PUT /patients/:id

| Test ID | Action | Expected |
|---------|--------|----------|
| IT-19 | PUT /patients/{id} `{ "city": "Dallas" }` | 200, updated patient |
| IT-20 | PUT /patients/{id} with invalid phone | 422, error |
| IT-21 | PUT /patients/{nonexistent-id} | 404, error |
| IT-22 | PUT /patients/{id} — updated_at changes | 200, `updated_at` > `created_at` |

### DELETE /patients/:id

| Test ID | Action | Expected |
|---------|--------|----------|
| IT-23 | DELETE /patients/{id} | 200, `{ "deleted": true, "id": "..." }` |
| IT-24 | DELETE /patients/{id} twice | 404 on second call |
| IT-25 | DELETE /patients/{nonexistent-id} | 404, error |

---

## Manual E2E Voice Test Cases

These require an active Twilio number linked to Vapi + a phone to call from.

| Test ID | Scenario | Steps | Expected |
|---------|----------|-------|----------|
| E2E-01 | Happy path, required fields only | Call, give all required info, decline optional, confirm | Record in DB, confirmation spoken |
| E2E-02 | Happy path, all fields | Call, give all fields, confirm | Full record in DB |
| E2E-03 | Correction during readback | Call, give info, say "fix my zip code" during readback, confirm | Corrected record saved |
| E2E-04 | Multiple corrections | Call, correct 3 fields, confirm on third readback | Correct record saved |
| E2E-05 | Invalid DOB re-prompt | Say "January 50th" as DOB | Agent re-prompts for DOB |
| E2E-06 | Invalid phone re-prompt | Say "call me at 555" | Agent re-prompts for full phone |
| E2E-07 | Caller hangs up mid-flow | Hang up after giving first name | No record in DB |
| E2E-08 | Restart request | Say "start over" | Agent resets to first_name |
| E2E-09 | Decline optional fields | Say "no" to optional fields | Record saved with only required fields |
| E2E-10 | Partial optional fields | Accept optional, skip insurance | Record with email/emergency but no insurance |
| E2E-11 (bonus) | Duplicate phone | Call from same number twice | Agent detects duplicate, offers update |

---

## Response Envelope Validation

All API tests must verify:

- [ ] `data` key exists in all responses
- [ ] `error` key exists in all responses
- [ ] `data` is null on error responses
- [ ] `error` is null on success responses
- [ ] `deleted_at` is null in all GET /patients results (soft-delete filter works)

---

## Test Data Fixtures

```python
# Minimum valid patient
VALID_PATIENT = {
    "first_name": "Jane",
    "last_name": "Doe",
    "date_of_birth": "1990-05-15",
    "sex": "female",
    "phone_number": "+15551234567",
    "address_line_1": "123 Main St",
    "city": "Austin",
    "state": "TX",
    "zip_code": "78701"
}

# Full patient with all optional fields
FULL_PATIENT = {
    **VALID_PATIENT,
    "email": "jane@example.com",
    "address_line_2": "Apt 4B",
    "insurance_provider": "BlueCross BlueShield",
    "insurance_member_id": "BC123456",
    "preferred_language": "Spanish",
    "emergency_contact_name": "John Doe",
    "emergency_contact_phone": "+15559876543"
}
```

---

## CI / CD Test Automation (Future)

```yaml
# .github/workflows/test.yml (future)
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: testpassword
          POSTGRES_DB: test_patients
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --tb=short
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:testpassword@localhost/test_patients
```
