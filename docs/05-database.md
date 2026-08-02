# Database Layer

## What does this component do?
This document outlines how data is persisted, queried, and protected within Outflow. The database layer consists of connection management (`database/db.py`) and complex query logic (`database/queries.py`).

## Technology Choice
Outflow uses **PostgreSQL** exclusively, accessed via the `psycopg2` adapter.

*   **Why PostgreSQL?** It provides enterprise-grade ACID compliance, robust date-math capabilities, and advanced JSON indexing (if needed for LLM logging). 
*   **Why Raw SQL?** We specifically chose to avoid ORMs like SQLAlchemy. By writing raw parameterized SQL strings, we retain total transparency over query execution plans, avoid the "N+1 query problem", and keep the dependency tree remarkably thin.

## Schema Architecture

The core architecture consists of two primary tables:

```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS expenses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    category TEXT NOT NULL,
    date DATE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Design Decisions:
*   **Referential Integrity:** `ON DELETE CASCADE` is enforced natively by Postgres. If a user deletes their account, all associated financial data is immediately wiped without requiring application-level cleanup logic.
*   **Numeric Typing:** Financial amounts are strictly stored as `NUMERIC(10, 2)` to avoid floating-point rounding errors common in standard `REAL` types.

## Security & Implementation Challenges
*   **SQL Injection Prevention:** Every query in `queries.py` and `db.py` uses `psycopg2`'s parameter binding (`%s`). String interpolation (`f-strings`) is strictly forbidden for user inputs.
*   **Migration Management:** Because we lack an ORM, we also lack tools like Alembic. Schema updates are currently applied manually or via `CREATE TABLE IF NOT EXISTS` blocks. This is a known limitation that will require a bespoke migration script as the app scales.

## Possible Future Improvements
*   **Connection Pooling:** Currently, connections are created relatively eagerly. Implementing `psycopg2.pool` would dramatically improve concurrent request throughput.
*   **Database Indexing:** As users accumulate thousands of transactions, querying by `(user_id, date)` will become a bottleneck. We need to add composite B-Tree indexes on the `expenses` table for these columns.
