# 10 ? Render.com Deployment Configuration

This guide provides the exact configuration required to deploy the **voice-patient-registration** FastAPI backend to Render.com (free tier).

---

## Deployment Option A: Render Dashboard (Manual)

1. Sign in to [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** ? **Web Service**.
3. Connect your GitHub repository: `https://github.com/KhuzaimaHassan/voice-patient-registration`.
4. Configure the service settings:

| Setting | Value |
|---|---|
| **Name** | `voice-patient-registration-api` |
| **Region** | `Oregon (US West)` or `Ohio (US East)` (match Supabase region) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && alembic upgrade head` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | `Free` |

5. Under **Environment Variables**, add:

| Key | Example Value | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:pwd@db.supabase.co:5432/postgres` | Supabase connection string (`asyncpg` driver) |
| `VAPI_WEBHOOK_SECRET` | `<your-webhook-secret>` | Webhook verification secret |
| `ENVIRONMENT` | `production` | Disables `/docs` and enables production settings |
| `LOG_LEVEL` | `INFO` | Standard application log level |

6. Click **Create Web Service**.

---

## Deployment Option B: Render Blueprint (`render.yaml`)

The repository includes a root `render.yaml` file. If deploying via Blueprints:

1. In Render Dashboard, click **New +** ? **Blueprint**.
2. Select your repository.
3. Render reads `render.yaml` and provisions the Web Service automatically.
4. Fill in the empty environment variables (`DATABASE_URL`, `VAPI_WEBHOOK_SECRET`) prompted in the UI.

---

## Health Check & Keep-Alive

- **Health Endpoint**: `/health` (returns `{"data": {"status": "ok"}, "error": null}`).
- **Keep-Alive**: Render free tier spins down after 15 minutes of inactivity. Set up a free ping monitor (e.g. UptimeRobot) targeting `https://<your-render-url>/health` every 5?10 minutes to prevent cold starts during voice calls.