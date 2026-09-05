# 03 · REST API Specification

## Base URL

```
Production:  https://<render-app-name>.onrender.com
Local dev:   http://localhost:8000
```

---

## Response Envelope

All responses follow a consistent envelope:

```json
{
  "data": <object | array | null>,
  "error": <string | null>
}
```

- `data` is populated on success, `null` on error.
- `error` is populated on failure, `null` on success.

---

## Authentication (MVP)

No auth for MVP. Future: API key header `X-API-Key` checked against env var.

---

## Endpoints

### GET /health

Health check — used by Render and keep-alive pings.

**Response 200**
```json
{ "data": { "status": "ok" }, "error": null }
```

---

### GET /patients

List all active (non-deleted) patients with optional filters.

**Query Parameters**

| Param | Type | Description |
|-------|------|-------------|
| `phone` | string | Exact E.164 match |
| `last_name` | string | Case-insensitive contains |
| `city` | string | Case-insensitive exact |
| `state` | string | 2-letter state code |
| `limit` | int | Max results (default 50, max 200) |
| `offset` | int | Pagination offset (default 0) |

**Response 200**
```json
{
  "data": [
    {
      "id": "uuid",
      "first_name": "Jane",
      "last_name": "Doe",
      "date_of_birth": "1990-05-15",
      "sex": "female",
      "phone_number": "+15551234567",
      "email": "jane@example.com",
      "address_line_1": "123 Main St",
      "address_line_2": null,
      "city": "Austin",
      "state": "TX",
      "zip_code": "78701",
      "insurance_provider": "BlueCross",
      "insurance_member_id": "BC123456",
      "preferred_language": "English",
      "emergency_contact_name": "John Doe",
      "emergency_contact_phone": "+15559876543",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ],
  "error": null
}
```

---

### GET /patients/{id}

Retrieve a single patient by UUID.

**Path Parameter:** `id` — UUID

**Response 200** — same shape as single item above.

**Response 404**
```json
{ "data": null, "error": "Patient not found." }
```

---

### POST /patients

Create a new patient record. Called by Vapi tool on confirmation.

**Request Body (JSON)**

```json
{
  "first_name": "Jane",
  "last_name": "Doe",
  "date_of_birth": "1990-05-15",
  "sex": "female",
  "phone_number": "+15551234567",
  "email": "jane@example.com",
  "address_line_1": "123 Main St",
  "address_line_2": null,
  "city": "Austin",
  "state": "TX",
  "zip_code": "78701",
  "insurance_provider": null,
  "insurance_member_id": null,
  "preferred_language": "English",
  "emergency_contact_name": null,
  "emergency_contact_phone": null
}
```

**Required fields:** `first_name`, `last_name`, `date_of_birth`, `sex`, `phone_number`, `address_line_1`, `city`, `state`, `zip_code`

**Response 201**
```json
{ "data": { ...full patient object... }, "error": null }
```

**Response 422 — Validation Error**
```json
{
  "data": null,
  "error": "Validation failed: phone_number must be in E.164 format."
}
```

**Response 409 — Duplicate (Bonus)**
```json
{
  "data": { ...existing patient... },
  "error": "A patient with this phone number already exists."
}
```

---

### PUT /patients/{id}

Update an existing patient record (partial update supported).

**Path Parameter:** `id` — UUID

**Request Body** — any subset of patient fields (same schema as POST, all optional).

**Response 200**
```json
{ "data": { ...updated patient... }, "error": null }
```

**Response 404**
```json
{ "data": null, "error": "Patient not found." }
```

---

### DELETE /patients/{id}

Soft-delete a patient (sets `deleted_at = NOW()`).

**Path Parameter:** `id` — UUID

**Response 200**
```json
{ "data": { "deleted": true, "id": "uuid" }, "error": null }
```

**Response 404**
```json
{ "data": null, "error": "Patient not found." }
```

---

## HTTP Status Code Summary

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable Entity (validation failure) |
| 500 | Internal Server Error |

---

## Field Validation Rules (server-side)

| Field | Rule |
|-------|------|
| `phone_number` | Matches regex `^\+[1-9]\d{7,14}$` |
| `date_of_birth` | ISO 8601 date; must be in the past; must be > 150 years ago |
| `state` | Exactly 2 uppercase letters |
| `zip_code` | Matches `^\d{5}(-\d{4})?$` |
| `sex` | One of: `male`, `female`, `other`, `prefer_not_to_say` |
| `email` | Valid email format if provided |
| `emergency_contact_phone` | Same as `phone_number` if provided |

---

## Vapi Tool Definition (register_patient)

```json
{
  "name": "register_patient",
  "description": "Saves the confirmed patient registration data to the database.",
  "parameters": {
    "type": "object",
    "properties": {
      "first_name":               { "type": "string" },
      "last_name":                { "type": "string" },
      "date_of_birth":            { "type": "string", "format": "date" },
      "sex":                      { "type": "string", "enum": ["male","female","other","prefer_not_to_say"] },
      "phone_number":             { "type": "string" },
      "email":                    { "type": "string" },
      "address_line_1":           { "type": "string" },
      "address_line_2":           { "type": "string" },
      "city":                     { "type": "string" },
      "state":                    { "type": "string" },
      "zip_code":                 { "type": "string" },
      "insurance_provider":       { "type": "string" },
      "insurance_member_id":      { "type": "string" },
      "preferred_language":       { "type": "string" },
      "emergency_contact_name":   { "type": "string" },
      "emergency_contact_phone":  { "type": "string" }
    },
    "required": ["first_name","last_name","date_of_birth","sex","phone_number",
                 "address_line_1","city","state","zip_code"]
  }
}
```

---

## Vapi Webhook Integration

### POST /vapi/register-patient

Dedicated webhook endpoint designed specifically for Vapi.ai's tool-calling protocol.

- **Authentication:** Validates `x-vapi-secret` or `Authorization: Bearer <secret>` against `VAPI_WEBHOOK_SECRET` (if configured on the server). Returns 401 if invalid.
- **Request Format:** Accepts Vapi's nested `tool-calls` event envelope containing `message.toolCalls[0].function.arguments`.
- **Validation:** Validates extracted arguments against `PatientCreate`.
- **Database Persistence:** Reuses `create_patient_record` service to insert and flush to Postgres.

**Request Example (from Vapi.ai):**
```json
{
  "message": {
    "type": "tool-calls",
    "toolCalls": [
      {
        "id": "call_123456",
        "type": "function",
        "function": {
          "name": "register_patient",
          "arguments": {
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
        }
      }
    ]
  }
}
```

**Success Response (HTTP 200):**
```json
{
  "results": [
    {
      "toolCallId": "call_123456",
      "result": "Patient Jane Doe has been successfully registered with ID 4dfd9d5b-d8f4-4850-9e53-1315fe53ef86."
    }
  ]
}
```

**Validation Error Response (HTTP 200):**
Returns HTTP 200 with the error message in the `results` array so Vapi's voice assistant speaks the error back to the caller instead of crashing with an unhandled webhook error:
```json
{
  "results": [
    {
      "toolCallId": "call_123456",
      "result": "Registration failed: phone_number must be in E.164 format (e.g. +15551234567)."
    }
  ]
}
```
