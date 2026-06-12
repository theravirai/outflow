# Spendly - Personal Finance Tracker

## Project Overview
Spendly is a web-based personal finance and expense tracking application built using **Python** and **Flask**. The project serves as an educational codebase (indicated by instructions like "students will write this file") aimed at teaching web development concepts. 

### Architecture & Tech Stack
- **Backend:** Python, Flask, Werkzeug.
- **Database:** SQLite (managed via `database/db.py`).
- **Frontend:** Vanilla HTML5, CSS3, and JavaScript. Jinja2 is used for server-side template rendering.
- **Testing:** Pytest and pytest-flask.
- **Design:** No heavy frontend frameworks or build steps are used. CSS variables and responsive flex/grid layouts are written in standard CSS.

## Directory Structure
- `app.py`: The main entry point for the Flask application containing the route definitions.
- `database/`: Contains database configuration and setup scripts (`db.py`).
- `templates/`: Jinja2 HTML templates (`base.html`, `landing.html`, `login.html`, `register.html`, etc.).
- `static/`: Static assets including CSS (`style.css`, `landing.css`) and JavaScript (`main.js`).
- `requirements.txt`: Python package dependencies.
- `venv/`: Standard location for the Python virtual environment.

## Building and Running

### Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   ```
2. Activate the virtual environment:
   - macOS/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the App
Start the Flask development server:
```bash
python app.py
```
The app will run locally in debug mode on port **5001** (e.g., `http://127.0.0.1:5001`).

### Testing
Run the test suite using pytest:
```bash
pytest
```

## Development Conventions
- **Educational Codebase:** Be aware that some files and routes contain placeholder comments or stubs (e.g., "coming in Step 3", "Students will write this file in Step 1"). Ensure changes align with the intended learning path or current phase of the project unless instructed otherwise.
- **Vanilla Frontend:** Keep styling in pure CSS without preprocessors. Use Vanilla JavaScript for DOM manipulation (like the video modal) without libraries like jQuery or React.
- **Templating:** Use Jinja2 template inheritance. New pages should extend `base.html` and place content within the `{% block content %}` block.
- **Database:** Use standard SQLite3 via the standard library for data persistence. Ensure raw SQL or simple abstractions are maintained unless an ORM (like SQLAlchemy) is explicitly introduced into the curriculum.


## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — it belongs in `database/db.py`
- **Never install new packages** mid-feature without flagging it — keep `requirements.txt` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **`database/db.py` is currently empty** — do not assume helpers exist until the step that implements them
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` must run `PRAGMA foreign_keys = ON` on every connection
- The app runs on **port 5001**, not the Flask default 5000 — don't change this