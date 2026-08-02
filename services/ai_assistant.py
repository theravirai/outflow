import os
import json
from datetime import date
from groq import Groq
from pydantic import BaseModel, ValidationError, Field, field_validator
from typing import Optional
from datetime import datetime, date, timedelta
from database.queries import get_summary_stats, get_category_breakdown, get_recent_transactions

class IntentResponse(BaseModel):
    intent: str

class AddExpenseResponse(BaseModel):
    amount: float = Field(..., gt=0, le=100000)
    category: str
    date: str
    description: str = Field(..., max_length=50)

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        try:
            d = datetime.strptime(v, "%Y-%m-%d").date()
            if d < date(2000, 1, 1):
                raise ValueError("Date is too far in the past")
            if d > date.today() + timedelta(days=30):
                raise ValueError("Date is too far in the future")
        except ValueError:
            raise ValueError("Invalid date format or bounds")
        return v

class NavigationResponse(BaseModel):
    url: str

class DeleteExpenseResponse(BaseModel):
    transaction_id: Optional[int] = None
    reason: Optional[str] = None

class UpdateExpenseResponse(BaseModel):
    transaction_id: Optional[int] = None
    amount: Optional[float] = Field(None, gt=0, le=100000)
    category: Optional[str] = None
    date: Optional[str] = None
    description: Optional[str] = Field(None, max_length=50)

    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            d = datetime.strptime(v, "%Y-%m-%d").date()
            if d < date(2000, 1, 1):
                raise ValueError("Date is too far in the past")
            if d > date.today() + timedelta(days=30):
                raise ValueError("Date is too far in the future")
        except ValueError:
            raise ValueError("Invalid date format or bounds")
        return v

def get_groq_client():
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not configured")
    return Groq(api_key=api_key)

def _build_messages(system_prompt, history, user_input):
    if history is None: history = []
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_input})
    return messages

def detect_intent(user_input, history=None):
    client = get_groq_client()
    system_prompt = """
You are the intent router for Outflow, a personal finance app.
Classify the user's intent into EXACTLY ONE of the following categories:
- add_expense: User wants to record a new expense or transaction.
- update_expense: User wants to edit or update an existing expense.
- delete_expense: User wants to delete or remove an existing expense.
- dashboard_query: User is asking a question about their past spending, aggregates, categories, or trends.
- navigation: User wants to navigate to a different page in the app (e.g. profile, add expense, home).
- help: User is asking for help on how to use the app, categories, or demo mode, or general chat.

Return ONLY a JSON object with a single key "intent" whose value is one of the categories above.
"""
    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    try:
        content = json.loads(response.choices[0].message.content)
        parsed = IntentResponse(**content)
        return parsed.intent
    except Exception:
        return "help"

def handle_add_expense(user_input, history=None):
    client = get_groq_client()
    today_date = date.today().isoformat()
    system_prompt = f"""
You are an expert expense parser for a fintech app. 
Extract the details from the user's input into JSON.
Return ONLY valid JSON.

JSON Schema:
{{
  "amount": float (the cost, strictly a number),
  "category": string (MUST be one of: Food, Transport, Bills, Health, Healthcare, Travel, Entertainment, Shopping, Other),
  "date": string (YYYY-MM-DD),
  "description": string (Concise 1-3 word description of the item)
}}

Important Rules:
1. If the year/month/date is not specified, assume today is {today_date}. If they say "yesterday", calculate the date relative to {today_date}.
2. Ensure the category EXACTLY matches one of the allowed options. If unsure, use "Other".
3. **CRITICAL:** Items like milk, groceries, coffee, restaurants, and eating out MUST be categorized as "Food".
4. Capitalize the description like a sentence. Limit description to 1-3 words maximum (e.g. "Weekly groceries", "Train ticket", "Starbucks coffee").
"""
    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        parsed = AddExpenseResponse(**data)
        data = parsed.model_dump()
        
        allowed = ["Food", "Transport", "Bills", "Health", "Healthcare", "Travel", "Entertainment", "Shopping", "Other"]
        if data.get("category") not in allowed:
            data["category"] = "Other"
            
        return {
            "type": "add_expense",
            "data": data,
            "message": "I can help with that. Please review and confirm the details below before saving:"
        }
    except Exception:
        return {
            "type": "chat",
            "message": "I couldn't quite understand the expense details. Could you repeat the amount, category, and description clearly?"
        }

def handle_navigation(user_input, history=None):
    client = get_groq_client()
    system_prompt = """
You are a navigation router. Map the user's request to one of the following exact URLs:
- "/profile" : The dashboard/home/profile showing transactions and charts
- "/expenses/add" : The page to manually add an expense
- "/" : The landing page
- "/logout" : To sign out

Return ONLY a JSON object with a single key "url" containing the mapped URL string.
"""
    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        response_format={"type": "json_object"}
    )
    try:
        data = json.loads(response.choices[0].message.content)
        parsed = NavigationResponse(**data)
        url = parsed.url
    except Exception:
        url = "/profile"
        
    return {
        "type": "navigation",
        "data": {"url": url},
        "message": "I'm redirecting you there now..."
    }

def handle_dashboard_query(user_input, user_id, history=None):
    summary = get_summary_stats(user_id)
    breakdown = get_category_breakdown(user_id)
    
    client = get_groq_client()
    system_prompt = f"""
You are Outflow's financial assistant. 
The user is asking a question about their spending. 
Answer their question using the following aggregated database metrics.
Do NOT mention that you are reading from a database or JSON. Just answer naturally.
Keep it concise (max 2-3 paragraphs). Avoid generic AI pleasantries.

Data context:
- Total Spent All Time: €{summary['total_spent']:.2f}
- Total Transactions: {summary['transaction_count']}
- Top Category: {summary['top_category']}

Category Breakdown All Time:
"""
    for item in breakdown:
        system_prompt += f"- {item['category']}: €{item['amount']:.2f}\n"

    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return {
        "type": "chat",
        "message": response.choices[0].message.content
    }

def handle_help(user_input, history=None):
    client = get_groq_client()
    system_prompt = """
You are Outflow's helpful personal finance assistant. 
Answer the user's question about the application. 
Keep your answer concise (max 3 short paragraphs).
Do not use generic AI wording. Be professional and helpful.

App Knowledge:
- Demo Mode: A safe sandbox mode with realistic pre-populated data. Changes are temporary. If a user registers while in demo mode, their demo transactions are permanently saved to their new account.
- Categories: Outflow supports Food, Transport, Bills, Health, Healthcare, Travel, Entertainment, Shopping, and Other.
- AI Assistant: You (the assistant) can add expenses automatically, answer questions about spending trends, and help navigate the app.
- Outflow is a personal finance tracker built to be minimal, fast, and completely focused on privacy.
"""
    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )
    return {
        "type": "chat",
        "message": response.choices[0].message.content
    }

def handle_delete_expense(user_input, user_id, history=None):
    recent = get_recent_transactions(user_id, limit=30)
    
    if not recent:
        return {
            "type": "chat",
            "message": "You don't have any recent transactions to delete."
        }
        
    transactions_text = "\n".join([
        f"ID: {tx['id']} | Date: {tx['date']} | Desc: {tx['description']} | Cat: {tx['category']} | Amt: {tx['amount']}"
        for tx in recent
    ])
    
    client = get_groq_client()
    system_prompt = f"""
The user wants to delete a transaction.
Here are the user's 30 most recent transactions:
{transactions_text}

Identify which transaction the user is referring to based on their input.
Return ONLY a JSON object with:
- "transaction_id": The ID integer of the matched transaction, or null if no match found.
- "reason": A brief reason why you matched it, or why you couldn't find it.
"""
    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        parsed = DeleteExpenseResponse(**data)
        tx_id = parsed.transaction_id
    except Exception:
        return {
            "type": "chat",
            "message": "I couldn't quite understand which transaction you meant. Could you be more specific?"
        }
    
    if not tx_id:
        return {
            "type": "chat",
            "message": "I couldn't confidently identify which transaction you want to delete. Could you be more specific?"
        }
        
    matched_tx = next((tx for tx in recent if tx['id'] == tx_id), None)
    if not matched_tx:
        return {
            "type": "chat",
            "message": "I couldn't find a matching transaction."
        }
        
    return {
        "type": "delete_expense",
        "data": matched_tx,
        "message": "I found this transaction. Please confirm you want to delete it:"
    }

def handle_update_expense(user_input, user_id, history=None):
    recent = get_recent_transactions(user_id, limit=30)
    
    if not recent:
        return {
            "type": "chat",
            "message": "You don't have any recent transactions to update."
        }
        
    transactions_text = "\n".join([
        f"ID: {tx['id']} | Date: {tx['date']} | Desc: {tx['description']} | Cat: {tx['category']} | Amt: {tx['amount']}"
        for tx in recent
    ])
    
    client = get_groq_client()
    system_prompt = f"""
The user wants to update an existing transaction.
Here are the user's 30 most recent transactions:
{transactions_text}

Identify which transaction the user is referring to, and what fields they want to change.
Return ONLY a JSON object with:
- "transaction_id": The ID integer of the matched transaction, or null if no match found.
- "amount": The updated amount, or null if unchanged.
- "category": The updated category (must be Food, Transport, Bills, Health, Healthcare, Travel, Entertainment, Shopping, or Other), or null if unchanged.
- "date": The updated date (YYYY-MM-DD), or null if unchanged.
- "description": The updated description, or null if unchanged.
"""
    messages = _build_messages(system_prompt, history, user_input)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    try:
        data = json.loads(response.choices[0].message.content)
        parsed = UpdateExpenseResponse(**data)
        tx_id = parsed.transaction_id
    except Exception:
        return {
            "type": "chat",
            "message": "I couldn't clearly parse the updates. Could you repeat which transaction to edit and what the new values should be?"
        }
    
    if not tx_id:
        return {
            "type": "chat",
            "message": "I couldn't confidently identify which transaction you want to update. Could you be more specific?"
        }
        
    matched_tx = next((tx for tx in recent if tx['id'] == tx_id), None)
    if not matched_tx:
        return {
            "type": "chat",
            "message": "I couldn't find a matching transaction."
        }
        
    # Merge updates
    updated_tx = dict(matched_tx)
    if data.get("amount") is not None: updated_tx["amount"] = data["amount"]
    if data.get("category"): updated_tx["category"] = data["category"]
    if data.get("date"): updated_tx["date"] = data["date"]
    if data.get("description"): updated_tx["description"] = data["description"]
    
    return {
        "type": "update_expense",
        "data": updated_tx,
        "message": "I've prepared the updates. Please review and confirm below:"
    }

def process_user_input(user_input, user_id, history=None):
    try:
        intent = detect_intent(user_input, history)
        if intent == "add_expense":
            return handle_add_expense(user_input, history)
        elif intent == "update_expense":
            return handle_update_expense(user_input, user_id, history)
        elif intent == "delete_expense":
            return handle_delete_expense(user_input, user_id, history)
        elif intent == "navigation":
            return handle_navigation(user_input, history)
        elif intent == "dashboard_query":
            return handle_dashboard_query(user_input, user_id, history)
        else:
            return handle_help(user_input, history)
    except Exception as e:
        return {
            "type": "error",
            "message": "I'm unable to reach the AI service right now. Please try again in a moment."
        }

def process_guest_input(user_input, history=None):
    client = get_groq_client()
    system_prompt = """
You are the Guest AI for Outflow, a personal finance app. You are a product and technology expert.
Your goal is to answer questions from unauthenticated visitors about Outflow's features, architecture, security, and AI stack.

Rules:
- NEVER attempt database operations.
- NEVER access or ask for personal financial data.
- Refuse any request to add, edit, delete, or list expenses. Politely redirect the user to sign up or use Demo Mode.
- Never leak internal secrets or API keys.
- Be concise, helpful, and professional.

App Knowledge:
- Architecture: Flask backend, PostgreSQL database, Vanilla JS/CSS frontend.
- AI Stack: Groq API with Llama 3.1 for intent parsing/chat, Whisper large v3 for voice transcription.
- Security: Password hashing, CSRF tokens, session-based auth.
- Features: Expense tracking, charts, demo mode, voice input, AI assistant.
"""
    messages = _build_messages(system_prompt, history, user_input)
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )
        return {
            "type": "chat",
            "message": response.choices[0].message.content
        }
    except Exception:
        return {
            "type": "error",
            "message": "I'm unable to reach the AI service right now. Please try again in a moment."
        }
