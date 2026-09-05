# 05 · Environment Variables and Secrets

## Principle

> Zero secrets in code or version control. Every sensitive value lives in the deployment platform's environment variable dashboard.

---

## Complete Variable Reference

### Backend (FastAPI on Render.com)

| Variable | Example Value | Required | Description |
|----------|--------------|----------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres` | YES | Supabase Postgres connection string (async driver) |
| `VAPI_WEBHOOK_SECRET` | `whsec_abc123...` | YES | Validates that inbound requests are from Vapi |
| `ENVIRONMENT` | `production` | YES | `development` or `production` (controls debug mode) |
| `LOG_LEVEL` | `INFO` | NO | Python logging level (default: INFO) |
| `ALLOWED_ORIGINS` | `https://dashboard.vapi.ai` | NO | CORS origins for future dashboard |

### Local Development Only (`.env` file — gitignored)

| Variable | Example Value | Description |
|----------|--------------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:password@localhost:5432/patients_dev` | Local Postgres or Supabase dev project |
| `VAPI_WEBHOOK_SECRET` | `test_secret_123` | Local test secret |
| `ENVIRONMENT` | `development` | Enables debug mode, auto-reload |

### External Services (configured IN the service dashboard, not in backend)

| Service | Where to set | Variable name |
|---------|-------------|---------------|
| Groq API key | Vapi.ai dashboard → Custom LLM headers | `Authorization: Bearer <GROQ_API_KEY>` |
| Twilio credentials | Vapi.ai dashboard → Phone Numbers | Set in Vapi, not in backend |
| Vapi API key | Your CI/CD or local env only if scripting Vapi setup | `VAPI_API_KEY` |

---

## .env File Template

Save as `.env` in `/backend` (never commit this file):

```dotenv
# =============================================
# voice-patient-registration — local .env
# =============================================

# Database
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/patients_dev

# Vapi webhook secret (get from Vapi dashboard)
VAPI_WEBHOOK_SECRET=your_vapi_webhook_secret_here

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

---

## Render.com Environment Variable Setup

1. Go to Render dashboard → your Web Service → **Environment**.
2. Click **Add Environment Variable** for each variable.
3. For `DATABASE_URL`: copy the "Connection String" from Supabase dashboard → Settings → Database → **Connection string** (choose URI format with `asyncpg` driver).
4. Enable **Auto-Deploy** so new values trigger a redeploy.

---

## Supabase Connection String Format

Supabase provides a connection string in this format:

```
postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

For asyncpg (async SQLAlchemy), change the scheme:

```
postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

> Note: Supabase free tier limits direct connections to 2. Use the Transaction Pooler (port 6543) for production:
> `postgresql+asyncpg://postgres:[PASSWORD]@db.[REF].supabase.co:6543/postgres`

---

## Secret Rotation Procedure

1. Generate new secret value.
2. Update in Render dashboard (or Supabase).
3. Trigger redeploy on Render.
4. Verify `/health` endpoint responds 200.
5. Revoke old secret.

---

## What Must NEVER Be Committed

- `.env` files of any kind
- API keys or passwords inline in source code
- Database connection strings in source code
- `*.pem`, `*.key` certificate files
- Any file containing the word `secret` unless it is a template with placeholder values

The `.gitignore` in the project root enforces this.

---

## Security Checklist

- [ ] `.env` is in `.gitignore`
- [ ] No hardcoded credentials in any `.py` file
- [ ] `DATABASE_URL` uses async driver (`asyncpg`)
- [ ] `VAPI_WEBHOOK_SECRET` set on Render before first deploy
- [ ] Supabase password is strong (>= 20 chars, random)
- [ ] Render service is set to "Auto-Deploy on push" only from main branch
