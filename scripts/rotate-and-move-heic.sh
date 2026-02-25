#!/usr/bin/env bash
# Rotates all HEIC files in data/turn-images/ 90° clockwise
# and moves them to data/heic-images/

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SRC_DIR="$ROOT_DIR/data/turn-images"
DEST_DIR="$ROOT_DIR/data/heic-images"

mkdir -p "$DEST_DIR"

shopt -s nullglob
files=("$SRC_DIR"/*.HEIC "$SRC_DIR"/*.heic)

if [ ${#files[@]} -eq 0 ]; then
  echo "No HEIC files found in $SRC_DIR"
  exit 0
fi

for file in "${files[@]}"; do
  filename="$(basename "$file")"
  echo "Rotating $filename 90° clockwise..."
  sips --rotate 90 "$file" --out "$DEST_DIR/$filename" >/dev/null
  rm "$file"
  echo "Moved $filename to $DEST_DIR/"
done

echo "Done. Processed ${#files[@]} file(s)."
