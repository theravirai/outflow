# Outflow Engineering Documentation

Welcome to the internal engineering documentation for Outflow. 

This repository of documents is intended for engineers, technical reviewers, and contributors who want to deeply understand the architecture, internal mechanics, and design decisions behind Outflow. It goes beyond the basic setup instructions in the `README.md` to explain *how* and *why* the system works.

## Documentation Index

### Phase 1: High-Level Architecture & Core Decisions
*   **[Architecture Overview](01-architecture.md):** A high-level view of the system components, data flow, and folder structure.
*   **[Engineering Decisions](02-decisions.md):** A detailed log of technical trade-offs, explaining why specific tools and patterns were chosen (e.g., Flask, Vanilla JS, raw SQL).

### Phase 2: The AI Assistant Engine
*   **[AI Assistant Pipeline](03-ai-assistant.md):** Explains how the natural language intent router, Whisper transcription, and LLM context-fetching work.
*   **[AI Guardrails](04-ai-guardrails.md):** Documents the strict safety bounds, Pydantic schemas, and rate-limiting designed to keep the AI safe and reliable.

### Phase 3: Data, Security, & Internal APIs
*   **[Database Layer](05-database.md):** Explains the PostgreSQL schema, query execution strategy, and migration philosophy.
*   **[Authentication & Demo Mode](06-authentication.md):** Covers session management, CSRF protection, and the technical architecture of the seamless demo-to-user conversion.
*   **[Internal APIs](07-api.md):** Documents the internal JSON APIs used by the frontend for dynamic updates and AI chat interactions.

### Phase 4: Frontend, Quality Assurance, & Reflection
*   **[Frontend Architecture](08-frontend.md):** Details the Vanilla JS approach, server-side rendering (SSR), and CSS design system.
*   **[Testing Strategy](09-testing.md):** Outlines the Pytest suite, database rollback techniques for unit tests, and AI endpoint mocking.
*   **[Deployment](10-deployment.md):** Explains the WSGI setup, environment variable requirements, and CI/CD philosophy.
*   **[Lessons Learned](11-lessons-learned.md):** A post-mortem of interesting bugs, architectural hurdles, and the lessons extracted from them.
*   **[Future Roadmap](12-future-roadmap.md):** Known technical debt and architectural improvements planned for the future.
