# Spec: Dark Mode

## Overview
Outflow requires a high-fidelity visual dark theme that integrates seamlessly across all pages. As a modern personal finance tool, enabling a toggleable dark mode is crucial for enhanced accessibility, reduced eye strain in low-light environments, and a premium user experience. This feature detects system preferences (using `prefers-color-scheme`), allows users to toggle the theme via a persistent navbar button, stores the preference in the browser's local storage to prevent visual flashes (FOUC) on load, and adapts all color variables (including category breakdowns and cards).

## Depends on
- **Step 04 — Profile page design**: Profile page structure, CSS custom properties, and general styles.

## Routes
No new routes.

## Database changes
No database changes.

## Templates
- **Create:** None.
- **Modify:**
  - `templates/base.html`:
    - Inject a tiny inline `<script>` in the `<head>` that immediately checks `localStorage` and system preference to apply `data-theme="dark"` to the `<html>` element before the browser renders the page, preventing theme flashing (FOUC).
    - Add a toggle button inside the navbar (`.nav-links`) containing a Lucide icon (`moon` or `sun` depending on current active state).

## Files to change
- `templates/base.html`: Add inline CSS theme pre-loader script and the theme toggle button.
- `static/css/style.css`: Add styling for the theme toggle button and define `[data-theme="dark"]` CSS variables override block.
- `static/css/profile.css`: Ensure dark mode adapts the category progress bars and other custom components cleanly.
- `static/js/main.js`: Implement the theme toggle event listener, local storage persistence, and Lucide icon swapping.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- The dark mode styling must be implemented by overriding CSS custom properties in `static/css/style.css` inside a `[data-theme="dark"]` selector block.
- Refactor any hardcoded colors in page-specific style sheets to use CSS variables if they cause readability issues in dark mode.
- The inline script in `<head>` must remain small and contain no external dependencies.
- Lucide icons should be re-rendered via `lucide.createIcons()` when the icon is dynamically changed.

## Definition of done
- [ ] A theme toggle button is present in the navbar on all pages (desktop and mobile responsive layout).
- [ ] Clicking the toggle button changes the theme dynamically from Light to Dark, and vice versa.
- [ ] The theme preference (`'dark'` or `'light'`) is persisted in the browser's `localStorage`.
- [ ] If no preference is stored in `localStorage`, the site automatically defaults to the system theme (`prefers-color-scheme: dark`).
- [ ] Loading any page directly (e.g. refresh, deep link) while in Dark Mode does not produce a "flash of light theme" (FOUC).
- [ ] The Lucide icon dynamically toggles: shows a moon icon in light mode, and a sun icon in dark mode.
- [ ] All pages (Landing, Login, Register, Profile/Dashboard, Add/Edit Expense, Privacy, Terms) render beautifully in Dark Mode, with no unreadable text or broken color contrasts.
- [ ] All pre-existing unit and integration tests continue to pass.
- [ ] Outflow runs correctly on port 5001.
