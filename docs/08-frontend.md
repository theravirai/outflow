# Frontend Architecture

## What does this component do?
This document explains the client-side technology stack of Outflow. It outlines how we achieve a fast, reactive user interface without relying on heavy JavaScript frameworks like React, Vue, or Angular.

## Core Technologies
*   **HTML:** Server-Side Rendered (SSR) via Jinja2 (`templates/`).
*   **CSS:** Vanilla CSS utilizing a custom CSS-variable design system (`static/css/`).
*   **JavaScript:** Vanilla JS (`static/js/`) explicitly constrained to handling localized dynamic states (like AI chat panels or Voice recording).

## Why Vanilla?
*   **Performance:** Sending pre-rendered HTML down the wire results in an exceptionally fast First Contentful Paint (FCP). The browser does not have to download, parse, and execute a massive JavaScript bundle before rendering the UI.
*   **Simplicity:** No build steps (Webpack/Vite), no `package.json`, and no state synchronization bugs between the client and server. The server is the single source of truth.

## CSS Design System
We opted out of frameworks like Bootstrap or Tailwind in favor of a bespoke CSS system (`style.css`).
*   **Tokenization:** All colors, spacing, and typography are managed via CSS variables (e.g., `var(--accent)`, `var(--ink)`, `var(--paper)`).
*   **Component Classes:** Buttons, cards, and form inputs use standardized classes (`.btn-primary`, `.card`) ensuring the application maintains a cohesive "fintech" aesthetic globally.

## Interactive Components
While most of the app is SSR, certain features demand client-side interactivity to feel modern.
*   **AJAX Filtering:** The Category Breakdown widget allows users to click a category and dynamically filter the Recent Expenses table. This is handled by `fetch()` pulling data from the server and updating the DOM, avoiding a jarring full-page reload.
*   **AI Chat Panel:** The floating AI assistant (`assistant.js`) manages its own localized DOM state, appending message bubbles dynamically and rendering the JSON payloads it receives from the backend into interactive Confirmation Cards.

## Limitations
*   **DOM Manipulation Complexity:** As features grow (e.g., adding dynamic drag-and-drop charting), manually querying and updating the DOM (`document.getElementById()`) becomes increasingly verbose and error-prone compared to a declarative framework like React.
