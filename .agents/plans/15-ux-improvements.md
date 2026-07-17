# Plan 15: UX & Design System Improvements

## Objective
Elevate the user experience of Outflow to feel like a premium, modern fintech product. This plan explicitly utilizes the intelligence and methodology from the [UI/UX Pro Max Skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) to generate and apply a highly tailored, professional Design System across all implemented pages and upcoming features.

## Design Methodology: UI/UX Pro Max Skill Integration
We will use the UI/UX Pro Max reasoning engine logic to define the exact aesthetics before implementing CSS changes:
1. **Multi-Domain Search & Reasoning:**
   - **Target / Product Type:** Personal Expense Tracker / Fintech
   - **Style Recommendation:** Soft UI Evolution / Premium Banking
   - **Color Palette:** Muted semantic colors (emerald for income, soft rose for expense) with a calming neutral background.
   - **Typography Pairing:** System fonts (or Inter) combined with `tabular-nums` for flawless financial data readability.
   - **Key Effects:** Soft shadows + Smooth transitions (200-300ms) + Gentle hover states.
2. **Anti-patterns to Avoid (Per the skill's rules):** 
   - Bright neon colors, harsh snapping animations, heavy/dark drop shadows, and default browser UI elements.
3. **Pre-delivery Checklist (Per the skill's output):**
   - [ ] No emojis as icons (use Lucide SVG).
   - [ ] `cursor-pointer` on all clickable elements.
   - [ ] Smooth transitions on hover states (150-300ms).
   - [ ] WCAG AA text contrast minimum for Light and Dark modes.
   - [ ] Focus states visible for keyboard navigation.

## Scope of Work

### Phase 1: Polish Authentication & Landing Experience
- Apply the AI-generated Design System colors and typography to `register.html` and `login.html`.
- **Forms & Error States:** Implement soft red warning banners and real-time interactive validation without jarring layout shifts.
- **Micro-animations:** Add gentle hover states (e.g., subtle `box-shadow` or slight `scale` transforms) to primary CTA buttons.

### Phase 2: Prepare Financial Data Display Rules
- **Typography Engine:** Implement `font-variant-numeric: tabular-nums;` in `style.css` for all Euro amounts as dictated by the typography rules.
- **Semantic Color Palette:** Define exact, muted hex codes in CSS variables derived from the Pro Max color selection process.

### Phase 3: Optimize Interactions & Modals
- **Modals vs. Pages:** Build a sleek, glass-like modal overlay system (consistent with the "Soft UI" style recommendation) for quick actions (like Step 7: Add Expense) to keep the user in context.
- **Transitions:** Standardize smooth transitions (e.g., `transition: all 0.2s ease-in-out;`) as required by the skill's Key Effects rules.

### Phase 4: Dark Mode & Accessibility Review
- **Focus Rings & Contrast:** Ensure all interactive elements have visible focus rings and verify that text contrast passes the UI/UX Pro Max Skill's pre-delivery checklist (WCAG AA).

## Constraints & Rules
- **Vanilla Tech Stack:** Use ONLY Vanilla CSS and Vanilla JavaScript to implement the design system. No external CSS frameworks.
- **Currency:** Ensure all added placeholder amounts explicitly use the Euro symbol (€).
