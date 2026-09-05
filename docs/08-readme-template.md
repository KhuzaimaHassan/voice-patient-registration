# 08 · README Template

> Copy this file to `README.md` in the project root and fill in the bracketed placeholders.

---

```markdown
# Voice Patient Registration

A voice AI phone agent for U.S. patient registration.
Callers dial a real phone number and speak with an AI agent that collects their registration
information and persists it to a database.

## Architecture

```
PSTN Caller → Free Vapi Number (Telephony) → Vapi.ai (Soniox STT + GPT Mini / Groq + Vapi Voice)
                                                        |
                                              FastAPI Backend (Render.com: /vapi/register-patient)
                                                        |
                                              Supabase Postgres
```

## Features

- Natural voice registration flow with re-prompts on invalid input
- Reads back all data for caller confirmation before saving
- Handles corrections and loops until confirmed
- Cost-optimized (Soniox STT at 1.8% WER, GPT Mini, Vapi Voice at ~$0.065/min)
- Optional field batch (email, insurance, emergency contact)
- Soft-delete via `deleted_at` — no data permanently lost
- Dedicated Vapi tool-call webhook (`/vapi/register-patient`) + public REST API (`/patients`)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Voice platform | Vapi.ai |
| Phone number | Free Vapi Number (US PSTN) |
| Speech-to-Text | Soniox STT RT v5 (1.8% WER) |
| LLM | GPT-5 Mini / GPT-4o Mini (or Groq Llama 3.3 70B) |
| Voice (TTS) | Vapi Elliot v2 / Clara v2 |
| Backend | FastAPI + SQLAlchemy (async) |
| Database | Supabase Postgres (PgBouncer pooler) |
| Hosting | Render.com free Web Service |

## Prerequisites

- Python 3.11+
- Vapi.ai free account
- Supabase free project
- Render.com free account

## Local Setup

```bash
git clone https://github.com/[YOUR-ORG]/voice-patient-registration.git
cd voice-patient-registration/backend
python -m venv venv
.\venv\Scripts\Activate.ps1     # Windows
source venv/bin/activate         # Mac/Linux
pip install -r requirements.txt
cp .env.example .env             # then edit .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

See `docs/05-env-and-secrets.md` for the full list.

Key variables:
- `DATABASE_URL` — Supabase Postgres connection string
- `VAPI_WEBHOOK_SECRET` — validates Vapi webhook requests
- `ENVIRONMENT` — `development` or `production`

## API Reference

Base URL: `https://[YOUR-RENDER-APP].onrender.com`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /patients | List patients (with filters) |
| GET | /patients/{id} | Get patient by ID |
| POST | /patients | Create patient |
| PUT | /patients/{id} | Update patient |
| DELETE | /patients/{id} | Soft-delete patient |

Full spec: `docs/03-api-spec.md`

Auto-generated docs available at `/docs` (FastAPI Swagger UI).

## Deployment

1. Push to GitHub.
2. Connect repo to Render.com.
3. Set environment variables in Render dashboard.
4. Build command: `pip install -r requirements.txt && alembic upgrade head`
5. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Full guide: `docs/06-setup-provisioning.md`

## Testing

```bash
pytest backend/tests/ -v
```

Test plan: `docs/07-testing-plan.md`

## Project Structure

```
voice-patient-registration/
|__ docs/
|   |__ 00-architecture.md
|   |__ 01-tech-stack.md
|   |__ 02-database-schema.md
|   |__ 03-api-spec.md
|   |__ 04-voice-agent-design.md
|   |__ 05-env-and-secrets.md
|   |__ 06-setup-provisioning.md
|   |__ 07-testing-plan.md
|   |__ 08-readme-template.md
|   |__ 09-next-steps-bonus.md
|__ backend/
|   |__ app/
|   |   |__ main.py
|   |   |__ models.py
|   |   |__ schemas.py
|   |   |__ database.py
|   |   |__ routers/
|   |       |__ patients.py
|   |__ alembic/
|   |__ tests/
|   |__ requirements.txt
|   |__ .env.example
|__ .gitignore
|__ README.md
```

## Free-Tier Limits

| Service | Limit |
|---------|-------|
| Groq | 30 req/min, 6 000 tokens/min |
| Vapi | Trial credits (~$10) |
| Twilio | $15.50 credit, verified numbers only |
| Supabase | 500 MB, 2 direct connections |
| Render | 750 h/month, spins down after 15 min |

## License

MIT
```
