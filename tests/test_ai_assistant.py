import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app import app
from services.ai_assistant import (
    detect_intent,
    handle_add_expense,
    handle_navigation,
    handle_dashboard_query,
    handle_help,
    process_user_input
)
from database.db import get_db, init_db, seed_db

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a test PostgreSQL database for testing."""
    test_db_url = os.environ.get("DATABASE_URL_TEST")
    if not test_db_url:
        pytest.fail("DATABASE_URL_TEST environment variable is not set.")
    
    monkeypatch.setattr("database.db.DATABASE_URL", test_db_url)
    monkeypatch.setenv("GROQ_API_KEY", "test-key-123")
    
    init_db()
    
    conn = get_db()
    with conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE users, expenses RESTART IDENTITY CASCADE;")
    conn.close()
    
    seed_db()
    yield

def mock_groq_response(content):
    """Helper to mock a Groq client response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

@patch('services.ai_assistant.get_groq_client')
def test_detect_intent(mock_get_client):
    mock_get_client.return_value = mock_groq_response('{"intent": "add_expense"}')
    intent = detect_intent("I bought a coffee")
    assert intent == "add_expense"

@patch('services.ai_assistant.get_groq_client')
def test_detect_intent_fallback(mock_get_client):
    mock_get_client.return_value = mock_groq_response('invalid json')
    intent = detect_intent("hello")
    # Should fallback to help gracefully
    assert intent == "help"

@patch('services.ai_assistant.get_groq_client')
def test_handle_add_expense(mock_get_client):
    mock_json = '{"amount": 5.50, "category": "Food", "date": "2023-10-01", "description": "Coffee"}'
    mock_get_client.return_value = mock_groq_response(mock_json)
    
    response = handle_add_expense("Coffee 5.50")
    
    assert response["type"] == "add_expense"
    assert response["data"]["amount"] == 5.50
    assert response["data"]["category"] == "Food"

@patch('services.ai_assistant.get_groq_client')
def test_handle_add_expense_invalid_category(mock_get_client):
    # LLM hallucinated an invalid category
    mock_json = '{"amount": 10, "category": "InvalidCat", "date": "2023-10-01", "description": "Stuff"}'
    mock_get_client.return_value = mock_groq_response(mock_json)
    
    response = handle_add_expense("Stuff 10")
    
    assert response["type"] == "add_expense"
    # Should fallback to "Other"
    assert response["data"]["category"] == "Other"

@patch('services.ai_assistant.get_groq_client')
def test_handle_navigation(mock_get_client):
    mock_get_client.return_value = mock_groq_response('{"url": "/profile"}')
    response = handle_navigation("Go to dashboard")
    
    assert response["type"] == "navigation"
    assert response["data"]["url"] == "/profile"

@patch('services.ai_assistant.get_groq_client')
def test_handle_help(mock_get_client):
    mock_get_client.return_value = mock_groq_response('This is a helpful answer.')
    response = handle_help("How do categories work?")
    
    assert response["type"] == "chat"
    assert "This is a helpful answer." in response["message"]

@patch('services.ai_assistant.detect_intent')
@patch('services.ai_assistant.handle_navigation')
def test_process_user_input_router(mock_handle_nav, mock_detect_intent):
    mock_detect_intent.return_value = "navigation"
    mock_handle_nav.return_value = {"type": "navigation", "data": {"url": "/profile"}}
    
    response = process_user_input("Take me home", 1)
    
    assert response["type"] == "navigation"
    assert mock_handle_nav.called

@patch('services.ai_assistant.detect_intent')
def test_process_user_input_error(mock_detect_intent):
    # Simulate API failure
    mock_detect_intent.side_effect = Exception("API down")
    
    response = process_user_input("hello", 1)
    assert response["type"] == "error"
    assert "unable to reach the AI service" in response["message"]

def test_api_assistant_unauthorized():
    with app.test_client() as client:
        response = client.post('/api/assistant', json={"text": "hello"})
        assert response.status_code == 401
        assert not response.json["success"]

@patch('app.process_user_input')
def test_api_assistant_authorized(mock_process):
    mock_process.return_value = {"type": "chat", "message": "Hello there!"}
    
    with app.test_client() as client:
        # Login to demo mode
        client.get('/demo', follow_redirects=True)
        
        response = client.post('/api/assistant', json={"text": "hi"})
        assert response.status_code == 200
        assert response.json["type"] == "chat"
        assert response.json["message"] == "Hello there!"
