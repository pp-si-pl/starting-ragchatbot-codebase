# Frontend Code Quality Tools

## What Changed

Added **Prettier** as an automatic code formatter for the frontend, bringing consistent formatting to all HTML, CSS, and JS files.

## Files Created

- **`frontend/package.json`** — Declares Prettier as a dev dependency with `format` and `format:check` npm scripts.
- **`frontend/.prettierrc`** — Prettier configuration: single quotes, semicolons, 2-space indent, 100 char print width, trailing commas (ES5), LF line endings.
- **`frontend/format.sh`** — Convenience shell script to run formatting without needing to remember npm commands. Supports `--check` flag for CI use.

## Files Reformatted

- **`frontend/index.html`** — Reformatted to Prettier standards.
- **`frontend/style.css`** — Reformatted to Prettier standards.
- **`frontend/script.js`** — Reformatted to Prettier standards (single quotes, consistent spacing).

## Usage

```bash
# Install dependencies (one-time)
cd frontend && npm install

# Auto-format all files
npm run format

# Check formatting without modifying (CI-friendly, exits non-zero on failure)
npm run format:check

# Or use the convenience script
./frontend/format.sh          # auto-fix
./frontend/format.sh --check  # check only
```
