#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Scanning for .env.example files under: $root_dir"

found=0
while IFS= read -r -d '' example_file; do
  found=1
  dir="$(dirname "$example_file")"
  for env in dev prod; do
    target="$dir/.env.$env"
    if [[ -f "$target" ]]; then
      echo "Exists: $target"
    else
      cp "$example_file" "$target"
      echo "Created: $target"
    fi
  done
done < <(find "$root_dir" -name ".env.example" -print0)

if [[ "$found" -eq 0 ]]; then
  echo "No .env.example files found."
fi
