# 09 · Next Steps and Bonus Features

## MVP Completion Checklist

Before considering the project "done", verify all items:

### Backend
- [ ] FastAPI app created in `/backend/app/`
- [ ] SQLAlchemy models defined (`Patient`)
- [ ] Pydantic schemas defined (Create, Update, Response)
- [ ] All 5 REST endpoints implemented (GET list, GET by ID, POST, PUT, DELETE)
- [ ] Soft-delete filter applied to all queries
- [ ] Response envelope `{ data, error }` on all routes
- [ ] Alembic migration created and tested
- [ ] `requirements.txt` complete and pinned
- [ ] `.env.example` committed (no real secrets)
- [ ] Tests written for all endpoints

### Infrastructure
- [ ] Supabase project created and schema applied
- [ ] Render.com Web Service deployed from GitHub
- [ ] All environment variables set on Render
- [ ] `/health` endpoint returns 200 after cold start
- [ ] Keep-alive ping configured (UptimeRobot or similar)

### Voice Agent
- [ ] Groq API key created
- [ ] Twilio number imported into Vapi
- [ ] Custom LLM provider configured in Vapi (Groq)
- [ ] Vapi assistant created with correct system prompt
- [ ] `register_patient` tool configured in Vapi, pointing to Render URL
- [ ] Full E2E call tested successfully
- [ ] Record confirmed in Supabase after test call

---

## Bonus Features (Time-Permitting)

### Bonus 1 — Duplicate Caller Detection (High Value)

**What:** Before creating a new patient, check if a patient with the same `phone_number` already exists.

**How:**
1. In `POST /patients`, before insert, query `SELECT * FROM patients WHERE phone_number = ? AND deleted_at IS NULL`.
2. If found, return `HTTP 409` with the existing patient in `data` and a message in `error`.
3. Update the Vapi system prompt to handle the 409 response: "I found an existing record for this phone number. Would you like to update your information instead?"
4. If caller says yes, agent collects updated fields and calls `PUT /patients/{id}`.

**Estimated effort:** 2–3 hours.

---

### Bonus 2 — SMS Confirmation After Registration

**What:** After successful registration, send the patient an SMS confirmation with their registration ID.

**How:**
1. Add `twilio` Python library to `requirements.txt`.
2. Add env vars: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`.
3. After successful `POST /patients`, call Twilio Messaging API to send SMS to `phone_number`.
4. SMS text: "Thank you for registering. Your patient ID is [UUID]. Reply STOP to opt out."

**Estimated effort:** 2 hours.

---

### Bonus 3 — Admin Dashboard (Read-Only)

**What:** A simple HTML page (served by FastAPI) that lists recent registrations.

**How:**
1. Add `jinja2` to requirements.
2. Add a `GET /admin` route that renders a Jinja2 template.
3. Template: table of patients sorted by `created_at DESC`, limit 50.
4. Add basic HTTP Basic Auth (username/password via env vars).

**Estimated effort:** 3–4 hours.

---

### Bonus 4 — Preferred Language Routing

**What:** If caller's `preferred_language` is not English, route future calls to a language-specific assistant.

**How:**
1. In Vapi, create assistants for Spanish, French, etc.
2. In the registration assistant, after collecting `preferred_language`, note it in the conversation.
3. Post-registration: look up patient by phone, check `preferred_language`, route via Vapi's `call.transfer` to the appropriate assistant.

**Estimated effort:** 4–6 hours.

---

### Bonus 5 — Webhook for Post-Registration Events

**What:** After a patient is registered, emit a webhook to an external system (e.g., EHR, scheduling system).

**How:**
1. Add `WEBHOOK_URL` and `WEBHOOK_SECRET` env vars.
2. After successful `POST /patients`, send `httpx.post(WEBHOOK_URL, json=patient_data, headers={"X-Signature": hmac_sig})` in a background task.
3. Implement HMAC-SHA256 signature for security.

**Estimated effort:** 2 hours.

---

## Recommended Build Order

```
Week 1, Day 1:  Supabase setup + Alembic migration (02-database-schema.md)
Week 1, Day 2:  FastAPI skeleton + all endpoints (03-api-spec.md)
Week 1, Day 3:  Unit + integration tests (07-testing-plan.md)
Week 1, Day 4:  Render.com deployment + env setup (06-setup-provisioning.md)
Week 1, Day 5:  Vapi assistant + Groq LLM + Twilio integration (04-voice-agent-design.md)
Week 2, Day 1:  E2E testing + bug fixes
Week 2, Day 2:  Bonus 1 (duplicate detection) — highest value
Week 2, Day 3:  Bonus 2 (SMS) or Bonus 3 (admin dashboard)
Week 2, Day 4+: Documentation, README, cleanup
```

---

## Known Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Groq rate limit during demo | Medium | High | Cache LLM responses for test scripts; use low-volume calls |
| Vapi trial credits exhausted | Low | High | Monitor usage dashboard; limit test calls to <30 |
| Supabase connection limit | Medium | Medium | Use connection pooler (port 6543) |
| Render cold start >30s | High | Medium | Keep-alive ping via UptimeRobot |
| LLM hallucinates patient data | Low | High | Re-prompt logic in system prompt; server-side validation |
| Twilio trial restricts callers | High | Medium | Verify all test phone numbers in Twilio console |

---

## Future Production Considerations

| Topic | Action |
|-------|--------|
| HIPAA compliance | Add BAA with all vendors, enable audit logging, encrypt PII at rest |
| Authentication | Add API key or OAuth2 to all endpoints |
| Rate limiting | Add per-IP rate limiting (SlowAPI) |
| Monitoring | Integrate Sentry for error tracking |
| CI/CD | GitHub Actions for automated test + deploy |
| Database backup | Enable Supabase daily backups (available on paid tier) |
| Multi-region | Deploy FastAPI to multiple Render regions for lower latency |
