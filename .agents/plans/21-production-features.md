# Plan: Production Features & Edge Cases

This document outlines the step-by-step implementation plan to transition Outflow from a functional prototype to a production-ready application. It introduces user lifecycle management, account security, core product expectations, and DevOps standards.

## Phase 1: User Profile Management
**Goal:** Allow authenticated users to manage their personal data, secure their account, and exercise their right to data deletion (GDPR).

1. **Settings UI (`templates/settings.html`)**
   - Create a new template extending `base.html`.
   - Design sections for: Profile Details (Name/Email), Change Password, and Danger Zone (Delete Account).
   - Integrate Gravatar (generate an MD5 hash of the user's email to display an automatic profile picture).

2. **Backend Routes (`app.py` & `database/db.py`)**
   - `GET /settings`: Render the settings page.
   - `POST /settings/profile`: Update name and email. Must include a check to ensure the new email is not already taken by another user.
   - `POST /settings/password`: Securely change the password. Must require the user to input their *current* password for verification.
   - `POST /settings/delete`: Permanently delete the user's account and cascade-delete all associated transactions. Clear the session and redirect to the landing page.

## Phase 2: Authentication Edge Cases & Security
**Goal:** Secure the application against brute-force attacks and provide an industry-standard password recovery flow.

1. **Rate Limiting**
   - Apply `Flask-Limiter` (`@limiter.limit`) to `/login` and `/register` routes to prevent credential stuffing and spam.

2. **Password Recovery Flow**
   - **Database:** Create a `password_resets` table (`id`, `user_id`, `token`, `expires_at`).
   - **UI:** Create `forgot_password.html` (request link) and `reset_password.html` (enter new password).
   - **Logic:** 
     - `POST /forgot-password`: Generate a secure, time-limited cryptographic token. Send a recovery link via email using Python's built-in `smtplib` (can be configured with Mailtrap or a dummy SMTP server for development).
     - `POST /reset-password/<token>`: Validate the token, update the user's password, and invalidate the token.

## Phase 3: Core Product Features
**Goal:** Add essential features that users expect from a modern financial application.

1. **Data Export (CSV)**
   - Add a `GET /expenses/export` route.
   - Query all transactions for the authenticated user.
   - Use Python's built-in `csv` module to generate a file in-memory.
   - Return the file to the browser with the `text/csv` mimetype and `Content-Disposition: attachment` headers.

2. **Advanced Search & Filtering**
   - Update the `/profile` route to accept a `q` (search query) parameter.
   - Modify the SQL query in `db.py` to filter transactions using `ILIKE` on the description field.
   - Update the UI to include a search bar alongside the existing date filters.

3. **Custom Categories (Optional / Advanced)**
   - Transition from hardcoded categories to a dynamic `categories` table (`id`, `user_id`, `name`).
   - Allow users to add, rename, and delete custom categories.
   - Update the AI expense parser to map transactions to the user's custom categories.

## Phase 4: Infrastructure & DevOps
**Goal:** Standardize the deployment pipeline and database lifecycle.

1. **Dockerization**
   - Create a `Dockerfile` using a lightweight Python 3.13 image. Configure it to install dependencies from `requirements.txt` and run the app via Gunicorn (or Flask dev server for local).
   - Create a `docker-compose.yml` defining two services: the `web` application and a `db` PostgreSQL instance.

2. **Database Migrations**
   - Since third-party packages like Alembic are restricted, build a lightweight `migrate.py` script.
   - This script will read versioned `.sql` files from a `migrations/` folder and execute them sequentially to manage schema changes (like adding the `password_resets` table) without data loss.
