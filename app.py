import sqlite3
from datetime import date, timedelta
import calendar
import math

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_expense, create_user, get_user_by_email, init_db, seed_db
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown

app = Flask(__name__)
app.secret_key = "dev-secret-change-in-prod"

with app.app_context():
    init_db()
    seed_db()

# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    # if session.get("user_id"):
    #     return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
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
    except sqlite3.IntegrityError:
        return _form_error("An account with that email already exists.")

    flash("Account created! Please sign in.")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
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
    session.clear()
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
    amount_str = request.form.get("amount", "").strip()
    category = request.form.get("category", "").strip()
    date_str = request.form.get("date", "").strip()
    description = request.form.get("description", "").strip()

    # Validation checks
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

    valid_categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
    if not error:
        if not category:
            error = "Category is required."
        elif category not in valid_categories:
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

    if error:
        return render_template(
            "add_expense.html",
            error=error,
            amount=amount_str,
            category=category,
            date=date_str,
            description=description
        )

    # Success: Insert and Redirect
    create_expense(user_id, amount, category, date_str, description)
    flash("Expense added successfully!")
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
