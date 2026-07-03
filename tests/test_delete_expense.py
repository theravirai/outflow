import pytest
import os
from app import app
from database.db import get_db, init_db, seed_db

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a test PostgreSQL database for testing."""
    test_db_url = os.environ.get("DATABASE_URL_TEST")
    if not test_db_url:
        pytest.fail("DATABASE_URL_TEST environment variable is not set. Testing requires a PostgreSQL database.")
    
    monkeypatch.setattr("database.db.DATABASE_URL", test_db_url)
    
    init_db()
    
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE users, expenses RESTART IDENTITY CASCADE;")
    conn.close()
    
    seed_db()
    yield

def test_delete_expense_route_unauthenticated():
    """Unauthenticated POST /expenses/<id>/delete should redirect to /login."""
    with app.test_client() as client:
        response = client.post("/expenses/1/delete")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

def test_delete_expense_nonexistent():
    """Accessing non-existent expense for deletion should return 404."""
    with app.test_client() as client:
        # Log in (user_id = 1)
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        response = client.post("/expenses/9999/delete")
        assert response.status_code == 404

def test_delete_expense_unauthorized():
    """Accessing another user's expense for deletion should return 403."""
    # First, let's create a second user and add an expense for them
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            # Insert User 2
            cur.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                ("User Two", "two@outflow.com", "dummy_hash")
            )
            user_two_id = cur.fetchone()[0]
            # Insert Expense for User 2 (user_id = 2)
            cur.execute(
                "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (user_two_id, 100.0, "Food", "2026-06-25", "Secret Lunch")
            )
            secret_expense_id = cur.fetchone()[0]
    conn.close()

    with app.test_client() as client:
        # Log in as Demo User (user_id = 1)
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # Try to delete User 2's expense
        response = client.post(f"/expenses/{secret_expense_id}/delete")
        assert response.status_code == 403

def test_delete_expense_success():
    """Successful POST /expenses/<id>/delete deletes the expense, redirects to /profile with flash."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # Check initial count and sum of expenses for user_id = 1
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count, SUM(amount) as total FROM expenses WHERE user_id = 1")
            initial_expenses = cur.fetchone()
        conn.close()
        
        # Delete one of the seeded expenses (id = 1)
        response = client.post("/expenses/1/delete", follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Should redirect to profile page and show success flash
        assert "Expense deleted successfully!" in html
        
        # Verify expense is deleted in DB
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM expenses WHERE id = 1")
            deleted_expense = cur.fetchone()
            cur.execute("SELECT COUNT(*) as count, SUM(amount) as total FROM expenses WHERE user_id = 1")
            updated_expenses = cur.fetchone()
        conn.close()
        
        assert deleted_expense is None
        assert updated_expenses["count"] == initial_expenses["count"] - 1
        assert updated_expenses["total"] == initial_expenses["total"] - 150.50  # Seeded expense 1 is 150.50
