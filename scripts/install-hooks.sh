#!/bin/bash
# Install git hooks dari scripts/hooks/ ke .git/hooks/
set -e
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$REPO_ROOT/scripts/hooks"
DST="$REPO_ROOT/.git/hooks"
[ -d "$DST" ] || { echo "ERROR: .git/hooks/ tidak ditemukan." >&2; exit 1; }
[ -d "$SRC" ] || { echo "ERROR: $SRC tidak ditemukan." >&2; exit 1; }
for hook in "$SRC"/*; do
  [ -f "$hook" ] || continue
  name=$(basename "$hook")
  cp "$hook" "$DST/$name"
  chmod +x "$DST/$name"
  echo "installed: $name"
done
echo "Done."
