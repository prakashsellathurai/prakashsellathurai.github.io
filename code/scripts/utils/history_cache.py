#!/usr/bin/env python3
"""Build a JSON cache of note/experiment file commit timestamps.

Scans the Grimoire submodule for notes and experiments, runs
``git log -2`` per file to grab the two most recent commit timestamps,
and writes the latest one to ``data/non-public/history-cache.json``.

The cache keys are relative paths from the Grimoire root
(e.g. ``notes/topic/file.md``, ``experiments/topic/script.py``).
"""

import json
import os
import pathlib
import subprocess

GRIMOIRE_DIR = pathlib.Path("data/non-public/submodules/Grimoire")
NOTES_DIR = GRIMOIRE_DIR / "notes"
EXPERIMENTS_DIR = GRIMOIRE_DIR / "experiments"
CACHE_PATH = pathlib.Path("data/non-public/history-cache.json")

ALLOWED_EXTS = {".md", ".py", ".c", ".txt", ".ipynb"}


def _last_commit_time(rel_path: str) -> int:
    """Return the most recent commit timestamp for *rel_path* in the Grimoire repo.

    Checks the last 2 commits so that the cache survives history rewrites
    or amends that only touch the latest commit.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(GRIMOIRE_DIR), "log", "-2", "--format=%ct", "--", rel_path],
            capture_output=True,
            text=True,
            check=True,
        )
        timestamps = result.stdout.strip().splitlines()
        if timestamps:
            return int(timestamps[0])
    except (subprocess.CalledProcessError, OSError, ValueError):
        pass
    return 0


def _scan_directory(base_dir: pathlib.Path, prefix: str, existing: dict[str, int]) -> dict[str, int]:
    """Walk *base_dir* and return {relative_path: timestamp} for new files only.

    Keys are relative to the Grimoire root (e.g. ``notes/topic/file.md``).
    Files already present in *existing* are skipped.
    """
    cache: dict[str, int] = {}
    if not base_dir.is_dir():
        return cache
    for root, dirs, filenames in os.walk(base_dir):
        dirs[:] = sorted(
            d for d in dirs
            if not d.startswith(".") and d != "__pycache__" and d != ".ipynb_checkpoints"
        )
        for fname in sorted(filenames):
            fpath = pathlib.Path(root) / fname
            if fpath.suffix.lower() not in ALLOWED_EXTS:
                continue
            rel = f"{prefix}/{fpath.relative_to(base_dir)}"
            if rel not in existing:
                cache[rel] = _last_commit_time(rel)
    return cache


def build_cache() -> None:
    """Build the history cache and write it to CACHE_PATH.

    Append-only: existing entries are preserved, only new files are queried.
    """
    if CACHE_PATH.exists():
        try:
            cache: dict[str, int] = json.loads(CACHE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            cache = {}
    else:
        cache = {}

    new_notes = _scan_directory(NOTES_DIR, "notes", cache)
    new_exps = _scan_directory(EXPERIMENTS_DIR, "experiments", cache)
    cache.update(new_notes)
    cache.update(new_exps)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(cache, f, indent=2)
    total_new = len(new_notes) + len(new_exps)
    print(f"History cache: {len(cache)} entries ({total_new} new) -> {CACHE_PATH}")


if __name__ == "__main__":
    build_cache()
