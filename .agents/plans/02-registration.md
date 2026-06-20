# Step 2 — Registration: Implementation Plan

## Background

Step 1 delivered a working data layer: `get_db()`, `init_db()`, `seed_db()`,
and the `users` / `expenses` tables. The `GET /register` route already renders
`register.html`, and the form already points to `POST /register`. This step
wires the form submission to the database.

**No new files, tables, or pip packages are needed.**

---

## Proposed Changes

### 1 · Database layer

---

#### [MODIFY] [db.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/database/db.py)

Two new helper functions are appended **after** `seed_db()`. Nothing existing
is touched.

**`get_user_by_email(email)`**
- Opens a connection via `get_db()`.
- Executes `SELECT * FROM users WHERE email = ?` with `(email,)` as the
  parameter tuple.
- Calls `fetchone()` and returns the `sqlite3.Row` (or `None` if no row found).
- Closes the connection.
- This function will be reused in Step 3 (Login) — defining it now avoids
  duplication later.

**`create_user(name, email, password_hash)`**
- Opens a connection via `get_db()`.
- Inside a `with conn:` block (auto-commit / auto-rollback), executes:
  `INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)`.
- Returns `cursor.lastrowid` (the new user's `id`).
- Does **not** catch `IntegrityError` here — that is the route's responsibility,
  keeping each layer focused on its own concern.
- Closes the connection.

> [!NOTE]
> The import line `from werkzeug.security import generate_password_hash` is
> already present. No new imports are needed in `db.py`.

---

### 2 · Application layer

---

#### [MODIFY] [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py)

Three discrete changes, in order:

**a) Expand the Flask import on line 1**

Add `request`, `redirect`, `url_for`, `flash` to the existing
`from flask import …` statement.

**b) Expand the `database.db` import on line 2**

Add `create_user` and `get_user_by_email` to the existing
`from database.db import …` statement.

**c) Set `app.secret_key` immediately after `app = Flask(__name__)`**

Flask requires `secret_key` to be set before any call to `flash()`.
Use the literal string `"dev-secret-change-in-prod"`.

> [!IMPORTANT]
> `secret_key` must be set **before** the `with app.app_context()` block
> so that it is available as soon as the app object is used.

**d) Upgrade the `/register` route**

The existing route decorator is `@app.route("/register")`. It needs to
accept both `GET` and `POST` methods:

```
@app.route("/register", methods=["GET", "POST"])
```

The route function body becomes a two-branch conditional:

**`GET` branch** — identical to today: `return render_template("register.html")`.

**`POST` branch** — the following steps run in order:

1. **Read form data** — pull `name`, `email`, `password` from `request.form`
   and `.strip()` each value.

2. **Server-side validation** — checked top-to-bottom; the first failure
   short-circuits and re-renders the form with an `error` variable:
   - Any field is empty (after stripping) →
     `error = "All fields are required."`
   - `len(password) < 8` →
     `error = "Password must be at least 8 characters."`

3. **Hash the password** — only reached if validation passes:
   `password_hash = generate_password_hash(password)`
   Import `generate_password_hash` from `werkzeug.security` is **already**
   present in `db.py` but must also be imported in `app.py` for use here.

4. **Insert the user** — call `create_user(name, email, password_hash)` inside
   a `try / except sqlite3.IntegrityError` block:
   - `IntegrityError` → re-render `register.html` with
     `error = "An account with that email already exists."`
   - Success → `flash("Account created! Please sign in.")` then
     `return redirect(url_for("login"))`

> [!NOTE]
> `sqlite3` must be imported in `app.py` to catch `sqlite3.IntegrityError`.
> Add `import sqlite3` near the top of the file.

---

### 3 · Template layer

---

#### [MODIFY] [register.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/register.html)

**One line change only** — line 20:

```
Current:   <form method="POST" action="/register">
Change to: <form method="POST" action="{{ url_for('register') }}">
```

Everything else in the template is already correct:
- `{% if error %}` / `{{ error }}` block is present (lines 16–18).
- All three `name` attributes (`name`, `email`, `password`) match what the
  route reads from `request.form`.
- The template extends `base.html`.

> [!NOTE]
> The flash message ("Account created! Please sign in.") will be displayed
> on the **login** page, not here. `base.html` does not yet render flashed
> messages. This will be addressed in Step 3 when `login.html` is updated;
> for now the flash is stored in the session and simply goes unrendered.
> This is acceptable — the redirect itself confirms success.

---

## Execution Order

1. Edit `database/db.py` — add the two helpers (no risk to existing routes).
2. Edit `app.py` — expand imports, set `secret_key`, upgrade the route.
3. Edit `templates/register.html` — swap the hardcoded `action` URL.
4. Restart the server and verify.

---

## Verification Plan

### Manual steps (run the app with `python app.py`)

| # | Action | Expected result |
|---|--------|-----------------|
| 1 | Visit `http://127.0.0.1:5001/register` | Form renders, no errors |
| 2 | Submit with all fields blank | Inline error: *"All fields are required."* — stays on register page |
| 3 | Submit with password `abc123` (7 chars) | Inline error: *"Password must be at least 8 characters."* |
| 4 | Submit with `demo@spendly.com` (seed user's email) | Inline error: *"An account with that email already exists."* |
| 5 | Submit with a fresh email and valid password | Redirected to `/login` |
| 6 | Open `expense_tracker.db` with any SQLite viewer | New row in `users`; `password_hash` begins with `scrypt:` or `pbkdf2:`, **not** plaintext |
| 7 | Visit `/`, `/login`, `/privacy`, `/terms` | All still render correctly |
| 8 | Restart the server and visit `/register` | App starts cleanly; no import errors |

### Automated tests
```bash
pytest
```
Existing tests must still pass. No new test file is added in this step.
