# 01 · Tech Stack

## Summary Table

| Layer | Technology | Version / Plan | Why |
|-------|-----------|----------------|-----|
| Voice platform | **Vapi.ai** | Free trial credits | Managed telephony + STT + TTS + LLM routing in one SDK |
| Phone number | **Twilio** | Trial account | Real PSTN number; imports into Vapi |
| LLM | **Groq — Llama 3.3 70B** | Free tier | Fast inference, high context window, tool-call support |
| STT | Vapi default (Deepgram Nova 2) | Bundled | Low-latency, accurate |
| TTS | Vapi default (ElevenLabs / PlayHT) | Bundled | Natural, low-latency voice |
| API framework | **FastAPI** | Latest stable | Async, auto-docs, Pydantic validation |
| ORM | **SQLAlchemy 2.x** | Latest stable | Pythonic, supports async; pairs well with FastAPI |
| DB migrations | **Alembic** | Latest stable | Tracks schema changes; integrates with SQLAlchemy |
| Database | **Supabase Postgres** | Free (500 MB) | Managed Postgres; survives restarts; free connection pooling |
| Hosting | **Render.com** | Free Web Service | Zero-config deploys from GitHub; free TLS |
| Secrets | Environment variables | — | Render env vars dashboard |
| Validation | **Pydantic v2** | Bundled with FastAPI | Schema enforcement, field-level error messages |
| HTTP client | **httpx** | Latest stable | Async requests (if backend calls external APIs) |
| Testing | **pytest + httpx** | Latest stable | Unit + integration tests |

---

## Free-Tier Constraints

| Service | Limit | Impact |
|---------|-------|--------|
| Groq free | 30 req/min, 6 000 tokens/min | Fine for demo/low volume |
| Vapi free | Trial credits (~$10) | Enough for 30–60 test calls |
| Twilio trial | $15.50 credit; calls to verified numbers only | Restrict test callers to verified numbers |
| Supabase free | 500 MB storage, 2 direct connections | Use connection pooling (PgBouncer) |
| Render free | 750 h/month, spins down after 15 min idle | Add keep-alive ping |

---

## Dependency List (requirements.txt skeleton)

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
sqlalchemy>=2.0.0
alembic>=1.13.0
asyncpg>=0.29.0          # async Postgres driver
pydantic>=2.7.0
pydantic-settings>=2.3.0 # .env loading
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

---

## Vapi Custom LLM Provider Setup

1. In Vapi dashboard → **Models** → **Custom LLM**.
2. Set endpoint to `https://api.groq.com/openai/v1/chat/completions`.
3. Set model to `llama-3.3-70b-versatile`.
4. Add header `Authorization: Bearer {GROQ_API_KEY}`.
5. Vapi forwards conversation messages in OpenAI chat format; Groq responds in OpenAI format.

---

## Why NOT SQLite

SQLite stores data in a local file. Render.com free services have an **ephemeral filesystem** — any file written is lost on redeploy or restart. Supabase Postgres is a **managed external database** that survives all restarts.

---

## Future Stack Additions (out of scope for MVP)

| Addition | Trigger |
|----------|---------|
| Redis | If async task queue needed (e.g., send confirmation SMS) |
| Celery | Background worker for post-registration tasks |
| Sentry | Error monitoring in production |
| GitHub Actions | CI/CD pipeline |
