# AI Assistant Pipeline

## What does this component do?
The AI Assistant acts as a smart interface over the user's financial data. It allows users to perform CRUD (Create, Read, Update, Delete) operations, navigate the application, and query their financial statistics using natural language—either via text input or voice dictation.

## The Request Flow

The entire AI interaction loop is decoupled from direct database mutation. 

```text
[User Input] --> (Frontend AJAX) --> [Flask API Endpoint]
                                           |
                                           v
[LLM Intent Router] <---------------- [ai_assistant.py]
    (Categorizes as: add, delete, update, navigate, etc.)
                                           |
                                           v
[Specific Handler Function] --------> (Fetches DB context if needed)
                                           |
                                           v
[LLM JSON Extractor] ----------------> [Groq API]
                                           |
                                           v
[Pydantic Validation] <---------------- (Validates schema & bounds)
                                           |
                                           v
[Frontend Renders Confirmation] <------ (JSON Payload Returned)
```

## How it works internally

### 1. Intent Detection
Before parsing complex entities, the system routes the query through an initial classification prompt (`detect_intent()`). 
The LLM (`llama-3.1-8b-instant` via Groq) is forced to output a JSON object indicating exactly one intent (e.g., `add_expense`, `delete_expense`, `dashboard_query`, `navigation`, `help`). This strict routing isolates the logic and prevents prompt injection attacks from crossing context boundaries.

### 2. Context Injection & Prompt Construction
Depending on the intent, the system fetches relevant database context before calling the LLM a second time.
*   **For Deletions/Updates:** The system pulls the user's 30 most recent transactions from PostgreSQL and injects them into the prompt. The LLM acts as a fuzzy-search engine, matching the natural language request (e.g., "Delete that coffee from yesterday") to the exact Database ID.
*   **For Queries:** The system pulls aggregated stats (Total Spent, Top Category, Breakdown) and injects them into the system prompt, allowing the LLM to generate a natural, conversational answer without writing SQL.

### 3. Voice Transcription (Whisper)
For voice inputs, the frontend utilizes the `MediaRecorder` API to capture `.webm` audio. This blob is sent to `/api/assistant/transcribe`, where it is piped through Groq's `whisper-large-v3` model to generate highly accurate text. That text is then routed through the standard chat pipeline.

## Implementation Challenges
*   **JSON Hallucinations:** Early iterations suffered from the LLM appending conversational pleasantries (e.g., "Sure, here is your JSON! { ... }") which broke Python's `json.loads()`. We mitigated this by enforcing strict `response_format={"type": "json_object"}` in the Groq API call.
*   **Context Windows:** Injecting the entire transaction history into the prompt to let the AI find an ID to delete was too expensive and slow. We optimized this by limiting the context window to only the 30 most recent transactions.

## Current Limitations
*   **Stateless Conversations:** The AI currently processes every request in isolation. It does not remember the previous message. You cannot say "Add a coffee for 5 euros", and then follow up with "Actually make it 6" unless the confirmation card is explicitly used.
*   **Complex Queries:** The AI cannot generate dynamic SQL. If a user asks "How much did I spend on food in August 2022?", the system will fail because the dashboard query context only injects *all-time* aggregated stats.

## Future Improvements
*   **Memory / Conversation History:** Implement a lightweight buffer (e.g., storing the last 5 user/assistant messages in the Flask session) to allow for conversational follow-ups.
*   **RAG / Dynamic SQL Generation:** Instead of injecting a static summary, allow the AI to generate read-only SQL queries to answer complex, arbitrary historical questions.
