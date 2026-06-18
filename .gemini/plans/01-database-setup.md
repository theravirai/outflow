# Implementation Plan: Database Setup (Step 1)

## 1. Objective
Replace the stub in `database/db.py` with a fully working SQLite implementation including database connection management, table initialization (`users` and `expenses`), and seed data generation. Integrate this setup into `app.py` so the database is initialized automatically on startup.

## 2. Key Files & Context
- `database/db.py`: Currently contains stub comments. Needs full implementation using standard library `sqlite3` and `werkzeug.security`.
- `app.py`: Needs to import the database setup functions and execute them within the application context before handling requests.

## 3. Implementation Steps

### A. Implement `database/db.py`
1. **Imports:**
   - Import `sqlite3`
   - Import `datetime` and `timedelta` from `datetime` (for seeding dates)
   - Import `generate_password_hash` from `werkzeug.security`

2. **`get_db()` Function:**
   - Connect to `expense_tracker.db` (as referenced in `.gitignore`).
   - Set `conn.row_factory = sqlite3.Row`.
   - Execute `PRAGMA foreign_keys = ON`.
   - Return the connection object.

3. **`init_db()` Function:**
   - Call `get_db()` to get a connection.
   - Use a context manager (`with conn:`) or manual commit/close.
   - Execute `CREATE TABLE IF NOT EXISTS users (...)` using the specified schema (id, name, email [unique], password_hash, created_at).
   - Execute `CREATE TABLE IF NOT EXISTS expenses (...)` using the specified schema (id, user_id [FK], amount, category, date, description, created_at).

4. **`seed_db()` Function:**
   - Call `get_db()`.
   - Check if any users exist (`SELECT COUNT(*) FROM users`). If > 0, return early to prevent duplicates.
   - Insert Demo User: 
     - name: 'Demo User', email: 'demo@spendly.com', password_hash: `generate_password_hash('demo123')`.
   - Fetch the new user's ID.
   - Insert 8 sample expenses for this user spanning the fixed categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other) using parameterized queries. 
   - Spread the dates across the current month (using `datetime.date.today()` and subtracting days).

### B. Update `app.py`
1. **Imports:**
   - Add `from database.db import init_db, seed_db` at the top.
2. **Application Context:**
   - Below the `app = Flask(__name__)` initialization, add an application context block:
     ```python
     with app.app_context():
         init_db()
         seed_db()
     ```

## 4. Verification & Testing
- Start the Flask app (`python app.py`).
- Verify that `expense_tracker.db` is created in the project root.
- Use a SQLite viewer or the `sqlite3` CLI tool to inspect the database:
  - Check that both `users` and `expenses` tables exist with the correct schemas.
  - Verify that exactly one user ('demo@spendly.com') exists with a hashed password.
  - Verify that 8 sample expenses are linked to the user's ID.
- Restart the Flask app and ensure no duplicate data is inserted (seed runs only once).
