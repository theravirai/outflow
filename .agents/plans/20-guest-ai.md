# Implementation Plan: Guest AI

This plan outlines the steps required to implement a Guest AI experience for unauthenticated visitors, keeping the AI chat accessible from the landing page as a product expert while restricting financial actions.

## Goal
To allow unauthenticated visitors to interact with a limited version of the Outflow AI assistant. The Guest AI will serve as a product and technology expert to answer questions about the app's architecture and capabilities without ever touching the database or user financial data.

## Proposed Changes

### 1. Backend Logic & API 

#### [MODIFY] `services/ai_assistant.py`
- Add a new function `process_guest_input(text)` designed specifically for unauthenticated visitors.
- **System Prompt**: Design a strict prompt for the Guest AI defining its persona as a product expert. Explicitly instruct it to:
  - Provide information about Outflow's features, architecture, security, and AI stack.
  - Refuse any request to add, edit, delete, or list expenses, redirecting the user to sign up or use Demo Mode.
  - Avoid leaking internal secrets or API keys.
- Do not provide the Guest AI with any tool-calling capabilities (no database query functions). It should only return standard conversational responses.

#### [MODIFY] `app.py`
- Update the `/api/assistant` route. Instead of returning `401 Unauthorized` when `session.get("user_id")` is missing, gracefully pass the request to `process_guest_input(text)` from `services/ai_assistant.py`.
- (The existing `@limiter.limit("20 per minute")` will naturally apply to the guest's IP address, satisfying rate limit requirements).
- Pass a boolean flag `is_authenticated` to the templates (e.g., in `base.html` context processor or directly) to allow the frontend to know which state the chat should be in.

### 2. Frontend UI & Javascript

#### [MODIFY] `templates/base.html`
- Ensure the floating AI chat button HTML is rendered regardless of authentication status (currently it might be wrapped in an `if session.get('user_id')` check).
- Pass the authentication status to the Javascript layer by injecting a `data-authenticated="true/false"` attribute on the chat container or via a `<script>` variable.

#### [MODIFY] Javascript (Chat logic)
- **Empty State**: Modify the initial welcome message rendering.
  - If authenticated: keep the current financial assistant welcome.
  - If guest: Display the new welcome: *"Hi. I'm the Outflow AI assistant. I can explain how the application works, its AI architecture, security, and features. To manage expenses or analyse spending, start Demo Mode or create an account."*
- **Suggested Prompts**: Update the clickable suggestions based on auth state.
  - If guest, show: "How does Outflow work?", "What can the AI assistant do?", "How does voice input work?", "Explain the architecture.", etc.
- **State Transitions**: Since the `/api/assistant` route dynamically handles auth state based on the backend session, upgrading or downgrading between Guest and Full AI works seamlessly. When the page is reloaded after logging in/out, the UI will fetch the new correct empty state and prompts.

## Verification Plan

### Manual Verification
1. **Unauthenticated Access**: Visit the landing page as an anonymous user and confirm the AI floating button is visible.
2. **Welcome & Prompts**: Open the chat and verify the correct Guest welcome message and technical suggested prompts are displayed.
3. **Information Retrieval**: Ask "What technologies are used in Outflow?" and verify the AI accurately describes the Flask + PostgreSQL + Llama 3.1 stack.
4. **Boundary Testing**: Ask "Add a $50 expense for food" and verify the AI politely refuses and prompts to enter Demo Mode or create an account.
5. **State Transition**: Click "Try Demo". Once logged into Demo Mode, open the chat and verify it has upgraded to the full financial assistant (different welcome message, ability to add expenses).
6. **Graceful Downgrade**: Log out. Re-open the chat and verify it has reverted to the Guest AI persona.

### Automated Verification
1. Run the test suite (`pytest`) to ensure no existing authenticated features or AI endpoints have regressed.
