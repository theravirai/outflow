import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
import uuid
import secrets
import logging
import time
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash

import sys
# Load environment variables from .env
load_dotenv()

IS_TESTING = "pytest" in sys.modules

if IS_TESTING:
    DATABASE_URL = os.environ.get("DATABASE_URL_TEST")
else:
    DATABASE_URL = os.environ.get("DATABASE_URL")


_LAST_CLEANUP_TIME = 0
_DB_INITIALIZED = False

class DatabaseConnectionError(Exception):
    """Raised when the database connection fails to establish or initialize."""
    pass

def _init_db_internal(conn):
    """Creates all tables using CREATE TABLE IF NOT EXISTS using the provided connection."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

def _seed_db_internal(conn):
    """Inserts sample data for development using the provided connection."""
    with conn.cursor() as cur:
        # Check if demo user already exists
        cur.execute("SELECT COUNT(*) as count FROM users")
        if cur.fetchone()['count'] > 0:
            return  # Seed data already exists

        # Insert Demo User
        password_hash = generate_password_hash("demo123")
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
            ("Demo User", "demo@outflow.com", password_hash)
        )
        user_id = cur.fetchone()[0]

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

        cur.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)",
            expenses
        )

def get_db():
    """Returns a native PostgreSQL connection with DictCursor."""
    global _DB_INITIALIZED
    
    if not DATABASE_URL:
        logging.error("DATABASE_URL environment variable is not set.")
        raise DatabaseConnectionError(
            "Unable to connect to the database. Please check the database configuration and try again."
        )
        
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=DictCursor)
    except psycopg2.Error as e:
        logging.exception("Database connection failed.")
        raise DatabaseConnectionError(
            "Unable to connect to the database. Please check the database configuration and try again."
        ) from e
        
    if not _DB_INITIALIZED:
        _DB_INITIALIZED = True
        try:
            with conn:
                _init_db_internal(conn)
                _seed_db_internal(conn)
        except Exception as e:
            _DB_INITIALIZED = False  # Reset so we try initializing next time
            conn.close()
            logging.exception("Database initialization failed.")
            raise DatabaseConnectionError(
                "Unable to connect to the database. Please check the database configuration and try again."
            ) from e
            
    return conn

def init_db():
    """Creates all tables using CREATE TABLE IF NOT EXISTS."""
    conn = get_db()
    try:
        with conn:
            _init_db_internal(conn)
    finally:
        conn.close()

def seed_db():
    """Inserts sample data for development."""
    conn = get_db()
    try:
        with conn:
            _seed_db_internal(conn)
    finally:
        conn.close()


def get_user_by_email(email):
    """Returns the users row matching email, or None if not found."""
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
    conn.close()
    return row


def create_user(name, email, password_hash):
    """Inserts a new user and returns the new row id.

    Raises psycopg2.IntegrityError if the email is already taken.
    """
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (name, email, password_hash),
                )
                user_id = cur.fetchone()[0]
        return user_id
    finally:
        conn.close()


def create_expense(user_id, amount, category, date, description):
    """Inserts a new expense into the database and returns the new row ID."""
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (user_id, amount, category, date, description)
                )
                expense_id = cur.fetchone()[0]
        return expense_id
    finally:
        conn.close()


def get_expense_by_id(expense_id):
    """Retrieves an expense row matching the given expense_id.

    Returns the DictRow object or None if not found.
    """
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
        row = cur.fetchone()
    conn.close()
    return row


def update_expense(expense_id, amount, category, date, description):
    """Updates the details of the specified expense."""
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE expenses SET amount = %s, category = %s, date = %s, description = %s WHERE id = %s",
                    (amount, category, date, description, expense_id)
                )
    finally:
        conn.close()


def delete_expense(expense_id):
    """Deletes the specified expense from the database."""
    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
    finally:
        conn.close()


def cleanup_old_demo_users():
    """Deletes temporary demo users and their expenses that are older than 24 hours."""
    global _LAST_CLEANUP_TIME
    now = time.time()
    if now - _LAST_CLEANUP_TIME < 3600:  # Only cleanup once per hour at most
        return
    _LAST_CLEANUP_TIME = now

    conn = get_db()
    try:
        with conn:
            with conn.cursor() as cur:
                # Select demo users created more than 24 hours ago
                cur.execute(
                    "SELECT id FROM users WHERE email LIKE 'demo_session_%%' AND created_at < NOW() - INTERVAL '1 day'"
                )
                rows = cur.fetchall()
                user_ids = [row["id"] for row in rows]
                if user_ids:
                    # Delete their expenses first to satisfy foreign key constraints
                    placeholders = ",".join("%s" for _ in user_ids)
                    cur.execute(f"DELETE FROM expenses WHERE user_id IN ({placeholders})", user_ids)
                    # Delete the users
                    cur.execute(f"DELETE FROM users WHERE id IN ({placeholders})", user_ids)
    except Exception as e:
        logging.exception("Error during cleanup of old demo users")
    finally:
        conn.close()


def create_demo_user():
    """Creates a temporary demo user and populates it with 90 days of realistic expense data."""
    conn = get_db()
    try:
        uid = uuid.uuid4().hex
        email = f"demo_session_{uid}@outflow.com"
        name = "Demo Mode"
        # Cryptographically secure random password hash
        password_hash = generate_password_hash(secrets.token_hex(16))
        
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                    (name, email, password_hash)
                )
                user_id = cur.fetchone()[0]
                
                # Seed realistic relative expenses
                today = date.today()
                expenses = [
                    # Bills
                    (user_id, 850.00, "Bills", str(today - timedelta(days=5)), "Monthly Rent Payment"),
                    (user_id, 120.00, "Bills", str(today - timedelta(days=6)), "Electricity & Gas Bill"),
                    (user_id, 39.99, "Bills", str(today - timedelta(days=10)), "Fiber Internet Subscription"),
                    (user_id, 850.00, "Bills", str(today - timedelta(days=35)), "Monthly Rent Payment"),
                    (user_id, 115.00, "Bills", str(today - timedelta(days=36)), "Electricity & Gas Bill"),
                    (user_id, 39.99, "Bills", str(today - timedelta(days=40)), "Fiber Internet Subscription"),
                    (user_id, 850.00, "Bills", str(today - timedelta(days=65)), "Monthly Rent Payment"),
                    (user_id, 125.00, "Bills", str(today - timedelta(days=66)), "Electricity & Gas Bill"),
                    (user_id, 39.99, "Bills", str(today - timedelta(days=70)), "Fiber Internet Subscription"),
                    
                    # Food - Groceries
                    (user_id, 74.50, "Food", str(today - timedelta(days=1)), "Groceries at Lidl"),
                    (user_id, 52.10, "Food", str(today - timedelta(days=4)), "Weekly groceries"),
                    (user_id, 82.30, "Food", str(today - timedelta(days=8)), "Lidl Supermarket"),
                    (user_id, 64.80, "Food", str(today - timedelta(days=12)), "Fresh vegetables and fruit"),
                    (user_id, 91.20, "Food", str(today - timedelta(days=18)), "Weekly food shopping"),
                    (user_id, 55.00, "Food", str(today - timedelta(days=22)), "Lidl"),
                    (user_id, 78.50, "Food", str(today - timedelta(days=29)), "Weekly groceries"),
                    (user_id, 83.40, "Food", str(today - timedelta(days=45)), "Food shopping"),
                    (user_id, 79.00, "Food", str(today - timedelta(days=60)), "Groceries"),
                    
                    # Food - Dining out & Coffee
                    (user_id, 15.50, "Food", str(today - timedelta(days=2)), "Coffee & pastry"),
                    (user_id, 45.00, "Food", str(today - timedelta(days=7)), "Dinner with colleagues"),
                    (user_id, 28.00, "Food", str(today - timedelta(days=14)), "Sushi delivery"),
                    (user_id, 12.00, "Food", str(today - timedelta(days=25)), "Lunch box"),
                    (user_id, 42.50, "Food", str(today - timedelta(days=38)), "Italian restaurant"),
                    
                    # Transport
                    (user_id, 49.00, "Transport", str(today - timedelta(days=3)), "Monthly Public Transport Pass"),
                    (user_id, 22.50, "Transport", str(today - timedelta(days=9)), "Uber ride home"),
                    (user_id, 18.00, "Transport", str(today - timedelta(days=21)), "Taxi ride"),
                    (user_id, 49.00, "Transport", str(today - timedelta(days=33)), "Monthly Public Transport Pass"),
                    (user_id, 25.00, "Transport", str(today - timedelta(days=50)), "Train ticket"),
                    (user_id, 49.00, "Transport", str(today - timedelta(days=63)), "Monthly Public Transport Pass"),
                    
                    # Shopping
                    (user_id, 110.00, "Shopping", str(today - timedelta(days=12)), "Winter jacket"),
                    (user_id, 89.99, "Shopping", str(today - timedelta(days=19)), "Mechanical Keyboard"),
                    (user_id, 45.00, "Shopping", str(today - timedelta(days=42)), "Sneakers sale"),
                    (user_id, 24.50, "Shopping", str(today - timedelta(days=55)), "Novel books"),
                    
                    # Entertainment
                    (user_id, 24.00, "Entertainment", str(today - timedelta(days=2)), "Movie tickets for two"),
                    (user_id, 15.99, "Entertainment", str(today - timedelta(days=15)), "Netflix subscription"),
                    (user_id, 65.00, "Entertainment", str(today - timedelta(days=28)), "Live music concert ticket"),
                    (user_id, 24.00, "Entertainment", str(today - timedelta(days=32)), "Movie tickets"),
                    (user_id, 15.99, "Entertainment", str(today - timedelta(days=45)), "Netflix subscription"),
                    (user_id, 15.99, "Entertainment", str(today - timedelta(days=75)), "Netflix subscription"),
                    
                    # Healthcare
                    (user_id, 24.50, "Healthcare", str(today - timedelta(days=8)), "Cold medicine & vitamins"),
                    (user_id, 18.20, "Healthcare", str(today - timedelta(days=37)), "First aid kit"),
                    (user_id, 75.00, "Healthcare", str(today - timedelta(days=48)), "Dental checkup"),
                    
                    # Travel
                    (user_id, 180.00, "Travel", str(today - timedelta(days=22)), "Flight ticket to Amsterdam"),
                    (user_id, 140.00, "Travel", str(today - timedelta(days=21)), "Hotel stay in Amsterdam"),
                    (user_id, 65.00, "Food", str(today - timedelta(days=21)), "Traditional dinner in Amsterdam"),
                    
                    # Other
                    (user_id, 35.00, "Other", str(today - timedelta(days=15)), "Birthday gift for friend"),
                    (user_id, 40.00, "Other", str(today - timedelta(days=72)), "Housewarming gift")
                ]
                
                cur.executemany(
                    "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)",
                    expenses
                )
        return user_id, name
    finally:
        conn.close()
