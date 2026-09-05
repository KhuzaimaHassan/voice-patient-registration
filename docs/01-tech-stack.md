# 01 · Tech Stack

## Summary Table

| Layer | Technology | Version / Plan | Why |
|-------|-----------|----------------|-----|
| Voice platform | **Vapi.ai** | Free trial credits ($10) | Managed telephony + STT + TTS + LLM routing + webhooks |
| Phone number | **Free Vapi Number** | Included in Vapi trial | Native US PSTN number directly in dashboard (no Twilio needed) |
| LLM | **GPT-5 Mini / GPT-4o Mini** *(or Groq Llama 3.3 70B)* | Cost Saver preset | High intelligence (14), ultra-reliable tool calling, $0.01/min |
| STT | **Soniox (STT RT v5)** | Bundled ($0.004/min) | Best accent accuracy (1.8% Word Error Rate vs 3.3% Deepgram) |
| TTS | **Vapi Elliot v2 / Clara v2** | Bundled ($0.02/min) | Natural, low-latency voice, avoids expensive ElevenLabs rates |
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
| Vapi Cost Saver | ~$0.065 – $0.08 / min total | ~$0.31 per 5-min call (~60+ mins of testing with $5 credit) |
| Free Vapi Number | Up to 5 free US numbers | Inbound calling from any phone without restrictions |
| Supabase free | 500 MB storage, connection pooler (port 6543) | Prepared statement cache disabled for PgBouncer |
| Render free | 750 h/month, spins down after 15 min idle | UptimeRobot keep-alive ping on /health prevents cold starts |

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
