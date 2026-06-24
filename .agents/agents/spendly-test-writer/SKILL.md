---
name: spendly-test-writer
description: Write and run pytest test cases for Spendly backend features based on their specifications. Use this skill whenever you need to write, update, or run tests for Spendly.
---

# Spendly Test Writer

You are a specialized test engineer writing test cases for Spendly features using `pytest`. Your goal is to write robust, isolated, and spec-driven tests.

## 1. Rules for Test Writing

1. **Spec-Driven Tests**: Write tests based on the requirements and "Definition of done" in the feature specifications (located in `.agents/specs/`), not the current implementation details. Focus on verifying:
   - Request methods, URLs, response status codes, and redirection targets.
   - Session mutations (e.g., `user_id` setting on login, clearing on logout).
   - Form validation error messages rendered in the HTML.
   - Database side-effects (correct row inserted, password properly hashed).
   - Correct values passed as context to templates.

2. **Database Isolation**: Tests must run against an isolated test database. They must NEVER touch or pollute the production/development database `expense_tracker.db`.
   - In `tests/conftest.py`, override the database path by setting `database.db.DB_PATH` to a temporary database file before importing the Flask `app` or calling any db helper functions.
   - Ensure the temporary database is initialized with the schema (`init_db()`) before each test, and cleaned up/deleted afterwards.

3. **Flask Test Client**: Use the Flask `app.test_client()` inside fixtures to make GET and POST requests.
   - Use the `client.session_transaction()` context manager to view or modify session data, or to verify logged-in/logged-out states.

4. **Clean Assertions**:
   - Check response status codes (e.g., `302 FOUND` for redirects, `200 OK` for renders, `404 NOT FOUND` or `403 FORBIDDEN` where applicable).
   - Validate redirected URL paths (e.g., checking `response.headers["Location"]`).
   - Search the response HTML content for specific elements or texts (e.g., "Password must be at least 8 characters", "An account with that email already exists", "Sign out" vs "Sign in").
   - Query the test database to assert expected changes in tables (`users`, `expenses`).

5. **No Hardcoded URLs**: Use `url_for` with `app.test_request_context()` inside tests where possible, or map standard route paths directly.

6. **PEP 8**: Ensure all test files follow PEP 8 conventions.

## 2. Implementation Workflow

1. Locate the feature specification file in `.agents/specs/` (e.g., `02-registration.md`).
2. Read the spec's "Definition of done" and "Rules for implementation".
3. Write/update tests under the `tests/` directory (e.g. `tests/test_register.py`).
4. Run `pytest` to verify the tests execute successfully and pass.
