# AI Assistant Implementation Plan

## 1. Overview
Implement a floating AI Assistant for Outflow to help users manage their personal finances through natural language. The assistant will handle expense tracking, answer financial queries, assist with navigation, and provide application support. It will use the existing Groq API (llama-3.1-8b-instant).

## 2. Frontend Implementation (UI & Chat Panel)

### 2.1 Floating Action Button (FAB)
- **Location:** Fixed in bottom-right corner of authenticated pages (added to `base.html` so it appears everywhere).
- **Design:** Circular, modern, minimal, using an AI sparkle/assistant icon (Lucide).
- **Animation:** Small notification pulse animation on the first visit.
- **Accessibility:** Keyboard navigable, WCAG AA compliant.

### 2.2 Chat Panel Interface
- **Trigger:** Clicking the FAB slides up the panel.
- **Header:** Title "✨ Ask Outflow" and subtitle "Your personal finance assistant".
- **Interaction Area:** Auto-scrolling conversation view.
- **Input Area:** Text input box, Voice input button (reusing existing `MediaRecorder`/Whisper pipeline), and Send button.
- **States:** Typing indicator, timestamps for messages, disable input while waiting.
- **Suggested Prompts:** Initial quick-action bubbles (e.g., "Add €25 spent on groceries", "How much did I spend this month?") that disappear after the first user message.
- **Polish:** Animate opening/closing, close on Escape or click outside, preserve chat history during the session (via `sessionStorage`), fully responsive/mobile-friendly.

## 3. Backend Implementation (AI Service Layer)

### 3.1 Architecture
- Create a dedicated service file: `services/ai_assistant.py` to separate AI logic from Flask routes.
- **Flask Route:** Add `POST /api/assistant` in `app.py`.
- **Components in `ai_assistant.py`:**
  - `detect_intent(user_input)`: Groq call to classify into one of the 4 supported intents.
  - `handle_add_expense(user_input)`: Extract amount, category, date, description. Return structured JSON for a confirmation card.
  - `handle_dashboard_query(user_input, user_id)`: Translate question to DB query, fetch aggregates, pass to Groq for natural response.
  - `handle_navigation(user_input)`: Map to route URLs.
  - `handle_help(user_input)`: Match against predefined app knowledge (no Groq call needed if exact match).

### 3.2 Supported Intents
1. **Add Expense:** Extracts data -> Frontend renders a confirmation card -> User confirms -> Frontend POSTs to standard `/expenses/add` endpoint. Never inserts directly.
2. **Dashboard Questions:** Backend queries PostgreSQL for aggregates (e.g., sum per category, total spent this month) -> Sends summary to Groq -> Returns concise, conversational response (max 3 paragraphs).
3. **Navigation:** Returns a specific JSON action `{ "action": "navigate", "url": "/profile" }`.
4. **Help:** Uses predefined knowledge (e.g., Demo Mode explanation).

### 3.3 Security & Error Handling
- **Security:** CSRF protection on the API endpoint, session validation, sanitize inputs, strict JSON schema validation for Groq responses.
- **Error Handling:** Graceful fallback message ("I'm unable to reach the AI service right now. Please try again in a moment.") on Groq timeout or failure. No stack traces exposed.

## 4. Execution Steps

1. **Step 1: UI & Styling Foundation**
   - Create the FAB and sliding panel HTML in `base.html` (or a partial included in `base.html`).
   - Write the CSS (`assistant.css`) for animations, layout, and responsive design.
2. **Step 2: Frontend Logic & State**
   - Write `assistant.js` to handle opening/closing, initial suggestions, voice recording integration, rendering messages, and `sessionStorage` history.
3. **Step 3: Backend AI Service Layer**
   - Create `services/ai_assistant.py`.
   - Implement intent detection logic.
   - Implement handlers for Navigation and Help (the simpler intents).
4. **Step 4: Expense & Dashboard Intents**
   - Implement the "Add Expense" extraction logic and format the UI confirmation card response.
   - Implement the "Dashboard Questions" logic with database aggregate fetching.
5. **Step 5: API Endpoint Integration**
   - Create the Flask route in `app.py`.
   - Connect the frontend `fetch` calls to the new endpoint.
6. **Step 6: Review & Polish**
   - Test UI states (typing, error, confirmations).
   - Ensure WCAG AA compliance and keyboard navigation.
   - Test voice input functionality.
