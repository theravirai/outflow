import pytest
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from database.db import get_db, init_db, seed_db, get_user_by_email
from database.queries import get_user_credentials

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

def login(client, email="demo@outflow.com", password="demo123"):
    return client.post("/login", data={
        "email": email,
        "password": password
    }, follow_redirects=True)

def test_settings_route_unauthenticated():
    with app.test_client() as client:
        response = client.get("/settings")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

def test_settings_route_authenticated():
    with app.test_client() as client:
        login(client)
        response = client.get("/settings")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Settings" in html
        assert "Profile" in html
        assert "Security" in html
        assert "Danger Zone" in html
        assert "demo@outflow.com" in html

def test_update_profile_success():
    with app.test_client() as client:
        login(client)
        response = client.post("/settings/profile", data={
            "name": "Updated Name",
            "email": "updated@outflow.com"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Profile updated successfully." in html
        
        user = get_user_by_email("updated@outflow.com")
        assert user is not None
        assert user["name"] == "Updated Name"

def test_update_profile_conflict():
    with app.test_client() as client:
        # Create a second user manually
        conn = get_db()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (%s, %s, %s)",
                    ("Other User", "other@outflow.com", "hash")
                )
        conn.close()

        login(client)
        response = client.post("/settings/profile", data={
            "name": "Updated Name",
            "email": "other@outflow.com"
        }, follow_redirects=True)
        
        html = response.data.decode("utf-8")
        assert "That email is already in use by another account." in html

def test_update_password_success():
    with app.test_client() as client:
        login(client)
        response = client.post("/settings/password", data={
            "current_password": "demo123",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }, follow_redirects=True)
        
        html = response.data.decode("utf-8")
        assert "Password updated successfully." in html
        
        # Verify hash changed
        user = get_user_by_email("demo@outflow.com")
        assert check_password_hash(user["password_hash"], "newpassword123")

def test_update_password_incorrect_current():
    with app.test_client() as client:
        login(client)
        response = client.post("/settings/password", data={
            "current_password": "wrongpassword",
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        }, follow_redirects=True)
        
        html = response.data.decode("utf-8")
        assert "Incorrect current password." in html

def test_update_password_mismatch():
    with app.test_client() as client:
        login(client)
        response = client.post("/settings/password", data={
            "current_password": "demo123",
            "new_password": "newpassword123",
            "confirm_password": "mismatchpassword"
        }, follow_redirects=True)
        
        html = response.data.decode("utf-8")
        assert "New passwords do not match." in html

def test_update_password_too_short():
    with app.test_client() as client:
        login(client)
        response = client.post("/settings/password", data={
            "current_password": "demo123",
            "new_password": "short",
            "confirm_password": "short"
        }, follow_redirects=True)
        
        html = response.data.decode("utf-8")
        assert "New password must be at least 8 characters." in html

def test_delete_account():
    with app.test_client() as client:
        login(client)
        
        user = get_user_by_email("demo@outflow.com")
        user_id = user["id"]
        
        response = client.post("/settings/delete", follow_redirects=True)
        assert response.status_code == 200
        
        # Verify session cleared and redirected to home
        html = response.data.decode("utf-8")
        assert "Track every Euro." in html  # Home page
        
        # Verify user is deleted
        deleted_user = get_user_by_email("demo@outflow.com")
        assert deleted_user is None
        
        # Verify expenses are deleted
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = %s", (user_id,))
            count = cur.fetchone()["count"]
        conn.close()
        assert count == 0
