#!/usr/bin/env python3
"""Dev server with auto-rebuild on file changes."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers.polling import PollingObserver as Observer

ROOT = Path(__file__).resolve().parent.parent.parent
OUT_DIR = ROOT / "out"

WATCH_DIRS = [
    ROOT / "data",
    ROOT / "code" / "scripts",
]

IGNORED_SUFFIXES = {".pyc", ".pyo", "__pycache__"}
IGNORED_NAMES = {".git", "__pycache__", ".DS_Store"}

_rebuild_lock = threading.Lock()
_pending_timer: threading.Timer | None = None



_prev_cpu_time: float = 0.0
_prev_wall_time: float = 0.0


def get_ram_mb() -> float:
    """Return current process RSS in MB from /proc/self/status."""
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) / 1024
    except (OSError, IndexError, ValueError):
        pass
    return 0.0


def get_cpu_percent() -> float:
    """Return CPU usage percentage since last call."""
    global _prev_cpu_time, _prev_wall_time
    try:
        with open("/proc/self/stat") as f:
            parts = f.read().split()
        utime = int(parts[13])
        stime = int(parts[14])
        cpu_time = utime + stime
        wall_time = time.monotonic()
        if _prev_wall_time == 0:
            _prev_cpu_time = cpu_time
            _prev_wall_time = wall_time
            return 0.0
        delta_cpu = cpu_time - _prev_cpu_time
        delta_wall = wall_time - _prev_wall_time
        _prev_cpu_time = cpu_time
        _prev_wall_time = wall_time
        if delta_wall == 0:
            return 0.0
        return (delta_cpu / os.sysconf("SC_CLK_TCK")) / delta_wall * 100
    except (OSError, IndexError, ValueError):
        pass
    return 0.0


def log_usage() -> None:
    """Print current RAM and CPU usage, overwriting the previous line."""
    mb = get_ram_mb()
    cpu = get_cpu_percent()
    print(f"\rRAM: {mb:.1f} MB | CPU: {cpu:.1f}%", end="", flush=True)

def rebuild() -> None:
    """Run the build script."""
    global _pending_timer
    _pending_timer = None
    print("\n--- Rebuilding site... ---")
    result = subprocess.run(
        [sys.executable, str(ROOT / "code" / "scripts" / "build.py")],
        cwd=str(ROOT),
    )
    if result.returncode == 0:
        print("--- Rebuild complete ---")
        log_usage()
    else:
        print(f"--- Rebuild failed (exit code {result.returncode}) ---")


def debounced_rebuild() -> None:
    """Debounce rapid file changes into a single rebuild."""
    global _pending_timer
    with _rebuild_lock:
        if _pending_timer is not None:
            _pending_timer.cancel()
        _pending_timer = threading.Timer(0.5, rebuild)
        _pending_timer.start()


class ChangeHandler(FileSystemEventHandler):
    """Triggers rebuild on any file change in watched directories."""

    def __init__(self, observer: Observer) -> None:
        super().__init__()
        self._observer = observer
        self._watched: set[str] = set()
        self._lock = threading.Lock()

    def on_any_event(self, event: FileSystemEvent) -> None:
        path = Path(event.src_path)

        if event.is_directory:
            if event.event_type == "created":
                self._watch_new_dir(path)
            elif event.event_type in ("deleted", "moved"):
                self._unschedule_dir(path)
            return

        if path.suffix in IGNORED_SUFFIXES:
            return
        if any(part in IGNORED_NAMES for part in path.parts):
            return
        print(f"Change detected: {path.relative_to(ROOT)}")
        debounced_rebuild()

    def _watch_new_dir(self, path: Path) -> None:
        """Recursively watch newly created directories."""
        if not path.is_dir():
            return
        if any(part in IGNORED_NAMES for part in path.parts):
            return
        key = str(path)
        with self._lock:
            if key in self._watched:
                return
            self._watched.add(key)
        self._observer.schedule(self, str(path), recursive=True)
        print(f"Now watching: {path.relative_to(ROOT)}")
        for child in path.iterdir():
            if child.is_dir():
                self._watch_new_dir(child)

    def _unschedule_dir(self, path: Path) -> None:
        """Remove watch for a deleted directory."""
        key = str(path)
        with self._lock:
            if key not in self._watched:
                return
            self._watched.discard(key)
        try:
            self._observer.unschedule(path)
        except KeyError:
            pass

    def cleanup(self) -> None:
        """Unschedule all watches and cancel pending timer."""
        global _pending_timer
        with _rebuild_lock:
            if _pending_timer is not None:
                _pending_timer.cancel()
                _pending_timer = None
        with self._lock:
            self._watched.clear()


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
    handler = ChangeHandler(observer)
    for watch_dir in WATCH_DIRS:
        if watch_dir.exists():
            observer.schedule(handler, str(watch_dir), recursive=True)
            print()
            print(f"Watching: {watch_dir.relative_to(ROOT)}")
    observer.start()

    server = start_ssserve()
    print("Dev server running. Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(5)
            log_usage()
    except KeyboardInterrupt:
        print("\nShutting down...")
        handler.cleanup()
        observer.stop()
        observer.join()
        server.terminate()
        server.wait()


if __name__ == "__main__":
    main()
