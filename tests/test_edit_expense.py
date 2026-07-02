import pytest
import os
from datetime import date
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

def test_edit_expense_route_unauthenticated():
    """Unauthenticated GET/POST /expenses/<id>/edit should redirect to /login."""
    with app.test_client() as client:
        # GET request
        response_get = client.get("/expenses/1/edit")
        assert response_get.status_code == 302
        assert "/login" in response_get.headers["Location"]
        
        # POST request
        response_post = client.post("/expenses/1/edit", data={
            "amount": "50.00",
            "category": "Food",
            "date": str(date.today()),
            "description": "Lunch"
        })
        assert response_post.status_code == 302
        assert "/login" in response_post.headers["Location"]

def test_edit_expense_nonexistent():
    """Accessing non-existent expense should return 404."""
    with app.test_client() as client:
        # Log in (user_id = 1)
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        response = client.get("/expenses/9999/edit")
        assert response.status_code == 404

def test_edit_expense_unauthorized():
    """Accessing another user's expense should return 403."""
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
        
        # Try to view User 2's expense
        response_get = client.get(f"/expenses/{secret_expense_id}/edit")
        assert response_get.status_code == 403

        # Try to edit User 2's expense
        response_post = client.post(f"/expenses/{secret_expense_id}/edit", data={
            "amount": "150.00",
            "category": "Food",
            "date": "2026-06-25",
            "description": "Hacked Lunch"
        })
        assert response_post.status_code == 403

def test_edit_expense_get_authenticated():
    """Authenticated GET /expenses/<id>/edit should pre-populate the form with current values."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # Get one of the seeded expenses (id = 1)
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM expenses WHERE id = %s", (1,))
            expense = cur.fetchone()
        conn.close()
        
        response = client.get("/expenses/1/edit")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        assert "Edit Expense" in html
        assert f'value="{expense["amount"]}"' in html
        assert f'value="{expense["date"]}"' in html
        assert f'value="{expense["description"]}"' in html
        assert f'<option value="{expense["category"]}" selected>' in html

def test_edit_expense_post_valid_data():
    """Successful POST updates expense in DB and redirects to /profile with success flash."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # Send valid POST to edit expense 1
        response = client.post("/expenses/1/edit", data={
            "amount": "99.99",
            "category": "Entertainment",
            "date": "2026-06-24",
            "description": "Updated movie tickets"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Should redirect to profile page and show success flash
        assert "Expense updated successfully!" in html
        
        # Verify expense is updated in DB
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM expenses WHERE id = 1")
            updated_expense = cur.fetchone()
        conn.close()
        
        assert updated_expense is not None
        assert updated_expense["amount"] == 99.99
        assert updated_expense["category"] == "Entertainment"
        assert updated_expense["date"] == "2026-06-24"
        assert updated_expense["description"] == "Updated movie tickets"

def test_edit_expense_post_validation_errors():
    """POST with invalid inputs should show error banner and preserve correct fields."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # 1. Invalid amount: negative
        response1 = client.post("/expenses/1/edit", data={
            "amount": "-20",
            "category": "Food",
            "date": "2026-06-24",
            "description": "Negative edit"
        })
        assert response1.status_code == 200
        html1 = response1.data.decode("utf-8")
        assert "Amount must be greater than 0." in html1
        assert 'value="-20"' in html1
        
        # 2. Invalid category
        response2 = client.post("/expenses/1/edit", data={
            "amount": "15.00",
            "category": "Luxury",
            "date": "2026-06-24",
            "description": "Invalid category edit"
        })
        assert "Invalid category selected." in response2.data.decode("utf-8")
        
        # 3. Invalid date format
        response3 = client.post("/expenses/1/edit", data={
            "amount": "15.00",
            "category": "Food",
            "date": "2026/06/24",
            "description": "Invalid date edit"
        })
        assert "Date must be in YYYY-MM-DD format." in response3.data.decode("utf-8")
        
        # 4. Description too long
        long_desc = "y" * 201
        response4 = client.post("/expenses/1/edit", data={
            "amount": "15.00",
            "category": "Food",
            "date": "2026-06-24",
            "description": long_desc
        })
        assert "Description must not exceed 200 characters." in response4.data.decode("utf-8")
