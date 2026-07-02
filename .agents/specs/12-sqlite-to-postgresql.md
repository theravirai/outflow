# Spec: SQLite to PostgreSQL

## Overview
This feature migrates Outflow's database engine completely from SQLite to PostgreSQL. This is necessary to deploy the application on Render's free tier (which uses an ephemeral filesystem) without data loss, and to connect to a serverless Neon PostgreSQL database in production. It also sets up the project for future CI/CD deployment automation.

## Depends on
- **Step 11 — Dark Mode** (or all preceding functional steps)

## Routes
No new routes.

## Database changes
Complete migration of schema from SQLite to PostgreSQL:
- `users`:
  - `id` $\rightarrow$ `SERIAL PRIMARY KEY`
  - `name` $\rightarrow$ `TEXT NOT NULL`
  - `email` $\rightarrow$ `TEXT UNIQUE NOT NULL`
  - `password_hash` $\rightarrow$ `TEXT NOT NULL`
  - `created_at` $\rightarrow$ `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- `expenses`:
  - `id` $\rightarrow$ `SERIAL PRIMARY KEY`
  - `user_id` $\rightarrow$ `INTEGER NOT NULL (FOREIGN KEY to users(id))`
  - `amount` $\rightarrow$ `DOUBLE PRECISION NOT NULL`
  - `category` $\rightarrow$ `TEXT NOT NULL`
  - `date` $\rightarrow$ `TEXT NOT NULL`
  - `description` $\rightarrow$ `TEXT`
  - `created_at` $\rightarrow$ `TIMESTAMP DEFAULT CURRENT_TIMESTAMP`

We will modify database connections in `database/db.py` to:
- Use native `psycopg2` instead of `sqlite3` without any connection/cursor wrappers.
- Initialize/Seed tables in PostgreSQL.


## Templates
No templates modified or created.

## Files to change
| File | What changes |
|---|---|
| `AGENTS.md` | Update "Tech constraints" to specify PostgreSQL instead of SQLite. |
| `requirements.txt` | Add `psycopg2-binary` and `python-dotenv`. |
| `database/db.py` | Replace `sqlite3` imports/connections with wrapped `psycopg2` connections. Update table schemas, insert queries, placeholders, and demo cleanup queries. |
| `database/queries.py` | Change parameter placeholders from `?` to `%s`. Adjust `created_at` date formatting to support both strings and native Python datetime objects. |
| `tests/` | All test files (`test_*.py`): update the `setup_test_db` fixture to read `DATABASE_URL_TEST` and run table cleanups (`TRUNCATE TABLE users, expenses RESTART IDENTITY CASCADE`) instead of overriding SQLite files. |

## Files to create
| File | Description |
|---|---|
| `.env.example` | Template for environment variables (`DATABASE_URL`, `DATABASE_URL_TEST`). |
| `migrate_to_pg.py` | One-off CLI script to migrate existing users and expenses from SQLite to PostgreSQL and reset auto-increment sequences. |

## New dependencies
- `psycopg2-binary==2.9.10`
- `python-dotenv==1.0.1`

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only (using `%s` placeholders for PostgreSQL).
- Passwords hashed with `werkzeug.security`.
- Support PostgreSQL connection string via `DATABASE_URL` (for application run) and `DATABASE_URL_TEST` (for test execution).
- Test suites must clean up and seed the test database using `TRUNCATE TABLE users, expenses RESTART IDENTITY CASCADE`.
- Do not use connection/cursor wrappers. All database operations in code and tests must explicitly instantiate standard cursors, use `%s` query parameters, and handle row fetching or insertion IDs (via `RETURNING id`) using native psycopg2 APIs.


## Definition of done
- [ ] `AGENTS.md` updated with PostgreSQL constraints.
- [ ] `requirements.txt` includes `psycopg2-binary` and `python-dotenv`.
- [ ] Local environment variables loaded correctly via `python-dotenv`.
- [ ] Main database connection (`DATABASE_URL`) connects to Neon PostgreSQL.
- [ ] Test database connection (`DATABASE_URL_TEST`) runs the test suite cleanly via `pytest`.
- [ ] One-off migration script `migrate_to_pg.py` successfully transfers existing users and expenses, updating PG sequences correctly.
- [ ] All database actions (User registration, login, add/edit/delete expense, demo mode) work perfectly.
- [ ] All automated tests pass successfully with the PostgreSQL backend.

