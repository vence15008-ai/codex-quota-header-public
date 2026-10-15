"""JSON-lines child process; headless and independent of legacy Tk UI."""
from __future__ import annotations

import json
import queue
import sys
import threading
import time

from account_reader import AccountReader
from quota_model import quota_view
from win32_job import protect_worker_tree


def main() -> None:
    worker_job = protect_worker_tree()
    commands: queue.Queue[str] = queue.Queue()
    reader = AccountReader()
    view = None
    updated_at = None

    def read_commands() -> None:
        for line in sys.stdin:
            try:
                command = json.loads(line).get("command")
                if command in ("refresh", "stop"):
                    commands.put(command)
            except (ValueError, AttributeError):
                pass
        commands.put("stop")

    def emit(loading: bool, error: str | None = None) -> None:
        print(json.dumps({"view": view, "updatedAt": updated_at,
                          "loading": loading, "error": error}, ensure_ascii=False), flush=True)

    threading.Thread(target=read_commands, daemon=True).start()
    command = "refresh"
    try:
        while command != "stop":
            emit(True)
            try:
                view = quota_view(reader.read_limits())
                updated_at = int(time.time() * 1000)
                emit(False)
            except Exception as exc:
                # Retain the last successful view, explicitly label stale/error.
                emit(False, str(exc)[:240])
            try:
                command = commands.get(timeout=60)
            except queue.Empty:
                command = "refresh"
    finally:
        reader.close()


if __name__ == "__main__":
    main()
