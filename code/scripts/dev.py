#!/usr/bin/env python3
"""Dev server with auto-rebuild on file changes."""
from __future__ import annotations

import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "out"

WATCH_DIRS = [
    ROOT / "data",
    ROOT / "code" / "scripts",
]

IGNORED_SUFFIXES = {".pyc", ".pyo", "__pycache__"}
IGNORED_NAMES = {".git", "__pycache__", ".DS_Store"}

_debounce_timer: threading.Timer | None = None
_rebuild_lock = threading.Lock()


def rebuild() -> None:
    """Run the build script."""
    print("\n--- Rebuilding site... ---")
    result = subprocess.run(
        [sys.executable, str(ROOT / "code" / "scripts" / "build.py")],
        cwd=str(ROOT),
    )
    if result.returncode == 0:
        print("--- Rebuild complete ---\n")
    else:
        print(f"--- Rebuild failed (exit code {result.returncode}) ---\n")


def debounced_rebuild() -> None:
    """Debounce rapid file changes into a single rebuild."""
    global _debounce_timer
    with _rebuild_lock:
        if _debounce_timer is not None:
            _debounce_timer.cancel()
        _debounce_timer = threading.Timer(0.5, rebuild)
        _debounce_timer.start()


class ChangeHandler(FileSystemEventHandler):
    """Triggers rebuild on any file change in watched directories."""

    def on_any_event(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        src = Path(event.src_path)
        if src.suffix in IGNORED_SUFFIXES:
            return
        if any(part in IGNORED_NAMES for part in src.parts):
            return
        print(f"Change detected: {src.relative_to(ROOT)}")
        debounced_rebuild()


def start_ssserve() -> subprocess.Popen[bytes]:
    """Start ssserve with live-reload in the background."""
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "ssserve",
            str(OUT_DIR),
            "--live-reload",
            "-u",
        ],
        cwd=str(ROOT),
    )


def main() -> None:
    """Watch source files and rebuild on changes."""
    rebuild()

    observer = Observer()
    for watch_dir in WATCH_DIRS:
        if watch_dir.exists():
            observer.schedule(ChangeHandler(), str(watch_dir), recursive=True)
            print(f"Watching: {watch_dir.relative_to(ROOT)}")
    observer.start()

    server = start_ssserve()
    print("Dev server running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        observer.stop()
        observer.join()
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
