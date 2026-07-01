# Plan - Dark Mode

This plan details the steps to implement a high-fidelity visual Dark Mode for Outflow.

## Proposed Changes

### 1. Stylesheets & Design System

#### [MODIFY] [style.css](/outflow/static/css/style.css)
- Inside the `:root` block, add new CSS variables for category backgrounds to avoid hardcoded hex colors:
  - `--color-shopping-light`: `#eaf1f7` (light blue)
  - `--color-transport-light`: `#f3f0f7` (light purple)
  - `--color-travel-light`: `#e8f5e9` (light green)
  - `--color-entertainment-light`: `#fdf3e3` (light amber)
  - `--info-light`: `#e6f0fa`
  - `--info`: `#2b6cb0`
- Define a `[data-theme="dark"]` selector block to override the light theme variables with high-contrast, accessible dark palette values:
  - `--ink`: `#f7f6f3` (soft white)
  - `--ink-soft`: `#eeebe4` (off-white)
  - `--ink-muted`: `#a0a0a0` (medium gray)
  - `--ink-faint`: `#6b6b6b` (dark gray)
  - `--paper`: `#121212` (deep charcoal background)
  - `--paper-warm`: `#1a1a19`
  - `--paper-card`: `#1d1d1b` (slightly lighter charcoal for card elevation elevation)
  - `--accent`: `#3da362` (brighter green for dark mode contrast)
  - `--accent-light`: `#162c1e` (deep green)
  - `--accent-2`: `#e59a3c` (brighter amber)
  - `--accent-2-light`: `#33220f` (deep amber)
  - `--danger`: `#e74c3c` (brighter red)
  - `--danger-light`: `#3a1e1b` (deep red)
  - `--danger-border`: `#5b2722`
  - `--border`: `#2d2d2d` (dark borders)
  - `--border-soft`: `#232323`
  - `--info`: `#63b3ed` (light blue)
  - `--info-light`: `#1a2d42` (deep blue)
  - Category variables overrides:
    - `--color-shopping`: `#75a3d1`
    - `--color-shopping-light`: `#1c2d3d`
    - `--color-transport`: `#af94c7`
    - `--color-transport-light`: `#281b33`
    - `--color-travel`: `#48c0b2`
    - `--color-travel-light`: `#12302a`
    - `--color-entertainment`: `#f57fa3`
    - `--color-entertainment-light`: `#3a1b24`
    - `--color-other`: `#b3b3b3`
- Add styling for the theme toggle button:
  - `.theme-toggle-btn`: transparent, borderless, circular hover effect, aligned within `.nav-links`.
  - Ensure the toggle icon colors and spacing match the rest of the navigation options.

#### [MODIFY] [profile.css](/outflow/static/css/profile.css)
- Refactor category badge background and text colors to use the new CSS variables instead of hardcoded hex values:
  - `.badge-transport`: use `background-color: var(--color-transport-light)` and `color: var(--color-transport)`.
  - `.badge-shopping`: use `background-color: var(--color-shopping-light)` and `color: var(--color-shopping)`.
  - `.badge-travel`: use `background-color: var(--color-travel-light)` and `color: var(--color-travel)`.
  - `.badge-entertainment`: use `background-color: var(--color-entertainment-light)` and `color: var(--color-entertainment)`.
  - `.text-info`: use `background-color: var(--info-light)` and `color: var(--info)`.
- Ensure date picker inputs on the profile page use `var(--paper-card)` background, `var(--ink)` color, and `var(--border)` border to render correctly.

#### [MODIFY] [landing.css](/outflow/static/css/landing.css)
- Refactor hardcoded colors to use CSS variables:
  - Replace `#111827` (hero title, buttons) with `var(--ink)`.
  - Replace `#ffffff` (stat cards background, frame header) with `var(--paper-card)`.
  - Replace `#f3f4f6` and `#e5e7eb` (borders, track backgrounds) with `var(--border)` and `var(--border-soft)`.
  - Replace `#f9fafb` (preview frame content background) with `var(--paper)`.
  - Replace `#6b7280` (labels) with `var(--ink-muted)`.
  - Replace `#4b5563` (hero subtitle) with `var(--ink-soft)`.
  - Ensure teal accents on the landing page remain readable (optionally use variables if color adaptation is preferred in dark mode).

### 2. Base Template

#### [MODIFY] [base.html](/outflow/templates/base.html)
- Inject a blocking, inline `<script>` in the `<head>` to immediately read the theme from `localStorage` (or match media preferences if none exists) and set the `data-theme="dark"` attribute on `document.documentElement` *before* the body elements start loading. This prevents any layout flashes (FOUC).
- Place a `<button id="theme-toggle">` element inside the navbar (`.nav-links`) as the first child, containing a default `<i data-lucide="moon"></i>` or `<i data-lucide="sun"></i>` icon.

### 3. JavaScript Theme Toggle Behavior

#### [MODIFY] [main.js](/outflow/static/js/main.js)
- Implement `DOMContentLoaded` event listener logic:
  - Retrieve the theme toggle button element.
  - Determine initial icon based on whether `document.documentElement` has `data-theme="dark"` attribute.
  - Update the icon element's `data-lucide` attribute (`sun` if dark, `moon` if light).
  - Call `lucide.createIcons()` to render the icon.
  - Attach a click listener to the toggle button:
    - Toggle `data-theme="dark"` attribute on `document.documentElement`.
    - Retrieve the new state (`'dark'` or `'light'`).
    - Save the new state to `localStorage.setItem('theme', state)`.
    - Update `data-lucide` attribute of the icon element and call `lucide.createIcons()` to swap it visually.

## Verification Plan

### Manual Verification
1. Verify the theme toggle button is present in the navbar across all pages.
2. Click the button to toggle between light and dark themes. Ensure the page immediately switches themes without lag or broken styling.
3. Verify that the Lucide icon dynamically changes (sun in dark theme, moon in light theme).
4. Reload the page while in dark mode. Confirm there is no "flash of light theme" (FOUC) during reload.
5. In an incognito window, verify that the theme defaults to the OS system settings (`prefers-color-scheme`).
6. Inspect all pages in Dark Mode:
   - Landing page (Hero section, preview mockup, buttons).
   - Sign In and Register pages (form containers, input fields, error banners).
   - Profile page (sidebar user details, category breakdown tracks and badges, summary stats cards, recent expenses table, filter presets, date input fields).
   - Add/Edit Expense pages (form card, currency overlay, input fields, cancel/submit buttons).
   - Privacy and Terms pages.

### Automated Verification
1. Run `pytest` to verify that existing authentication and expense management flows continue to function without errors.
