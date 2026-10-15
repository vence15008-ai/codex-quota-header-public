"""Headless, read-only Codex app-server client. No Tk or credential-file access."""
from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time


def find_codex() -> str:
    """Rediscover native CLI on every reconnect, including after desktop updates."""
    explicit = os.environ.get("CODEX_QUOTA_CODEX")
    if explicit:
        candidate = Path(explicit)
        if not candidate.is_file() or candidate.suffix.lower() != ".exe":
            raise RuntimeError("CODEX_QUOTA_CODEX must point to an existing native codex.exe")
        return str(candidate.resolve())
    candidate = shutil.which("codex.exe")
    if candidate and Path(candidate).is_file():
        return candidate
    local = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData/Local")
    candidates = [p for p in (local / "OpenAI/Codex/bin").glob("*/codex.exe") if p.is_file()]
    if candidates:
        return str(max(candidates, key=lambda p: p.stat().st_mtime))
    raise RuntimeError("Native codex.exe not found; set CODEX_QUOTA_CODEX (not codex.cmd)")


class AccountReader:
    def __init__(self) -> None:
        self.process: subprocess.Popen[str] | None = None
        self.lines: queue.Queue[str] = queue.Queue()
        self.next_id = 1
        self.lock = threading.Lock()

    def _start(self) -> None:
        options = {}
        if os.name == "nt":
            info = subprocess.STARTUPINFO()
            info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            info.wShowWindow = subprocess.SW_HIDE
            options.update(startupinfo=info, creationflags=subprocess.CREATE_NO_WINDOW)
        self.process = subprocess.Popen(
            [find_codex(), "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1, **options,
        )
        self.lines = queue.Queue()
        process, lines = self.process, self.lines

        def read_output() -> None:
            assert process.stdout
            for line in process.stdout:
                lines.put(line.rstrip("\r\n"))

        threading.Thread(target=read_output, daemon=True).start()
        request_id = self.next_id
        self.next_id += 1
        self._send({"id": request_id, "method": "initialize", "params": {
            "clientInfo": {"name": "codex_quota_header", "version": "0.1.0"}}})
        self._wait_for(request_id, timeout=15)
        self._send({"method": "initialized", "params": {}})

    def _send(self, message: dict) -> None:
        if not self.process or not self.process.stdin:
            raise RuntimeError("Codex app-server is not running")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _wait_for(self, request_id: int, timeout: float = 30) -> dict:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                line = self.lines.get(timeout=min(0.5, max(0.001, deadline - time.monotonic())))
            except queue.Empty:
                if self.process and self.process.poll() is not None:
                    raise RuntimeError("Codex app-server exited")
                continue
            try:
                response = json.loads(line)
            except ValueError:
                continue
            if not isinstance(response, dict) or response.get("id") != request_id:
                continue
            if "error" in response:
                # Do not forward arbitrary server payloads into UI/logs.
                error = response["error"]
                code = error.get("code") if isinstance(error, dict) else None
                safe_code = code if isinstance(code, int) and not isinstance(code, bool) else "unknown"
                raise RuntimeError(f"Codex quota request failed (code {safe_code}); check desktop login")
            result = response.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("Invalid Codex app-server result")
            return result
        raise TimeoutError("Codex quota request timed out")

    def read_limits(self) -> dict:
        with self.lock:
            for attempt in range(2):
                try:
                    if self.process is None or self.process.poll() is not None:
                        self._start()
                    request_id = self.next_id
                    self.next_id += 1
                    self._send({"id": request_id, "method": "account/rateLimits/read"})
                    return self._wait_for(request_id)
                except Exception:
                    self.close()
                    if attempt:
                        raise
        raise RuntimeError("Unreachable quota reader state")

    def close(self) -> None:
        process, self.process = self.process, None
        if process:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            for stream in (process.stdin, process.stdout):
                if stream:
                    stream.close()


if __name__ == "__main__":
    # Discovery only. Never starts a server or reads account data.
    print("Native CLI:", find_codex())
