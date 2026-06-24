# Spec: Date Filter for Profile Page

## Overview
Step 6 implements date filtering on the dashboard/profile page of Spendly. Currently, the profile page displays all expenses for the logged-in user since the beginning of time. This feature adds a date filtering control block at the top of the profile page, enabling users to filter all dynamic sections (Summary Stats, Category Breakdown, and Recent Expenses) by standard presets (e.g., Last 7 Days, Last 30 Days, This Month, All Time) or by entering a custom start and end date range.

## Depends on
- **Step 5 — Backend Connection** (`database/queries.py` and query helpers exist)

## Routes
No new routes. The existing route `GET /profile` is upgraded to accept optional query parameters:
- `start_date` (optional, format: `YYYY-MM-DD`) — the start date of the filter range
- `end_date` (optional, format: `YYYY-MM-DD`) — the end date of the filter range
- `preset` (optional, values: `7d`, `30d`, `this-month`, `all`, `custom`) — predefined quick-select ranges

If `preset` is provided:
- `7d`: Filter from today - 6 days to today
- `30d`: Filter from today - 29 days to today
- `this-month`: Filter from the 1st of the current month to the last day of the current month (or today)
- `all`: Clear date parameters (show all transactions)
- `custom` or omitted: Use the specified `start_date` and `end_date` directly

The resolved start/end dates must be passed to the template context as well as the active preset name so they can be set as selected in the UI form inputs.

## Database changes
No database changes. We query the `date` text column in the `expenses` table.

## Templates
- **Modify**: `templates/profile.html`
  - Add a `.filter-card` container right inside `<section class="profile-main">` (above the `.stats-grid`).
  - The card must feature:
    - Quick-select preset buttons/links: "Last 7 Days", "Last 30 Days", "This Month", and "All Time". Highlight the active preset using an `.active` CSS class.
    - A custom range form (`<form method="GET">`) containing:
      - `<input type="date" id="start_date" name="start_date">`
      - `<input type="date" id="end_date" name="end_date">`
      - A submit button ("Apply") and a "Clear" link that resets all filters.
      - A hidden input for `<input type="hidden" name="preset" value="custom">` to indicate the user has submitted a custom range.

## Files to change
- `app.py`:
  - Update `/profile` route to read `start_date`, `end_date`, and `preset` from query parameters.
  - Calculate start/end dates for presets based on the current system date.
  - Pass the resolved dates to the updated helper functions and inject them into `render_template`.
- `database/queries.py`:
  - Modify the following query functions to accept optional parameters `start_date` (default `None`) and `end_date` (default `None`):
    - `get_summary_stats(user_id, start_date=None, end_date=None)`
    - `get_recent_transactions(user_id, limit=10, start_date=None, end_date=None)`
    - `get_category_breakdown(user_id, start_date=None, end_date=None)`
  - Dynamically construct SQL queries using parameterized checks (`AND date >= ?` and `AND date <= ?`) without SQL injection vulnerabilities.
- `static/css/profile.css`:
  - Style the filter card, forms, date inputs, buttons, and preset links to match Spendly's high-fidelity minimal theme. Ensure responsive styling (stacked forms on smaller viewports).

## Files to create
None.

## New dependencies
No new dependencies. Standard Python `datetime`, `timedelta`, and `date` utilities.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only.
- Parameterised SQL queries only — build query string safely by appending parameters to the SQL placeholder list.
- Keep CSS variables for styling.
- All templates must extend `base.html`.
- If a user has no expenses matching the selected range:
  - `total_spent` must display `€0.00`
  - `transaction_count` must display `0`
  - `top_category` must display `—`
  - Category breakdown must show a descriptive empty message (e.g. "No expenses in this range")
  - Recent expenses table must show a descriptive empty message (e.g. "No transactions found in this range")
- Presets must calculate dates relative to the current date dynamically.

## Tests to write
File: `tests/test_date_filter.py`

### Unit tests
- Test `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown` with valid date filters:
  - Validate that only expenses within the range are included in the results.
  - Validate that an empty range returns empty/zero results gracefully.
  - Validate that open-ended ranges (only `start_date` or only `end_date` provided) function correctly.

### Route tests
- Test `GET /profile` with query parameters:
  - Validate that `/profile?preset=7d` correctly updates stats to only include last 7 days of expenses.
  - Validate that `/profile?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&preset=custom` returns only transactions matching the custom range.
  - Validate that the rendered HTML contains the values for inputs and has the correct `.active` preset highlighted.

## Definition of done
- [ ] Profile page displays a beautiful filter bar with preset buttons ("Last 7 Days", "Last 30 Days", "This Month", "All Time") and custom date inputs.
- [ ] Selecting "Last 7 Days" filters all dashboard stats, the transaction list, and the category breakdown to only show the last 7 days of expenses. The "Last 7 Days" button is visually active.
- [ ] Entering a custom start and end date and clicking "Apply" correctly filters all stats and transactions to the matching range.
- [ ] Clicking "Clear" resets the filters to show all transactions.
- [ ] When no transactions exist in the selected range, the page displays €0.00 total spent, 0 transactions, "—" top category, and clean empty state messages for transactions/breakdown, without raising exceptions.
- [ ] All unit and route tests in `tests/test_date_filter.py` pass.
