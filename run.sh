#!/usr/bin/env bash
# Run API + frontend from project root. Installs deps if missing. Ctrl+C kills both.

set -e
cd "$(dirname "$0")"

# --- Backend: ensure Python and deps installed ---
PYTHON=""
for cmd in python3 python py; do
  if command -v "$cmd" &>/dev/null; then
    PYTHON="$cmd"
    break
  fi
done
if [ -z "$PYTHON" ]; then
  echo "Error: Python not found. Install Python 3.11+ or Poetry and try again." >&2
  exit 1
fi

POETRY_CMD=""
if command -v poetry &>/dev/null; then
  POETRY_CMD="poetry"
fi
if [ -z "$POETRY_CMD" ]; then
  echo "Poetry not found. Installing Poetry..."
  curl -sSL https://install.python-poetry.org | "$PYTHON" -
  if [ -n "$APPDATA" ]; then
    POETRY_DIR="$APPDATA/Python/Scripts"
    export PATH="$POETRY_DIR:$PATH"
    for p in "$POETRY_DIR/poetry.exe" "$POETRY_DIR/poetry"; do
      if [ -x "$p" ] 2>/dev/null || [ -f "$p" ]; then POETRY_CMD="$p"; break; fi
    done
    if [ -z "$POETRY_CMD" ] && command -v cygpath &>/dev/null; then
      POETRY_DIR_UNIX="$(cygpath -u "$POETRY_DIR" 2>/dev/null)"
      for p in "$POETRY_DIR_UNIX/poetry.exe" "$POETRY_DIR_UNIX/poetry"; do
        if [ -x "$p" ] 2>/dev/null || [ -f "$p" ]; then POETRY_CMD="$p"; break; fi
      done
    fi
    if [ -z "$POETRY_CMD" ] && [[ "$APPDATA" == *:* ]]; then
      POETRY_DIR_UNIX="/${APPDATA%%:*}/${APPDATA#*:}"
      POETRY_DIR_UNIX="${POETRY_DIR_UNIX//\\//}/Python/Scripts"
      for p in "$POETRY_DIR_UNIX/poetry.exe" "$POETRY_DIR_UNIX/poetry"; do
        if [ -x "$p" ] 2>/dev/null || [ -f "$p" ]; then POETRY_CMD="$p"; break; fi
      done
    fi
  fi
  if [ -z "$POETRY_CMD" ]; then
    for p in "$HOME/.local/bin/poetry" "$HOME/.local/bin/poetry.exe"; do
      if [ -x "$p" ] 2>/dev/null || [ -f "$p" ]; then POETRY_CMD="$p"; break; fi
    done
  fi
  if [ -z "$POETRY_CMD" ]; then
    echo "Error: Poetry was installed but could not be found. Add to PATH and re-run: $APPDATA\\Python\\Scripts (Windows) or $HOME/.local/bin (Unix)" >&2
    exit 1
  fi
fi
echo "Using Poetry for backend..."
"$POETRY_CMD" install
# Scanner uses Playwright Chromium; ensure browsers are installed (idempotent, quick if already present)
"$POETRY_CMD" run playwright install chromium || echo "Warning: Playwright Chromium install failed. Scanner may fail. Run: $POETRY_CMD run playwright install" >&2
RUN_API="\"$POETRY_CMD\" run jackai serve"

# --- Frontend: ensure deps installed ---
if [ ! -d "frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi
if ! command -v npm &>/dev/null; then
  echo "Error: npm not found. Install Node.js and try again." >&2
  exit 1
fi

echo "Starting API (port 8000) and frontend..."
eval "$RUN_API" &
API_PID=$!
sleep 2
(cd frontend && npm run dev) &
FRONT_PID=$!

cleanup() {
  echo "Shutting down..."
  kill $API_PID 2>/dev/null || true
  kill $FRONT_PID 2>/dev/null || true
  exit 0
}
trap cleanup SIGINT SIGTERM

wait
