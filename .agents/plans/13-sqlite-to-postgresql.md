# Plan - SQLite to PostgreSQL Migration

This plan details the steps to completely migrate Outflow's database engine from SQLite to PostgreSQL (Neon serverless Postgres), update constraints, refactor connection wrappers, adapt the test suite, and provide a data migration script.

---

## Proposed Changes

### 1. Requirements & Project Setup

#### [MODIFY] [AGENTS.md](/outflow/AGENTS.md)
- Update tech constraints to replace SQLite references with PostgreSQL.
- Document environment variables required: `DATABASE_URL` (application run) and `DATABASE_URL_TEST` (pytest).

#### [MODIFY] [requirements.txt](/outflow/requirements.txt)
- Add `psycopg2-binary==2.9.10`
- Add `python-dotenv==1.0.1`

#### [NEW] [.env.example](/outflow/.env.example)
- Provide template environment configurations for local and production setups:
  ```env
  DATABASE_URL=postgresql://username:password@localhost:5432/outflow
  DATABASE_URL_TEST=postgresql://username:password@localhost:5432/outflow_test
  ```

---

### 2. Database Connection and Native Refactoring

#### [MODIFY] [database/db.py](/outflow/database/db.py)
- Load environment variables with `dotenv.load_dotenv()` at startup.
- Import `psycopg2` and `DictCursor` from `psycopg2.extras`.
- Modify `get_db()`:
  - Connect via `psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)`.
  - Return the standard `psycopg2` connection object directly.
- Refactor all functions to create a cursor object (`cur = conn.cursor()`) and call `.execute()` on the cursor rather than directly on the connection (`conn.execute`).
- Update all placeholders in database query strings: change `?` to `%s`.
- Update all insert methods to append `RETURNING id` to the SQL query and retrieve the inserted row ID using `cur.fetchone()[0]` (replacing `cur.lastrowid`):
  - In `seed_db()`, retrieve the demo user's ID using `cur.fetchone()[0]`.
  - In `create_user()`, retrieve the new user's ID using `cur.fetchone()[0]`.
  - In `create_expense()`, retrieve the new expense's ID using `cur.fetchone()[0]`.
  - In `create_demo_user()`, retrieve the demo user's ID using `cur.fetchone()[0]`.
- Modify `init_db()` DDL queries to use PostgreSQL compatible schemas:
  - Replace `INTEGER PRIMARY KEY AUTOINCREMENT` with `SERIAL PRIMARY KEY`.
  - Replace `REAL` with `DOUBLE PRECISION`.
  - Replace `TEXT DEFAULT CURRENT_TIMESTAMP` with `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.
- Modify `cleanup_old_demo_users()`:
  - Replace SQLite helper `datetime('now', '-1 day')` with PostgreSQL `NOW() - INTERVAL '1 day'`.

---

### 3. Query Compatibility Refactoring

#### [MODIFY] [database/queries.py](/outflow/database/queries.py)
- Refactor all database operations to instantiate standard cursors (`cur = conn.cursor()`) and execute queries using cursors.
- Replace all `?` placeholders with `%s` in all queries.
- Update `get_user_by_id()`:
  - Handle `created_at` when returned as a native Python `datetime` object from PostgreSQL, bypassing the `strptime` string parsing loop.

---

### 4. Test Suite Refactoring

#### [MODIFY] all test files in [tests/](/outflow/tests/)
- Refactor the `setup_test_db` fixture in all test files:
  - Read `DATABASE_URL_TEST` from the environment (raise an exception if missing).
  - Connect to the PostgreSQL database, execute `init_db()`.
  - Truncate all tables using:
    ```sql
    TRUNCATE TABLE users, expenses RESTART IDENTITY CASCADE;
    ```
  - Call `seed_db()`.
- Refactor all tests calling `conn.execute(...)` to explicitly create cursors and execute statements:
  ```python
  cur = conn.cursor()
  cur.execute(...)
  ```
- Change all `?` placeholders to `%s` in test queries.
- Change `cur.lastrowid` references to retrieve insertion IDs via `cur.fetchone()[0]` (or `cur.fetchone()['id']`).

---


### 5. SQLite to PostgreSQL Data Migration Script

#### [NEW] [migrate_to_pg.py](/outflow/migrate_to_pg.py)
- Establish connections to `expense_tracker.db` (SQLite) and `DATABASE_URL` (PostgreSQL).
- Fetch rows from `users` in SQLite and insert into `users` in PostgreSQL.
- Fetch rows from `expenses` in SQLite and insert into `expenses` in PostgreSQL.
- Reset primary key auto-increment sequences in PostgreSQL using:
  ```sql
  SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));
  SELECT setval('expenses_id_seq', COALESCE((SELECT MAX(id) FROM expenses), 1));
  ```
- Log summary statistics of transferred records.

---

## Verification Plan

### Automated Verification
1. Export the environment variable `DATABASE_URL_TEST` pointing to a local or development test database.
2. Run `pytest` to execute all tests:
   ```bash
   pytest
   ```
3. Confirm all tests pass successfully using the new PostgreSQL schema and connection.

### Manual Verification
1. Configure `DATABASE_URL` in a local `.env` file pointing to a PostgreSQL server.
2. Run the application:
   ```bash
   python app.py
   ```
3. Register a new user, log in, add expenses, edit/delete them, and access the profile dashboard.
4. Execute `python migrate_to_pg.py` and verify all existing SQLite data is correctly copied to the PostgreSQL database.
