# Pre-Release Security & Repository Audit Report

This report documents the security, Git hygiene, dependency, configuration, code quality, and repository readiness status of the Outflow project before its public release to GitHub.

---

## 1. Critical Issues (Must be Fixed Before Pushing)

The following issues pose significant security risks or will cause runtime application failures in production:

### 🚨 Uncaught Database Integrity Exceptions on Registration
In [app.py](/outflow/app.py#L96-L97), the `/register` route attempts to catch duplicate email sign-up errors using `sqlite3.IntegrityError`:
```python
except sqlite3.IntegrityError:
    return _form_error("An account with that email already exists.")
```
However, the application has been migrated to use PostgreSQL via `psycopg2`. Duplicate registration attempts will raise a `psycopg2.IntegrityError` (specifically `psycopg2.errors.UniqueViolation`), which will bypass this block. This results in an unhandled exception and a **500 Internal Server Error** presented to the user instead of a clean validation warning.


### 🚨 Lack of CSRF Protection
The application performs state-modifying actions via POST routes (e.g., `/login`, `/register`, `/expenses/add`, and `/expenses/<int:id>/edit`) and even deletes data via a GET route (`/expenses/<int:id>/delete`) without validating Cross-Site Request Forgery (CSRF) tokens. An attacker can construct malicious sites that execute transactions, delete user data, or modify profile details on behalf of logged-in Outflow users.

### 🚨 Hardcoded Debug Mode in Production Entrypoint
In [app.py](/outflow/app.py#L381-L382), debug mode is hardcoded to `True` when launching the file directly:
```python
if __name__ == "__main__":
    app.run(debug=True, port=5001)
```
If deployed or executed directly using `python app.py` in production, this enables the Werkzeug interactive debugger, exposing an interactive Python shell on errors which allows arbitrary remote code execution (RCE).

### 🚨 Untracked Critical Template & Configuration Files
The following files exist locally but are untracked by Git:
1. `templates/db_error.html`: Without this file committed, any database connection failure in a deployed environment will trigger a `TemplateNotFound` crash instead of displaying the database connection error page.
2. `.env.example`: Other developers and automated deployment scripts will have no template showing which environment variables are required.

---

## 2. Recommended Improvements

These improvements address code quality, maintainability, and security hardening:

### ⚠️ Completely Outdated README
The [README.md](/outflow/README.md) describes Outflow as an **SQLite-backed** database project. It references automatic creation of `expense_tracker.db` and SQLite-specific database configurations (`PRAGMA foreign_keys = ON`), which are no longer used. Additionally, it fails to mention required setup steps for PostgreSQL, such as defining `DATABASE_URL` and `DATABASE_URL_TEST` in `.env`.

### ⚠️ 100% Duplicate Validation Logic
The expense form input parsing and validation logic in `add_expense()` ([app.py:L230-277](/outflow/app.py#L230-L277)) and `edit_expense()` ([app.py:L308-356](/outflow/app.py#L308-L356)) is completely duplicated. This logic should be consolidated into a single helper validator function to keep code clean and maintainable.

### ⚠️ Using `psycopg2-binary` in Production
[requirements.txt](/outflow/requirements.txt#L5) relies on `psycopg2-binary`. The official `psycopg2` documentation warns that the binary package should only be used for development and testing, advising developers to use the source-compiled `psycopg2` package for production to prevent conflicts with SSL libraries and other system dependencies.

### ⚠️ Incomplete `.gitignore`
The [.gitignore](/outflow/.gitignore) file lacks standard exclusions for:
- Pytest runtime caches (`.pytest_cache/`)
- Common IDE config directories (e.g., `.vscode/`, `.idea/`)
- System log directories and files (e.g., `*.log`)
- General temporary artifact formats

### ⚠️ Dead Imports and Variables
- [app.py](/outflow/app.py#L1) imports `sqlite3`, which is no longer needed.
- [app.py](/outflow/app.py#L9) imports `init_db`, `seed_db`, and `IS_TESTING` from `database.db`, but none of these symbols are referenced within the routing module.
- Commented-out logic is present at the beginning of the `landing` route ([app.py:L39-40](/outflow/app.py#L39-L40)).

### ⚠️ Unreachable Parsing Logic
In [database/queries.py](/outflow/database/queries.py#L22-L32), the `get_user_by_id()` helper checks if `created_at` is a string and parses it using a list of format strings. Since PostgreSQL returns native Python `datetime` objects for timestamp fields, this string-parsing fallback logic is dead code.

---

## 3. Files That Should Never Be Committed

Ensure the following files remain untracked and excluded from the repository:

1. **`.env`**: Contains sensitive developer-specific database credentials, local passwords, and connection paths.
2. **`expense_tracker.db`**: Local SQLite database leftovers from early iterations.
3. **`.DS_Store`**: macOS finder state files.
4. **`venv/`**: The local Python virtual environment.
5. **`__pycache__/` / `*.pyc`**: Python bytecode compilations.
6. **`.pytest_cache/`**: Pytest internal testing run caches.

---

## 4. Final Verdict

### ❌ NOT READY FOR GITHUB

The repository **cannot** be pushed to GitHub in its current state.
The presence of a hardcoded security secret key (`app.secret_key`), the omission of CSRF protection on critical state mutations, the risk of Remote Code Execution via debug mode, and incorrect exception handling that will crash user signup in production are high-severity vulnerabilities. Furthermore, key project files like `templates/db_error.html` and `.env.example` are missing from source tracking, and the documentation in `README.md` is incorrect.
