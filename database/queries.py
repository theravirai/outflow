from datetime import datetime
from database.db import get_db

def get_user_by_id(user_id):
    """Returns a dict with name, email, member_since, and initials for a user."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, email, created_at FROM users WHERE id = %s", (user_id,)
            )
            row = cur.fetchone()
        if not row:
            return None
        
        name = row["name"]
        email = row["email"]
        created_at = row["created_at"]
        
        # Parse created_at and format as "Month YYYY"
        member_since = "—"
        if created_at and isinstance(created_at, datetime):
            member_since = created_at.strftime("%B %Y")
        
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

def get_summary_stats(user_id, start_date=None, end_date=None):
    """Returns a dict with total_spent, transaction_count, and top_category."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Total spent and transaction count
            query = "SELECT SUM(amount) as total_spent, COUNT(*) as transaction_count FROM expenses WHERE user_id = %s"
            params = [user_id]
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
                
            cur.execute(query, params)
            stats_row = cur.fetchone()
            
            total_spent = stats_row["total_spent"] if stats_row and stats_row["total_spent"] is not None else 0.0
            transaction_count = stats_row["transaction_count"] if stats_row and stats_row["transaction_count"] is not None else 0
            
            # Top category by sum of amounts
            top_cat_query = """
                SELECT category, SUM(amount) as total_amount
                FROM expenses
                WHERE user_id = %s
            """
            top_cat_params = [user_id]
            if start_date:
                top_cat_query += " AND date >= %s"
                top_cat_params.append(start_date)
            if end_date:
                top_cat_query += " AND date <= %s"
                top_cat_params.append(end_date)
            top_cat_query += """
                GROUP BY category
                ORDER BY total_amount DESC, category ASC
                LIMIT 1
            """
            
            cur.execute(top_cat_query, top_cat_params)
            top_cat_row = cur.fetchone()
            
            top_category = top_cat_row["category"] if top_cat_row else "—"
            
            return {
                "total_spent": total_spent,
                "transaction_count": transaction_count,
                "top_category": top_category
            }
    finally:
        conn.close()

def get_recent_transactions(user_id, limit=10, start_date=None, end_date=None):
    """Returns a list of dicts, each with id, date, description, category, amount."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            query = """
                SELECT id, date, description, category, amount
                FROM expenses
                WHERE user_id = %s
            """
            params = [user_id]
            if start_date:
                query += " AND date >= %s"
                params.append(start_date)
            if end_date:
                query += " AND date <= %s"
                params.append(end_date)
            query += " ORDER BY date DESC, id DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            return [
                {
                    "id": row["id"],
                    "date": row["date"],
                    "description": row["description"] if row["description"] is not None else "",
                    "category": row["category"],
                    "amount": row["amount"]
                }
                for row in rows
            ]
    finally:
        conn.close()

def get_category_breakdown(user_id, start_date=None, end_date=None):
    """Returns a list of dicts, each with category, name, amount, percentage, pct, and class."""
    conn = get_db()
    try:
        with conn.cursor() as cur:
            # Get total spend first
            query_total = "SELECT SUM(amount) as total_spent FROM expenses WHERE user_id = %s"
            params_total = [user_id]
            if start_date:
                query_total += " AND date >= %s"
                params_total.append(start_date)
            if end_date:
                query_total += " AND date <= %s"
                params_total.append(end_date)
                
            cur.execute(query_total, params_total)
            total_row = cur.fetchone()
            
            total_spent = total_row["total_spent"] if total_row and total_row["total_spent"] is not None else 0.0
            
            if total_spent == 0.0:
                return []
                
            # Get amounts grouped by category ordered by amount desc
            query_breakdown = """
                SELECT category, SUM(amount) as total_amount
                FROM expenses
                WHERE user_id = %s
            """
            params_breakdown = [user_id]
            if start_date:
                query_breakdown += " AND date >= %s"
                params_breakdown.append(start_date)
            if end_date:
                query_breakdown += " AND date <= %s"
                params_breakdown.append(end_date)
            query_breakdown += """
                GROUP BY category
                ORDER BY total_amount DESC
            """
            
            cur.execute(query_breakdown, params_breakdown)
            rows = cur.fetchall()
            
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
