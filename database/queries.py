import sqlite3
from datetime import datetime
from database.db import get_db

def get_user_by_id(user_id):
    """Returns a dict with name, email, member_since, and initials for a user."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if not row:
            return None
        
        name = row["name"]
        email = row["email"]
        created_at = row["created_at"]
        
        # Parse created_at and format as "Month YYYY"
        member_since = "—"
        if created_at:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(created_at, fmt)
                    member_since = dt.strftime("%B %Y")
                    break
                except ValueError:
                    continue
        
        # Generate initials
        parts = name.split()
        initials = "".join([p[0].upper() for p in parts if p])[:2]
        if not initials:
            initials = "?"
            
        return {
            "name": name,
            "email": email,
            "member_since": member_since,
            "initials": initials
        }
    finally:
        conn.close()

def get_summary_stats(user_id):
    """Returns a dict with total_spent, transaction_count, and top_category."""
    conn = get_db()
    try:
        # Total spent and transaction count
        stats_row = conn.execute(
            "SELECT SUM(amount) as total_spent, COUNT(*) as transaction_count FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        total_spent = stats_row["total_spent"] if stats_row["total_spent"] is not None else 0.0
        transaction_count = stats_row["transaction_count"] if stats_row["transaction_count"] is not None else 0
        
        # Top category by sum of amounts
        top_cat_row = conn.execute(
            """
            SELECT category, SUM(amount) as total_amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total_amount DESC, category ASC
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()
        
        top_category = top_cat_row["category"] if top_cat_row else "—"
        
        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category
        }
    finally:
        conn.close()

def get_recent_transactions(user_id, limit=10):
    """Returns a list of dicts, each with date, description, category, amount."""
    conn = get_db()
    try:
        rows = conn.execute(
            """
            SELECT date, description, category, amount
            FROM expenses
            WHERE user_id = ?
            ORDER BY date DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit)
        ).fetchall()
        
        return [
            {
                "date": row["date"],
                "description": row["description"] if row["description"] is not None else "",
                "category": row["category"],
                "amount": row["amount"]
            }
            for row in rows
        ]
    finally:
        conn.close()

def get_category_breakdown(user_id):
    """Returns a list of dicts, each with category, name, amount, percentage, pct, and class."""
    conn = get_db()
    try:
        # Get total spend first
        total_row = conn.execute(
            "SELECT SUM(amount) as total_spent FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        total_spent = total_row["total_spent"] if total_row["total_spent"] is not None else 0.0
        
        if total_spent == 0.0:
            return []
            
        # Get amounts grouped by category ordered by amount desc
        rows = conn.execute(
            """
            SELECT category, SUM(amount) as total_amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY total_amount DESC
            """,
            (user_id,)
        ).fetchall()
        
        breakdown = []
        for row in rows:
            category = row["category"]
            amount = row["total_amount"]
            # Raw percentage rounding
            pct = round((amount / total_spent) * 100)
            breakdown.append({
                "category": category,
                "name": category,
                "amount": amount,
                "percentage": pct,
                "pct": pct,
                "class": category.lower()
            })
            
        # Ensure percentages sum to exactly 100
        total_pct = sum(item["percentage"] for item in breakdown)
        diff = 100 - total_pct
        if diff != 0 and breakdown:
            # Adjust the largest category (first in list since ordered by total_amount desc)
            breakdown[0]["percentage"] += diff
            breakdown[0]["pct"] += diff
            
        return breakdown
    finally:
        conn.close()
