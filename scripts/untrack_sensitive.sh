#!/usr/bin/env bash
# POSIX shell helper to untrack local/sensitive files from git and add .gitignore
# Run from repository root: ./scripts/untrack_sensitive.sh

set -euo pipefail

patterns=(
  ".venv"
  "venv"
  "env"
  "web/node_modules"
  "web/dist"
  ".env"
  ".pytest_cache"
  "__pycache__"
)

if [ ! -d .git ]; then
  echo "No .git directory found. Initialize a git repo first or run the equivalent git commands manually." >&2
  exit 1
fi

for p in "${patterns[@]}"; do
  if [ -e "$p" ]; then
    echo "Untracking: $p"
    git rm -r --cached --quiet "$p" || true
  else
    echo "Not present: $p"
  fi
done

git add .gitignore

echo "Run: git commit -m 'chore: ignore local env and build artifacts'" 
