#!/usr/bin/env bash
set -euo pipefail

# ---- Configuration ----
# Commit you know works (pick one before the breakage appeared)
GOOD_COMMIT="${1:-<last-known-good-sha>}"

# Whether a submodule is present (this repo has one)
USE_SUBMODULE=true

# ---- Sanity checks ----
if [[ "$GOOD_COMMIT" == "<last-known-good-sha>" ]]; then
  echo "Usage: $0 <last-known-good-sha>" >&2
  echo "Example: $0 1a2b3c4" >&2
  exit 1
fi
command -v make >/dev/null || { echo "make not found" >&2; exit 1; }

# ---- Bisect driver: run on each candidate commit ----
run_test() {
  if $USE_SUBMODULE; then
    git submodule update --init --recursive
  fi
  make install-dev
  make install-playwright
  make test
}

echo ">>> Starting bisect: good=$GOOD_COMMIT bad=HEAD"
git bisect start
git bisect bad HEAD
git bisect good "$GOOD_COMMIT"

git bisect run bash -c 'run_test' 2>&1 || true

echo
echo ">>> Result:"
git bisect log
git bisect reset
