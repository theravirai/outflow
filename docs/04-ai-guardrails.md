# AI Guardrails & Security

## What does this component do?
Because LLMs are inherently non-deterministic, hallucinatory, and vulnerable to prompt injection, granting an AI access to a user's financial data requires strict boundaries. This document outlines the guardrails built into Outflow to ensure absolute data integrity and system stability.

## 1. The "Human-in-the-Loop" Mandate
The most critical architectural decision regarding the AI is that **the AI cannot execute database queries.**
*   **Why:** If the AI hallucinates parsing a 5.00€ coffee as 50,000€, or misunderstands an intent and executes a `DELETE` on the wrong transaction ID, the user's data is permanently corrupted.
*   **How it works:** The AI only produces a structured JSON payload representing its *intention*. The backend passes this JSON directly to the frontend, which renders a visual "Confirmation Card." The user must physically click the "Confirm & Save" or "Confirm Delete" button to trigger the actual database mutation via a standard AJAX POST request.

## 2. Strict Schema Validation (Pydantic)
Even with `response_format={"type": "json_object"}` enabled, LLMs can hallucinate keys, return string values instead of integers, or invent logic that breaks application code.
*   **How it works:** We integrated `pydantic` in `services/ai_assistant.py` to enforce rigid schemas (e.g., `AddExpenseResponse`, `UpdateExpenseResponse`).
*   **Data Coercion:** If the LLM returns `"amount": "15"`, Pydantic seamlessly coerces it into the required `float`. 
*   **Graceful Fallbacks:** If the LLM entirely botches the structure (causing a `ValidationError`), a `try/except` block catches the error and returns a friendly chat fallback (e.g., *"I couldn't quite understand the expense details. Could you repeat the amount?"*) instead of crashing the Flask server with a 500 error.

## 3. Business Logic Sanity Bounds
We implemented mathematical and logical boundaries directly inside the Pydantic models to prevent the AI from generating absurd proposals.
*   **Amount Limits:** The `amount` field must strictly be greater than 0 and less than or equal to 100,000 (`Field(gt=0, le=100000)`). The AI cannot propose negative expenses.
*   **Chronological Sanity:** A custom `@field_validator('date')` prevents the AI from assigning expenses to the distant past (pre-2000) or into the distant future (more than 30 days ahead).
*   **UI Protection:** Descriptions are capped at 50 characters (`max_length=50`) to guarantee that hallucinated walls of text do not break the frontend CSS grid.

## 4. Rate Limiting & Cost Control
To prevent malicious spamming or accidental infinite loops that could drain Groq API credits, strict rate limits are enforced.
*   **Implementation:** Using `Flask-Limiter`, the `/api/assistant` and `/api/assistant/transcribe` endpoints are hard-capped at **20 requests per minute per IP**.
*   **UX Handling:** If a user hits this limit, the backend returns a `429 Too Many Requests` HTTP code. The JavaScript client (`assistant.js`) explicitly intercepts this and renders a friendly message in the chat panel: *"You're chatting a bit too fast! Please wait a moment."*

## 5. Tenant Data Isolation
When the AI requires context to fulfill a request (e.g., fetching recent transactions to figure out which one the user wants to delete), it must never leak data.
*   **Implementation:** All AI endpoints require a verified `@login_required` session. The Flask backend extracts the secure `user_id` from the HTTP-only cookie and passes it strictly to the SQL queries (`get_recent_transactions(user_id)`). The LLM is physically incapable of seeing or modifying another user's financial data.
