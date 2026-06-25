import pytest
from datetime import date
from app import app
from database.db import get_db, init_db, seed_db, create_expense

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Sets up a temporary SQLite database for testing and overrides the database path."""
    db_file = tmp_path / "test_expense_tracker_07.db"
    
    # Override the DB_PATH in the database module
    monkeypatch.setattr("database.db.DB_PATH", str(db_file))
    
    # Initialize and seed database
    init_db()
    seed_db()
    
    yield
    # Temp file is automatically cleaned up

# ------------------------------------------------------------------ #
# Authorization Guards
# ------------------------------------------------------------------ #

def test_get_add_expense_unauthenticated():
    """Requirement: GET /expenses/add blocks unauthenticated users and redirects to login."""
    with app.test_client() as client:
        response = client.get("/expenses/add")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

def test_post_add_expense_unauthenticated():
    """Requirement: POST /expenses/add blocks unauthenticated users and redirects to login."""
    with app.test_client() as client:
        response = client.post("/expenses/add", data={
            "amount": "50.00",
            "category": "Food",
            "date": str(date.today()),
            "description": "Lunch"
        })
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
        
        # Verify no expense was inserted into the database
        conn = get_db()
        cursor = conn.execute("SELECT COUNT(*) as count FROM expenses")
        count = cursor.fetchone()["count"]
        # Default seeded expenses is 8
        assert count == 8
        conn.close()

# ------------------------------------------------------------------ #
# GET Request & Form Rendering Requirements
# ------------------------------------------------------------------ #

def test_get_add_expense_authenticated():
    """Requirement: Authenticated users can access GET /expenses/add and see the form."""
    with app.test_client() as client:
        # Log in first
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        response = client.get("/expenses/add")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        assert "Add" in html or "Expense" in html
        assert 'name="amount"' in html or 'id="amount"' in html
        assert 'name="category"' in html or 'id="category"' in html
        assert 'name="date"' in html or 'id="date"' in html
        assert 'name="description"' in html or 'id="description"' in html

def test_add_expense_date_defaults_to_today():
    """Requirement: The date field defaults to today's date in YYYY-MM-DD format on GET."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        response = client.get("/expenses/add")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        today_str = date.today().isoformat()
        assert f'value="{today_str}"' in html

def test_add_expense_contains_predefined_categories():
    """Requirement: Category dropdown options include all predefined categories."""
    valid_categories = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        response = client.get("/expenses/add")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        for category in valid_categories:
            assert f'value="{category}"' in html or f'>{category}</option>' in html

# ------------------------------------------------------------------ #
# POST Request & Validation Requirements
# ------------------------------------------------------------------ #

def test_add_expense_successful_insertion():
    """Requirement: Valid submission inserts record in DB, redirects to profile, and flashes success."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        # Initial check
        conn = get_db()
        cursor = conn.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = 1")
        initial_count = cursor.fetchone()["count"]
        assert initial_count == 8
        conn.close()
        
        # Submit valid expense
        response = client.post("/expenses/add", data={
            "amount": "12.50",
            "category": "Food",
            "date": "2026-06-25",
            "description": "   Sandwich for lunch   "
        }, follow_redirects=True)
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Redirected back to profile and shows success flash message
        assert "Expense added successfully!" in html
        
        # Verify db insertion and description stripping
        conn = get_db()
        cursor = conn.execute("SELECT * FROM expenses WHERE user_id = 1 ORDER BY id DESC LIMIT 1")
        new_expense = cursor.fetchone()
        assert new_expense is not None
        assert new_expense["amount"] == 12.50
        assert new_expense["category"] == "Food"
        assert new_expense["date"] == "2026-06-25"
        assert new_expense["description"] == "Sandwich for lunch"  # Whitespaces stripped
        
        # Total count increased by 1
        cursor = conn.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = 1")
        assert cursor.fetchone()["count"] == 9
        conn.close()

def test_validation_amount_missing():
    """Requirement: Missing amount displays error and preserves other form values."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        response = client.post("/expenses/add", data={
            "amount": "",
            "category": "Bills",
            "date": "2026-06-24",
            "description": "Electric bill"
        })
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Amount is required." in html or "Amount must be" in html
        
        # Preserve submitted fields
        assert 'value="Bills"' in html or 'selected' in html
        assert 'value="2026-06-24"' in html
        assert "Electric bill" in html

def test_validation_amount_must_be_positive():
    """Requirement: Zero or negative amount displays error and preserves other form values."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        # Test negative amount
        response_neg = client.post("/expenses/add", data={
            "amount": "-50",
            "category": "Entertainment",
            "date": "2026-06-24",
            "description": "Movie tickets"
        })
        assert response_neg.status_code == 200
        html_neg = response_neg.data.decode("utf-8")
        assert "Amount must be greater than 0." in html_neg
        assert 'value="-50"' in html_neg
        assert 'value="2026-06-24"' in html_neg
        assert "Movie tickets" in html_neg
        
        # Test zero amount
        response_zero = client.post("/expenses/add", data={
            "amount": "0",
            "category": "Entertainment",
            "date": "2026-06-24",
            "description": "Movie tickets"
        })
        assert response_zero.status_code == 200
        html_zero = response_zero.data.decode("utf-8")
        assert "Amount must be greater than 0." in html_zero
        assert 'value="0"' in html_zero

def test_validation_amount_must_be_numeric():
    """Requirement: Non-numeric amount displays error and preserves other form values."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        response = client.post("/expenses/add", data={
            "amount": "abc",
            "category": "Transport",
            "date": "2026-06-24",
            "description": "Bus ticket"
        })
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Amount must be a valid number." in html
        assert 'value="abc"' in html
        assert 'value="2026-06-24"' in html
        assert "Bus ticket" in html

def test_validation_category_invalid():
    """Requirement: Category not in predefined list displays error and preserves other values."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        response = client.post("/expenses/add", data={
            "amount": "45.00",
            "category": "Luxury", # Invalid category
            "date": "2026-06-24",
            "description": "Designer clothes"
        })
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Invalid category selected." in html
        assert 'value="45.00"' in html
        assert 'value="2026-06-24"' in html
        assert "Designer clothes" in html

def test_validation_date_format_invalid():
    """Requirement: Date in invalid format displays error and preserves other values."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        invalid_dates = ["2026/06/24", "24-06-2026", "not-a-date", ""]
        for invalid_date in invalid_dates:
            response = client.post("/expenses/add", data={
                "amount": "15.00",
                "category": "Health",
                "date": invalid_date,
                "description": "Prescription"
            })
            assert response.status_code == 200
            html = response.data.decode("utf-8")
            assert "Date must be in YYYY-MM-DD format." in html or "Date is required." in html
            assert 'value="15.00"' in html
            assert f'value="{invalid_date}"' in html
            assert "Prescription" in html

def test_validation_description_too_long():
    """Requirement: Description exceeding 200 characters displays error and preserves other values."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        })
        
        long_description = "x" * 201
        response = client.post("/expenses/add", data={
            "amount": "15.00",
            "category": "Other",
            "date": "2026-06-24",
            "description": long_description
        })
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Description must not exceed 200 characters." in html
        assert 'value="15.00"' in html
        assert 'value="2026-06-24"' in html
        assert long_description in html

# ------------------------------------------------------------------ #
# Database Helper Tests
# ------------------------------------------------------------------ #

def test_database_helper_create_expense():
    """Requirement: The database helper create_expense correctly inserts values and returns row ID."""
    # Test adding an expense directly via database helper
    expense_id = create_expense(
        user_id=1,
        amount=99.99,
        category="Bills",
        date="2026-06-24",
        description="Wi-Fi Router"
    )
    
    assert expense_id is not None
    assert isinstance(expense_id, int)
    
    # Retrieve and verify
    conn = get_db()
    cursor = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,))
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None
    assert row["user_id"] == 1
    assert row["amount"] == 99.99
    assert row["category"] == "Bills"
    assert row["date"] == "2026-06-24"
    assert row["description"] == "Wi-Fi Router"
