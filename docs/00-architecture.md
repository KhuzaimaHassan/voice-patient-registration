# 00 · System Architecture

## Overview

A fully free-tier, voice-first patient registration pipeline. A caller dials a real U.S. phone number; a voice AI agent captures their registration data; a FastAPI backend persists it to Postgres.

---

## High-Level Architecture Diagram

```
Caller (PSTN / Mobile / Landline)
     │
     ▼
Free Vapi U.S. Phone Number
(Built-in Vapi telephony / SIP gateway)
     │
     ▼
Vapi.ai Platform
  ├─ Telephony layer (Native Vapi voice gateway)
  ├─ STT engine  (Soniox STT RT v5 — 1.8% WER, accent-optimized)
  ├─ TTS engine  (Vapi Elliot v2 / Clara v2)
  └─ LLM  ──────►  OpenAI GPT-5/4o Mini (or Groq Llama 3.3 70B)
              │
              │  Tool call: register_patient
              ▼
       FastAPI Backend  (Render.com free Web Service: /vapi/register-patient)
              │
              ▼
       Supabase Postgres  (free tier)
```

---

## Component Responsibilities

| Component | Role | Free Tier |
|-----------|------|-----------|
| **Vapi Free Number** | Native PSTN U.S. phone number & voice gateway | Yes – included in Vapi trial |
| **Vapi.ai** | Orchestrates telephony + STT + TTS + LLM + tools | Yes – free trial credits ($10) |
| **Soniox STT** | Speech-to-Text (1.8% WER, accent-tolerant, $0.004/min) | Bundled in Cost Saver |
| **GPT-5/4o Mini** | Conversational reasoning & tool argument generation | Bundled in Cost Saver ($0.01/min) |
| **Vapi Voice (Elliot/Clara)** | Natural, low-latency TTS audio ($0.02/min) | Bundled in Cost Saver |
| **FastAPI** | REST API, validation, business logic, webhook | n/a (code) |
| **SQLAlchemy** | ORM, schema migrations | n/a (library) |
| **Supabase Postgres** | Persistent relational database | Yes – 500 MB free |
| **Render.com** | Host the FastAPI app | Yes – free Web Service |

---

## Data Flow — Happy Path

```
1. Caller dials Free Vapi Phone Number from any phone.
2. Vapi answers natively via its telephony gateway.
3. Vapi starts conversation with the configured assistant ("Patient Registration Assistant").
4. Vapi transcribes speech with Soniox STT and sends utterance to LLM (GPT Mini / Groq).
5. LLM returns either:
     (a) A spoken reply (next question, read-back, confirmation)
     (b) A tool-call JSON: register_patient({...})
6. Vapi executes the tool call by POSTing to FastAPI /vapi/register-patient on Render.
7. FastAPI validates, writes to Supabase Postgres, returns { results: [...] }.
8. Vapi speaks the confirmation message to the caller.
9. Call ends cleanly.
```

---

## Data Flow — Correction Loop

```
After read-back, if caller says "no" or "fix ...":
  LLM identifies field(s) to correct, re-prompts.
  Once corrected, LLM reads back all data again.
  Loop until caller confirms, then tool call fires.
```

---

## Failure Modes and Mitigations

| Failure | Mitigation |
|---------|-----------|
| Groq API timeout | Vapi retry / fallback message |
| FastAPI cold start on Render free | Keep-alive ping (UptimeRobot) |
| Supabase connection limit | SQLAlchemy connection pool (max 5) |
| Invalid field (bad DOB, bad phone) | LLM re-prompts; server-side 422 validation |
| Duplicate phone number (bonus) | GET /patients?phone=... before POST |

---

## Security Considerations

- All secrets (API keys, DB URL) in environment variables — never hardcoded.
- Vapi webhook secret header validated on every inbound request.
- HTTPS enforced by Render.com (TLS termination).
- Soft-delete pattern (deleted_at) avoids accidental data loss.
- No PII logged beyond what Supabase stores (opt-in logging only).

---

## Scalability Notes (for future)

- Render free tier to paid tier when call volume grows.
- Supabase free to paid (8 GB) when storage grows.
- Groq free to paid for higher RPM limits.
- Add Redis queue if concurrent registrations spike.
