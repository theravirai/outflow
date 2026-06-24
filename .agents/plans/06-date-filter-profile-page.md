# Implementation Plan - Date Filter for Profile Page

This plan details the implementation for Step 6: Date Filter for Profile Page.

## Goal
Implement interactive date filtering for the dashboard stats, category breakdown, and recent expenses on the Spendly profile page using a dynamic, responsive filter bar.

## Proposed Changes

### 1. Database Query Upgrades
In [database/queries.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/database/queries.py), modify the following query helpers to accept optional parameters `start_date` and `end_date`:
* **`get_summary_stats(user_id, start_date=None, end_date=None)`**
  * Apply parameterised `date >= ?` and `date <= ?` filters on both the total spend/count query and the top category query.
* **`get_recent_transactions(user_id, limit=10, start_date=None, end_date=None)`**
  * Apply parameterised date range constraints when querying the expenses list.
* **`get_category_breakdown(user_id, start_date=None, end_date=None)`**
  * Apply parameterised date range constraints to both the total spend query and the category sum queries.

### 2. Flask Route Integration
In [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py):
* Modify the `@app.route("/profile")` route.
* Extract query parameters: `preset`, `start_date`, and `end_date`.
* Compute dynamic date bounds for presets using Python's `datetime.date` and `datetime.timedelta`:
  * `7d`: From `today - 6 days` to `today`
  * `30d`: From `today - 29 days` to `today`
  * `this-month`: From the first day of the current month to today
  * `all`: No date filtering (`start_date=None`, `end_date=None`)
  * `custom` or omitted: Use standard inputs `start_date` and `end_date` (validated/formatted to `YYYY-MM-DD`).
* Pass the computed dates into query helper calls and inject the resolved `start_date`, `end_date`, and `preset` into the template context.

### 3. Frontend / UI Upgrades
* **Template ([templates/profile.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/profile.html))**:
  * Insert a `.filter-card` above `.stats-grid`.
  * Render a form with:
    - Quick-select links/buttons for presets: "Last 7 Days", "Last 30 Days", "This Month", and "All Time", adding the `.active` class to the current active preset.
    - Custom date range input fields (`start_date` and `end_date`).
    - An "Apply" submit button and a "Clear" link which routes back to `/profile` with no parameters.
* **Styles ([static/css/profile.css](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/static/css/profile.css))**:
  * Style the `.filter-card` component with card styles matching the rest of the application.
  * Style form layout, labels, and input fields to be clean, modern, and aligned with Spendly's color palette.
  * Make the form layout responsive, transitioning from a single-row flex alignment on desktop to a stacked block layout on mobile viewports.

### 4. Verification Plan
* Create a dedicated test file `tests/test_date_filter.py`.
* Write unit tests for all modified queries under various date bounds.
* Write route tests checking that query params for presets and custom date inputs return the expected filtered content and set appropriate initial values in the template inputs.
