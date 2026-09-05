# 06 · Setup and Provisioning Guide

## Prerequisites Checklist

- [ ] Python 3.11+ installed locally
- [ ] Git installed
- [ ] GitHub account (for Render.com auto-deploy)
- [ ] Twilio account (trial) — https://twilio.com
- [ ] Vapi.ai account (free) — https://vapi.ai
- [ ] Groq account (free) — https://console.groq.com
- [ ] Supabase account (free) — https://supabase.com
- [ ] Render.com account (free) — https://render.com

---

## Step 1 — Twilio Setup

1. Sign up for a Twilio trial account at https://twilio.com.
2. Verify your personal phone number (required for trial calls).
3. Go to **Phone Numbers → Manage → Buy a number**.
4. Search for a U.S. number with voice capability.
5. Purchase the number using your $15.50 trial credit.
6. Note down the number in E.164 format (e.g., `+15551234567`).
7. **Do NOT configure the Twilio webhook** — Vapi will handle routing.

---

## Step 2 — Groq Setup

1. Sign up at https://console.groq.com.
2. Go to **API Keys** → **Create API Key**.
3. Name it `vapi-patient-registration`.
4. Copy and save the key securely (shown only once).
5. Verify you have access to `llama-3.3-70b-versatile` under **Models**.

---

## Step 3 — Vapi.ai Setup

### 3a. Connect Twilio Phone Number

1. Log in to Vapi dashboard.
2. Go to **Phone Numbers** → **Import Twilio Number**.
3. Enter your Twilio Account SID and Auth Token.
4. Select the phone number you purchased.
5. Click **Import**.

### 3b. Create Custom LLM Provider

1. Go to **Models** → **Add Model** → **Custom LLM**.
2. Configure:
   - Name: `Groq Llama 3.3 70B`
   - Endpoint: `https://api.groq.com/openai/v1/chat/completions`
   - Model: `llama-3.3-70b-versatile`
   - Headers: `Authorization: Bearer <YOUR_GROQ_API_KEY>`
3. Save.

### 3c. Create Assistant

1. Go to **Assistants** → **Create Assistant**.
2. Set:
   - Name: `Patient Registration Assistant`
   - LLM: (the Groq custom model you just created)
   - System prompt: (copy from `04-voice-agent-design.md`)
   - First message: `Hello! Welcome to the patient registration line...`
   - Voice: choose a U.S. English voice
3. Add Tool: `register_patient`
   - Type: Function
   - Server URL: `https://<your-render-app>.onrender.com/patients` (update after Step 6)
   - Method: POST
   - Schema: (copy from `03-api-spec.md` → Vapi Tool Definition)
4. Assign the imported Twilio number to this assistant.
5. Save.

---

## Step 4 — Supabase Setup

1. Sign up at https://supabase.com.
2. Click **New Project**.
   - Name: `voice-patient-registration`
   - Password: generate a strong password (save it!)
   - Region: US East (closest to Render free region)
3. Wait for project to provision (~2 minutes).
4. Go to **Settings → Database → Connection string**.
5. Copy the URI and replace `[YOUR-PASSWORD]` with your actual password.
6. Change driver from `postgresql://` to `postgresql+asyncpg://`.
7. Go to **SQL Editor** and run the table creation SQL from `02-database-schema.md`.
8. Verify table exists under **Table Editor → patients**.

---

## Step 5 — Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/voice-patient-registration.git
cd voice-patient-registration/backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate       # Mac/Linux
.\venv\Scripts\Activate.ps1    # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your actual DATABASE_URL and VAPI_WEBHOOK_SECRET

# 5. Run Alembic migrations
alembic upgrade head

# 6. Start the dev server
uvicorn app.main:app --reload --port 8000

# 7. Test the health endpoint
curl http://localhost:8000/health
```

---

## Step 6 — Render.com Deployment

1. Push your backend code to GitHub.
2. Log in to Render.com → **New** → **Web Service**.
3. Connect your GitHub repository.
4. Configure:
   - Name: `voice-patient-registration-api`
   - Environment: `Python 3`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt && alembic upgrade head`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Go to **Environment** tab → add all variables from `05-env-and-secrets.md`.
6. Click **Create Web Service**.
7. Wait for first deploy to complete (3–5 minutes).
8. Copy the URL: `https://<app-name>.onrender.com`.
9. Go back to Vapi → Assistant → Tool → update Server URL with the Render URL.

---

## Step 7 — End-to-End Test

- [ ] Call the Twilio number from a Twilio-verified phone number.
- [ ] Complete the registration flow.
- [ ] Verify record appears in Supabase Table Editor.
- [ ] Test `GET /patients` via browser or curl.
- [ ] Test `GET /patients/:id` with the new UUID.
- [ ] Test `PUT /patients/:id` with a field change.
- [ ] Test `DELETE /patients/:id` and verify `deleted_at` is set.

---

## Keep-Alive (Prevent Render Cold Starts)

Render free Web Services spin down after 15 minutes of inactivity. To prevent this during demos:

1. Use UptimeRobot (free) → New Monitor → HTTP(s).
2. URL: `https://<app-name>.onrender.com/health`
3. Interval: every 5 minutes.
4. This will keep the service warm.

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError` on Render | Missing dependency in requirements.txt | Add missing package, redeploy |
| `asyncpg.exceptions.TooManyConnectionsError` | Supabase connection limit | Use connection pooler (port 6543) |
| Vapi tool call returns 422 | Invalid field format from LLM | Check system prompt validation rules |
| Cold start takes >30s | Render free spin-up | Use keep-alive ping |
| Groq rate limit error | Too many test calls | Wait 1 minute, calls reset |
| Twilio call drops | Trial account restriction | Make sure caller number is verified |
