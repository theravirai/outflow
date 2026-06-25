# Spec: Add Expense

## Overview
Step 7 implements the expense addition flow, allowing logged-in users to record new expenses with an amount, category, date, and description. This feature connects the dashboard directly to user activity, moving the application from a read-only view of seeded data to an interactive financial tracker. Users can access this flow via a clean button in the "Recent Expenses" section on their profile dashboard.

## Depends on
- **Step 3 — Login / Logout** (`session["user_id"]` validation check)
- **Step 5 — Backend Connection** (to render the profile dashboard with dynamic expenses)
- **Step 6 — Date Filter for Profile Page** (the profile page layout includes the filter card and date filtering structure)

## Routes
| Method | Path            | Description                                              | Access    |
|--------|-----------------|----------------------------------------------------------|-----------|
| `GET`  | `/expenses/add` | Renders the "Add Expense" form template                  | Logged-in |
| `POST` | `/expenses/add` | Validates and processes the form submission, inserts DB  | Logged-in |

## Database changes
No database changes. The `expenses` table created in Step 1 already contains the necessary columns (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`).

We will add a database helper function to `database/db.py`:
- **`create_expense(user_id, amount, category, date, description)`** — inserts a row into the `expenses` table and returns the row's `id`.

## Templates
- **Create:**
  - `templates/add_expense.html` — The new standalone template that extends `base.html` and renders the expense addition form.
- **Modify:**
  - `templates/profile.html` — Update the Recent Expenses section header to include an "Add Expense" button next to the title, wrapped in a flexbox container.

## Files to change
| File                     | What changes                                                                                                               |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------|
| `app.py`                 | Import `create_expense` from `database.db`; update `/expenses/add` route to support `GET` and `POST` with validation and auth. |
| `database/db.py`         | Add `create_expense(user_id, amount, category, date, description)` database helper function.                               |
| `templates/profile.html` | Wrap the card title and add the "Add Expense" link in a `.card-header-flex` container.                                     |
| `static/css/profile.css` | Style `.card-header-flex` to align title and button, and clean up border/padding styles on `.transactions-card`.           |

## Files to create
| File                          | Description                                                                                       |
|-------------------------------|---------------------------------------------------------------------------------------------------|
| `templates/add_expense.html`  | Jinja2 template for the Add Expense form page.                                                     |
| `static/css/expense.css`      | Page-specific CSS styling for the Add Expense page and form elements (inputs, select, textarea).   |
| `tests/test_add_expense.py`   | Pytest tests validating route authorization, server-side validation, and successful DB insertion.   |

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No JS frameworks — vanilla JS only
- No DB logic in route functions — all database write queries must live in `database/db.py`
- Server-side validation:
  - `amount` must be present and a positive number (greater than 0).
  - `category` must be one of the predefined categories: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`.
  - `date` must be present and in a valid date format (`YYYY-MM-DD`).
  - `description` is optional, but must not exceed 200 characters if provided, and should be stripped of leading/trailing whitespace.
  - If validation fails, the page must re-render showing the error message and preserving the user's inputs.

## Definition of done
- [ ] Profile page contains a stylized "Add Expense" button in the Recent Expenses section header.
- [ ] Clicking "Add Expense" redirects the user to `/expenses/add` (or requests login if not authenticated).
- [ ] The Add Expense page renders a clean, responsive form with inputs for Amount (prefixed with €), Category (dropdown select), Date (defaults to today), and Description (textarea/text input).
- [ ] Submitting the form with valid data inserts the expense into the SQLite database under the logged-in user, and redirects the user back to the profile page.
- [ ] A success flash message is shown on the profile page after successful expense addition.
- [ ] Submitting invalid inputs (e.g., negative/zero amount, invalid date, invalid category, or long description) halts database insertion, displays a clean error banner, and preserves entered form fields.
- [ ] Standard Euro formatting (`€X.XX`) is maintained.
- [ ] All tests in `tests/test_add_expense.py` pass.
