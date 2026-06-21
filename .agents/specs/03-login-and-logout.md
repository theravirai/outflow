# Spec: Login and Logout

## Overview
Step 3 implements authentication by upgrading the `GET /login` and `GET /logout` routes. When a user submits the login form, the server verifies their credentials against the database using Werkzeug's `check_password_hash`. If valid, the user's ID is stored in the Flask session. The logout route simply clears this session. Navigation links in the base template are also updated to reflect the user's authentication state.

## Depends on
- **Step 2 — Registration**: User accounts must exist and `get_user_by_email()` must be available in `database/db.py`.

## Routes
- `POST /login` — Process login form, verify credentials, set session, and redirect — Public
- `GET /logout` — Clear session and redirect to login — Logged-in

## Database changes
No database changes.

## Templates
- **Create:** None.
- **Modify:**
  - `templates/login.html`: Update form action to `{{ url_for('login') }}`. Display flashed messages (like the success message from registration) if present.
  - `templates/base.html`: Update navbar to conditionally show "Sign in" / "Get started" for logged-out users, and a "Sign out" link for logged-in users.

## Files to change
- `app.py`
- `templates/login.html`
- `templates/base.html`

## Files to create
None.

## New dependencies
No new dependencies. Uses `flask.session` and `werkzeug.security.check_password_hash`.

## Rules for implementation
- No SQLAlchemy or ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug (`check_password_hash(user['password_hash'], password)`).
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- On failed login, re-render `login.html` with an `error` variable (do not redirect).
- On successful login, set `session["user_id"]` and redirect to `/profile`.
- In `base.html`, use `{% if session.get('user_id') %}` to toggle navigation items.

## Definition of done
- [ ] `POST /login` with an unknown email renders an inline error.
- [ ] `POST /login` with a known email but wrong password renders an inline error.
- [ ] `POST /login` with correct credentials sets `session["user_id"]` and redirects to `/profile`.
- [ ] `GET /logout` clears the session using `session.clear()` and redirects to `/login`.
- [ ] The navbar shows "Sign out" (and hides auth links) when the user is logged in.



