# Engineering Decisions & Trade-offs

## What does this component do?
This document acts as an Architectural Decision Record (ADR). It catalogs the "why" behind the most significant technology and design choices in the Outflow repository.

---

## 1. Why Flask instead of FastAPI?
While FastAPI is the modern standard for API development in Python (offering speed and native asynchronous support), Outflow chose Flask.
*   **Why:** Outflow is fundamentally a monolithic, Server-Side Rendered (SSR) application relying heavily on HTML templates, not just a standalone JSON API. Flask integrates flawlessly with Jinja2 and session-based cookie management out-of-the-box.
*   **Trade-off:** We lack native `async/await` handling for database connections, which slightly bottlenecks high-concurrency performance, but drastically simplifies the mental model for routing and rendering.

## 2. Why PostgreSQL?
*   **Why:** PostgreSQL offers robust data integrity, advanced JSONB indexing (should we ever need it for AI logs), and enterprise-grade reliability.
*   **Trade-off:** It requires a dedicated database server or container to run locally, increasing developer friction compared to a zero-config SQLite setup.

## 3. Why Raw SQL instead of SQLAlchemy (ORM)?
The `database/` layer exclusively uses `psycopg2` with raw parameterized SQL queries rather than an Object-Relational Mapper (ORM) like SQLAlchemy.
*   **Why:** Performance and transparency. We wanted absolute control over how transactions are queried and filtered. By avoiding an ORM, we bypassed the notorious "N+1 query problem" and prevented bloated abstraction layers.
*   **Trade-off:** Queries are statically written as strings. This means we lack the Python-level type-checking that an ORM ecosystem provides. However, we have integrated Alembic to manage and version our schema migrations independently of an ORM.

## 4. Why Server-Side Rendering (SSR)?
Instead of building a React SPA (Single Page Application) that consumes a REST API, Outflow renders HTML directly on the server.
*   **Why:** Security and simplicity. SSR means no massive JavaScript bundles, zero "loading spinners" while waiting for initial data, and significantly easier SEO and accessibility management. Authentication is handled effortlessly via HTTP-only cookies without dealing with complex JWT storage logic on the client.
*   **Trade-off:** Building highly complex, app-like interactive features requires more manual DOM manipulation.

## 5. Why Custom Vanilla CSS over Tailwind or Bootstrap?
*   **Why:** To maintain absolute control over the design aesthetic and keep the payload size incredibly small. We designed a custom CSS variable token system (`style.css`) that mimics modern fintech SaaS products.
*   **Trade-off:** We have to manually write media queries, responsive grids, and cross-browser fixes that a mature framework would handle automatically.

## 6. Why Groq for the AI Assistant?
*   **Why:** Groq provides ultra-low latency inference via their specialized LPU architecture. For a chat assistant, perceived latency is the most critical UX metric. By using `llama-3.1-8b-instant` on Groq, the AI feels instantaneous.
*   **Trade-off:** We are locked into the models supported by the Groq ecosystem, which may lag behind frontier models like GPT-4 or Claude 3.5 Sonnet.

## 7. Why the AI Never Writes Directly to the Database
A core architectural mandate is that the AI Assistant is entirely decoupled from the database execution layer.
*   **Why:** Data safety and user trust. LLMs hallucinate. If the AI was granted direct `UPDATE` or `DELETE` access to the PostgreSQL database, a prompt injection or simple misinterpretation could permanently destroy a user's financial records.
*   **Implementation:** The AI only parses intent and proposes structured JSON payloads. The frontend renders these as visual "Confirmation Cards," requiring explicit human interaction (a button click) to actually hit the secure database mutation endpoints.
