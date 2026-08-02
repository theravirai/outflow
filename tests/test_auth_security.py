import pytest
import os
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, limiter
from database.db import get_db, init_db, seed_db, get_user_by_email, get_password_reset_by_token
from datetime import datetime, timedelta

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a test PostgreSQL database for testing."""
    test_db_url = os.environ.get("DATABASE_URL_TEST")
    if not test_db_url:
        pytest.fail("DATABASE_URL_TEST environment variable is not set.")
    
    monkeypatch.setattr("database.db.DATABASE_URL", test_db_url)
    
    # Disable rate limiting for testing
    limiter.enabled = False
    
    init_db()
    
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE users, expenses, password_resets RESTART IDENTITY CASCADE;")
    conn.close()
    
    seed_db()
    yield
    
    # Re-enable rate limiting for other tests if needed
    limiter.enabled = True

def test_forgot_password_route():
    with app.test_client() as client:
        response = client.get("/forgot-password")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "Reset your password" in html

def test_forgot_password_post_valid_email():
    with app.test_client() as client:
        response = client.post("/forgot-password", data={
            "email": "demo@outflow.com"
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "password reset link has been sent" in html
        
        # Check DB for token
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM password_resets")
            row = cur.fetchone()
        conn.close()
        
        assert row is not None
        assert row["user_id"] == 1

def test_reset_password_route_invalid_token():
    with app.test_client() as client:
        response = client.get("/reset-password/invalid-token", follow_redirects=True)
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "password reset link is invalid or has expired" in html

def test_reset_password_post_success():
    with app.test_client() as client:
        # First request reset token
        client.post("/forgot-password", data={"email": "demo@outflow.com"})
        
        # Fetch token from DB
        conn = get_db()
        with conn.cursor() as cur:
            cur.execute("SELECT token FROM password_resets WHERE user_id = 1")
            token = cur.fetchone()["token"]
        conn.close()
        
        # Now use token
        response = client.post(f"/reset-password/{token}", data={
            "password": "newsecurepassword123",
            "confirm_password": "newsecurepassword123"
        }, follow_redirects=True)
        
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        assert "password has been successfully reset" in html
        
        # Check token is deleted
        assert get_password_reset_by_token(token) is None
        
        # Verify can login with new password
        login_res = client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "newsecurepassword123"
        }, follow_redirects=True)
        
        assert "Sign out" in login_res.data.decode("utf-8")
