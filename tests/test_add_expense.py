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

def test_add_expense_route_unauthenticated():
    """Unauthenticated GET/POST /expenses/add should redirect to /login."""
    with app.test_client() as client:
        # GET request
        response_get = client.get("/expenses/add")
        assert response_get.status_code == 302
        assert "/login" in response_get.headers["Location"]
        
        # POST request
        response_post = client.post("/expenses/add", data={
            "amount": "50.00",
            "category": "Food",
            "date": str(date.today()),
            "description": "Lunch"
        })
        assert response_post.status_code == 302
        assert "/login" in response_post.headers["Location"]

def test_add_expense_get_authenticated():
    """Authenticated GET /expenses/add should render the form with default date."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        response = client.get("/expenses/add")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        assert "Add New Expense" in html
        assert 'id="amount"' in html
        assert 'id="category"' in html
        # Checks that date input defaults to today's date
        today_str = date.today().isoformat()
        assert f'value="{today_str}"' in html
        
        # Predefined categories should be in the select list
        assert '<option value="Food"' in html
        assert '<option value="Transport"' in html
        assert '<option value="Bills"' in html

def test_add_expense_post_valid_data():
    """Successful POST adds expense to DB and redirects to /profile with success flash."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # Verify initial expense count for demo user (user_id = 1 has 8 seeded expenses)
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = 1")
            initial_count = cur.fetchone()["count"]
        assert initial_count == 8
        conn.close()
        
        # Send valid POST
        response = client.post("/expenses/add", data={
            "amount": "75.50",
            "category": "Shopping",
            "date": "2026-06-20",
            "description": "New shoes"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Should redirect to profile page and show success flash
        assert "Expense added successfully!" in html
        assert "Demo User" in html
        
        # Verify expense exists in DB
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM expenses WHERE user_id = 1 ORDER BY id DESC LIMIT 1")
            new_expense = cur.fetchone()
            assert new_expense is not None
            assert new_expense["amount"] == 75.50
            assert new_expense["category"] == "Shopping"
            assert new_expense["date"] == "2026-06-20"
            assert new_expense["description"] == "New shoes"
            
            # Total count should be 9 now
            cur.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = 1")
            assert cur.fetchone()["count"] == 9
        conn.close()

def test_add_expense_post_validation_errors():
    """POST with invalid inputs should show error banner and preserve correct fields."""
    with app.test_client() as client:
        # Log in
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        })
        
        # 1. Invalid amount: negative
        response1 = client.post("/expenses/add", data={
            "amount": "-50",
            "category": "Food",
            "date": "2026-06-20",
            "description": "Negative expense"
        })
        assert response1.status_code == 200
        html1 = response1.data.decode("utf-8")
        assert "Amount must be greater than 0." in html1
        assert 'value="-50"' in html1  # preserved
        assert 'value="2026-06-20"' in html1  # preserved
        assert 'value="Negative expense"' in html1  # preserved
        
        # 2. Invalid amount: non-numeric
        response2 = client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Food",
            "date": "2026-06-20",
            "description": "Invalid amount"
        })
        assert "Amount must be a valid number." in response2.data.decode("utf-8")
        
        # 3. Missing amount
        response3 = client.post("/expenses/add", data={
            "amount": "",
            "category": "Food",
            "date": "2026-06-20",
            "description": "Missing amount"
        })
        assert "Amount is required." in response3.data.decode("utf-8")
        
        # 4. Invalid category
        response4 = client.post("/expenses/add", data={
            "amount": "25.00",
            "category": "Luxury",
            "date": "2026-06-20",
            "description": "Invalid category"
        })
        assert "Invalid category selected." in response4.data.decode("utf-8")
        
        # 5. Invalid date format
        response5 = client.post("/expenses/add", data={
            "amount": "25.00",
            "category": "Food",
            "date": "2026/06/20",
            "description": "Invalid date format"
        })
        assert "Date must be in YYYY-MM-DD format." in response5.data.decode("utf-8")
        
        # 6. Description too long
        long_desc = "x" * 201
        response6 = client.post("/expenses/add", data={
            "amount": "25.00",
            "category": "Food",
            "date": "2026-06-20",
            "description": long_desc
        })
        assert "Description must not exceed 200 characters." in response6.data.decode("utf-8")

        # 7. NaN amount
        response7 = client.post("/expenses/add", data={
            "amount": "nan",
            "category": "Food",
            "date": "2026-06-20",
            "description": "NaN amount"
        })
        assert "Amount must be greater than 0." in response7.data.decode("utf-8")

        # 8. Infinity amount
        response8 = client.post("/expenses/add", data={
            "amount": "inf",
            "category": "Food",
            "date": "2026-06-20",
            "description": "Infinity amount"
        })
        assert "Amount must be greater than 0." in response8.data.decode("utf-8")
