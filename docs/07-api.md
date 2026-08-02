# Internal APIs

## What does this component do?
Although Outflow relies heavily on Server-Side Rendering (SSR), it exposes a small subset of internal JSON APIs. These endpoints are designed strictly to hydrate highly interactive client-side components (like the AI Chat and the "Magic Add" voice button) without requiring full page reloads.

## 1. AI Chat Endpoint
**`POST /api/assistant`**
*   **Purpose:** Routes natural language text to the LLM backend for intent parsing and payload generation.
*   **Authentication:** Requires an active `user_id` session.
*   **Security:** Protected by a 20 request/minute rate limit and strict CSRF validation.
*   **Request Payload:**
    ```json
    { "text": "Delete that 5 dollar coffee" }
    ```
*   **Response Payload (Example - Delete Intent):**
    ```json
    {
      "type": "delete_expense",
      "data": { "transaction_id": 142 },
      "message": "Are you sure you want to delete this?"
    }
    ```

## 2. Voice Transcription Endpoint
**`POST /api/assistant/transcribe`**
*   **Purpose:** Accepts an audio blob (recorded via the browser's `MediaRecorder` API) and sends it to Groq's `whisper-large-v3` for speech-to-text.
*   **Request Payload:** `FormData` containing a `file` blob (`audio/webm`).
*   **Response Payload:**
    ```json
    {
      "success": true,
      "text": "I just spent 20 bucks on gas."
    }
    ```
*   **Note:** The frontend Javascript receives this transcribed text and immediately pipes it back into `POST /api/assistant` seamlessly.

## 3. Magic Voice Expense
**`POST /api/magic-voice`**
*   **Purpose:** A dedicated, single-purpose transcription endpoint for the primary "Add Expense" page, streamlining voice-to-form-fill functionality outside of the chat panel.
*   **Response Payload:** Identical to the transcribe route, returning a string that is then fed to the Magic Add pipeline.

## 4. Magic Add Extraction
**`POST /api/magic-add`**
*   **Purpose:** Similar to the assistant, but stripped down explicitly for form-filling. It forces the LLM to parse text directly into the `AddExpenseResponse` Pydantic schema so the frontend can auto-populate the HTML inputs.

## Why was it designed this way?
By treating these specific high-interactivity zones as miniature single-page apps (communicating via fetch/JSON), we get the snappy, modern UX of a React app without abandoning the secure, fast-loading benefits of our SSR Jinja2 monolith for the rest of the application.
