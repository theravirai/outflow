# Architecture Overview

## What does this component do?
This document provides a high-level overview of Outflow's system architecture, illustrating how the frontend, backend, and external services collaborate to form a cohesive personal finance application.

## High-Level Architecture

Outflow is built around a monolithic, server-side rendered (SSR) web architecture augmented by dynamic vanilla JavaScript APIs.

```text
+---------------------+        HTTP/HTTPS       +-------------------------+
|     Web Browser     | <=====================> |   Flask Web Server      |
|---------------------|                         |-------------------------|
| - Vanilla JS        |       AJAX (JSON)       | - app.py (Routing)      |
| - Vanilla CSS       | <---------------------> | - Jinja2 Templates      |
| - HTML (SSR)        |                         | - Flask Session         |
+---------------------+                         +-------------------------+
                                                            |
                                                            | Internal Calls
                                                            v
+-------------------------+     PostgreSQL      +-------------------------+
|     Service Layer       | <=================> |     Database Layer      |
|-------------------------|                     |-------------------------|
| - ai_assistant.py       |    REST (Groq)      | - database/db.py        |
| - Pydantic Validation   | <=================> | - database/queries.py   |
| - Data Processing       |                     | - Raw SQL Execution     |
+-------------------------+                     +-------------------------+
```

## Core Components

### 1. Frontend Layer
Outflow eschews heavy JavaScript frameworks (like React or Vue) in favor of a fast, lightweight Vanilla stack.
*   **Routing & Rendering:** The application is heavily server-side rendered using Flask and Jinja2 (`templates/`).
*   **Interactivity:** Vanilla JavaScript (`static/js/`) handles client-side dynamic state, such as AJAX-based category filtering, voice recording for the AI assistant, and the dynamic chat UI.
*   **Styling:** A custom, token-based Vanilla CSS system (`static/css/`) provides a sleek, fintech-oriented aesthetic without the bloat of frameworks like Bootstrap.

### 2. The Flask Backend
The backend serves as the orchestration layer.
*   **Single-File Routing:** All core web and API routes reside in `app.py`.
*   **Security:** Flask natively handles secure cookie sessions. CSRF tokens are strictly generated and validated on all state-mutating requests. Rate limiting is applied to high-risk endpoints.

### 3. Service Layer (AI Assistant)
The `services/ai_assistant.py` module isolates external LLM logic from core application logic.
*   **Integration:** It communicates securely with the Groq API using `llama-3.1-8b-instant`.
*   **Guardrails:** Pydantic is used to enforce strict schema boundaries. The backend isolates the LLM from the database entirely—the AI merely returns formatted JSON payloads which are then rendered as confirmation UI blocks to the user.

### 4. Database Layer
All data persistence happens through PostgreSQL via `psycopg2`.
*   **Separation of Concerns:** `database/db.py` manages connections and initialization, while `database/queries.py` handles complex data retrieval (filtering, summary stats).
*   **Execution:** We use raw parameterized SQL queries exclusively.

## Folder Structure

```text
outflow/
├── app.py                  # Core application logic and all route definitions
├── database/               # Data access layer
│   ├── db.py               # Connection pooling, table init, and migrations
│   └── queries.py          # Abstracted data retrieval (stats, filtering)
├── docs/                   # Internal engineering documentation
├── services/               # Business logic isolating external dependencies
│   └── ai_assistant.py     # AI routing, parsing, and LLM interaction
├── static/                 # Frontend assets
│   ├── css/                # Global and component-level Vanilla CSS
│   └── js/                 # Client-side interactivity (assistant.js, main.js)
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Core application shell
│   └── *.html              # Individual page views
└── tests/                  # Pytest unit and integration tests
```

## Why was it designed this way?
Outflow is designed to minimize architectural complexity while remaining extremely robust. 
By choosing a server-side rendered monolith, we eliminate the need for complex state synchronization (like Redux) and avoid the overhead of building a distinct, versioned REST API just to serve a separate frontend. The architecture forces a clean separation of concerns without requiring a microservice topology.

## What are the limitations?
*   **Scaling the Monolith:** As the application grows, putting all routes in a single `app.py` file will become unmaintainable. 
*   **Client-Side State:** As the frontend grows more complex (e.g., highly interactive dashboard charting), managing DOM state entirely with Vanilla JS will become brittle.

## Possible Future Improvements
*   **Blueprint Refactoring:** The Flask application should eventually be split into Blueprints (e.g., `api/`, `auth/`, `views/`) to better organize the routing layer.
*   **WebSockets:** Replacing HTTP polling/AJAX with WebSockets for the AI Assistant could provide a snappier, real-time typing experience.
