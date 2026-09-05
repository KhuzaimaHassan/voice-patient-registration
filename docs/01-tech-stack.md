# 01 · Tech Stack

## Summary Table

| Layer | Technology | Version / Plan | Why |
|-------|-----------|----------------|-----|
| Voice platform | **Vapi.ai** | Free trial credits ($10) | Managed telephony + STT + TTS + LLM routing + webhooks |
| Phone number | **Free Vapi Number** | Included in Vapi trial | Native US PSTN number directly in dashboard (no Twilio needed) |
| LLM | **GPT-5 Mini via Vapi OpenAI Integration** | Cost Saver preset | High intelligence (14), native tool calling reliability, $0.01/min |
| STT | **Soniox (STT RT v5)** | Bundled ($0.004/min) | Best accent accuracy (1.8% Word Error Rate vs 3.3% Deepgram) |
| TTS | **Vapi Elliot v2** | Bundled ($0.02/min) | Natural, low-latency voice, avoids expensive ElevenLabs rates |
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

## Architecture Decision: Vapi Cost Saver (GPT-5 Mini) vs Groq Llama 3.3

The initial architecture plan evaluated using Groq (`llama-3.3-70b-versatile`) as a custom LLM provider. However, during live testing, Vapi's native **"Cost Saver" preset** was adopted as the production stack for several decisive reasons:
- **Speech-to-Text Accuracy:** Uses **Soniox (`STT RT v5`)**, which demonstrated a **1.8% Word Error Rate** (vs 3.3% for Deepgram Nova-2), dramatically improving pronunciation and accent comprehension (e.g. capturing cities and street names accurately without phonetic errors).
- **Tool Calling Reliability:** OpenAI's **GPT-5 Mini** integration in Vapi features native function-calling with strict schema adherence, eliminating JSON parsing edge cases during registration.
- **Cost & Latency:** The Cost Saver bundle (Soniox + GPT-5 Mini + Elliot voice) slashed live test call costs from **$0.94** to **$0.31** for a ~5-minute call (a 3x cost reduction), with average turn latency under 2 seconds.
- **Unified Billing:** All voice components (telephony, STT, LLM, TTS) are billed directly through Vapi's wallet/trial credit without needing separate API key maintenance or rate-limit monitoring on external providers.

*(Note: Groq was the original planned LLM and remains a documented fallback via Vapi's Custom LLM provider endpoint if self-hosted or open-weight models are required in the future).*

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
