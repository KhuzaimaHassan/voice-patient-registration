# 00 · System Architecture

## Overview

A fully free-tier, voice-first patient registration pipeline. A caller dials a real U.S. phone number; a voice AI agent captures their registration data; a FastAPI backend persists it to Postgres.

---

## High-Level Architecture Diagram

```
Caller (PSTN)
     │
     ▼
Twilio Trial Number
(SIP trunk / voice gateway)
     │
     ▼
Vapi.ai Platform
  ├─ Telephony layer (Twilio integration)
  ├─ STT engine  (Vapi default / Deepgram)
  ├─ TTS engine  (Vapi default / ElevenLabs)
  └─ LLM  ──────►  Groq API  (Llama 3.3 70B)
              │
              │  Tool call: register_patient
              ▼
       FastAPI Backend  (Render.com free Web Service)
              │
              ▼
       Supabase Postgres  (free tier)
```

---

## Component Responsibilities

| Component | Role | Free Tier |
|-----------|------|-----------|
| **Twilio Trial** | PSTN phone number, call routing | Yes – trial credits |
| **Vapi.ai** | Orchestrates telephony + STT + TTS + LLM calls | Yes – free trial credits |
| **Groq API** | LLM inference (Llama 3.3 70B) via Vapi custom LLM | Yes – free tier |
| **FastAPI** | REST API, validation, business logic | n/a (code) |
| **SQLAlchemy** | ORM, schema migrations | n/a (library) |
| **Supabase Postgres** | Persistent relational database | Yes – 500 MB free |
| **Render.com** | Host the FastAPI app | Yes – free Web Service |

---

## Data Flow — Happy Path

```
1. Caller dials Twilio number.
2. Twilio routes call to Vapi.ai webhook/SIP.
3. Vapi starts a conversation with the configured assistant.
4. Vapi sends each user utterance to Groq (Llama 3.3 70B) as the LLM.
5. LLM returns either:
     (a) A spoken reply (next question / confirmation)
     (b) A tool-call JSON: register_patient({...})
6. Vapi executes the tool call by POSTing to FastAPI  /patients.
7. FastAPI validates, writes to Supabase Postgres, returns { data, error }.
8. Vapi reads the tool result back to the caller as confirmation.
9. Call ends.
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
