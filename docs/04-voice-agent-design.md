# 04 · Voice Agent Design

## Overview

The Vapi.ai assistant is configured as a patient registration intake agent. It follows a structured script, validates inputs in real-time (via LLM reasoning), reads back all data for confirmation, handles corrections, and fires a tool call to persist the record.

---

## Conversation State Machine

```
[START]
    |
    v
[GREETING]
    |
    v
[COLLECT REQUIRED FIELDS]  <--+
    |                          |
    v                          |
[VALIDATE FIELD]               |
    |-- invalid ---------------+
    |-- valid
    v
[ALL REQUIRED COLLECTED?]
    |-- no --> next field
    |-- yes
    v
[OFFER OPTIONAL FIELDS BATCH]
    |-- caller says yes --> collect optional fields
    |-- caller says no/skip
    v
[READ BACK ALL COLLECTED DATA]
    |
    v
[CALLER CONFIRMS?]
    |-- no --> [CORRECTION FLOW] --> back to READ BACK
    |-- yes
    v
[TOOL CALL: register_patient]
    |
    v
[CONFIRMATION MESSAGE]
    |
    v
[END CALL]
```

---

## Field Collection Order

### Phase 1 — Required Fields (collected in this order)

1. `first_name`
2. `last_name`
3. `date_of_birth`
4. `sex`
5. `phone_number`
6. `address_line_1`
7. `city`
8. `state`
9. `zip_code`

### Phase 2 — Optional Fields (offered as a batch)

After confirming required fields, agent asks: "Would you like to provide some additional optional information?"

If yes, collect in order:
1. `address_line_2`
2. `email`
3. `insurance_provider` + `insurance_member_id` (together)
4. `preferred_language` (if not English)
5. `emergency_contact_name` + `emergency_contact_phone` (together)

---

## Sample Dialogue Script

```
AGENT: Hello! Welcome to the patient registration line. I am here to help
       you register as a new patient. This should take about 2 to 3 minutes.
       Let's get started. What is your first name?

CALLER: Jane.

AGENT: Thank you, Jane. And your last name?

CALLER: Doe.

AGENT: Got it. Jane Doe. What is your date of birth? Please say the month,
       day, and year — for example, May 15th, 1990.

CALLER: May 15, 1990.

AGENT: Perfect. Are you male, female, or would you prefer to say other or
       prefer not to say?

CALLER: Female.

AGENT: And what is the best phone number to reach you? Please include the
       area code.

CALLER: 555-123-4567.

AGENT: I have that as +1 555 123 4567. Is that correct?

CALLER: Yes.

AGENT: What is your street address?

CALLER: 123 Main Street.

AGENT: And your city?

CALLER: Austin.

AGENT: Your state?

CALLER: Texas.

AGENT: And your ZIP code?

CALLER: 78701.

AGENT: Great. Would you like to provide some optional additional information,
       such as your email, insurance details, or an emergency contact?

CALLER: Sure.

[... optional field collection ...]

AGENT: Let me read back everything to make sure I have it right.
       Name: Jane Doe. Date of birth: May 15, 1990. Sex: Female.
       Phone: +1 555 123 4567. Address: 123 Main Street, Austin, Texas, 78701.
       [any optional fields collected]
       Does everything look correct?

CALLER: Actually, my zip code is 78702, not 78701.

AGENT: Of course. Let me update that. Your ZIP code is now 78702.
       Let me read everything back again...

       [reads back again]

       Does that all look correct?

CALLER: Yes, that is correct.

AGENT: Wonderful. I am saving your registration now...

       [tool call fires]

       You have been successfully registered. Your registration ID is [ID].
       Is there anything else I can help you with?

CALLER: No, thank you.

AGENT: Thank you, Jane. Have a great day. Goodbye!
```

---

## Field Validation (LLM-level, before tool call)

| Field | Validation | Re-prompt message |
|-------|-----------|-------------------|
| `date_of_birth` | Must be parseable date; must be in the past | "I did not quite catch that. Could you repeat your date of birth? Please say month, day, and year." |
| `phone_number` | 10 digits after stripping formatting | "Could you repeat that phone number including the area code?" |
| `state` | Must be a valid US state name or abbreviation | "Could you confirm the state? For example, say Texas or TX." |
| `zip_code` | Exactly 5 digits (or 5+4) | "I need a 5-digit ZIP code. Could you repeat that?" |
| `sex` | One of allowed values | "Please say male, female, other, or prefer not to say." |
| `email` | Basic email pattern if provided | "That email did not sound right. Could you spell it out?" |

---

## LLM System Prompt Structure

```
You are a friendly and professional patient registration assistant.
Your job is to collect patient registration information over the phone.

Rules:
1. Collect fields in the specified order.
2. After receiving a value, repeat it back to confirm before moving on.
3. If a value seems invalid (bad date, too few digits for phone, etc.), re-prompt once.
4. After all required fields, offer optional fields.
5. Before calling register_patient, read back ALL collected data and ask for confirmation.
6. If the caller wants to correct a field, update it and read back all data again.
7. Only call register_patient once the caller has explicitly confirmed all data is correct.
8. Be concise, warm, and professional. Avoid medical jargon.
9. If the caller asks something unrelated to registration, politely redirect them.
10. Do not make up or assume any field values.
```

---

## Vapi Assistant Configuration Checklist

- [ ] Assistant name: "Patient Registration Assistant"
- [ ] Voice: select a clear, neutral U.S. English voice
- [ ] LLM: Custom LLM → Groq → `llama-3.3-70b-versatile`
- [ ] First message: "Hello! Welcome to the patient registration line..."
- [ ] Tool: `register_patient` → Server URL: `https://<render-app>.onrender.com/patients`
- [ ] Phone number: Twilio number imported into Vapi
- [ ] End call after confirmation message: enabled
- [ ] Recording: disabled (HIPAA consideration)
- [ ] Max call duration: 10 minutes

---

## Handling Edge Cases

| Edge Case | Behavior |
|-----------|---------|
| Caller hangs up mid-flow | No record saved; partial data discarded |
| Caller cannot hear agent | Agent speaks slower on request |
| Caller speaks too fast | Vapi STT transcribes; LLM asks to confirm |
| API error on tool call | Agent says "I encountered an issue saving your record. Please call back." |
| Duplicate phone number | (Bonus) Agent says "I found an existing record. Would you like to update it instead?" |
| Caller refuses all optional fields | Agent skips to confirmation |
| Caller wants to start over | Agent resets collected fields and restarts from first_name |
