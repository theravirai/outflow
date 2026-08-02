# Future Roadmap

## What does this component do?
This document outlines the known technical debt, limitations, and the planned architectural improvements for Outflow. It serves as a backlog for the engineering team.

## 1. Architectural Refactoring: Flask Blueprints
*   **Current State:** All routes (web, API, auth) live in a single `app.py` file. As the application expands, this monolithic file has become bloated and harder to navigate.
*   **Next Steps:** Refactor `app.py` utilizing Flask Blueprints.
    *   `routes/auth.py` (Login, Register, Demo)
    *   `routes/api.py` (AI Assistant, Transcribe, Magic Add)
    *   `routes/views.py` (Dashboard, Landing, Legal)

## 2. Advanced AI Memory
*   **Current State:** The AI Assistant is completely stateless. It processes each prompt in total isolation. If a user asks a follow-up question, the AI loses context.
*   **Next Steps:** Implement a lightweight, short-term conversational buffer.
    *   Store the last 5 user-assistant interaction pairs in the Flask session or a temporary Redis cache.
    *   Inject this memory into the Groq LLM `messages` array, enabling the AI to answer context-dependent queries (e.g., "Actually, change that amount to 15").

## 3. Database Migration Tooling
*   **Current State:** Table schemas are instantiated via raw `CREATE TABLE IF NOT EXISTS` commands in `database/db.py`. Altering existing tables (e.g., adding a new column) requires manual SQL scripts run directly against the PostgreSQL instance.
*   **Next Steps:** Build a lightweight migration runner script, or integrate Alembic (even though we don't use SQLAlchemy) specifically for handling robust, version-controlled up/down database migrations.

## 4. WebSocket Integration for Streaming Chat
*   **Current State:** The AI Assistant uses standard HTTP POST requests. The user clicks "Send", sees a static loading indicator, and waits ~1 second for the full JSON response to arrive.
*   **Next Steps:** Implement WebSockets (e.g., using `Flask-SocketIO` and `gevent`) combined with Groq's streaming API. This would allow the AI's chat text to type out dynamically, character by character, dramatically improving the perceived performance and UX of the assistant.

## 5. End-to-End Testing (Playwright)
*   **Current State:** Outflow has solid unit test coverage via `pytest`, ensuring database transactions rollback securely and AI services process JSON correctly. However, the client-side interactivity (Vanilla JS DOM manipulation) is untested.
*   **Next Steps:** Integrate Playwright to run headless browser tests against the dynamic UI. We need automated tests that actually click the "Confirm Delete" AI card button and verify that the HTML DOM dynamically removes the row from the table.
