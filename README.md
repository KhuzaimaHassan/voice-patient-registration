# Voice Patient Registration

A production-ready, voice AI-driven intake agent and backend pipeline for U.S. patient registration.

Callers dial a real U.S. phone number and speak with an empathetic, conversational AI agent that collects essential registration details, accurately interprets accents and street addresses, offers optional information, performs a full verbal read-back for confirmation, handles real-time corrections, and persists the patient record into a cloud PostgreSQL database.

---

## Live Deployment & Demo

- **Repository**: [https://github.com/KhuzaimaHassan/voice-patient-registration](https://github.com/KhuzaimaHassan/voice-patient-registration)
- **Live API Base URL**: [https://voice-patient-registration-b4n2.onrender.com](https://voice-patient-registration-b4n2.onrender.com)
- **Interactive Swagger Docs**: [https://voice-patient-registration-b4n2.onrender.com/docs](https://voice-patient-registration-b4n2.onrender.com/docs)
- **Health Check**: [https://voice-patient-registration-b4n2.onrender.com/health](https://voice-patient-registration-b4n2.onrender.com/health)
- **Vapi Inbound Phone Number**: `+1 (346) 344-1337` *(Assigned via Vapi Free Number)*

---

## High-Level Architecture

```
PSTN Caller (Mobile / Landline)
             │
             ▼
    Free Vapi U.S. Phone Number
    (Built-in Vapi Telephony / SIP Gateway — No Twilio needed)
             │
             ▼
    Vapi.ai Voice Platform
      ├─ Speech-to-Text: Soniox (STT RT v5 — 1.8% Word Error Rate)
      ├─ LLM Engine:     GPT-5 Mini via Vapi OpenAI Integration (Cost Saver Preset)
      ├─ Text-to-Speech: Vapi Elliot v2 (Low-latency native voice)
      └─ Tool Calling:   register_patient function call
             │
             ▼  POST /vapi/register-patient (HMAC Secret Verified)
    FastAPI Web Service (Render.com Free Tier)
      ├─ Routers:
      │    ├─ POST /vapi/register-patient  (Vapi Tool-Call Envelope Handler)
      │    └─ /patients                    (Standard CRUD REST API)
      ├─ Business Logic: patient_service.create_patient_record()
      └─ Validation:     Pydantic v2 (ISO DOB, E.164 phone, state regex)
             │
             ▼  SQLAlchemy 2.x (asyncpg, statement_cache_size=0)
    Supabase PostgreSQL Database
      └─ Table: patients (PgBouncer Transaction Pooler, Soft Deletes)
```

---

## Tech Stack Summary

| Layer | Technology | Version / Tier | Role |
|---|---|---|---|
| **Voice Platform** | **Vapi.ai** | Free Trial Credits ($10) | Managed telephony, speech streaming, and tool execution orchestration |
| **Phone Gateway** | **Free Vapi Number** | Included in Vapi Trial | Direct inbound U.S. PSTN phone number (no external telephony carrier) |
| **Speech-to-Text (STT)** | **Soniox (`STT RT v5`)** | Cost Saver ($0.004/min) | Ultra-low 1.8% Word Error Rate, accent-resilient transcription |
| **Conversational LLM** | **GPT-5 Mini** | Cost Saver ($0.01/min) | Dialogue flow reasoning and strict JSON parameter extraction |
| **Text-to-Speech (TTS)** | **Vapi Elliot v2** | Cost Saver ($0.02/min) | Natural, low-latency conversational voice synthesis |
| **API Framework** | **FastAPI** | >= 0.111.0 (Python 3.11+) | Async REST API, OpenAPI docs, and dedicated webhook router |
| **Validation Layer** | **Pydantic v2** | >= 2.7.0 | Strict schema enforcement, ISO date validation, and E.164 parsing |
| **ORM & Migrations** | **SQLAlchemy 2.x + Alembic** | Async (`asyncpg`) | Async relational persistence, schema versioning, and constraint checks |
| **Database** | **Supabase Postgres** | Free Tier (500 MB) | Managed PostgreSQL with PgBouncer connection pooler |
| **Cloud Hosting** | **Render.com** | Free Web Service | Automated Git deploys with TLS termination and environment management |
| **Testing** | **pytest + pytest-asyncio + httpx** | Latest | Unit and integration test suite (11/11 automated tests passing) |

---

## Design Decisions & Trade-offs

### 1. Vapi Free U.S. Number vs. Twilio Telephony
* **Decision**: Deployed Vapi's built-in **Free Vapi Number** instead of Twilio SIP trunking.
* **Rationale**: Twilio trial accounts are restricted or unavailable in certain developer countries and require caller-ID pre-verification for every outbound/inbound number. Vapi provides native, unverified U.S. PSTN numbers directly in the dashboard, enabling anyone to dial in immediately from any mobile phone or landline with zero provisioning barriers.

### 2. Vapi Cost Saver Preset (Soniox / GPT-5 Mini / Elliot) vs. Groq Custom LLM
* **Decision**: Swapped the originally planned external Groq (`llama-3.3-70b-versatile`) setup for Vapi's native **"Cost Saver" preset**.
* **Rationale**:
  - **Speech Accuracy**: Soniox `STT RT v5` delivers a **1.8% Word Error Rate** (compared to 3.3% on Deepgram Nova-2), which eliminated frequent acoustic errors on addresses and cities (e.g., mishearing *"Austin"* as *"Awesome"*).
  - **Tool Calling Reliability**: GPT-5 Mini natively adhered to the function schema on the first turn without dropping optional attributes or formatting errors.
  - **Cost & Latency**: Total call costs dropped from **$0.94** to **$0.31** for a 5-minute call (~67% savings, ~$0.065/min), billed directly through Vapi wallet credits without maintaining external API keys or hitting strict per-minute rate limits. *(Groq remains fully documented as an architectural fallback).*

### 3. Supabase Postgres vs. SQLite
* **Decision**: Used hosted Supabase PostgreSQL instead of a local SQLite database.
* **Rationale**: Render's free tier runs on an **ephemeral filesystem** — any local file (including SQLite databases) is permanently wiped whenever the service restarts, redeploys, or spins down from inactivity. Supabase provides persistent, cloud-managed PostgreSQL with automated backups.

### 4. Dedicated `/vapi/register-patient` Webhook vs. Plain `/patients` REST Route
* **Decision**: Created an isolated endpoint (`POST /vapi/register-patient`) rather than modifying `POST /patients` to accept dual formats.
* **Rationale**:
  - `POST /patients` strictly complies with the REST specification in `docs/03-api-spec.md`, consuming a flat JSON body and returning a uniform `{ "data": ..., "error": null }` envelope.
  - Vapi sends a nested tool-call payload (`message.toolCalls[0].function.arguments`) and requires a proprietary response structure (`{ "results": [{ "toolCallId": "...", "result": { ... } }] }`).
  - Separation of concerns: Common patient creation logic was factored into `app/services/patient_service.py` (`create_patient_record`), allowing both endpoints to share the exact same database operations and validation while keeping the public REST contract pristine.

---

## Conversational Voice Interaction Flow

The voice agent is built around a structured state machine with defensive conversational rules:

1. **Required Fields (Sequential Collection)**:
   - `first_name`, `last_name`
   - `date_of_birth` (spoken format converted to ISO `YYYY-MM-DD`, checked for past dates within 150 years)
   - `sex` (mapped to `male`, `female`, `other`, or `prefer_not_to_say`; ambiguous answers like *"yes"* trigger a specific re-prompt rather than generic off-topic deflection)
   - `phone_number` (validated and formatted to E.164: `+1XXXXXXXXXX`)
   - `address_line_1`, `city`, `state` (converted to 2-letter uppercase postal code), `zip_code` (5 digits)
2. **Mandatory Optional Fields Offer**:
   - The agent asks: *"Would you like to provide a few optional details, such as an apartment or suite number, email address, insurance details, or an emergency contact?"*
   - If declined, advances immediately to read-back. If accepted, gathers `address_line_2`, `email`, `insurance_provider`, `insurance_member_id`, `preferred_language`, and `emergency_contact`.
3. **Comprehensive Read-Back & Confirmation**:
   - The agent speaks the entire collected profile and asks: *"Does all of that information sound correct to you?"*
4. **Correction Loop**:
   - If the caller says *"No"* or specifies a mistake (e.g., *"My zip code is 78702, not 78701"*), the agent updates the specific field and re-reads the full summary until explicit verbal confirmation is granted.
5. **Tool Execution**:
   - Upon confirmation, invokes `register_patient`. Once HTTP 200 is received, confirms registration to the caller and concludes the call gracefully.

---

## REST API Reference

All REST endpoints return a standardized envelope:
```json
{
  "data": { ... },
  "error": null
}
```

| Method | Endpoint | Description | Auth / Secret |
|---|---|---|---|
| `GET` | `/health` | Service health check | None |
| `GET` | `/patients` | List active patients (supports `phone_number` filter) | None |
| `GET` | `/patients/{id}` | Retrieve single patient by UUID | None |
| `POST` | `/patients` | Create patient via standard REST body | None |
| `PUT` | `/patients/{id}` | Update existing patient record | None |
| `DELETE` | `/patients/{id}` | Soft-delete patient (`deleted_at` timestamp set) | None |
| `POST` | `/vapi/register-patient` | Dedicated Vapi tool-call webhook endpoint | `X-Vapi-Secret` (Required) |

---

## Local Setup & Development

### Prerequisites
- Python 3.11+
- Git
- Supabase account (free)
- Vapi.ai account (free trial)

### Installation

```bash
# 1. Clone repository
git clone https://github.com/KhuzaimaHassan/voice-patient-registration.git
cd voice-patient-registration/backend

# 2. Set up virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and supply your DATABASE_URL and VAPI_WEBHOOK_SECRET

# 5. Run database migrations
alembic upgrade head

# 6. Start development server
uvicorn app.main:app --reload --port 8000
```

---

## Automated Test Suite

The test suite validates both standard REST operations and Vapi tool-call webhook flows against an async in-memory SQLite database:

```bash
cd backend
pytest tests/ -v
```

### Test Coverage Highlights
- **REST & System Endpoints (`tests/test_patients_api.py`)**:
  - `GET /health` & `GET /docs` (health check and interactive OpenAPI Swagger UI availability)
  - `POST /patients` (successful creation & validation error handling)
  - `GET /patients` & `GET /patients/{id}` (fetching & soft-delete query exclusions)
  - `PUT /patients/{id}` (partial and full updates)
  - `DELETE /patients/{id}` (soft deletion verification)
- **Vapi Webhook (`tests/test_vapi_webhook.py`)**:
  - Valid Vapi tool call payload unpacking and database creation
  - Missing or malformed argument validation
  - Missing tool calls error handling
  - `X-Vapi-Secret` authentication verification and rejection

---

## Known Limitations

1. **Render Free-Tier Cold Starts**:
   - Render free instances spin down after 15 minutes of inactivity. The initial spin-up can take 30–50 seconds, which would cause a voice call webhook to time out if triggered while dormant.
   - **Mitigation**: An external keep-alive monitor (such as UptimeRobot) pinging `GET /health` every 5 minutes maintains warm instances.
2. **Free-Tier Telephony & Database Quotas**:
   - **Vapi**: Free trial includes ~$10 in credits (~120–150 minutes of calls on the Cost Saver preset).
   - **Supabase**: Free tier permits up to 500 MB database storage and limited direct connections (mitigated by using Supabase's transaction pooler on port 6543).
3. **Duplicate Caller Detection (HTTP 409)**:
   - In the MVP, multiple registrations with the same phone number create separate patient records. Duplicate check and update branching is not enabled in this release (see Next Steps).

---

## Next Steps (Bonus Features Backlog)

The following planned bonus features were prioritized after the core MVP voice intake and REST engine:

1. **Duplicate Caller Detection & Update Flow**:
   - Query existing records by phone before creating. If found, return HTTP 409 and prompt the caller: *"I found an existing record. Would you like to update your information instead?"*, calling `PUT /patients/{id}`.
2. **SMS Registration Confirmation**:
   - Dispatch an automated SMS summary with registration confirmation ID to the caller's phone upon successful database commit.
3. **Read-Only Admin Dashboard**:
   - Lightweight server-rendered web view (FastAPI + Jinja2) displaying recent patient registrations with basic authentication.
4. **Multilingual Routing**:
   - Detect caller language preferences and dynamically transfer calls to dedicated Spanish/French Vapi voice assistants.
5. **Outbound EHR Event Webhook**:
   - Emit an HMAC-signed event to external scheduling and electronic health record (EHR) platforms when new patients register.

---

## Project Structure

```
voice-patient-registration/
│
├── .gitignore
├── README.md
├── render.yaml                      # Render Blueprint deployment definition
│
├── docs/                            # Comprehensive engineering specifications
│   ├── 00-architecture.md
│   ├── 01-tech-stack.md
│   ├── 02-database-schema.md
│   ├── 03-api-spec.md
│   ├── 04-voice-agent-design.md
│   ├── 05-env-and-secrets.md
│   ├── 06-setup-provisioning.md
│   ├── 07-testing-plan.md
│   ├── 08-readme-template.md
│   ├── 09-next-steps-bonus.md
│   ├── 10-render-config.md
│   └── 11-vapi-assistant-config.md
│
└── backend/
    ├── .env.example
    ├── alembic.ini
    ├── pytest.ini
    ├── requirements.txt
    │
    ├── alembic/                     # Database migrations
    │   ├── env.py
    │   ├── script.py.mako
    │   └── versions/
    │
    ├── app/
    │   ├── __init__.py
    │   ├── config.py                # Environment & settings configuration
    │   ├── database.py              # Async SQLAlchemy engine & session factory
    │   ├── main.py                  # FastAPI application entrypoint & middleware
    │   ├── models.py                # SQLAlchemy declarative ORM models
    │   ├── schemas.py               # Pydantic v2 validation & response schemas
    │   │
    │   ├── routers/
    │   │   ├── __init__.py
    │   │   ├── patients.py          # Public CRUD REST API endpoints
    │   │   └── vapi_webhook.py      # Dedicated Vapi tool-call webhook router
    │   │
    │   └── services/
    │       ├── __init__.py
    │       └── patient_service.py   # Reusable patient creation & business logic
    │
    └── tests/                       # Automated test suite
        ├── __init__.py
        ├── conftest.py              # Pytest fixtures & async SQLite setup
        ├── test_patients_api.py     # REST API endpoint tests
        └── test_vapi_webhook.py     # Vapi webhook envelope & auth tests
```

---

## License

This project is licensed under the MIT License.
