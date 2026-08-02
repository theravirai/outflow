# Outflow

![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791?logo=postgresql&logoColor=white)
![Vanilla JS](https://img.shields.io/badge/Vanilla_JS-ES6+-F7DF1E?logo=javascript&logoColor=black)
![AI Powered](https://img.shields.io/badge/AI_Powered-Groq_Llama_3-FF4F00?logo=meta)

Track expenses, understand spending habits, and visualize where your money goes. Outflow is a lightweight personal expense tracker designed for simplicity, speed, and privacy. It is powered by a Flask backend, a PostgreSQL database, and features a blazing-fast conversational AI assistant built on Groq's LPU architecture.

## Quick Start

```bash
git clone https://github.com/theravirai/outflow.git
cd outflow
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # Configure DATABASE_URL and GROQ_API_KEY
python app.py
```

---

## Features

- **AI Assistant:** A conversational AI assistant that can log expenses, update entries, delete transactions, and answer questions about your spending in natural language.
- **Voice-to-Text Input:** Seamlessly record audio using the browser's MediaRecorder API and transcribe it using Whisper (`whisper-large-v3`) to log expenses hands-free.
- **AI Guardrails:** Strict safety bounds enforce rate limits (20 requests/minute), schema validation via Pydantic, and a non-negotiable "Human-in-the-Loop" confirmation flow to protect database integrity.
- **Expense Tracking:** Log expenditures with fields for amount, category, date, and description.
- **Dynamic Date Filtering:** Filter transaction history using quick presets (7 Days, 30 Days, This Month, All Time) or custom date ranges.
- **Financial Dashboard:** View high-level metrics including total spending, total transactions, and the primary category driving expenditure.
- **Responsive Interface:** A clean mobile-responsive layout styled entirely with modular, custom CSS (no heavy frameworks like Tailwind or Bootstrap).
- **Demo Mode:** One-click preview environment populated with realistic multi-month mock data. When you sign up, your demo data seamlessly transitions to your real account.
- **Secure Authentication:** User sign-up and login powered by secure session management, salted password hashing, and global CSRF token interception.
- **Dark Mode:** High-fidelity toggleable dark theme with system preference auto-detection and persistent state.

---

## Tech Stack

### Frontend
- **HTML5 & Jinja2:** Server-side template rendering with full layout inheritance.
- **Vanilla CSS:** Custom token-based design system (`style.css`) ensuring extreme performance and cohesive "fintech" aesthetic.
- **Vanilla JavaScript:** AJAX category filtering, persistent theme toggling, and complex DOM state management for the AI Chat panel.

### Backend & API
- **Python:** Core programming language.
- **Flask:** WSGI web application framework facilitating routing, request lifecycle handling, and session management.
- **Flask-Limiter:** In-memory rate limiting to protect AI endpoints from abuse.

### AI & NLP Pipeline
- **Groq API:** Ultra-low latency inference using `llama-3.1-8b-instant` for intent routing and `whisper-large-v3` for speech transcription.
- **Pydantic:** Strict structural typing and bounds validation for LLM JSON outputs.

### Database
- **PostgreSQL:** Robust relational database accessed via `psycopg2`.
- **Native SQL:** All queries are written in raw SQL using parameterized structures to prevent SQL injection (no ORM used).

---

## Installation

### Prerequisites
- Python 3.13+
- PostgreSQL instance (local server or hosted, e.g., Neon)
- [Groq API Key](https://console.groq.com/) for the AI features

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
   Open the `.env` file and set the required variables:
   - `DATABASE_URL`: Your development PostgreSQL connection string.
   - `DATABASE_URL_TEST`: A separate test PostgreSQL database (mandatory for running tests).
   - `GROQ_API_KEY`: Your Groq API key to power the AI Assistant.

5. **Verify the installation by running the test suite:**
   > [!IMPORTANT]
   > The test suite requires `DATABASE_URL_TEST` to be set. Running the tests will automatically truncate and re-seed the test database in an isolated sandbox.
   ```bash
   pytest
   ```

6. **Start the local development server:**
   ```bash
   python app.py
   ```
   *Note: The application runs on port 5001.* Open [http://localhost:5001](http://localhost:5001) in your browser.

---

## Environment Variables

Configure the following settings in your `.env` file:

| Variable | Description | Required | Default |
|---|---|---|---|
| `DATABASE_URL` | Connection string for the PostgreSQL application database. | Yes | `postgresql://postgres:postgres@localhost:5432/outflow` |
| `DATABASE_URL_TEST` | Connection string for the PostgreSQL test database (wiped and seeded on test runs). | Yes | `postgresql://postgres:postgres@localhost:5432/outflow_test` |
| `SECRET_KEY` | Used by Flask to cryptographically sign session cookies and CSRF tokens. | Yes | (Auto-generated in example) |
| `GROQ_API_KEY` | Powers the LLM Intent Router and Whisper voice transcription. | Yes | None |
| `FLASK_DEBUG` | Controls the interactive debugger execution behavior. | No | `False` |

---
