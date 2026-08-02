# Deployment Architecture

## What does this component do?
This document details how Outflow transitions from a local development environment to a production-ready application.

## 1. Environment Configuration
Outflow strictly adheres to the Twelve-Factor App methodology regarding configuration. All sensitive credentials and environment-specific toggles are injected via environment variables.

Required variables:
*   `SECRET_KEY`: Cryptographic key used by Flask to securely sign session cookies and CSRF tokens.
*   `DATABASE_URL`: The PostgreSQL connection string for the primary database.
*   `DATABASE_URL_TEST`: The PostgreSQL connection string dedicated to the CI/CD test runner.
*   `GROQ_API_KEY`: Authentication key required to communicate with the Groq LLM inference endpoints.

## 2. Server Architecture
Flask's built-in development server (`app.run()`) is explicitly not designed for production use, as it cannot handle concurrent requests efficiently and lacks security hardening.

*   **WSGI Server:** In production, Outflow must be served by a production-grade WSGI HTTP Server like **Gunicorn**.
*   **Reverse Proxy:** Gunicorn should ideally sit behind a robust reverse proxy like **Nginx**, which handles SSL termination (HTTPS), serves the static assets (`/static/*`) directly from disk to reduce Python overhead, and buffers slow clients.

## 3. Dependency Management
Dependencies are managed entirely via `requirements.txt`.
*   **Rule of Thumb:** We avoid introducing pip packages unless absolutely necessary (e.g., `Flask`, `psycopg2`, `pydantic`, `groq`, `Flask-Limiter`). This keeps the Docker image tiny, builds incredibly fast, and dramatically shrinks the application's attack surface.

## Future Improvements
*   **Containerization:** Wrapping the application in a `Dockerfile` would guarantee parity between the developer's laptop and the production server.
*   **Database Migrations:** Integrating a deployment-time migration script (e.g., via Alembic or a custom SQL runner) rather than relying on `CREATE TABLE IF NOT EXISTS` upon application boot.
