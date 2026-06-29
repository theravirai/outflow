import pytest
from app import app
from database.db import get_db, init_db, seed_db

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Sets up a temporary SQLite database for testing and overrides the path."""
    db_file = tmp_path / "test_expense_tracker.db"
    monkeypatch.setattr("database.db.DB_PATH", str(db_file))
    init_db()
    seed_db()
    yield

def test_demo_login_flow():
    """Verify that GET /demo registers and logs in a unique temporary demo user."""
    with app.test_client() as client:
        # Before demo login, session should be empty
        response = client.get("/demo", follow_redirects=True)
        assert response.status_code == 200
        
        # Verify redirect to profile
        html = response.data.decode("utf-8")
        assert "Demo Mode" in html
        assert "Welcome to Outflow in Demo Mode!" in html
        assert "You're exploring a fully interactive version of Outflow using sample financial data." in html
        
        # Verify session state
        with client.session_transaction() as sess:
            assert sess.get("user_id") is not None
            assert sess.get("user_name") == "Demo Mode"
            assert sess.get("is_demo") is True
            user_id = sess["user_id"]
            
        # Verify the database has the new user and expenses
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        assert user is not None
        assert user["name"] == "Demo Mode"
        assert user["email"].startswith("demo_session_")
        
        expenses_count = conn.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = ?", (user_id,)).fetchone()["count"]
        assert expenses_count == 47  # Total seeded demo expenses
        conn.close()

def test_demo_isolation():
    """Verify that multiple demo logins create separate accounts and data is isolated."""
    with app.test_client() as client1:
        client1.get("/demo")
        with client1.session_transaction() as sess1:
            user_id_1 = sess1["user_id"]
            
    with app.test_client() as client2:
        client2.get("/demo")
        with client2.session_transaction() as sess2:
            user_id_2 = sess2["user_id"]
            
    assert user_id_1 != user_id_2

def test_demo_logout_clears_session():
    """Verify logout clears demo session variables."""
    with app.test_client() as client:
        client.get("/demo")
        with client.session_transaction() as sess:
            assert sess.get("is_demo") is True
            
        # Log out
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess.get("user_id") is None
            assert sess.get("is_demo") is None
