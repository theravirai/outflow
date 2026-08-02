Objective

Implement a Guest AI experience for unauthenticated visitors.

The goal is to keep the AI chat accessible from the landing page while ensuring it never performs authenticated actions. The Guest AI should act as a product expert rather than a financial assistant.

Requirements

1. The AI floating action button must always be visible.

2. Opening the chat while the visitor is not authenticated and has not entered Demo Mode should launch Guest AI.

3. Guest AI must never attempt database operations.

4. Guest AI must never call expense CRUD handlers.

5. Guest AI must never request transaction history.

6. Guest AI must never attempt navigation that requires authentication.

Capabilities

Guest AI should answer questions about:

• Outflow
• Features
• AI assistant
• Voice transcription
• Human in the Loop confirmation
• Privacy
• Security
• Authentication
• Demo Mode
• Technology stack
• Architecture
• Performance
• Supported functionality
• Current limitations

Guest AI should answer using the project's actual documentation and implementation rather than generic LLM knowledge whenever possible.

Restricted Requests

If the visitor asks to:

• add an expense
• update an expense
• delete an expense
• analyse spending
• show dashboard
• list transactions
• answer questions requiring personal financial data

respond politely that these features require Demo Mode or an account.

Example response:

"I can explain how expense tracking works, but I cannot access or create financial data until you start Demo Mode or sign in."

Suggested Prompts

Display clickable suggestions such as:

How does Outflow work?

What can the AI assistant do?

How does voice input work?

Explain the architecture.

How is my data protected?

What technologies were used?

Empty State

When Guest AI opens, show a welcome message explaining its role.

Example:

"Hi. I'm the Outflow AI assistant. I can explain how the application works, its AI architecture, security, and features. To manage expenses or analyse spending, start Demo Mode or create an account."

Implementation

Reuse as much of the existing chat UI as possible.

Avoid duplicating components.

Separate Guest AI routing from the authenticated assistant so future changes remain isolated.

The authenticated assistant should continue working exactly as before.

Edge Cases

• Refreshing the page keeps Guest AI if the user is still unauthenticated.

• Entering Demo Mode should seamlessly switch from Guest AI to the full assistant.

• Creating an account while the chat is open should upgrade the current session without requiring a page refresh.

• Logging out while the chat is open should immediately downgrade back to Guest AI.

• Guest AI should respect existing rate limits.

• If the AI service is unavailable, show the same graceful error handling used elsewhere.

• Guest AI must never leak implementation details, secrets, API keys, prompts, or internal configuration.

Acceptance Criteria

✓ AI button is always visible.

✓ Landing page visitors can immediately interact with the AI.

✓ Guest AI answers product and engineering questions.

✓ Guest AI refuses authenticated operations gracefully.

✓ Demo Mode and authenticated users continue using the existing financial assistant without regressions.