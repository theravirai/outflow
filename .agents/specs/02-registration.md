# Spec: Registration

## Overview
Step 2 upgrades the `GET /register` stub into a fully working registration flow.
When a visitor submits the sign-up form, the server validates the input,
hashes the password with Werkzeug, inserts a new row into the `users` table,
and redirects the user to the login page with a success flash message.
This is the first step that writes user data to the database and is a
prerequisite for every authenticated feature in the Spendly roadmap.

---

## Depends on
- **Step 1 — Database Setup**: `get_db()`, `init_db()`, and the `users` table
  must already exist and be wired into `app.py`.

---

## Routes

| Method | Path        | Description                                      | Access  |
|--------|-------------|--------------------------------------------------|---------|
| `GET`  | `/register` | Render the registration form *(already exists)*  | Public  |
| `POST` | `/register` | Process form submission, create user, redirect   | Public  |

---

## Database changes

No new tables or columns are required. The `users` table created in Step 1
already has all necessary columns (`id`, `name`, `email`, `password_hash`,
`created_at`).

Add two new helper functions to `database/db.py`:

- **`create_user(name, email, password_hash)`** — inserts a row into `users`
  and returns the new `id`. Raises an `IntegrityError` if the email is already
  taken (UNIQUE constraint).
- **`get_user_by_email(email)`** — looks up a user row by email; returns the
  `sqlite3.Row` or `None`. (Needed to check for duplicates before insert and
  will be reused in Step 3 — Login.)

---

## Templates

### Modify
- **`templates/register.html`**
  - Change `<form action="/register">` to `action="{{ url_for('register') }}"`.
  - Add `method="POST"` if not already present (it is).
  - Ensure the `{% if error %}` block is present — it already is.
  - No structural changes needed; the template is already well-formed.

### Create
None.

---

## Files to change

| File                      | What changes                                                                 |
|---------------------------|------------------------------------------------------------------------------|
| `app.py`                  | Add `POST` handler for `/register`; import `create_user`, `get_user_by_email` from `database.db`; configure `app.secret_key` for flash messages |
| `database/db.py`          | Add `create_user()` and `get_user_by_email()` helper functions               |
| `templates/register.html` | Minor: use `url_for('register')` in the form `action` attribute              |

---

## Files to create

None.

---

## New dependencies

No new pip packages. Uses only:
- `sqlite3` (standard library)
- `werkzeug.security.generate_password_hash` (already installed)
- `flask.flash`, `flask.redirect`, `flask.url_for`, `flask.request`,
  `flask.session` (all part of Flask, already installed)

---

## Rules for implementation

- **No SQLAlchemy or ORMs** — use raw `sqlite3` with `get_db()`.
- **Parameterised queries only** — never use string formatting in SQL.
- **Passwords hashed with Werkzeug** — `generate_password_hash(password)`;
  never store plaintext.
- **Use CSS variables** — never hardcode hex values; re-use existing
  `auth-error` class from `style.css` for inline error display.
- **All templates extend `base.html`** — `register.html` already does.
- **No JS frameworks** — the frontend is intentionally vanilla.
- **No DB logic in route functions** — all queries live in `database/db.py`.
- **`app.secret_key`** must be set before any `flash()` call; use a hard-coded
  dev string for now (e.g. `"dev-secret-change-in-prod"`).
- **Server-side validation** (performed in the route before touching the DB):
  - All three fields (`name`, `email`, `password`) must be non-empty.
  - Password must be at least 8 characters.
  - Email must already pass browser `type="email"` validation; no extra regex
    needed at this stage.
- On **duplicate email** catch `sqlite3.IntegrityError` and re-render
  `register.html` with `error="An account with that email already exists."`.
- On **success** use `flash("Account created! Please sign in.")` then
  `redirect(url_for('login'))`.
- **Do not implement login logic** — that is Step 3.

---

## Definition of done

- [ ] `POST /register` with valid data inserts a new row into `users` and
      redirects to `/login`.
- [ ] The redirected `/login` page displays the flash message
      "Account created! Please sign in."
- [ ] Submitting the form with a blank name, email, or password shows an
      inline error on `register.html` (no redirect, no 500).
- [ ] Submitting with a password shorter than 8 characters shows an inline
      error.
- [ ] Registering with an email that already exists shows
      "An account with that email already exists." inline.
- [ ] Password is stored as a hash — `password_hash` column never contains
      plaintext when inspected in the SQLite DB.
- [ ] `create_user()` and `get_user_by_email()` live in `database/db.py`, not
      in `app.py`.
- [ ] The app starts without errors after the changes (`python app.py`).
- [ ] All existing routes (`/`, `/login`, `/privacy`, `/terms`) still work.
