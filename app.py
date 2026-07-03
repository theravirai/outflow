import os
import secrets
import psycopg2
from datetime import date, timedelta
import calendar
import math
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_expense, create_user, get_user_by_email, get_expense_by_id, update_expense, delete_expense as db_delete_expense, cleanup_old_demo_users, create_demo_user, IS_TESTING, DatabaseConnectionError
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)

# Enforce SECRET_KEY always exists
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is missing.")

app.secret_key = SECRET_KEY

# CSRF Protection Setup
@app.before_request
def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

@app.context_processor
def inject_csrf_token():
    def csrf_token_input():
        return f'<input type="hidden" name="csrf_token" value="{session.get("csrf_token", "")}">'
    return dict(csrf_token=lambda: session.get("csrf_token", ""), csrf_token_input=csrf_token_input)

@app.before_request
def validate_csrf():
    if IS_TESTING:
        return
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
        expected_token = session.get("csrf_token")
        if not expected_token or not token or not secrets.compare_digest(expected_token, token):
            abort(400, description="CSRF token validation failed.")

@app.errorhandler(DatabaseConnectionError)
def handle_database_connection_error(e):
    app.logger.error(f"Database connection error: {e}")
    return render_template("db_error.html", error_message=str(e)), 503

VALID_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Healthcare", "Travel", "Entertainment", "Shopping", "Other"]

def validate_expense_form(form_data):
    """Parses and validates expense form inputs.
    Returns a tuple: (amount, category, date_str, description, error_message)
    """
    amount_str = form_data.get("amount", "").strip()
    category = form_data.get("category", "").strip()
    date_str = form_data.get("date", "").strip()
    description = form_data.get("description", "").strip()

    error = None
    amount = None

    if not amount_str:
        error = "Amount is required."
    else:
        try:
            amount = float(amount_str)
            if not math.isfinite(amount) or amount <= 0:
                error = "Amount must be greater than 0."
        except ValueError:
            error = "Amount must be a valid number."

    if not error:
        if not category:
            error = "Category is required."
        elif category not in VALID_CATEGORIES:
            error = "Invalid category selected."

    if not error:
        if not date_str:
            error = "Date is required."
        else:
            try:
                date.fromisoformat(date_str)
            except ValueError:
                error = "Date must be in YYYY-MM-DD format."

    if not error:
        if len(description) > 200:
            error = "Description must not exceed 200 characters."

    return amount, category, date_str, description, error


@app.before_request
def check_demo_expiry():
    path = request.path
    if (path == "/profile" or path.startswith("/expenses")) and not session.get("user_id"):
        if request.cookies.get("was_demo"):
            response = redirect(url_for("landing"))
            response.delete_cookie("was_demo")
            flash("Your demo session has expired.")
            return response

# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/demo")
def demo_login():
    if session.get("user_id") and not session.get("is_demo"):
        return redirect(url_for("profile"))

    cleanup_old_demo_users()
    user_id, user_name = create_demo_user()
    session["user_id"] = user_id
    session["user_name"] = user_name
    session["is_demo"] = True
    flash("Welcome to Outflow in Demo Mode!")
    
    response = redirect(url_for("profile"))
    response.set_cookie("was_demo", "1", max_age=3600)  # expires in 1 hour
    return response


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        if session.get("is_demo"):
            session.clear()
            flash("Create your own Outflow account to start tracking your personal finances.")
        else:
            return redirect(url_for("profile"))
    if request.method == "GET":
        return render_template("register.html")

    # --- POST: process form submission ---
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    def _form_error(message):
        """Re-render the form preserving name and email, but never password."""
        return render_template("register.html", error=message, name=name, email=email)

    # Server-side validation
    if not name or not email or not password or not confirm_password:
        return _form_error("All fields are required.")

    if len(password) < 8:
        return _form_error("Password must be at least 8 characters.")

    if password != confirm_password:
        return _form_error("Passwords do not match.")

    # Hash password and persist
    password_hash = generate_password_hash(password)
    try:
        create_user(name, email, password_hash)
    except psycopg2.IntegrityError:
        return _form_error("An account with that email already exists.")

    flash("Account created! Please sign in.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        if session.get("is_demo"):
            session.clear()
        else:
            return redirect(url_for("profile"))
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    is_demo = session.get("is_demo")
    session.clear()
    if is_demo:
        response = redirect(url_for("landing"))
        response.delete_cookie("was_demo")
        return response
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # Extract query parameters
    preset = request.args.get("preset")
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()

    # Determine preset if not explicitly provided but dates are
    if not preset:
        if start_date_str or end_date_str:
            preset = "custom"
        else:
            preset = "all"

    today = date.today()
    start_date = None
    end_date = None

    if preset == "7d":
        start_date = today - timedelta(days=6)
        end_date = today
    elif preset == "30d":
        start_date = today - timedelta(days=29)
        end_date = today
    elif preset == "this-month":
        start_date = today.replace(day=1)
        _, last_day = calendar.monthrange(today.year, today.month)
        end_date = today.replace(day=last_day)
    elif preset == "custom":
        if start_date_str:
            try:
                start_date = date.fromisoformat(start_date_str)
            except ValueError:
                start_date = None
        if end_date_str:
            try:
                end_date = date.fromisoformat(end_date_str)
            except ValueError:
                end_date = None

    # Convert date objects to ISO string representation for query execution
    start_date_query = start_date.isoformat() if start_date else None
    end_date_query = end_date.isoformat() if end_date else None

    # If preset is custom and both dates are empty, treat as preset = all
    if preset == "custom" and not start_date_query and not end_date_query:
        preset = "all"

    user_info = get_user_by_id(user_id)
    summary_stats = get_summary_stats(user_id, start_date=start_date_query, end_date=end_date_query)
    recent_expenses = get_recent_transactions(user_id, limit=10, start_date=start_date_query, end_date=end_date_query)
    category_breakdown = get_category_breakdown(user_id, start_date=start_date_query, end_date=end_date_query)

    return render_template(
        "profile.html",
        user_info=user_info,
        summary_stats=summary_stats,
        recent_expenses=recent_expenses,
        category_breakdown=category_breakdown,
        preset=preset,
        start_date=start_date_query,
        end_date=end_date_query
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    if request.method == "GET":
        default_date = date.today().isoformat()
        return render_template("add_expense.html", date=default_date)

    # POST method: process submission
    amount, category, date_str, description, error = validate_expense_form(request.form)

    if error:
        return render_template(
            "add_expense.html",
            error=error,
            amount=request.form.get("amount", ""),
            category=category,
            date=date_str,
            description=description
        )

    # Success: Insert and Redirect
    create_expense(user_id, amount, category, date_str, description)
    flash("Expense added successfully!")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if not expense:
        abort(404)

    if expense["user_id"] != user_id:
        abort(403)

    if request.method == "GET":
        return render_template(
            "edit_expense.html",
            expense=expense,
            amount=expense["amount"],
            category=expense["category"],
            date=expense["date"],
            description=expense["description"] or ""
        )

    # POST method: process submission
    amount, category, date_str, description, error = validate_expense_form(request.form)

    if error:
        return render_template(
            "edit_expense.html",
            expense=expense,
            error=error,
            amount=request.form.get("amount", ""),
            category=category,
            date=date_str,
            description=description
        )

    # Success: Update and Redirect
    update_expense(id, amount, category, date_str, description)
    flash("Expense updated successfully!")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if not expense:
        abort(404)

    if expense["user_id"] != user_id:
        abort(403)

    db_delete_expense(id)
    flash("Expense deleted successfully!")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    flask_debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1")
    app.run(debug=flask_debug, port=5001)
