import pytest
import os
from datetime import datetime, timedelta, timezone
from flask import session
from app import app
from database.db import get_db, init_db, seed_db, cleanup_old_demo_users

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
    # Reset cleanup rate limit
    monkeypatch.setattr("database.db._LAST_CLEANUP_TIME", 0)
    yield

def test_demo_happy_path():
    """Verify that GET /demo registers and logs in a unique temporary demo user, redirects to profile,

    seeds expenses covering all 8 core categories, and secure auto-login exposes no credentials.
    """
    with app.test_client() as client:
        # GET /demo
        # This will internally invoke database methods
        response = client.get("/demo")
        # Should redirect to /profile
        assert response.status_code == 302
        assert "/profile" in response.headers["Location"]
        
        # Follow the redirect
        redirect_response = client.get(response.headers["Location"])
        assert redirect_response.status_code == 200
        html = redirect_response.data.decode("utf-8")
        
        # Check session variables
        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None
            assert sess.get("user_name") == "Demo Mode"
            assert sess.get("is_demo") is True
            user_id = sess["user_id"]
            
        # Verify user is created in database
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            assert user is not None
            assert user["name"] == "Demo Mode"
            assert user["email"].startswith("demo_session_")
            assert user["email"].endswith("@outflow.com")
            
            # Verify security: no credentials or sensitive hashes exposed in UI
            assert user["password_hash"] is not None
            assert user["password_hash"] != ""
            assert user["password_hash"] not in html
            
            # Verify seeded expenses exist and cover multiple categories:
            # Food, Transport, Bills, Shopping, Entertainment, Healthcare, Travel, and Other
            cur.execute("SELECT * FROM expenses WHERE user_id = %s", (user_id,))
            expenses = cur.fetchall()
            assert len(expenses) > 0
            
            categories = {exp["category"] for exp in expenses}
            expected_categories = {"Food", "Transport", "Bills", "Shopping", "Entertainment", "Healthcare", "Travel", "Other"}
            for cat in expected_categories:
                assert cat in categories, f"Category '{cat}' was not seeded in demo mode"
                
        # Verify credentials are not exposed on landing or login pages
        landing_response = client.get("/")
        assert user["email"] not in landing_response.data.decode("utf-8")
        login_response = client.get("/login")
        assert user["email"] not in login_response.data.decode("utf-8")
        
        # Verify UI indicators are present in the response page
        assert "You're exploring a fully interactive version of Outflow using sample financial data." in html
        assert "Demo Mode" in html
        assert "Create Account" in html or "Create Your Account" in html
        
        conn.close()

def test_demo_data_isolation():
    """Verify that sequential demo logins generate different users with independent data."""
    with app.test_client() as client_a:
        client_a.get("/demo")
        with client_a.session_transaction() as sess_a:
            user_id_a = sess_a["user_id"]
            
    with app.test_client() as client_b:
        client_b.get("/demo")
        with client_b.session_transaction() as sess_b:
            user_id_b = sess_b["user_id"]
            
    # Distinct user IDs
    assert user_id_a != user_id_b
    
    # Separate data in database
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id_a,))
        user_a = cur.fetchone()
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id_b,))
        user_b = cur.fetchone()
        assert user_a["email"] != user_b["email"]
        
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (user_id_a,))
        expenses_a = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (user_id_b,))
        expenses_b = cur.fetchone()[0]
        assert expenses_a > 0
        assert expenses_b > 0
    conn.close()

def test_normal_authentication_still_works():
    """Verify that normal registration and login pathways work correctly and do not trigger demo indicators."""
    with app.test_client() as client:
        # Register a normal user
        reg_res = client.post("/register", data={
            "name": "Normal User",
            "email": "normal@outflow.com",
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)
        assert reg_res.status_code == 200
        
        # Log in
        login_res = client.post("/login", data={
            "email": "normal@outflow.com",
            "password": "password123"
        }, follow_redirects=True)
        assert login_res.status_code == 200
        
        # Verify session state
        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None
            assert sess.get("user_name") == "Normal User"
            assert sess.get("is_demo") is None or sess.get("is_demo") is False
            
        # Verify that UI warning banner is NOT present on profile
        html = login_res.data.decode("utf-8")
        assert "You are exploring Outflow in Demo Mode" not in html
        assert "nav-demo-badge" not in html

def test_healthcare_and_travel_categories_accepted():
    """Verify that categories 'Healthcare' and 'Travel' are accepted in add_expense and edit_expense routes."""
    with app.test_client() as client:
        # Log in demo user
        client.get("/demo")
        with client.session_transaction() as sess:
            user_id = sess["user_id"]
            
        # Add expense with category "Healthcare"
        response = client.post("/expenses/add", data={
            "amount": "15.50",
            "category": "Healthcare",
            "date": "2026-07-01",
            "description": "Medicine"
        }, follow_redirects=True)
        assert response.status_code == 200
        
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM expenses WHERE user_id = %s AND category = %s ORDER BY id DESC LIMIT 1",
                (user_id, "Healthcare")
            )
            expense = cur.fetchone()
            assert expense is not None
            assert expense["amount"] == 15.50
            assert expense["description"] == "Medicine"
            expense_id = expense["id"]
            
            # Add expense with category "Travel"
            response2 = client.post("/expenses/add", data={
                "amount": "120.00",
                "category": "Travel",
                "date": "2026-07-01",
                "description": "Flight"
            }, follow_redirects=True)
            assert response2.status_code == 200
            
            cur.execute(
                "SELECT * FROM expenses WHERE user_id = %s AND category = %s ORDER BY id DESC LIMIT 1",
                (user_id, "Travel")
            )
            expense2 = cur.fetchone()
            assert expense2 is not None
            assert expense2["amount"] == 120.00
            
            # Edit expense to change category from Healthcare to Travel
            response3 = client.post(f"/expenses/{expense_id}/edit", data={
                "amount": "18.50",
                "category": "Travel",
                "date": "2026-07-02",
                "description": "Updated Medicine"
            }, follow_redirects=True)
            assert response3.status_code == 200
            
            cur.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
            updated_expense = cur.fetchone()
            assert updated_expense["category"] == "Travel"
            assert updated_expense["amount"] == 18.50
            assert updated_expense["date"] == "2026-07-02"
            assert updated_expense["description"] == "Updated Medicine"
            
            # Edit expense back to Healthcare
            response4 = client.post(f"/expenses/{expense_id}/edit", data={
                "amount": "18.50",
                "category": "Healthcare",
                "date": "2026-07-02",
                "description": "Updated Medicine"
            }, follow_redirects=True)
            assert response4.status_code == 200
            
            cur.execute("SELECT * FROM expenses WHERE id = %s", (expense_id,))
            updated_expense = cur.fetchone()
            assert updated_expense["category"] == "Healthcare"
        conn.close()

def test_demo_logout():
    """Verify that logging out clears demo session variables."""
    with app.test_client() as client:
        client.get("/demo")
        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None
            assert sess.get("is_demo") is True
            
        # Log out
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        
        # Verify session is cleared
        with client.session_transaction() as sess:
            assert sess.get("user_id") is None
            assert sess.get("is_demo") is None

def test_cleanup_old_demo_users_correctness(monkeypatch):
    """Verify cleanup_old_demo_users() deletes demo users and their expenses older than 24 hours while respecting foreign keys."""
    # Reset cleanup interval rate limit to force execution
    monkeypatch.setattr("database.db._LAST_CLEANUP_TIME", 0)
    
    conn = get_db()
    with conn.cursor() as cur:
        # 1. Create an old demo user (created 25 hours ago)
        old_time = (datetime.now(timezone.utc) - timedelta(hours=25)).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
            ("Demo Mode", "demo_session_old@outflow.com", "dummy_hash", old_time)
        )
        old_demo_id = cur.fetchone()[0]
        
        # Add expense for old demo user
        cur.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)",
            (old_demo_id, 10.0, "Food", "2026-07-01", "old expense")
        )
        
        # 2. Create a recent demo user (created 2 hours ago)
        recent_time = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
            ("Demo Mode", "demo_session_recent@outflow.com", "dummy_hash", recent_time)
        )
        recent_demo_id = cur.fetchone()[0]
        
        # Add expense for recent demo user
        cur.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)",
            (recent_demo_id, 20.0, "Food", "2026-07-01", "recent expense")
        )
        
        # 3. Create a normal user created more than 24 hours ago
        cur.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (%s, %s, %s, %s) RETURNING id",
            ("Normal User", "normal_old@example.com", "dummy_hash", old_time)
        )
        normal_id = cur.fetchone()[0]
        
        # Add expense for normal user
        cur.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (%s, %s, %s, %s, %s)",
            (normal_id, 30.0, "Food", "2026-07-01", "normal old expense")
        )
        
    conn.commit()
    conn.close()
    
    # Verify records exist prior to cleanup
    conn = get_db()
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM users WHERE id = %s", (old_demo_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (old_demo_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM users WHERE id = %s", (recent_demo_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (recent_demo_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM users WHERE id = %s", (normal_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (normal_id,))
        assert cur.fetchone()[0] == 1
    conn.close()
    
    # Trigger database cleanup
    cleanup_old_demo_users()
    
    # Verify records state post-cleanup
    conn = get_db()
    with conn.cursor() as cur:
        # Old demo user & expenses must be deleted
        cur.execute("SELECT COUNT(*) FROM users WHERE id = %s", (old_demo_id,))
        assert cur.fetchone()[0] == 0
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (old_demo_id,))
        assert cur.fetchone()[0] == 0
        
        # Recent demo user & expenses must remain untouched
        cur.execute("SELECT COUNT(*) FROM users WHERE id = %s", (recent_demo_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (recent_demo_id,))
        assert cur.fetchone()[0] == 1
        
        # Normal old user & expenses must remain untouched
        cur.execute("SELECT COUNT(*) FROM users WHERE id = %s", (normal_id,))
        assert cur.fetchone()[0] == 1
        cur.execute("SELECT COUNT(*) FROM expenses WHERE user_id = %s", (normal_id,))
        assert cur.fetchone()[0] == 1
    conn.close()
