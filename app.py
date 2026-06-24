import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_user, get_user_by_email, init_db, seed_db

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
    if not session.get("user_id"):
        return redirect(url_for("login"))

    # Hardcoded data for Step 4 profile design isolation
    user_info = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "member_since": "June 2026",
        "initials": "JD"
    }

    summary_stats = {
        "total_spent": 1240.00,
        "transaction_count": 15,
        "top_category": "Food"
    }

    recent_expenses = [
        {"date": "2026-06-24", "description": "Weekly Grocery Shopping", "category": "Food", "amount": 85.50},
        {"date": "2026-06-23", "description": "Monthly Train Pass", "category": "Transport", "amount": 49.00},
        {"date": "2026-06-20", "description": "Electricity Bill", "category": "Utilities", "amount": 112.00},
        {"date": "2026-06-18", "description": "Dinner with friends", "category": "Food", "amount": 64.20},
        {"date": "2026-06-15", "description": "New Wireless Headphones", "category": "Shopping", "amount": 129.99}
    ]

    category_breakdown = [
        {"category": "Food", "amount": 350.20, "percentage": 28, "class": "food"},
        {"category": "Utilities", "amount": 450.00, "percentage": 36, "class": "utilities"},
        {"category": "Shopping", "amount": 329.99, "percentage": 27, "class": "shopping"},
        {"category": "Transport", "amount": 109.81, "percentage": 9, "class": "transport"}
    ]

    return render_template(
        "profile.html",
        user_info=user_info,
        summary_stats=summary_stats,
        recent_expenses=recent_expenses,
        category_breakdown=category_breakdown
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
