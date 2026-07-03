# Outflow

Track expenses, understand spending habits, and visualize where your money goes. Outflow is a lightweight personal expense tracker designed for simplicity, speed, and privacy. It is powered by a Flask backend and backed by a PostgreSQL database, ensuring robust data management and high performance.

<!-- ## Live Demo

🔗 [https://your-live-url.com](https://your-live-url.com)

Try Demo mode is available instantly. No registration is required. -->

## Quick Start

```bash
git clone https://github.com/theravirai/outflow.git
cd outflow
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure your DATABASE_URL and DATABASE_URL_TEST
python app.py
```
---

## Features

- **Expense Tracking:** Log expenditures with fields for amount, category, date, and description.
- **Categorization:** Classify transactions under pre-defined categories including Food, Transport, Bills, Health, Healthcare, Travel, Entertainment, Shopping, and Other.
- **Dynamic Date Filtering:** Filter transaction history using quick presets (7 Days, 30 Days, This Month, All Time) or custom date ranges.
- **Financial Dashboard:** View high-level metrics including total spending, total transactions, and the primary category driving expenditure.
- **Category Analytics:** Visualize category-wise spending with proportional percentage breakdowns and formatted metrics.
- **Responsive Interface:** A clean mobile-responsive layout styled entirely with modular, custom CSS.
- **Demo Mode:** One-click preview environment populated with realistic multi-month mock data, requiring no account creation.
- **Secure Authentication:** User sign-up and login powered by secure session management and salted password hashing.
- **Dark Mode:** High-fidelity toggleable dark theme with system preference auto-detection (`prefers-color-scheme`), custom-styled categories, and persistent state.

---

## Demo

Outflow features a dedicated **Demo Mode** designed to allow developers and prospective users to explore the application's full range of capabilities instantly.

- **Instant Access:** Explore the active dashboard, add new transactions, and test date filters immediately without registering for an account.
- **Isolated Sessions:** Each demo session is assigned a temporary, dynamically generated user account with an isolated database scope.
- **Automatic Seeding:** The system automatically seeds 90 days of realistic expense history (bills, groceries, transportation, travel) to demonstrate how the dashboard looks with mature data.
- **Lifecycle Management:** Demo accounts are isolated using a browser-session cookie. The cookie is configured to expire in 1 hour. Additionally, a server-side cleanup routine purges demo user accounts and their associated expenses from the database after 24 hours.

---

## Tech Stack

### Frontend
- **HTML5:** Semantic document structure.
- **Jinja2:** Server-side template rendering with full layout inheritance.
- **Vanilla CSS:** Custom stylesheets modularized by page context (`style.css`, `profile.css`, `landing.css`, `expense.css`) for performance and lightweight layouts without external framework overhead.
- **Vanilla JavaScript:** Persistent theme toggling, Lucide dynamic asset re-rendering, and lightweight interactivity.

### Backend
- **Python:** Core programming language.
- **Flask (v3.1):** WSGI web application framework facilitating routing, request lifecycle handling, and session management.
- **Werkzeug:** Cryptographic password hashing and validation.

### Database
- **PostgreSQL:** Robust relational database storing application and transaction data (compatible with Neon and local instances).
- **Native SQL:** All queries are written in raw SQL using parameterized query structures to prevent SQL injection vulnerabilities.

### Testing
- **pytest:** Automated test framework.
- **pytest-flask:** Flask-specific test client fixtures.

---

## Project Structure

- [app.py](/outflow/app.py): Application configuration, routing, and request handling.
- [database/](/outflow/database): Core database module.
- [database/db.py](/outflow/database/db.py): Database connection lifecycle, schema initialization, and demo session seeding.
- [database/queries.py](/outflow/database/queries.py): Relational SQL queries for dashboard statistics and data retrieval.
- [static/](/outflow/static): Frontend static assets.
- [static/css/](/outflow/static/css): Stylesheets containing custom design variables and layout rules.
  - [style.css](/outflow/static/css/style.css): Core variables, typography, and base layout styles.
  - [landing.css](/outflow/static/css/landing.css): Styles specific to the public landing page.
  - [profile.css](/outflow/static/css/profile.css): Grid definitions, tables, and analytics modules for the user dashboard.
  - [expense.css](/outflow/static/css/expense.css): Form component styling.
- [static/js/](/outflow/static/js): Client-side script directory containing global script files.
- [templates/](/outflow/templates): Server-rendered templates.
  - [base.html](/outflow/templates/base.html): Primary HTML structure including navigation headers, messages, and footers.
- [tests/](/outflow/tests): Automated unit and integration test suite.
- [requirements.txt](/outflow/requirements.txt): Declared project dependencies.

---

## Installation

### Prerequisites
- Python 3.10 or higher
- Git
- PostgreSQL instance (local server or hosted, e.g., [Neon](https://neon.tech))

### Step-by-Step Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/theravirai/outflow.git
   cd outflow
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   # On Windows: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Copy `.env.example` to create a `.env` file:
   ```bash
   cp .env.example .env
   ```
   Open the `.env` file and set the following database connection variables:
   - Set `DATABASE_URL` to your development PostgreSQL connection string.
   - Set `DATABASE_URL_TEST` to a separate test PostgreSQL database connection string (mandatory for running tests).

5. **Migrate existing SQLite data (Optional):**
   If you have a legacy SQLite database (`expense_tracker.db`), migrate its data directly to your PostgreSQL database by running:
   ```bash
   python migrate_to_pg.py
   ```

6. **Verify the installation by running the test suite:**
   > [!IMPORTANT]
   > The test suite requires `DATABASE_URL_TEST` to be set in your `.env`. Running the tests will automatically truncate and re-seed the test database.
   ```bash
   pytest
   ```

7. **Start the local development server:**
   ```bash
   python3 app.py
   ```
   *Note: The application is configured to run on port 5001.*

8. **Access the application:**
   Open [http://localhost:5001](http://localhost:5001) in your browser. The database tables will be automatically created and seeded with demo data upon startup if the database is empty.

---

## Environment Variables

Configure the following settings in your `.env` file:

| Variable | Description | Required | Default / Recommended |
|---|---|---|---|
| `DATABASE_URL` | Connection string for the PostgreSQL application database. | Yes | `postgresql://postgres:postgres@localhost:5432/outflow` |
| `DATABASE_URL_TEST` | Connection string for the PostgreSQL test database (wiped and seeded on test runs). | Yes | `postgresql://postgres:postgres@localhost:5432/outflow_test` |
| `SECRET_KEY` | Used by Flask to cryptographically sign session cookies. | No (Dev fallback) | Generate a secure random hex string for production. |
| `FLASK_DEBUG` | Controls the execution behavior of the Flask interactive debugger. | No | `False` in production; `True` during active development. |

---

## Technical Architecture & Decisions

### Automated Database Bootstrapping
To reduce configuration friction, the application checks for database tables and seeds initial development data automatically upon application startup. This guarantees the server is immediately functional upon executing `python app.py`.

### Native Referencing & Foreign Keys
Outflow relies on native PostgreSQL foreign key constraints to ensure strong referential integrity. When user or expense records are deleted, database cascades and constraints are enforced natively.

### Database-Level Aggregation
Dashboard data is computed dynamically on the database level. Queries accept optional date boundaries, enabling the database engine to handle aggregation, sums, and category sorting directly. This keeps the Flask application controller thin and focused solely on HTTP handling.

### Zero-Framework Frontend
To showcase clean DOM structure and styling proficiency, the application relies on native CSS grids, flexbox layouts, and semantic HTML structure rather than CSS frameworks. Page-specific stylesheets ensure browsers only load styles relevant to the active route, keeping loading times low.

### Anti-FOUC Theme Engine
To prevent the "Flash of Unstyled Content" (FOUC) when loading in Dark Mode, a blocking inline script in the `<head>` evaluates `localStorage` and OS preferences before the page elements render. All styling overrides are applied via CSS variables dynamically toggled on the `<html>` root element.
