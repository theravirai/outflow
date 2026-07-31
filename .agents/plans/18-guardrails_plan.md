# AI Guardrails Implementation Plan

This document outlines the phased implementation of robust AI guardrails for the Outflow AI Assistant to ensure data integrity, cost control, and business logic safety.

## Phase 1: Strict Output Parsing with Pydantic
**Goal:** Guarantee that the LLM's JSON outputs exactly match our expected data structures, completely eliminating application crashes caused by hallucinated text.

**Implementation Steps:**
1. **Dependencies:** Add `pydantic` to `requirements.txt`.
2. **Define Schemas:** Create Pydantic models in `services/ai_assistant.py` for each intent's expected output (e.g., `IntentResponse`, `ExpensePayload`, `DeletePayload`).
3. **Validation Logic:** Update the parsing logic to feed the `json.loads()` dictionary directly into the Pydantic models. 
4. **Fallback Handling:** If a Pydantic `ValidationError` occurs (meaning the AI hallucinated the wrong structure or missing fields), catch it and return a graceful fallback chat message to the user asking them to repeat themselves, rather than crashing the backend.

## Phase 2: Rate Limiting & Cost Guardrails
**Goal:** Prevent abuse (both intentional and accidental) that could result in excessive Groq API costs or server overload.

**Implementation Steps:**
1. **Dependencies:** Add `Flask-Limiter` to `requirements.txt`.
2. **Setup Limiter:** Initialize the limiter in `app.py` (using in-memory storage, which is perfectly suitable for our Flask setup).
3. **Apply Limits:** Add the `@limiter.limit("20 per minute")` decorator strictly to the two AI endpoints (`/api/assistant` and `/api/assistant/transcribe`).
4. **Frontend UX:** Update `assistant.js` to detect `429 Too Many Requests` HTTP status codes. If hit, show a friendly message in the chat panel: *"You're chatting a bit too fast! Please wait a moment."*

## Phase 3: Sanity Bounds & Business Logic Validation
**Goal:** Prevent the AI from proposing mathematically absurd, negative, or structurally illogical transactions, even if the JSON is perfectly formatted.

**Implementation Steps:**
1. **Amount Bounds:** Add Pydantic field validators to ensure `amount` is strictly greater than `0` and less than a reasonable ceiling (e.g., `100,000`).
2. **Date Bounds:** Add validators to ensure the `date` is not in the distant future or absurdly far in the past.
3. **Description Constraints:** Enforce a maximum character limit on the description (e.g., 50 characters) so it doesn't break UI tables.
4. **Interception:** If the AI proposes an expense that violates these bounds (e.g., an expense of €500,000), the backend will catch the validation error and return a chat message: *"That amount seems unusually high. Could you confirm the exact amount?"* rather than proposing the confirmation card.

---
*Status: Pending Approval*
