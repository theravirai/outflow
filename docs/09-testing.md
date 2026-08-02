# Testing Strategy

## What does this component do?
This document outlines the Quality Assurance (QA) and testing mechanisms utilized in Outflow to ensure data integrity and application stability.

## Framework
Outflow uses `pytest` as its primary testing framework.

## Database Isolation for Tests
Testing a database-heavy application poses a risk of polluting the production or development databases with mock data.
*   **Implementation:** The database connection layer (`database/db.py`) dynamically detects if `pytest` is currently running the application instance.
*   **How it works:** If `IS_TESTING = "pytest" in sys.modules` evaluates to True, the application completely abandons the standard `DATABASE_URL` and routes all queries to `DATABASE_URL_TEST`. 
*   **Result:** The test suite runs against a completely isolated, sandbox PostgreSQL database. The test runner can safely create tables, insert mock users, test the "Demo User Conversion" logic, and wipe the database clean without ever touching real user data.

## Mocking External APIs
Testing the AI Assistant requires simulating Groq LLM responses to avoid racking up API charges or dealing with network latency during CI/CD.
*   **Approach:** We utilize Python's `unittest.mock.patch` to intercept calls to the Groq API.
*   **Validation:** By mocking the return value, we can explicitly test how our Pydantic validation handles malformed JSON, and verify that the backend correctly routes the user to the fallback chat message without throwing a 500 server error.

## Future Improvements
*   **End-to-End (E2E) Testing:** Currently, testing is isolated to backend unit and integration tests. Introducing an E2E framework like Playwright or Cypress would allow us to programmatically test the Vanilla JS interactivity, ensuring the AJAX category filters and AI chat panel render correctly in a real browser environment.
