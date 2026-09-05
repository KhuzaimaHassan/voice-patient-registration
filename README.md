# Voice Patient Registration

A production-ready voice AI intake agent and backend pipeline for U.S. patient registration.

Callers dial a real U.S. phone number and speak with an empathetic, conversational AI agent that collects their registration information, checks for misheard pronunciations, reads back the summary for verbal confirmation, and persists the record to a Postgres database via a dedicated webhook.

---

## High-Level Architecture

```
PSTN Caller (Mobile/Landline)
             │
             ▼
   Free Vapi U.S. Number (Native Telephony)
             │
             ▼
      Vapi.ai Platform
        ├─ STT: Soniox (STT RT v5 — 1.8% Word Error Rate, accent-tolerant)
        ├─ LLM: OpenAI GPT-5 Mini / GPT-4o Mini (or Groq Llama 3.3 70B)
        ├─ TTS: Vapi Native Voice (Elliot v2 / Clara v2)
        └─ Tool Call: register_patient
             │
             ▼
   FastAPI Webhook & REST Backend (Render.com)
     ├─ POST /vapi/register-patient  (Vapi tool-calls webhook)
     └─ REST /patients               (Public CRUD API)
             │
             ▼
   Supabase PostgreSQL (via PgBouncer transaction pooler)
```

---

## Live Endpoints

* **Base URL:** `https://voice-patient-registration-b4n2.onrender.com`
* **Health Check:** `https://voice-patient-registration-b4n2.onrender.com/health`
* **Vapi Tool Webhook:** `https://voice-patient-registration-b4n2.onrender.com/vapi/register-patient`
* **Patients REST API:** `https://voice-patient-registration-b4n2.onrender.com/patients`

---

## Key Features

1. **Natural Dialogue & Edge-Case Guardrails:**
   - Detects state vs city (e.g. catches "San Francisco" when asked for a state).
   - Assembles chunked spoken digits for phone numbers and street addresses.
   - Clarifies ambiguous answers before progressing.
2. **Pronunciation & Accent Tolerant (Soniox STT):**
   - Uses Soniox `STT RT v5` with a low 1.8% Word Error Rate (vs 3.3% in standard engines) to accurately capture medical names, street addresses, and cities.
3. **Conversational Correction Loop:**
   - Reads back all collected details with a single, unambiguous confirmation question: *"Does all of that information sound correct to you?"*.
   - Allows caller to say *"No"*, catches errors, updates memory, and re-reads the summary.
4. **Cost-Optimized Architecture (~$0.065/min):**
   - Uses Vapi's **Cost Saver** preset (Soniox STT at $0.004/min, GPT Mini at $0.01/min, Vapi Voice at $0.02/min), reducing call cost by **67%** compared to standard tiers (~$0.31 per 5-minute registration call).
5. **Robust Database Layer:**
   - Supabase Postgres with async SQLAlchemy (`asyncpg`) and Alembic migrations.
   - Configured with `statement_cache_size=0` to support PgBouncer transaction pooling.
   - Soft-delete pattern (`deleted_at`) prevents accidental data loss.

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **Voice Platform** | Vapi.ai | Telephony, speech streaming, LLM routing |
| **Phone Gateway** | Free Vapi Number | Direct U.S. inbound phone number |
| **Speech-to-Text** | Soniox (`STT RT v5`) | Real-time transcription (1.8% WER, $0.004/min) |
| **LLM Inference** | GPT-5 Mini / GPT-4o Mini | Dialogue management & tool argument extraction ($0.01/min) |
| **Text-to-Speech** | Vapi Elliot v2 / Clara v2 | Low-latency natural voice synthesis ($0.02/min) |
| **Backend Framework** | FastAPI (Python 3.13) | REST API & Vapi webhook handler |
| **Database ORM** | SQLAlchemy 2.x + Alembic | Async relational persistence & migrations |
| **Database** | Supabase Postgres | Hosted PostgreSQL database with connection pooler |
| **Cloud Hosting** | Render.com | Automated deployment from GitHub with free SSL |

---

## Local Development & Testing

### 1. Setup Environment
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
```

### 2. Run Test Suite
```bash
pytest tests -v
```

### 3. Start Local Server
```bash
uvicorn app.main:app --reload --port 8000
```
