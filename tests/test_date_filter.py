import pytest
import sqlite3
import re
from datetime import datetime, timedelta
import calendar

from app import app
from database.db import get_db, init_db, seed_db
from database.queries import (
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a test PostgreSQL database for testing."""
    import os
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


# Helper to check active preset in HTML
def assert_preset_active(html, active_text, inactive_texts):
    # Find active_text tag and verify active class is present in it
    active_match = re.search(r'<a\b[^>]*>\s*' + re.escape(active_text) + r'\s*</a>', html, re.IGNORECASE)
    assert active_match is not None, f"Could not find active preset label: {active_text}"
    active_tag = active_match.group(0)
    assert re.search(r'\bactive\b', active_tag, re.IGNORECASE), f"Expected active class in tag: {active_tag}"
    
    # Ensure inactive_texts anchor tags do NOT have active class
    for text in inactive_texts:
        match = re.search(r'<a\b[^>]*>\s*' + re.escape(text) + r'\s*</a>', html, re.IGNORECASE)
        if match:
            tag = match.group(0)
            assert not re.search(r'\bactive\b', tag, re.IGNORECASE), f"Expected '{text}' to not be highlighted as active. Tag: {tag}"

# ==============================================================================
# Unit Tests (Database Queries)
# ==============================================================================

def test_get_summary_stats_valid_range():
    """Test get_summary_stats with a valid date range that includes expenses."""
    # User 1 is Demo User seeded by seed_db
    today = datetime.today().date()
    
    # Filter for the last 5 days (today - 5 to today - 1)
    # Expected matching expenses from seed_db:
    # - (user_id, 150.50, "Food", today - 1)
    # - (user_id, 45.00, "Transport", today - 2)
    # - (user_id, 1200.00, "Bills", today - 5)
    # Total spent: 150.50 + 45.00 + 1200.00 = 1395.50
    # Count: 3
    # Top Category: Bills
    start_date = str(today - timedelta(days=5))
    end_date = str(today - timedelta(days=1))
    
    stats = get_summary_stats(1, start_date=start_date, end_date=end_date)
    assert stats is not None
    assert stats["transaction_count"] == 3
    assert stats["total_spent"] == 1395.50
    assert stats["top_category"] == "Bills"

def test_get_summary_stats_open_ended():
    """Test get_summary_stats with open-ended date ranges (only start or only end)."""
    today = datetime.today().date()
    
    # Open-ended start (from today - 5 onwards)
    # Expected: same 3 expenses as above
    start_date = str(today - timedelta(days=5))
    stats_start = get_summary_stats(1, start_date=start_date, end_date=None)
    assert stats_start["transaction_count"] == 3
    assert stats_start["total_spent"] == 1395.50
    assert stats_start["top_category"] == "Bills"
    
    # Open-ended end (up to today - 10)
    # Expected matching expenses:
    # - today - 10 (60.00, Health)
    # - today - 12 (20.00, Entertainment)
    # - today - 15 (85.00, Shopping)
    # - today - 18 (15.00, Food)
    # - today - 20 (35.00, Other)
    # Total spent: 60 + 20 + 85 + 15 + 35 = 215.00
    # Count: 5
    # Top Category: Shopping (85.00)
    end_date = str(today - timedelta(days=10))
    stats_end = get_summary_stats(1, start_date=None, end_date=end_date)
    assert stats_end["transaction_count"] == 5
    assert stats_end["total_spent"] == 215.00
    assert stats_end["top_category"] == "Shopping"

def test_get_summary_stats_empty_range():
    """Test get_summary_stats with a date range containing no expenses."""
    today = datetime.today().date()
    
    # Date range in the future
    start_date = str(today + timedelta(days=1))
    end_date = str(today + timedelta(days=10))
    
    stats = get_summary_stats(1, start_date=start_date, end_date=end_date)
    assert stats == {
        "total_spent": 0.0,
        "transaction_count": 0,
        "top_category": "—"
    }

def test_get_recent_transactions_valid_range():
    """Test get_recent_transactions with a valid date range."""
    today = datetime.today().date()
    
    # Filter for today - 5 to today - 1
    start_date = str(today - timedelta(days=5))
    end_date = str(today - timedelta(days=1))
    
    txs = get_recent_transactions(1, start_date=start_date, end_date=end_date)
    assert len(txs) == 3
    # Check descending date order
    assert txs[0]["date"] >= txs[1]["date"] >= txs[2]["date"]
    # Check that they match the expected amounts
    amounts = [tx["amount"] for tx in txs]
    assert 150.50 in amounts
    assert 45.00 in amounts
    assert 1200.00 in amounts

def test_get_recent_transactions_open_ended():
    """Test get_recent_transactions with open-ended date ranges."""
    today = datetime.today().date()
    
    # From today - 5 onwards
    start_date = str(today - timedelta(days=5))
    txs_start = get_recent_transactions(1, start_date=start_date, end_date=None)
    assert len(txs_start) == 3
    
    # Up to today - 10
    end_date = str(today - timedelta(days=10))
    txs_end = get_recent_transactions(1, start_date=None, end_date=end_date)
    assert len(txs_end) == 5

def test_get_recent_transactions_empty_range():
    """Test get_recent_transactions with a date range containing no expenses."""
    today = datetime.today().date()
    start_date = str(today + timedelta(days=1))
    end_date = str(today + timedelta(days=10))
    
    txs = get_recent_transactions(1, start_date=start_date, end_date=end_date)
    assert txs == []

def test_get_category_breakdown_valid_range():
    """Test get_category_breakdown with a valid date range."""
    today = datetime.today().date()
    
    # Filter for today - 5 to today - 1
    # Total spent: 1395.50
    # Bills: 1200.00 (86%)
    # Food: 150.50 (11% -> adjusted to 11% or 14% depending on rounding, but sum is 100%)
    # Transport: 45.00 (3%)
    start_date = str(today - timedelta(days=5))
    end_date = str(today - timedelta(days=1))
    
    breakdown = get_category_breakdown(1, start_date=start_date, end_date=end_date)
    assert len(breakdown) == 3
    
    categories = [b["category"] for b in breakdown]
    assert "Bills" in categories
    assert "Food" in categories
    assert "Transport" in categories
    
    # Verify that total percentage sums to 100
    total_pct = sum(b["percentage"] for b in breakdown)
    assert total_pct == 100

def test_get_category_breakdown_open_ended():
    """Test get_category_breakdown with open-ended date ranges."""
    today = datetime.today().date()
    
    # From today - 5 onwards
    start_date = str(today - timedelta(days=5))
    breakdown_start = get_category_breakdown(1, start_date=start_date, end_date=None)
    assert len(breakdown_start) == 3
    
    # Up to today - 10
    end_date = str(today - timedelta(days=10))
    breakdown_end = get_category_breakdown(1, start_date=None, end_date=end_date)
    assert len(breakdown_end) == 5

def test_get_category_breakdown_empty_range():
    """Test get_category_breakdown with a date range containing no expenses."""
    today = datetime.today().date()
    start_date = str(today + timedelta(days=1))
    end_date = str(today + timedelta(days=10))
    
    breakdown = get_category_breakdown(1, start_date=start_date, end_date=end_date)
    assert breakdown == []


# ==============================================================================
# Route Tests (GET /profile)
# ==============================================================================

def test_profile_route_preset_7d():
    """Test GET /profile with preset=7d query parameter."""
    today = datetime.today().date()
    start_date = str(today - timedelta(days=6))
    end_date = str(today)
    
    with app.test_client() as client:
        # Authenticate first
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        }, follow_redirects=True)
        
        response = client.get("/profile?preset=7d")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verify the stats for last 7 days (today - 6 to today)
        # Seeded expenses: today - 1 (150.50), today - 2 (45.00), today - 5 (1200.00)
        # Total Spent: 1395.50
        # Transactions count: 3
        assert "1395.50" in html
        assert "3" in html
        
        # Verify preset highlighting
        assert_preset_active(html, "Last 7 Days", ["Last 30 Days", "This Month", "All Time"])
        
        # Verify input fields are populated with correct resolved dates
        assert f'value="{start_date}"' in html or f"value='{start_date}'" in html
        assert f'value="{end_date}"' in html or f"value='{end_date}'" in html

def test_profile_route_preset_30d():
    """Test GET /profile with preset=30d query parameter."""
    today = datetime.today().date()
    start_date = str(today - timedelta(days=29))
    end_date = str(today)
    
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        }, follow_redirects=True)
        
        response = client.get("/profile?preset=30d")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verify the stats for last 30 days (all 8 expenses)
        # Total Spent: 1610.50
        # Transactions count: 8
        assert "1610.50" in html
        assert "8" in html
        
        # Verify preset highlighting
        assert_preset_active(html, "Last 30 Days", ["Last 7 Days", "This Month", "All Time"])
        
        # Verify input fields are populated with correct resolved dates
        assert f'value="{start_date}"' in html or f"value='{start_date}'" in html
        assert f'value="{end_date}"' in html or f"value='{end_date}'" in html

def test_profile_route_preset_this_month():
    """Test GET /profile with preset=this-month query parameter."""
    today = datetime.today().date()
    start_date = str(today.replace(day=1))
    
    # Calculate end of month or today for validation
    _, last_day = calendar.monthrange(today.year, today.month)
    end_date_month_end = str(today.replace(day=last_day))
    end_date_today = str(today)
    
    # Dynamically compute expected sum/count based on how many seeded expenses fall in this month
    all_offsets = [1, 2, 5, 10, 12, 15, 18, 20]
    amounts = [150.50, 45.00, 1200.00, 60.00, 20.00, 85.00, 15.00, 35.00]
    first_of_month = today.replace(day=1)
    
    expected_count = 0
    expected_sum = 0.0
    for offset, amt in zip(all_offsets, amounts):
        exp_date = today - timedelta(days=offset)
        if exp_date >= first_of_month:
            expected_count += 1
            expected_sum += amt
            
    expected_sum_str = f"{expected_sum:.2f}"
    
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        }, follow_redirects=True)
        
        response = client.get("/profile?preset=this-month")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verify dynamic stats
        assert expected_sum_str in html
        assert str(expected_count) in html
        
        # Verify preset highlighting
        assert_preset_active(html, "This Month", ["Last 7 Days", "Last 30 Days", "All Time"])
        
        # Verify start input is first of month
        assert f'value="{start_date}"' in html or f"value='{start_date}'" in html
        # Verify end input is either today or end of month
        has_end_date = (
            f'value="{end_date_today}"' in html or f"value='{end_date_today}'" in html or
            f'value="{end_date_month_end}"' in html or f"value='{end_date_month_end}'" in html
        )
        assert has_end_date, "Expected end_date value to be today or the end of the month"

def test_profile_route_preset_all():
    """Test GET /profile with preset=all query parameter."""
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        }, follow_redirects=True)
        
        response = client.get("/profile?preset=all")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verify the stats for all time
        assert "1610.50" in html
        assert "8" in html
        
        # Verify preset highlighting
        assert_preset_active(html, "All Time", ["Last 7 Days", "Last 30 Days", "This Month"])
        
        # Verify input fields are empty/cleared (i.e. do not contain populated date values)
        # An empty input shouldn't have a value attribute or value should be empty
        # We can search for the value attribute on start_date and check it's not set to a date
        # (e.g. check no pattern value="YYYY-MM-DD" is present on the input tag)
        start_input_match = re.search(r'id=["\']start_date["\'][^>]*value=["\']([^"\']+)["\']', html)
        end_input_match = re.search(r'id=["\']end_date["\'][^>]*value=["\']([^"\']+)["\']', html)
        if start_input_match:
            assert start_input_match.group(1) == ""
        if end_input_match:
            assert end_input_match.group(1) == ""

def test_profile_route_custom_range():
    """Test GET /profile with custom date filters and preset=custom."""
    today = datetime.today().date()
    start_date = str(today - timedelta(days=15))
    end_date = str(today - timedelta(days=10))
    
    # Expected matching expenses:
    # - today - 10 (60.00)
    # - today - 12 (20.00)
    # - today - 15 (85.00)
    # Total: 165.00, count: 3
    
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        }, follow_redirects=True)
        
        response = client.get(f"/profile?start_date={start_date}&end_date={end_date}&preset=custom")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verify custom stats
        assert "165.00" in html
        assert "3" in html
        
        # Verify highlighting (no quick-select preset should be active)
        for preset in ["Last 7 Days", "Last 30 Days", "This Month", "All Time"]:
            t_idx = html.find(preset)
            if t_idx != -1:
                t_window = html[max(0, t_idx - 150): min(len(html), t_idx + 150)]
                active_class_pattern = r'class=["\'][^"\']*\bactive\b[^"\']*["\']'
                assert not re.search(active_class_pattern, t_window, re.IGNORECASE), f"Expected '{preset}' to not be highlighted as active for custom range"
                
        # Verify inputs are populated with the custom range dates
        assert f'value="{start_date}"' in html or f"value='{start_date}'" in html
        assert f'value="{end_date}"' in html or f"value='{end_date}'" in html
        # Check hidden input preset="custom"
        assert 'name="preset"' in html
        assert 'value="custom"' in html

def test_profile_route_no_matching_transactions():
    """Test GET /profile with a range containing no matching expenses."""
    today = datetime.today().date()
    start_date = str(today + timedelta(days=1))
    end_date = str(today + timedelta(days=10))
    
    with app.test_client() as client:
        client.post("/login", data={
            "email": "demo@outflow.com",
            "password": "demo123"
        }, follow_redirects=True)
        
        response = client.get(f"/profile?start_date={start_date}&end_date={end_date}&preset=custom")
        assert response.status_code == 200
        html = response.data.decode("utf-8")
        
        # Verify the empty stats
        assert "€0.00" in html
        assert "0" in html
        assert "—" in html
        
        # Verify empty state messages
        assert "No expenses in this range" in html
        assert "No transactions found in this range" in html
