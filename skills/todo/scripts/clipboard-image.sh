#!/usr/bin/env bash
# Save the image currently in the macOS clipboard as PNG.
# Usage: clipboard-image.sh <target.png>   → exits 1 if clipboard has no image.
set -euo pipefail
out="$1"
mkdir -p "$(dirname "$out")"
osascript - "$out" <<'OSA' >/dev/null 2>&1 || { echo "no image in clipboard" >&2; exit 1; }
on run argv
  set png to the clipboard as «class PNGf»
  set f to open for access POSIX file (item 1 of argv) with write permission
  set eof f to 0
  write png to f
  close access f
end run
OSA
echo "$out"
