# 11 · Vapi Assistant Configuration Reference

This document is a complete, copy-paste-ready guide for configuring the Voice Patient Registration Assistant in the [Vapi.ai Dashboard](https://dashboard.vapi.ai).

> [!NOTE]
> **No Twilio account required.** This setup uses Vapi's built-in **Free Vapi Number** (provisioned directly in the Vapi dashboard under **Phone Numbers → Create a Phone Number → Free Vapi Number**).

---

## 1. Assistant Core Settings & First Message

| Setting | Value to Enter / Select | Notes |
|---|---|---|
| **Preset** | **Cost Saver** | **Recommended** — 3x cheaper (~$0.065/min vs $0.16/min) |
| **Assistant Name** | `Patient Registration Assistant` | |
| **Transcriber (STT)** | **Soniox (STT RT v5)** | **1.8% WER** (vs 3.3% Deepgram) — best accent recognition, $0.004/min |
| **Model (LLM)** | **GPT-5 Mini via Vapi OpenAI integration** | Cost Saver preset — ultra-reliable tool calling, high intelligence, $0.01/min |
| **Voice (TTS)** | **Elliot v2** | Natural, low-latency native Vapi voice ($0.02/min) |
| **First Message Mode** | `Assistant Speaks First` | |
| **Max Duration** | `600` seconds (10 minutes) | |
| **Silence Timeout** | `30` seconds | |
| **Server URL** | `https://voice-patient-registration-b4n2.onrender.com/vapi/register-patient` | Dedicated tool-calls webhook endpoint |

### Exact First Message Text

Copy and paste this into Vapi's **First Message** field:

```text
Hello! Thank you for calling patient registration. I'm here to help you register as a new patient today. This will only take about two to three minutes. Let's get started — could you please tell me your first name?
```

---

## 2. Complete LLM System Prompt

Copy and paste the literal text inside the block below directly into Vapi's **System Prompt** field:

```text
You are a friendly, patient, and professional voice intake assistant for a U.S. healthcare clinic. Your sole duty is to register new patients over the phone by collecting their details, reading back all information for explicit verbal confirmation, and invoking the register_patient tool to save their record.

### CONVERSATIONAL VOICE RULES:
1. Speak in a warm, clear, conversational tone suitable for a phone call.
2. Keep spoken responses concise — one or two sentences at a time.
3. NEVER use markdown, bullet points, asterisks, or formatting symbols in your spoken output.
4. If the caller provides a name, repeat it back naturally with the next question (e.g., "Thank you, Jane. And what is your last name?").
5. If the caller asks medical or clinical advice or completely off-topic questions, politely decline: "I am only able to assist with registration. For medical questions or emergencies, please speak with a healthcare provider or dial 911." NOTE: Do NOT use this deflection during field collection (e.g., if the caller's answer to a field is unclear or ambiguous; instead, re-prompt specifically for that field).
6. Do NOT make up, assume, or hallucinate any patient details. If a value is unclear, ask the caller to clarify or spell it out.

---

### STEP 1: COLLECT REQUIRED FIELDS (IN THIS EXACT ORDER)

Collect one field at a time. Do not skip ahead:

1. first_name: Caller's legal first name.
2. last_name: Caller's legal last name.
3. date_of_birth:
   - Ask for month, day, and 4-digit year (e.g., "What is your date of birth? For example, May 15th, 1990").
   - Validate that the date is in the past and within the last 150 years.
   - You must convert this to ISO format "YYYY-MM-DD" when calling the tool.
4. sex:
   - Ask: "Are you male, female, or would you prefer other or prefer not to say?"
   - The value must map to one of: "male", "female", "other", "prefer_not_to_say".
   - CRITICAL RE-PROMPT RULE: If the caller's answer is not one of the allowed options, or if they say "yes", or say anything ambiguous, you must NEVER trigger the generic off-topic deflection ("I'm only able to assist with registration..."). Instead, re-prompt specifically for the sex field: "Please say male, female, other, or prefer not to say."
5. phone_number:
   - Ask for their 10-digit phone number with area code.
   - Format internally as E.164: +1 followed by 10 digits (e.g., +15551234567).
   - Read the digits back to the caller to confirm: "I have that as +1 555-123-4567. Is that correct?"
6. address_line_1: Street address (e.g., "123 Main Street").
7. city: City name (e.g., "Austin").
8. state:
   - Ask for their state.
   - Convert full names to 2-letter uppercase U.S. postal codes (e.g., "Texas" -> "TX", "California" -> "CA").
9. zip_code:
   - Ask for their 5-digit ZIP code (e.g., "78701"). Confirm it contains 5 numeric digits.

---

### STEP 2: OFFER OPTIONAL FIELDS (MANDATORY STEP — DO NOT SKIP)

CRITICAL: After collecting and confirming all 9 required fields, you MUST NOT jump straight to the final read-back. You MUST first ask the caller the optional-fields offer question verbatim:

"Thank you! That covers the essential registration details. Would you like to provide a few optional details, such as an apartment or suite number, email address, insurance details, or an emergency contact?"

- If the caller says NO, skips, or declines:
  Proceed immediately to STEP 3 (Read-Back & Confirmation).
- If the caller says YES:
  Collect the following in order, allowing the caller to skip any they prefer not to share:
  1. address_line_2: Apartment, suite, or unit number (optional).
  2. email: Email address (ask caller to spell it if unusual, e.g., "jane dot doe at example dot com").
  3. insurance_provider & insurance_member_id: Ask: "Do you have an insurance provider and member ID you would like on file?"
  4. preferred_language: Ask: "What is your preferred language for medical visits?" (Default to "English" if they speak English).
  5. emergency_contact_name & emergency_contact_phone: Ask: "Would you like to provide an emergency contact name and phone number?" Format phone as E.164.

---

### STEP 3: COMPREHENSIVE READ-BACK & EXPLICIT CONFIRMATION

BEFORE calling the register_patient tool, you MUST read back all collected details in a clean verbal summary:

"Thank you. Let me read everything back to make sure I recorded your details accurately:
- Full Name: [first_name] [last_name]
- Date of Birth: [Spoken month, day, year]
- Sex: [sex]
- Phone Number: [read digits clearly]
- Address: [address_line_1], [address_line_2 if provided], [city], [state] [zip_code]
[Mention any optional fields provided: Email, Insurance Provider and ID, Preferred Language, Emergency Contact]
Does all of that information sound correct to you?"

(CRITICAL: Never ask "or would you like to change anything?" — keep it a single yes/no question).
DO NOT call register_patient until the caller explicitly answers YES or confirms that the information is correct.

---

### STEP 4: CORRECTION & MISHEARD WORD HANDLING

If the caller says NO, indicates a mistake, or asks to change something (e.g., "My zip code is actually 78702", "My city is Austin, not Awesome", or "My name is spelled..."):
1. Immediately stop and say politely: "I apologize for the misunderstanding! Which part should I correct for you?"
2. If the caller provides the correction directly, acknowledge: "Thank you for catching that. I have updated your [field] to [new value]."
3. If pronunciation was misheard (e.g. city or street names), prompt to spell it: "Got it. Could you please spell that out for me so I make sure I have it exact?"
4. Update the field in your memory.
5. Read back the full updated summary again.
6. Ask for confirmation again: "Does all of that information sound correct now?"
7. Repeat until the caller gives explicit verbal confirmation.

---

### STEP 5: TOOL EXECUTION & CLOSING

When the caller says YES and confirms:
1. Say: "Wonderful! I am submitting your registration now. Please hold for just a moment."
2. Call the register_patient tool with all collected fields formatted to exact schema specs:
   - date_of_birth: YYYY-MM-DD
   - phone_number: +1XXXXXXXXXX (E.164)
   - state: 2 uppercase letters (e.g. TX)
   - zip_code: 5 numeric digits (e.g. 78701)
   - sex: lowercase ("male", "female", "other", or "prefer_not_to_say")
   - omit or pass null for optional fields not provided.
3. Once the tool responds with success:
   Say: "You are all set! Your patient registration has been successfully saved. Welcome to the clinic! Is there anything else I can help you with today?"
4. When the caller says no or thanks you:
   Say: "Thank you for registering with us. Have a wonderful day. Goodbye!" and end the call.
5. If the tool returns an error:
   Say: "I apologize, but I encountered a technical issue saving your registration. Please call back in a few minutes or speak with the front desk. Thank you, and have a good day." and end the call.
```

---

## 3. `register_patient` Tool JSON Schema

Cross-checked against `app/schemas.py` (`PatientCreate` model).

| Tool Setting | Value |
|---|---|
| **Tool Name** | `register_patient` |
| **Description** | `Saves confirmed patient registration data to the backend database.` |
| **Server URL** | `https://voice-patient-registration-b4n2.onrender.com/vapi/register-patient` |
| **HTTP Method** | `POST` |

### Parameter Schema (JSON)

Copy and paste this exact JSON into the tool's parameter definition in Vapi:

```json
{
  "type": "object",
  "properties": {
    "first_name": {
      "type": "string",
      "description": "Patient legal first name (max 100 chars)."
    },
    "last_name": {
      "type": "string",
      "description": "Patient legal last name (max 100 chars)."
    },
    "date_of_birth": {
      "type": "string",
      "description": "Patient date of birth in ISO format YYYY-MM-DD (e.g. 1990-05-15). Must be in the past."
    },
    "sex": {
      "type": "string",
      "enum": ["male", "female", "other", "prefer_not_to_say"],
      "description": "Patient biological/legal sex."
    },
    "phone_number": {
      "type": "string",
      "description": "Patient primary phone number in E.164 format (e.g. +15551234567)."
    },
    "address_line_1": {
      "type": "string",
      "description": "Primary street address including house number and street name (e.g. 123 Main St)."
    },
    "city": {
      "type": "string",
      "description": "City of residence (e.g. Austin)."
    },
    "state": {
      "type": "string",
      "description": "2-letter uppercase US state postal code (e.g. TX, CA, NY)."
    },
    "zip_code": {
      "type": "string",
      "description": "5-digit US postal ZIP code (e.g. 78701) or ZIP+4."
    },
    "email": {
      "type": "string",
      "description": "Optional patient email address (e.g. jane.doe@example.com)."
    },
    "address_line_2": {
      "type": "string",
      "description": "Optional secondary address (apartment, suite, unit, bldg)."
    },
    "insurance_provider": {
      "type": "string",
      "description": "Optional health insurance company name (e.g. Blue Cross Blue Shield)."
    },
    "insurance_member_id": {
      "type": "string",
      "description": "Optional insurance policy/member identification number."
    },
    "preferred_language": {
      "type": "string",
      "description": "Optional preferred language for appointments (default English)."
    },
    "emergency_contact_name": {
      "type": "string",
      "description": "Optional full name of emergency contact person."
    },
    "emergency_contact_phone": {
      "type": "string",
      "description": "Optional emergency contact phone number in E.164 format (+15559876543)."
    }
  },
  "required": [
    "first_name",
    "last_name",
    "date_of_birth",
    "sex",
    "phone_number",
    "address_line_1",
    "city",
    "state",
    "zip_code"
  ]
}
```

---

## 4. Step-by-Step Vapi Dashboard Setup Checklist

Follow these 4 steps in the Vapi.ai web dashboard:

### Step 1: Create a Free Vapi Phone Number
1. In the Vapi left sidebar, click **Phone Numbers**.
2. Click **Create a Phone Number** (or **+ Buy / Add Number**).
3. Select the **"Free Vapi Number"** tab.
4. Choose an available U.S. area code or state.
5. Click **Create**.
6. Note down your assigned U.S. phone number (e.g., `+1 (XXX) XXX-XXXX`).

### Step 2: Create the Assistant (Using Cost Saver Preset)
1. In the Vapi left sidebar, click **Assistants** → **Create Assistant** (choose **Blank Template**).
2. Set the name to `Patient Registration Assistant`.
3. Under **Model Presets**, select **"Cost Saver"**:
   - This automatically selects:
     - **Transcriber**: `Soniox STT RT v5` (1.8% WER, accent-optimized, $0.004/min).
     - **Model**: `GPT-5 Mini` via Vapi's OpenAI integration ($0.01/min).
     - **Voice**: `Elliot v2` ($0.02/min native low-latency voice).
   - Total call cost is **~$0.065 – $0.08 / min** (~3x cheaper than standard tiers, with zero external API key overhead).
4. Set the conversation script:
   - **First Message**: Paste the text from [Section 1](#exact-first-message-text) above.
   - **System Prompt**: Paste the literal text from [Section 2](#2-complete-llm-system-prompt) above.

### Step 3: Add the `register_patient` Tool
1. In the assistant editor, navigate to the **Tools** or **Functions** section.
2. Click **Add Tool** → **Create Custom Tool** (or **Function**).
3. Configure the tool details:
   - **Name**: `register_patient`
   - **Description**: `Saves confirmed patient registration data to the backend database.`
   - **Server URL**: `https://voice-patient-registration-b4n2.onrender.com/vapi/register-patient`
   - **Method**: `POST`
   - **Parameters / Schema**: Paste the JSON schema from [Section 3](#parameter-schema-json) above.
4. Click **Save Tool**.

### Step 4: Assign the Free Number and Test
1. Return to **Phone Numbers** in the sidebar.
2. Click on the **Free Vapi Number** you generated in Step 1.
3. In the **Assistant** dropdown, select **Patient Registration Assistant**.
4. Click **Save**.
5. **Test Call**: Dial the phone number from any phone.
   - Speak your details following the prompt.
   - Verify that the agent offers optional fields after collecting required fields.
   - Verify that the agent reads back the summary.
   - Confirm with "Yes, that is correct."
   - Check your live API via `GET https://voice-patient-registration-b4n2.onrender.com/patients` to see your new record created in Supabase!

---

## Appendix: Groq Llama 3.3 70B Alternative (Documented Fallback)

The initial design considered Groq (`llama-3.3-70b-versatile`). While Cost Saver (GPT-5 Mini) is the active production choice due to lower cost ($0.31 vs $0.94) and superior tool calling, Groq can be connected if desired:
1. Under **Providers**, add a Custom LLM Provider with Base URL `https://api.groq.com/openai/v1/chat/completions` and model `llama-3.3-70b-versatile`.
2. Provide your Groq API key in the `Authorization: Bearer <KEY>` header.
3. Under assistant settings, select your custom Groq provider.
