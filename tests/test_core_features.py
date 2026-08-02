import pytest
import os
import csv
from io import StringIO
from app import app, limiter
from database.db import get_db, init_db, seed_db, create_user, create_expense
from werkzeug.security import generate_password_hash

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a test PostgreSQL database for testing."""
    test_db_url = os.environ.get("DATABASE_URL_TEST")
    if not test_db_url:
        pytest.fail("DATABASE_URL_TEST environment variable is not set.")
    
    monkeypatch.setattr("database.db.DATABASE_URL", test_db_url)
    limiter.enabled = False
    
    init_db()
    
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE users, expenses, password_resets RESTART IDENTITY CASCADE;")
    conn.close()
    
    # Create test user
    create_user("Test User", "test@outflow.com", generate_password_hash("password123"))
    
    # Create test expenses
    create_expense(1, 150.0, "Food", "2023-10-01", "Groceries at Walmart")
    create_expense(1, 50.0, "Transport", "2023-10-02", "Uber to airport")
    create_expense(1, 1000.0, "Bills", "2023-10-03", "Monthly rent")
    
    yield
    limiter.enabled = True

@pytest.fixture
def auth_client():
    client = app.test_client()
    client.post("/login", data={
        "email": "test@outflow.com",
        "password": "password123"
    }, follow_redirects=True)
    return client

def test_search_expenses_in_profile(auth_client):
    """Test that the search query filters transactions on the profile page."""
    # Search for 'Walmart'
    response = auth_client.get("/profile?q=Walmart")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    
    assert "Groceries at Walmart" in html
    assert "Uber to airport" not in html
    assert "Monthly rent" not in html
    
    # Search for 'rent'
    response2 = auth_client.get("/profile?q=rent")
    html2 = response2.data.decode("utf-8")
    assert "Monthly rent" in html2
    assert "Walmart" not in html2

def test_export_expenses_csv(auth_client):
    """Test that the CSV export endpoint returns all transactions as a CSV."""
    response = auth_client.get("/expenses/export")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/csv; charset=utf-8"
    assert "attachment; filename=outflow_expenses.csv" in response.headers["Content-Disposition"]
    
    csv_data = response.data.decode("utf-8")
    reader = csv.reader(StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 4 # Header + 3 expenses
    assert rows[0] == ["Date", "Description", "Category", "Amount"]
    
    # Check that expenses are present (order is date desc, so rent is first)
    assert rows[1] == ["2023-10-03", "Monthly rent", "Bills", "1000.00"]
    assert rows[2] == ["2023-10-02", "Uber to airport", "Transport", "50.00"]
    assert rows[3] == ["2023-10-01", "Groceries at Walmart", "Food", "150.00"]

def test_export_expenses_csv_with_search(auth_client):
    """Test that the CSV export respects the search filter."""
    response = auth_client.get("/expenses/export?q=Uber")
    assert response.status_code == 200
    
    csv_data = response.data.decode("utf-8")
    reader = csv.reader(StringIO(csv_data))
    rows = list(reader)
    
    assert len(rows) == 2 # Header + 1 expense
    assert rows[1] == ["2023-10-02", "Uber to airport", "Transport", "50.00"]
