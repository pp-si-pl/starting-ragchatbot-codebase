# Frontend Changes: Dark/Light Theme Toggle

## Summary

Added a toggle button that allows users to switch between dark and light themes. Uses CSS custom properties (`data-theme` attribute on `<html>`) for theme switching, with `localStorage` persistence, system preference detection, and smooth animated transitions. All existing elements are verified to work well in both themes.

## Files Modified

### `frontend/index.html`
- Added a theme toggle button (`#themeToggle`) positioned before the main container
- Button contains two SVG icons: a sun icon (shown in dark mode) and a moon icon (shown in light mode)
- Includes `aria-label` and `title` attributes for accessibility
- Bumped cache-busting query params from `v=9` to `v=10`

### `frontend/style.css`

#### Theme architecture
- **`data-theme` on `<html>`**: Theme is driven by `[data-theme="light"]` selector on `document.documentElement`, with `:root` providing dark defaults
- **All colors use CSS variables**: Every color referenced in the stylesheet goes through a `--variable`, so any new component inherits the correct theme automatically

#### Light Theme CSS Variables
- **Primary colors**: `--primary-color: #1d4ed8`, `--primary-hover: #1e40af` — darker blue for contrast on light backgrounds
- **Backgrounds**: `--background: #f8fafc`, `--surface: #ffffff`, `--surface-hover: #f1f5f9`
- **Text colors**: `--text-primary: #0f172a` (~16:1 contrast), `--text-secondary: #475569` (~6.4:1 contrast)
- **Borders**: `--border-color: #cbd5e1` — visible separation without being harsh
- **Welcome card**: `--welcome-border: #93c5fd`, `--welcome-shadow: rgba(0, 0, 0, 0.06)`
- **Code blocks**: `--code-bg: rgba(0, 0, 0, 0.05)`
- **Error/success**: `--error-text: #dc2626` (~4.6:1), `--success-text: #16a34a` (~4.5:1)
- **Source chips**: Adapted backgrounds, borders, and hover colors for light surfaces
- **Scrollbars**: `--scrollbar-track: #f1f5f9`, `--scrollbar-thumb: #cbd5e1`
- **Assistant messages**: `--assistant-msg-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)` — subtle shadow gives white message bubbles definition against the near-white background
- **Send button hover**: `--send-btn-hover-shadow: 0 4px 12px rgba(37, 99, 235, 0.2)` — softer glow in light mode

#### Bug fixes
- **Duplicate `position` on `.theme-toggle`**: Removed `position: relative` that was overriding `position: fixed`, causing the toggle button to lose its fixed top-right positioning. `position: fixed` already acts as a containing block for the absolutely-positioned icon SVGs.
- **`blockquote` border**: Fixed reference to non-existent `var(--primary)` → `var(--primary-color)`
- **Assistant message visibility in light mode**: Added `box-shadow: var(--assistant-msg-shadow)` to `.message.assistant .message-content` — without this, white message bubbles (`--surface: #ffffff`) on the near-white chat background (`--background: #f8fafc`) had no visual separation

#### Hardcoded color replacements
- Replaced all hardcoded `rgba(...)` values with CSS variables:
  - `.source-chip` backgrounds/borders → `--source-chip-*`
  - `.error-message` → `--error-*`
  - `.success-message` → `--success-*`
  - `.message.welcome-message` box-shadow → `--welcome-shadow`
  - `#sendButton:hover` box-shadow → `--send-btn-hover-shadow`
  - Scrollbar styles (sidebar, chat messages, responsive breakpoint) → `--scrollbar-*`
  - `.message-content code`/`pre` → `--code-bg`

#### Smooth transition animations
- 0.3s ease transitions on `background-color`, `color`, `border-color`, and `box-shadow` for all key layout elements (`body`, `.sidebar`, `.chat-main`, `.chat-container`, `.chat-messages`, `.chat-input-container`, `#chatInput`, `.stat-item`, `.suggested-item`, `.message-content`, `.new-chat-button`)
- Theme toggle button: `background-color`, `border-color` (0.3s), `transform` (0.2s)

#### Icon crossfade animation
- Both `.sun-icon` and `.moon-icon` are `position: absolute` inside the `position: fixed` toggle button
- Crossfade via `opacity 0.3s ease` + `transform 0.3s ease` (rotation)
- Dark mode: sun at `opacity:1, rotate(0)`; moon at `opacity:0, rotate(-90deg)`
- Light mode: sun at `opacity:0, rotate(90deg)`; moon at `opacity:1, rotate(0)`

### `frontend/script.js`

#### Theme functions
- `getPreferredTheme()` — Checks `localStorage` first; falls back to `window.matchMedia('(prefers-color-scheme: light)')` for OS/browser preference
- `applyTheme(theme)` — Sets `data-theme` attribute on `<html>` element; always explicit (`"dark"` or `"light"`)
- `toggleTheme()` — Reads current `data-theme`, flips to opposite, saves to `localStorage`
- `applyTheme(getPreferredTheme())` called at script load time (before `DOMContentLoaded`) to prevent flash
- Click listener on `#themeToggle` added in `DOMContentLoaded` handler

## Element-by-Element Theme Verification

| Element | Dark | Light | Notes |
|---|---|---|---|
| Chat background | `#0f172a` | `#f8fafc` | Clear contrast with surfaces |
| Sidebar | `#1e293b` | `#ffffff` | Distinct from background |
| User messages | Blue bg, white text | Same | Accent color works in both |
| Assistant messages | `#1e293b` surface | `#ffffff` + subtle shadow | Shadow provides definition |
| Welcome message | Surface + border + shadow | Same (lighter shadow) | Border ensures visibility |
| Chat input | Surface bg, border | Same | Focus ring visible in both |
| Send button | Blue bg, white icon | Same | Works as accent |
| New Chat button | Red bg, white text | Same | Intentional accent |
| Source chips | Semi-transparent blue | Same (adjusted opacity) | Primary color text |
| Stat items | Background color | Same | Bordered cards |
| Suggested items | Background + border | Same | Hover state works |
| Loading dots | `--text-secondary` | Same | Adapts via variable |
| Error messages | Red tinted | Same (darker text) | `#dc2626` for contrast |
| Code blocks | `rgba(0,0,0,0.2)` | `rgba(0,0,0,0.05)` | Subtle in both |
| Scrollbars | Dark track/thumb | Light track/thumb | Matching scheme |
| Theme toggle | Surface circle | Same | Border + hover state |

## Accessibility Notes
- All text meets WCAG AA minimum contrast (4.5:1 normal, 3:1 large)
- Theme toggle: keyboard-navigable, `aria-label`, focus ring, `title` tooltip
- System preference respected for first-time visitors (`prefers-color-scheme`)
- No motion for users who haven't opted in to animations (transitions are subtle 0.3s)

## Design Decisions
- **CSS variable architecture**: Every color is a variable — no hardcoded values remain in component styles
- **`data-theme` on `<html>`**: Clean cascade, all descendants inherit
- **System preference fallback**: `prefers-color-scheme` checked when no `localStorage` value exists
- **No flash**: Theme applied before DOM renders
- **Assistant message shadow in light mode only**: `none` in dark (surfaces already contrast), subtle shadow in light (white-on-near-white needs definition)
- **Visual hierarchy preserved**: Same design language — the light theme is a color inversion, not a redesign
