# Implementation Plan - Backend Connection (Profile Page)

This plan details the implementation for Step 5: Backend Connection for the profile page.

## Goal
Replace all hardcoded data in the `/profile` route with live SQLite queries. This will display dynamic and correct user info, summary stats, transaction history, and category breakdown for any logged-in user.

## Proposed Changes

### 1. Create Database Query Helpers
We will create a new file [database/queries.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/database/queries.py) containing pure SQLite queries to isolate DB interactions from the Flask app.

* **`get_user_by_id(user_id)`**
  * Fetches `name`, `email`, and `created_at` from the `users` table.
  * Formats `created_at` (e.g., `"2026-06-24 12:00:00"`) into `member_since` with the format `"Month YYYY"` (e.g., `"June 2026"`).
  * Computes initials (up to 2 letters, capitalized) from the user's name for the profile avatar.

* **`get_summary_stats(user_id)`**
  * Queries `expenses` for total amount spent and total transaction count.
  * Determines the `top_category` by summing amount grouped by category and returning the highest one.
  * Handles users with no expenses by returning `{"total_spent": 0.0, "transaction_count": 0, "top_category": "—"}`.

* **`get_recent_transactions(user_id, limit=10)`**
  * Returns the latest transactions for a user ordered by `date` desc and `id` desc.
  * Handles empty state by returning an empty list.

* **`get_category_breakdown(user_id)`**
  * Sums amounts grouped by category, ordered by amount descending.
  * Computes percentages rounded to the nearest integer.
  * **Critical constraint**: Ensures percentages sum to exactly 100% by adjusting the largest category to absorb any rounding remainder.
  * Maps `class` to the lowercase category name (e.g., `food`, `utilities`, `shopping`, `transport`).

### 2. Modify Flask Routes
In [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py):
* Import queries from `database.queries`.
* Modify `@app.route("/profile")` to fetch data from the database using `session["user_id"]`.

We will divide the changes in [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py) across 3 parallel subagents:
* **Subagent 1**: Fetches user info & transaction history via `get_user_by_id` and `get_recent_transactions`, passing `user_info` and `recent_expenses` to the template.
* **Subagent 2**: Fetches summary stats via `get_summary_stats`, passing `summary_stats` to the template.
* **Subagent 3**: Fetches category breakdown via `get_category_breakdown`, passing `category_breakdown` to the template.

### 3. Verification Plan
* Run unit tests on database queries.
* Validate the profile route is protected by login and redirects unauthenticated users to `/login`.
* Validate that logged-in users see correct and dynamic information.
* Confirm that amounts are formatted with the `€` symbol.
