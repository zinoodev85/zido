#!/usr/bin/env bash
# Rebuild TODO.md and commit everything. Usage: save.sh "<commit message>"
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cd "${TODO_HOME:-$HOME/todos}"
python3 "$here/index.py"
git add -A
git diff --cached --quiet || git commit -qm "${1:-todo: update}"
git remote | grep -q . && git push -q 2>/dev/null || true
