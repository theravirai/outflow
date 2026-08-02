import os
import secrets
import psycopg2
from datetime import date, timedelta, datetime
import calendar
import math
from dotenv import load_dotenv
import json
from groq import Groq

# Load environment variables
load_dotenv()

import csv
from io import StringIO
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for, jsonify, Response
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_expense, create_user, convert_demo_user, get_user_by_email, get_expense_by_id, update_expense, delete_expense as db_delete_expense, cleanup_old_demo_users, create_demo_user, IS_TESTING, DatabaseConnectionError, update_user_profile, update_user_password, delete_user_account, create_password_reset_token, get_password_reset_by_token, delete_password_reset_token
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown, get_transaction_count, get_user_credentials
from services.ai_assistant import process_user_input, process_guest_input
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.config["TESTING"] = IS_TESTING
app.config["RATELIMIT_ENABLED"] = not IS_TESTING
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri="memory://",
)

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
        if request.is_json and not token:
            token = request.json.get("csrf_token") if request.json else None
        expected_token = session.get("csrf_token")
        if not expected_token or not token or not secrets.compare_digest(expected_token, token):
            if request.path.startswith("/api/"):
                return jsonify({"success": False, "error": "CSRF token validation failed."}), 400
            abort(400, description="CSRF token validation failed.")

from werkzeug.exceptions import HTTPException

@app.errorhandler(Exception)
def handle_api_error(e):
    if request.path.startswith("/api/"):
        app.logger.error(f"API Error: {e}")
        code = 500
        message = "Internal server error"
        if isinstance(e, HTTPException):
            code = e.code
            message = e.description
        return jsonify({"success": False, "error": message}), code
    # For non-API routes, re-raise or let default handle
    if isinstance(e, HTTPException):
        return e
    return "Internal Server Error", 500

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
# AI Assistant API Routes
# ------------------------------------------------------------------ # AI Assistant Routes
@app.route("/api/assistant", methods=["POST"])
@limiter.limit("20 per minute")
def ai_assistant_chat():
    data = request.json
    if not data or not data.get("text"):
        return jsonify({"success": False, "error": "Missing input text"}), 400
        
    user_id = session.get("user_id")
    history = data.get("history", [])
    
    if not user_id:
        response = process_guest_input(data["text"], history)
    else:
        response = process_user_input(data["text"], user_id, history)
    return jsonify(response)

@app.route("/api/assistant/transcribe", methods=["POST"])
@limiter.limit("20 per minute")
def ai_assistant_transcribe():
    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        return jsonify({"success": False, "error": "API key not configured"}), 500

    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        audio_content = audio_file.read()
        transcription = client.audio.transcriptions.create(
            file=("assistant.webm", audio_content),
            model="whisper-large-v3",
            prompt="Specify the question, navigation request, or expense details.",
            response_format="json"
        )
        return jsonify({"success": True, "text": transcription.text})
    except Exception as e:
        app.logger.error(f"Transcription Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
@limiter.limit("5 per minute")
def register():
    if session.get("user_id"):
        if not session.get("is_demo"):
            return redirect(url_for("profile"))
        elif request.method == "GET":
            flash("Create an account to save your demo transactions and continue tracking.")

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
        if session.get("is_demo") and session.get("user_id"):
            convert_demo_user(session["user_id"], name, email, password_hash)
            session.pop("is_demo", None)
            session["user_name"] = name
            flash("Account created! Your demo transactions have been saved.")
            return redirect(url_for("profile"))
        else:
            create_user(name, email, password_hash)
            flash("Account created! Please sign in.")
            return redirect(url_for("login"))
    except psycopg2.IntegrityError:
        return _form_error("An account with that email already exists.")


@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
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


@app.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html")
        
    email = request.form.get("email", "").strip()
    user = get_user_by_email(email)
    
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=1)
        create_password_reset_token(user["id"], token, expires_at)
        
        reset_url = url_for("reset_password", token=token, _external=True)
        # Mock sending email (in a real app, use smtplib or an email service here)
        app.logger.info(f"PASSWORD RESET LINK FOR {email}: {reset_url}")
        
    # Always show same message to prevent email enumeration
    flash("If an account exists with that email, a password reset link has been sent.")
    return redirect(url_for("login"))

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    reset_record = get_password_reset_by_token(token)
    
    if not reset_record or reset_record["expires_at"] < datetime.now():
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("forgot_password"))
        
    if request.method == "GET":
        return render_template("reset_password.html", token=token)
        
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    if len(password) < 8:
        return render_template("reset_password.html", token=token, error="Password must be at least 8 characters.")
        
    if password != confirm_password:
        return render_template("reset_password.html", token=token, error="Passwords do not match.")
        
    update_user_password(reset_record["user_id"], generate_password_hash(password))
    delete_password_reset_token(token)
    
    flash("Your password has been successfully reset. Please log in.", "success")
    return redirect(url_for("login"))

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


# ------------------------------------------------------------------ #
# Placeholder routes#
# ------------------------------------------------------------------ #
# Settings Routes
# ------------------------------------------------------------------ #

@app.route("/settings", methods=["GET"])
def settings():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    user_info = get_user_by_id(user_id)
    return render_template("settings.html", user_info=user_info)

@app.route("/settings/profile", methods=["POST"])
def update_profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    
    if not name or not email:
        flash("Name and email are required.", "error")
        return redirect(url_for("settings"))
        
    try:
        update_user_profile(user_id, name, email)
        flash("Profile updated successfully.", "success")
        session["user_name"] = name
    except psycopg2.IntegrityError:
        flash("That email is already in use by another account.", "error")
        
    return redirect(url_for("settings"))

@app.route("/settings/password", methods=["POST"])
def update_password():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
        
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    
    if new_password != confirm_password:
        flash("New passwords do not match.", "error")
        return redirect(url_for("settings"))
        
    if len(new_password) < 8:
        flash("New password must be at least 8 characters.", "error")
        return redirect(url_for("settings"))
        
    password_hash = get_user_credentials(user_id)
    if not password_hash or not check_password_hash(password_hash, current_password):
        flash("Incorrect current password.", "error")
        return redirect(url_for("settings"))
        
    update_user_password(user_id, generate_password_hash(new_password))
    flash("Password updated successfully.", "success")
    return redirect(url_for("settings"))

@app.route("/settings/delete", methods=["POST"])
def delete_account():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
        
    delete_user_account(user_id)
    session.clear()
    return redirect(url_for("landing"))

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

    # Pagination
    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Category Filter
    category = request.args.get("category")
    if category == "all":
        category = None

    # Search Query
    search_query = request.args.get("q", "").strip()

    user_info = get_user_by_id(user_id)
    summary_stats = get_summary_stats(user_id, start_date=start_date_query, end_date=end_date_query, search_query=search_query)
    
    total_transactions = get_transaction_count(user_id, start_date=start_date_query, end_date=end_date_query, category=category, search_query=search_query)
    total_pages = (total_transactions + per_page - 1) // per_page
    if total_pages == 0:
        total_pages = 1
        
    recent_expenses = get_recent_transactions(user_id, limit=per_page, offset=offset, start_date=start_date_query, end_date=end_date_query, category=category, search_query=search_query)
    category_breakdown = get_category_breakdown(user_id, start_date=start_date_query, end_date=end_date_query, search_query=search_query)

    # Generate pagination pages (1 2 3 ... 15 16 17)
    def get_pagination_pages(current, total):
        if total <= 7:
            return list(range(1, total + 1))
        pages = set([1, total, current, current - 1, current + 1])
        pages = sorted([p for p in pages if 1 <= p <= total])
        result = []
        prev = 0
        for p in pages:
            if p - prev > 1:
                result.append(None)
            result.append(p)
            prev = p
        return result
        
    pagination_pages = get_pagination_pages(page, total_pages)

    return render_template(
        "profile.html",
        user_info=user_info,
        summary_stats=summary_stats,
        recent_expenses=recent_expenses,
        category_breakdown=category_breakdown,
        preset=preset,
        start_date=start_date_query,
        end_date=end_date_query,
        page=page,
        total_pages=total_pages,
        pagination_pages=pagination_pages,
        category=category or "all",
        search_query=search_query
    )


def validate_ai_expense_data(data):
    try:
        amount = float(data.get("amount", 0))
        if amount <= 0:
            return False, "Amount must be greater than zero."
        category = str(data.get("category", ""))
        if category not in VALID_CATEGORIES:
            return False, "Invalid category provided."
        return True, ""
    except Exception:
        return False, "Failed to parse required fields."

@app.route("/api/magic-add", methods=["POST"])
def magic_add():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or not data.get("text"):
        return jsonify({"success": False, "error": "No text provided"}), 400

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        return jsonify({"success": False, "error": "Groq API key not configured"}), 500

    try:
        client = Groq(api_key=groq_api_key)
        today_date = date.today().isoformat()
        
        system_prompt = f"""
You are an expert expense parser for a fintech app. 
Extract the details from the user's input into JSON.
Return ONLY valid JSON. Do not include markdown formatting or explanations.

JSON Schema:
{{
  "amount": float (the cost, strictly a number),
  "category": string (MUST be one of: Food, Transport, Bills, Health, Healthcare, Travel, Entertainment, Shopping, Other),
  "date": string (YYYY-MM-DD),
  "description": string (short summary of what the expense was)
}}

Rules:
1. Today's date is {today_date}.
2. If the user says "yesterday", use the date before today.
3. If the user mentions no date at all, you MUST default to {today_date}.
4. The description MUST be a concise 1-3 word summary (e.g., "Coffee", "Groceries", "Movie tickets"). DO NOT copy the user's entire sentence.
"""
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data.get("text")}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result_json = json.loads(response.choices[0].message.content)
        valid, err_msg = validate_ai_expense_data(result_json)
        if not valid:
            return jsonify({"success": False, "error": err_msg}), 400
        return jsonify({"success": True, "data": result_json})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/magic-voice", methods=["POST"])
def magic_voice():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if "audio" not in request.files:
        return jsonify({"success": False, "error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        return jsonify({"success": False, "error": "API key not configured"}), 500

    try:
        client = Groq(api_key=groq_api_key)
        
        # 1. Transcribe audio
        audio_content = audio_file.read()
        transcription = client.audio.transcriptions.create(
            file=("expense.webm", audio_content),
            model="whisper-large-v3",
            prompt="Specify the amount, category, date, and description of the expense.",
            response_format="json"
        )
        
        transcript_text = transcription.text
        if not transcript_text.strip():
            return jsonify({"success": False, "error": "Could not understand audio. Please try again."}), 400
            
        # 2. Parse text to JSON
        today_date = date.today().isoformat()
        system_prompt = f"""
You are an expert expense parser for a fintech app. 
Extract the details from the user's input into JSON.
Return ONLY valid JSON. Do not include markdown formatting or explanations.

JSON Schema:
{{
  "amount": float (the cost, strictly a number),
  "category": string (MUST be one of: Food, Transport, Bills, Health, Healthcare, Travel, Entertainment, Shopping, Other),
  "date": string (YYYY-MM-DD),
  "description": string (short summary of what the expense was)
}}

Rules:
1. Today's date is {today_date}.
2. If the user says "yesterday", use the date before today.
3. If the user mentions no date at all, you MUST default to {today_date}.
4. The description MUST be a concise 1-3 word summary (e.g., "Coffee", "Groceries", "Movie tickets"). DO NOT copy the user's entire sentence.
"""
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": transcript_text}
            ],
            model="llama-3.1-8b-instant",
            response_format={"type": "json_object"},
            temperature=0
        )
        
        result_json = json.loads(response.choices[0].message.content)
        valid, err_msg = validate_ai_expense_data(result_json)
        if not valid:
            return jsonify({"success": False, "error": err_msg}), 400
            
        result_json["transcript"] = transcript_text
        return jsonify({"success": True, "data": result_json})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


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

@app.route("/expenses/export")
def export_expenses():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
        
    # Re-use the existing filters from the query string
    start_date_str = request.args.get("start_date", "").strip()
    end_date_str = request.args.get("end_date", "").strip()
    category = request.args.get("category")
    if category == "all":
        category = None
    search_query = request.args.get("q", "").strip()
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = date.fromisoformat(start_date_str).isoformat()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = date.fromisoformat(end_date_str).isoformat()
        except ValueError:
            pass

    # Get ALL matching expenses by passing limit=None
    expenses = get_recent_transactions(
        user_id, 
        limit=None, 
        start_date=start_date, 
        end_date=end_date, 
        category=category, 
        search_query=search_query
    )
    
    # Generate CSV
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["Date", "Description", "Category", "Amount"])
    
    for expense in expenses:
        writer.writerow([
            expense["date"],
            expense["description"],
            expense["category"],
            f"{expense['amount']:.2f}"
        ])
        
    output = si.getvalue()
    
    filename = "outflow_expenses.csv"
    if start_date and end_date:
        filename = f"outflow_expenses_{start_date}_to_{end_date}.csv"
        
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    flask_debug = os.environ.get("FLASK_DEBUG", "false").lower() in ("true", "1")
    app.run(debug=flask_debug, port=5001)
