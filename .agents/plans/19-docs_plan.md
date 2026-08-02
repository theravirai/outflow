# Outflow Engineering Documentation Plan

This plan breaks down the creation of a professional `docs/` folder for the Outflow repository. The documentation will explain internal mechanics, architectural decisions, and system interactions without merely duplicating the README.

## Phase 1: High-Level Architecture & Core Decisions
**Goal:** Establish the foundational blueprint of the application and document the most critical engineering trade-offs.
*   **`index.md`:** The central directory linking to all documentation with brief summaries.
*   **`architecture.md`:** High-level system overview detailing the interaction between the vanilla frontend, Flask backend, service layer, and database. Includes an ASCII architecture diagram and folder structure explanation.
*   **`decisions.md`:** A deep dive into engineering trade-offs (e.g., Why Flask instead of FastAPI, why raw SQL over SQLAlchemy, why vanilla CSS, why Groq).

## Phase 2: The AI Assistant & Safety Systems
**Goal:** Document the most complex subsystem of the application—the AI Assistant—and the safety mechanisms built around it.
*   **`ai-assistant.md`:** Explains the NLP pipeline, intent detection router (Llama 3.1), prompt construction, context fetching, and the Voice-to-Text Whisper pipeline.
*   **`ai-guardrails.md`:** Documents the safety layer, explaining Pydantic structured parsing, business logic bounds, rate limiting, and the crucial "Human-in-the-Loop" database protection.

## Phase 3: Data, Security, & Internal APIs
**Goal:** Outline how data flows securely through the application.
*   **`database.md`:** Details the database layer (PostgreSQL), schema design, why raw parameterized SQL is used over ORMs, and the migration strategy.
*   **`authentication.md`:** Covers cookie-based session management, CSRF token security, and the technical architecture of "Demo Mode" (including the seamless demo-to-user data conversion).
*   **`api.md`:** Documents the internal JSON APIs that power dynamic frontend features (e.g., AJAX category filters, AI endpoints).

## Phase 4: Frontend, Testing, & Reflection
**Goal:** Document the client-side execution, quality assurance, and project post-mortems.
*   **`frontend.md`:** Explains the Vanilla JS/CSS setup, Server-Side Rendering (SSR) via Jinja2, and complex interactive components (like dynamic pagination and the AI chat panel).
*   **`testing.md`:** Details the Pytest suite, how unit tests handle database rollbacks, and how the AI services are mocked/tested.
*   **`deployment.md`:** Outlines environment variable requirements, WSGI server configurations, and deployment strategies.
*   **`lessons-learned.md`:** A professional post-mortem of bugs encountered (e.g., CSRF failures on landing pages, AI JSON hallucinations) and how they were solved.
*   **`future-roadmap.md`:** Identifies technical debt, limitations, and future architectural improvements.
