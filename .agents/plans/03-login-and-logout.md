# Implementation Plan: Login and Logout

This plan details the implementation for Step 03: Login and Logout. 

## Goal
Implement a fully functional authentication flow based on the existing `users` table and session management.

## User Review Required
No breaking changes. This implements the login/logout functionality as outlined in the spec and adds a standard `.auth-success` CSS class for rendering flash messages.

## Open Questions
None.

## Proposed Changes

### Backend

#### [MODIFY] [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py)
- **Imports**: Add `check_password_hash` from `werkzeug.security` and `session` from `flask`.
- **`login` Route**:
  - Change `@app.route("/login")` to accept `methods=["GET", "POST"]`.
  - On `GET`, return `render_template("login.html")`.
  - On `POST`:
    - Retrieve `email` and `password` from `request.form`.
    - Fetch the user via `get_user_by_email(email)`.
    - If user is missing or `check_password_hash(user['password_hash'], password)` fails, `return render_template("login.html", error="Invalid email or password.")`.
    - If successful, set `session["user_id"] = user["id"]` and `return redirect(url_for("profile"))`.
- **`logout` Route**:
  - Remove the stub return.
  - Call `session.clear()`.
  - `return redirect(url_for("login"))`.

### Frontend Templates

#### [MODIFY] [login.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/login.html)
- Update the `<form>` to ensure `action="{{ url_for('login') }}"`.
- Add a block to display flashed messages (for successful registration feedback).
  ```html
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for message in messages %}
        <div class="auth-success">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  ```

#### [MODIFY] [base.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/base.html)
- Update the navigation links to reflect authentication state using `session.get('user_id')`.
  ```html
  <div class="nav-links">
      {% if session.get('user_id') %}
          <a href="{{ url_for('logout') }}">Sign out</a>
      {% else %}
          <a href="{{ url_for('login') }}">Sign in</a>
          <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
      {% endif %}
  </div>
  ```

#### [MODIFY] [style.css](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/static/css/style.css)
- Add an `.auth-success` class to style the flash messages properly using CSS variables.
  ```css
  .auth-success {
      background: var(--accent-light);
      color: var(--accent);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 0.75rem 1rem;
      font-size: 0.875rem;
      margin-bottom: 1.25rem;
  }
  ```

## Verification Plan

### Manual Verification
1. Run the app (`python app.py`).
2. Register a new user to test the flash message appearing on the login screen.
3. Attempt to login with invalid credentials and confirm the error message.
4. Login with valid credentials and confirm it redirects to `/profile` (which is a stub route).
5. Verify that the navigation bar updates to show "Sign out".
6. Click "Sign out" and verify it clears the session and redirects to `/login`.
