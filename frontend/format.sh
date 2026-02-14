#!/usr/bin/env bash
# Convenience script to format all frontend files with Prettier.
# Usage: ./format.sh          (auto-fix)
#        ./format.sh --check  (CI-friendly check, no changes)

set -e
cd "$(dirname "$0")"

if [ ! -d node_modules ]; then
  echo "Installing dependencies..."
  npm install
fi

if [ "$1" = "--check" ]; then
  npx prettier --check .
else
  npx prettier --write .
fi
