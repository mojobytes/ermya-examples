#!/usr/bin/env bash
set -euo pipefail

if git ls-files | rg -i 'tessera'; then
  echo 'Legacy brand found in tracked paths.' >&2
  exit 1
fi

if git grep -Iin 'tessera'; then
  echo 'Legacy brand found in tracked content.' >&2
  exit 1
fi

echo 'Brand residue check passed.'
