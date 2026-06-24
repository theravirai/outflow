# Implementation Plan: Profile Page Design

This plan details the implementation for **Step 04: Profile Page Design**. The goal is to replace the `/profile` stub route with a high-fidelity, responsive profile page containing hardcoded data to isolate and validate the UI layout.

## Goal

Create a premium, modern fintech dashboard style profile page featuring:
1. **User info card** with user avatar initials, full name, email address, and membership date.
2. **Summary stats row** showing total spent, transaction count, and the top category.
3. **Category breakdown section** showing spent totals by category with styled progress-bar rows.
4. **Recent transaction history table** with details of recent mock expenses, category badges, and clean formatting.
5. **Navbar enhancements** to display the user's name next to the Sign out button when authenticated.

---

## User Review Required

- **Navbar modification**: Update [base.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/base.html) to conditionally display the logged-in user's name.
- **Session management**: Modify the `/login` route to store the user's name in `session["user_name"]`.
- **Lucide icons integration**: Load the Lucide CDN in [base.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/base.html) to enable lightweight icons.

---

## Open Questions

None.

---

## Proposed Changes

### 1. Backend Modifications

#### [MODIFY] [app.py](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/app.py)
- **`login` route**:
  - Store the user's name in the session when credentials are verified.
  ```python
  session["user_id"] = user["id"]
  session["user_name"] = user["name"]
  ```
- **`profile` route**:
  - Remove the placeholder response.
  - Implement an authentication guard checking for `session.get("user_id")`. If missing, redirect to `/login`.
  - Construct hardcoded Python dicts and lists to represent:
    - `user_info`: Avatar initials, name, email, member-since date.
    - `summary_stats`: Total spent, transaction count, top category.
    - `recent_expenses`: List of 5 recent expenses (date, description, category, amount in Euro).
    - `category_breakdown`: List of category objects (category name, amount spent, percentage share, css indicator class).
  - Return `render_template("profile.html", ...)` passing these hardcoded data sets.

### 2. Frontend Templates

#### [MODIFY] [base.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/base.html)
- Include the Lucide CDN script tag before the closing `</body>` tag (e.g. `https://unpkg.com/lucide@latest`).
- Add a script call to initialize Lucide icons: `lucide.createIcons();`.
- Update the navigation section to show the logged-in username if `session.get('user_name')` exists:
  ```html
  <div class="nav-links">
      {% if session.get('user_id') %}
          <span class="nav-user-greeting">
              <i data-lucide="user" class="nav-user-icon"></i>
              {{ session.get('user_name') }}
          </span>
          <a href="{{ url_for('logout') }}" class="nav-signout-btn">Sign out</a>
      {% else %}
          <a href="{{ url_for('login') }}">Sign in</a>
          <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
      {% endif %}
  </div>
  ```

#### [CREATE] [profile.html](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/templates/profile.html)
- Extend `base.html`.
- Add page-specific stylesheet `static/css/profile.css` inside `{% block head %}`.
- Build the profile dashboard layout within `{% block content %}`:
  - **Main Container**: `.profile-container` (two-column layout on desktop: sidebar + main dashboard).
  - **Sidebar**:
    - **User Card**: Show an avatar circle `.avatar-circle` containing initials, user's name, email, and member-since text. Includes a settings icon or link.
    - **Category Breakdown Card**: List breakdown rows showing the category title, amount (`€X.XX`), and a track bar representing the percentage share.
  - **Main Dashboard**:
    - **Stats Grid**: Three cards showing key statistics:
      - Total Spent (Euro currency, formatted with class `.tabular-nums`).
      - Transaction Count.
      - Top Category.
    - **Transactions History Card**:
      - Table layout displaying Date, Description, Category (styled as color-coded badges), and Amount.
      - Align text properly: dates and amounts should align right or center appropriately.
      - Category badges should only use CSS classes, never inline style colors.
      - Currency must be Euros (`€`).

### 3. Frontend Styles

#### [CREATE] [profile.css](file:///Volumes/BrainStorm/Github/Agentic%20AI/expense-tracker/static/css/profile.css)
- Implement a responsive grid layout using CSS custom variables from `style.css` (e.g., `--paper-card`, `--border`, `--ink`, `--ink-soft`, `--ink-muted`).
- Define the following rules:
  - **Grid Layout**:
    - `.profile-container` utilizes `display: grid` with `grid-template-columns: 320px 1fr` and `gap: 2rem`. On screen sizes below `900px`, stack columns vertically (`grid-template-columns: 1fr`).
  - **Card Component styling**:
    - `.profile-card` inherits standard layout patterns: white background, border, subtle box shadow, and `var(--radius-md)`.
  - **User Avatar**:
    - `.avatar-circle`: Circular shape (e.g., width/height of `72px`), centered text, styled with `--accent-light` background and `--accent` text.
  - **Stats Card Layout**:
    - `.stats-grid` uses CSS Grid or Flexbox to display the 3 stats cards side-by-side with equal spacing.
    - Large typography for values (e.g., `font-size: 1.75rem`, `font-family: var(--font-display)`).
  - **Category Breakdown Fills**:
    - Style custom progress tracks: `.progress-track` and `.progress-fill`.
    - Distinct fill classes (e.g., `.bar-food { background-color: var(--accent); }`, `.bar-utilities { background-color: var(--accent-2); }`, etc.).
  - **Table Layout**:
    - Horizontally scrollable table container `.table-responsive`.
    - Tabular font variants for numeric alignment (`font-variant-numeric: tabular-nums`).
    - Zebra striping or clean border divider lines.
    - Category Badges:
      - `.badge`: Inline-block, rounded pill, font size `0.75rem`, font weight `600`.
      - Specific classes: `.badge-food`, `.badge-utilities`, `.badge-shopping`, `.badge-transport` with harmonious light background colors and dark text colors.

---

## Verification Plan

### Manual Verification Steps
1. **Unauthenticated Redirect**:
   - Access `/profile` without logging in.
   - Verify it successfully redirects to `/login`.
2. **Authenticated Access**:
   - Log in using `demo@spendly.com` / `demo123`.
   - Verify it routes successfully to `/profile` with HTTP status code 200.
3. **Navbar State Verification**:
   - Confirm that the navbar displays `Demo User` with a user icon next to "Sign out".
4. **Layout Verification**:
   - Verify that all four components render correctly:
     - User Card (Avatar initials: `DU` or `JD`, member since date shown).
     - Summary Stats (3 panels showing € values, counts, and categories).
     - Category Breakdown (Progress bars showing percentage fills).
     - Transactions History Table (At least 3 rows visible).
   - Resize the browser window to verify the columns stack correctly on tablet and mobile displays.
5. **No Hex Colors in HTML**:
   - Inspect page source or search files to ensure absolutely no inline hex values (e.g. `#1a472a`) exist in `profile.html`.
6. **Euros Currency Check**:
   - Verify all money fields display with the Euro sign (`€`) and not rupees (`₹`) or dollars (`$`).
