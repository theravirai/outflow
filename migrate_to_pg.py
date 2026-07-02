import os
import sys
import sqlite3
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SQLITE_DB = "expense_tracker.db"
DATABASE_URL = os.environ.get("DATABASE_URL")

def migrate():
    if not DATABASE_URL:
        print("Error: DATABASE_URL environment variable is not set.", file=sys.stderr)
        print("Please check your .env file or configuration.", file=sys.stderr)
        sys.exit(1)
        
    if not os.path.exists(SQLITE_DB):
        print(f"No SQLite database found at '{SQLITE_DB}'. Nothing to migrate.", file=sys.stderr)
        sys.exit(0)

    print(f"Connecting to SQLite database at '{SQLITE_DB}'...")
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cur = sqlite_conn.cursor()

    print("Connecting to PostgreSQL database...")
    try:
        pg_conn = psycopg2.connect(DATABASE_URL)
        pg_cur = pg_conn.cursor()
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}", file=sys.stderr)
        sqlite_conn.close()
        sys.exit(1)

    print("Ensuring target database tables exist...")
    # Import init_db from our module to reuse the same schema DDL
    from database.db import init_db
    init_db()

    try:
        with pg_conn:
            # 1. Migrate Users
            print("Reading users from SQLite...")
            sqlite_cur.execute("SELECT id, name, email, password_hash, created_at FROM users")
            users = sqlite_cur.fetchall()
            
            if users:
                print(f"Migrating {len(users)} users to PostgreSQL...")
                # We use ON CONFLICT DO NOTHING to avoid duplicate keys if seed/runs exist
                pg_cur.executemany(
                    """
                    INSERT INTO users (id, name, email, password_hash, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (email) DO NOTHING
                    """,
                    users
                )
                
                # Sync users serial primary key sequence
                pg_cur.execute("SELECT MAX(id) FROM users")
                max_user_id = pg_cur.fetchone()[0]
                if max_user_id:
                    pg_cur.execute("SELECT setval('users_id_seq', %s)", (max_user_id,))
                    print(f"User ID sequence reset to {max_user_id}")
            else:
                print("No users found to migrate.")

            # 2. Migrate Expenses
            print("Reading expenses from SQLite...")
            sqlite_cur.execute("SELECT id, user_id, amount, category, date, description, created_at FROM expenses")
            expenses = sqlite_cur.fetchall()
            
            if expenses:
                print(f"Migrating {len(expenses)} expenses to PostgreSQL...")
                pg_cur.executemany(
                    """
                    INSERT INTO expenses (id, user_id, amount, category, date, description, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    expenses
                )
                
                # Sync expenses serial primary key sequence
                pg_cur.execute("SELECT MAX(id) FROM expenses")
                max_expense_id = pg_cur.fetchone()[0]
                if max_expense_id:
                    pg_cur.execute("SELECT setval('expenses_id_seq', %s)", (max_expense_id,))
                    print(f"Expense ID sequence reset to {max_expense_id}")
            else:
                print("No expenses found to migrate.")

        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration failed due to an error: {e}", file=sys.stderr)
        pg_conn.rollback()
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()
