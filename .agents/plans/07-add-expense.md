# Implementation Plan - Add Expense

This plan details the implementation for Step 7: Add Expense.

## Goal
Implement the expense addition flow, allowing logged-in users to record new expenses with an amount, category, date, and description.

## Proposed Changes

### 1. Database Helpers
In [database/db.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/database/db.py):
* Add `create_expense(user_id, amount, category, date, description)` helper function to insert a row into the `expenses` table.

### 2. Flask Route and Views
In [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py):
* Import `create_expense` from `database.db`.
* Update the placeholder `@app.route("/expenses/add")` route to support `GET` and `POST` methods:
  - If user is not logged in (`session.get("user_id")` is absent), redirect to the login page.
  - On `GET`, render `add_expense.html` with the default date set to today.
  - On `POST`, retrieve and validate the request form parameters (`amount`, `category`, `date`, `description`):
    - `amount`: non-empty, numeric float, greater than 0.
    - `category`: non-empty, must be one of `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`.
    - `date`: non-empty, matches `YYYY-MM-DD`.
    - `description`: optional, maximum 200 characters.
  - If validation fails, render `add_expense.html` with an `error` message and preserve the user's form inputs.
  - If validation succeeds, insert the expense row into the DB using `create_expense`, flash a success message, and redirect to the `/profile` page.

### 3. Templates and CSS Styling
* **Template ([templates/profile.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/profile.html))**:
  - Wrap the Recent Expenses card title in a `.card-header-flex` container.
  - Add an "Add Expense" link in the card header that references `url_for('add_expense')`.
  - Render success flash messages at the top of the profile main section.
* **Styles ([static/css/profile.css](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/static/css/profile.css))**:
  - Implement flex alignment styling for `.card-header-flex` to layout the section title and "Add Expense" button side-by-side.
  - Add styling for the `.flash-success` alert banner (light green theme).
* **Template ([templates/add_expense.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/add_expense.html)) [NEW]**:
  - Create the standalone Jinja2 template extending `base.html`.
  - Build the input form containing Amount (with a fixed Euro symbol prefix), Category select dropdown, Date picker, and Description input.
  - Include cancel link routing back to `/profile` and submit button.
  - Show error banner if an error is present.
* **Styles ([static/css/expense.css](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/static/css/expense.css)) [NEW]**:
  - Add page-specific styles for the Add Expense layout.
  - Include form controls styling, button layouts, amount input prefix alignment, and dropdown customizations.

### 4. Verification Plan
* Create a dedicated test file `tests/test_add_expense.py`.
* Test unauthenticated access (should redirect to `/login`).
* Test input validations (empty fields, non-numeric/negative amount, invalid category, long description).
* Test successful form submission (DB write, redirect, and dynamic calculations validation).
