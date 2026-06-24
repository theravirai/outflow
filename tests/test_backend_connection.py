import pytest
import sqlite3
from datetime import datetime, timedelta
from app import app
from database.db import get_db, init_db, seed_db
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Sets up a temporary SQLite database for testing."""
    db_file = tmp_path / "test_expense_tracker.db"
    
    # Override the DB_PATH in the db module (used by get_db)
    monkeypatch.setattr("database.db.DB_PATH", str(db_file))
    
    init_db()
    seed_db()
    
    yield
    
    # DB is automatically removed with tmp_path

def test_get_user_by_id_valid():
    # User 1 is Demo User seeded by seed_db
    user = get_user_by_id(1)
    assert user is not None
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    assert "member_since" in user
    # Check that initials are correct
    assert user["initials"] == "DU"

def test_get_user_by_id_invalid():
    user = get_user_by_id(99999)
    assert user is None

def test_get_summary_stats_with_expenses():
    stats = get_summary_stats(1)
    assert stats is not None
    # Demo User has 8 expenses. Total spent in db.py:
    # 150.50 + 45.00 + 1200.00 + 60.00 + 20.00 + 85.00 + 15.00 + 35.00 = 1610.50
    assert stats["transaction_count"] == 8
    assert stats["total_spent"] == 1610.50
    assert stats["top_category"] == "Bills"

def test_get_summary_stats_no_expenses():
    # Insert a user with no expenses
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("No Expense User", "noexpenses@spendly.com", "hash")
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    stats = get_summary_stats(user_id)
    assert stats == {
        "total_spent": 0.0,
        "transaction_count": 0,
        "top_category": "—"
    }

def test_get_recent_transactions_with_expenses():
    txs = get_recent_transactions(1, limit=5)
    assert len(txs) == 5
    # Order should be newest date first.
    # The date fields of recent transactions are sorted descending.
    for i in range(len(txs) - 1):
        assert txs[i]["date"] >= txs[i+1]["date"]

def test_get_recent_transactions_no_expenses():
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("No Expense User", "noexpenses@spendly.com", "hash")
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    txs = get_recent_transactions(user_id)
    assert txs == []

def test_get_category_breakdown_with_expenses():
    breakdown = get_category_breakdown(1)
    assert len(breakdown) > 0
    
    # Assert breakdown has correct keys
    for item in breakdown:
        assert "category" in item
        assert "name" in item
        assert "amount" in item
        assert "percentage" in item
        assert "pct" in item
        assert "class" in item
        
    # Assert ordered by amount descending
    for i in range(len(breakdown) - 1):
        assert breakdown[i]["amount"] >= breakdown[i+1]["amount"]
        
    # Assert percentage values sum to exactly 100
    total_pct = sum(item["percentage"] for item in breakdown)
    assert total_pct == 100
    
    total_pct_alt = sum(item["pct"] for item in breakdown)
    assert total_pct_alt == 100

def test_get_category_breakdown_no_expenses():
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("No Expense User", "noexpenses@spendly.com", "hash")
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()

    breakdown = get_category_breakdown(user_id)
    assert breakdown == []

def test_profile_route_unauthenticated():
    with app.test_client() as client:
        response = client.get("/profile")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

def test_profile_route_authenticated(monkeypatch, tmp_path):
    # Setup test DB file path override for the app client too
    db_file = tmp_path / "test_expense_tracker.db"
    monkeypatch.setattr("database.db.DB_PATH", str(db_file))
    
    init_db()
    seed_db()

    with app.test_client() as client:
        # Perform login first
        login_res = client.post("/login", data={
            "email": "demo@spendly.com",
            "password": "demo123"
        }, follow_redirects=True)
        assert login_res.status_code == 200
        
        # Request profile page
        response = client.get("/profile")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verification expectations
        assert "Demo User" in html
        assert "demo@spendly.com" in html
        assert "€" in html
        assert "Bills" in html
        assert "1610.50" in html
        
        # Verify currency format displays € everywhere needed
        assert "€1610.50" in html
