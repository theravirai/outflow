# Authentication & Demo Mode

## What does this component do?
This document outlines how Outflow securely identifies users, protects them from cross-site attacks, and implements a frictionless "Demo Mode" for onboarding.

## 1. Session Management
Outflow uses standard, cryptographically signed HTTP-only cookies provided natively by Flask (`flask.session`).
*   **Why not JWT?** Since Outflow is a monolithic SSR app, there is no need to pass a stateless JWT back and forth to a detached frontend. Http-only cookies natively prevent Cross-Site Scripting (XSS) attacks from stealing session identifiers via `document.cookie`.
*   **Password Hashing:** Handled via `werkzeug.security.generate_password_hash` utilizing `pbkdf2:sha256`.

## 2. CSRF Protection
Because we rely on cookie-based sessions, we are vulnerable to Cross-Site Request Forgery (CSRF). 
*   **Implementation:** 
    1. A `@app.before_request` hook assigns a cryptographically random `csrf_token` to every user session.
    2. A `@app.context_processor` injects this token globally into all Jinja2 templates via `<meta name="csrf-token">`.
    3. Another `@app.before_request` hook intercepts *all* state-mutating requests (`POST`, `PUT`, `DELETE`). If the header `X-CSRF-Token` or the form payload does not perfectly match the session's token, the server hard-aborts with a `400 Bad Request`.
*   **Challenges:** The Landing Page initially lacked the CSRF token in its `base.html` head, causing AI Voice-to-Text (`POST /api/assistant/transcribe`) to randomly fail for unauthenticated demo users. This was solved by globally injecting the `<meta>` tag across all layouts.

## 3. Demo Mode Architecture
To reduce onboarding friction, Outflow allows users to try the full application without creating an account.

*   **How it works:**
    1. When a user clicks "Try Demo", `create_demo_user()` dynamically inserts a ghost user into the PostgreSQL database.
    2. We seed this ghost user with realistic transaction history (spanning dates relative to `date.today()`).
    3. The Flask session is tagged with `user_id = ghost_id` and a cookie `was_demo = True`.
*   **Seamless Conversion:** If the user enjoys the app and clicks "Sign Up", they are routed to registration. Upon successful registration, `convert_demo_user()` swaps the ghost email for the real email and applies the new password hash. **All of their demo data instantly becomes their real data.**
*   **Garbage Collection:** Ghost accounts that are abandoned are swept from the database periodically via `cleanup_old_demo_users()`, ensuring the database doesn't bloat with dead records.

## 4. Password Recovery
Users who forget their password can reset it via the `/forgot-password` and `/reset-password/<token>` routes.
*   **Implementation:** When a user requests a reset, the system generates a cryptographically secure, URL-safe 32-byte token (`secrets.token_urlsafe(32)`).
*   **Expiration:** Tokens are stored in the `password_resets` table with a strict 1-hour expiration timestamp.
*   **Security:** To prevent email enumeration attacks, the system always returns the exact same "success" message ("If an account exists... a link has been sent") whether the email exists in the database or not. Tokens are automatically deleted upon successful password reset.
