#!/usr/bin/env bash
set -euo pipefail

# ---- Configuration ----
GOOD_COMMIT="${1:-}"
USE_SUBMODULE=true

# ---- Sanity checks ----
if [[ -z "$GOOD_COMMIT" ]]; then
  echo "Usage: $0 <last-known-good-sha>" >&2
  echo "Example: $0 1a2b3c4" >&2
  exit 1
fi

command -v make >/dev/null || { echo "make not found" >&2; exit 1; }

# ---- Bisect driver: run on each candidate commit ----
run_test() {
  set -euo pipefail

  if [ "$USE_SUBMODULE" = true ]; then
    git submodule update --init --recursive
  fi

  # Optional: Exit 125 tells git bisect to SKIP commits that cannot be built/installed
  make install-dev || return 125
  make install-playwright || return 125

  # Run test suite: exit 0 = good, non-zero = bad
  make test
}

# Export variables and function so the subshell invoked by 'git bisect run' can access them
export -f run_test
export USE_SUBMODULE

# Ensure any previous bisect state is cleared
git bisect reset 2>/dev/null || true

echo ">>> Starting bisect: good=$GOOD_COMMIT bad=HEAD"
git bisect start
git bisect bad HEAD
git bisect good "$GOOD_COMMIT"

# Run bisect driver
git bisect run bash -c '
  git submodule update --init --recursive
  make install-dev
  make install-playwright
  make test
'

echo
echo ">>> Result:"
git bisect log
git bisect reset