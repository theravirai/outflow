import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

DB_PATH = "expense_tracker.db"

def get_db():
    """Returns a SQLite connection with row_factory and foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
    conn.close()

def seed_db():
    """Inserts sample data for development."""
    conn = get_db()
    
    # Check if demo user already exists
    cur = conn.execute("SELECT COUNT(*) as count FROM users")
    if cur.fetchone()['count'] > 0:
        conn.close()
        return  # Seed data already exists

    with conn:
        # Insert Demo User
        password_hash = generate_password_hash("demo123")
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash)
        )
        user_id = cur.lastrowid

        # Insert 8 sample expenses spread across the current month
        today = datetime.today().date()
        expenses = [
            (user_id, 150.50, "Food", str(today - timedelta(days=1)), "Groceries at Whole Foods"),
            (user_id, 45.00, "Transport", str(today - timedelta(days=2)), "Gas station"),
            (user_id, 1200.00, "Bills", str(today - timedelta(days=5)), "Monthly Rent"),
            (user_id, 60.00, "Health", str(today - timedelta(days=10)), "Pharmacy run"),
            (user_id, 20.00, "Entertainment", str(today - timedelta(days=12)), "Movie ticket"),
            (user_id, 85.00, "Shopping", str(today - timedelta(days=15)), "New shirt"),
            (user_id, 15.00, "Food", str(today - timedelta(days=18)), "Coffee shop"),
            (user_id, 35.00, "Other", str(today - timedelta(days=20)), "Gift for friend")
        ]

        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses
        )
    conn.close()


def get_user_by_email(email):
    """Returns the users row matching email, or None if not found."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return row


def create_user(name, email, password_hash):
    """Inserts a new user and returns the new row id.

    Raises sqlite3.IntegrityError if the email is already taken.
    """
    conn = get_db()
    with conn:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
    user_id = cur.lastrowid
    conn.close()
    return user_id


def create_expense(user_id, amount, category, date, description):
    """Inserts a new expense into the database and returns the new row ID."""
    conn = get_db()
    with conn:
        cur = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description)
        )
    expense_id = cur.lastrowid
    conn.close()
    return expense_id

