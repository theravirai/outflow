# Lessons Learned & Post-Mortem

## What does this component do?
This document acts as an engineering log of notable bugs, architectural hurdles, and the lessons learned while building Outflow. Documenting mistakes is critical for preventing regressions and onboarding new engineers.

## 1. The Global CSRF Interception Bug
*   **The Issue:** We implemented CSRF protection via an `@app.before_request` hook. State-mutating routes (like `POST /api/assistant/transcribe` for voice memos) required a token. However, when users tested the voice feature from the Landing Page (`/`), the request failed with a `400 Bad Request`.
*   **The Cause:** The Landing Page (`index.html`) did not inherit the `base.html` template where the `<meta name="csrf-token">` tag was injected. Because the Vanilla JS dynamically grabbed the token from the `<meta>` tag, the fetch payload was missing the token entirely.
*   **The Fix:** We ensured the `<meta>` tag injection via Jinja2's `@app.context_processor` was globally available across all layout bases, including the unauthenticated landing page.
*   **Lesson Learned:** Security features that rely on DOM elements (like `<meta>` tags or hidden inputs) must be implemented globally at the highest possible architectural layer. 

## 2. LLM Parsing Crashes (The Guardrails Pivot)
*   **The Issue:** Initially, the LLM extracted expense data and returned it to the Flask backend. The backend parsed this via a raw `json.loads(content)`. Occasionally, the Groq API would return a response formatted like: *"Sure, here is your expense! { ... }"*. This crashed the entire Flask thread with a `JSONDecodeError`.
*   **The Cause:** We overly trusted the LLM to adhere to the system prompt's instruction ("Return ONLY valid JSON").
*   **The Fix:** We implemented Phase 1 of our Guardrails plan. We integrated Pydantic to enforce strict typed schemas, and wrapped the `json.loads()` inside a `try/except Exception` block. If the JSON is malformed, we catch it gracefully and instruct the AI to reply to the user with a fallback request for clarification.
*   **Lesson Learned:** Never trust LLM output. Treat it exactly like user input from a public HTML form—sanitize, validate, and try/catch aggressively.

## 3. UI Bugs from Missing CSS Classes
*   **The Issue:** The AI Assistant generated an interactive "Confirm Delete" button, but it appeared as a completely unstyled, ugly default HTML button. Furthermore, hovering over the "Send" icon in the chat made it turn completely invisible.
*   **The Cause:** The JavaScript assigned `.btn-danger` to the delete button, but that class did not exist in our bespoke `style.css`. For the hover bug, `assistant.css` referenced `var(--accent-hover)`, which also hadn't been defined in the CSS variables.
*   **The Fix:** Added `.btn-danger` and `.btn-sm` to `style.css` for global reuse, and replaced the undefined variable with a CSS opacity fade (`opacity: 0.9`).
*   **Lesson Learned:** When building custom Vanilla CSS design systems, it is extremely easy for UI tokens to drift or be referenced before they exist. 

## 4. The Infinite Pagination Trap
*   **The Issue:** We needed to display hundreds of expenses. We considered building an "infinite scroll" utilizing an Intersection Observer in JS.
*   **The Decision:** We opted against it and implemented strict SaaS-style numbered pagination instead. Infinite scroll on mobile makes footer links inaccessible and breaks the "back button" browser expectation.
*   **Lesson Learned:** Boring, standard UX patterns (like numbered pagination via query parameters `?page=2`) are often vastly superior to technically complex "modern" patterns.
