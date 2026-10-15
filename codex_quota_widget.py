"""Small always-on-top Codex quota widget for Windows.

Reads the authenticated account rate limits through the local Codex app-server.
No credentials are read or stored by this script.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
import ctypes
import tkinter as tk
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path


REFRESH_MS = 60_000
FOLLOW_MS = 120
WIDGET_WIDTH = 1000
WIDGET_HEIGHT = 38
SPINNER_FRAMES = ("/", "—", "\\", "|")
APP_NAME = "CodexQuotaWidget"
BG = "#20232b"
FG = "#f2f4f8"
MUTED = "#d0d6e0"
FONT_FAMILY = "Microsoft YaHei UI"
ACCENT = "#80c7ff"
WARNING = "#f0b86e"
DANGER = "#ff777f"

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
GA_ROOT = 2

user32.EnumWindows.argtypes = (WNDENUMPROC, wintypes.LPARAM)
user32.EnumWindows.restype = wintypes.BOOL
user32.IsWindowVisible.argtypes = (wintypes.HWND,)
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsIconic.argtypes = (wintypes.HWND,)
user32.IsIconic.restype = wintypes.BOOL
user32.GetWindowThreadProcessId.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
user32.GetWindowThreadProcessId.restype = wintypes.DWORD
user32.GetWindowTextLengthW.argtypes = (wintypes.HWND,)
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = (wintypes.HWND, wintypes.LPWSTR, ctypes.c_int)
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetWindowRect.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.RECT))
user32.GetWindowRect.restype = wintypes.BOOL
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetAncestor.argtypes = (wintypes.HWND, wintypes.UINT)
user32.GetAncestor.restype = wintypes.HWND
kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = (
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)
)
kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
kernel32.GetCurrentProcessId.restype = wintypes.DWORD
_IMAGE_CACHE: dict[int, str] = {}


def image_for_pid(pid: int) -> str:
    if pid in _IMAGE_CACHE:
        return _IMAGE_CACHE[pid]
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        _IMAGE_CACHE[pid] = ""
        return ""
    try:
        size = wintypes.DWORD(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            _IMAGE_CACHE[pid] = buffer.value
        else:
            _IMAGE_CACHE[pid] = ""
        return _IMAGE_CACHE[pid]
    finally:
        kernel32.CloseHandle(handle)


def find_codex_window() -> tuple[int, tuple[int, int, int, int]] | None:
    matches: list[tuple[int, tuple[int, int, int, int], int]] = []

    @WNDENUMPROC
    def visit(hwnd: int, _lparam: int) -> bool:
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value or not image_for_pid(pid.value).lower().endswith("\\chatgpt.exe"):
            return True
        title_len = user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(max(2, title_len + 1))
        user32.GetWindowTextW(hwnd, title, len(title))
        rect = wintypes.RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
            return True
        width, height = rect.right - rect.left, rect.bottom - rect.top
        if width >= 600 and height >= 400:
            score = width * height + (10_000_000 if title.value.strip() else 0)
            matches.append((int(hwnd), (rect.left, rect.top, rect.right, rect.bottom), score))
        return True

    user32.EnumWindows(visit, 0)
    if not matches:
        return None
    hwnd, rect, _score = max(matches, key=lambda item: item[2])
    return hwnd, rect


class AccountReader:
    def __init__(self) -> None:
        self.codex = shutil.which("codex")
        self.process: subprocess.Popen[str] | None = None
        self.lines: queue.Queue[str] = queue.Queue()
        self.next_id = 1
        self.lock = threading.Lock()

    def _start(self) -> None:
        # Explorer/startup shortcuts may inherit a PATH pointing to a removed build.
        self.codex = shutil.which("codex")
        if not self.codex or not Path(self.codex).is_file():
            local_app_data = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
            candidates = list((local_app_data / "OpenAI" / "Codex" / "bin").glob("*/codex.exe"))
            candidates = [path for path in candidates if path.is_file()]
            self.codex = str(max(candidates, key=lambda path: path.stat().st_mtime)) if candidates else None
        if not self.codex:
            raise RuntimeError("找不到 codex 命令")
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        self.process = subprocess.Popen(
            [self.codex, "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            startupinfo=startupinfo,
        )
        self.lines = queue.Queue()
        process, lines = self.process, self.lines

        def read_output() -> None:
            assert process.stdout
            for line in process.stdout:
                lines.put(line.rstrip("\r\n"))

        threading.Thread(target=read_output, daemon=True).start()
        self._send({
            "id": self.next_id,
            "method": "initialize",
            "params": {"clientInfo": {"name": APP_NAME, "version": "1.0.0"}},
        })
        self._wait_for(self.next_id, timeout=15)
        self.next_id += 1
        self._send({"method": "initialized", "params": {}})

    def _send(self, message: dict) -> None:
        if not self.process or not self.process.stdin:
            raise RuntimeError("Codex app-server 未启动")
        self.process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _wait_for(self, request_id: int, timeout: float = 30) -> dict:
        deadline = __import__("time").monotonic() + timeout
        while __import__("time").monotonic() < deadline:
            try:
                line = self.lines.get(timeout=0.5)
            except queue.Empty:
                if self.process and self.process.poll() is not None:
                    raise RuntimeError("Codex app-server 已退出")
                continue
            try:
                response = json.loads(line)
            except json.JSONDecodeError:
                continue
            if response.get("id") == request_id:
                if "error" in response:
                    raise RuntimeError(str(response["error"].get("message", response["error"])))
                return response.get("result", {})
        raise TimeoutError("读取 Codex 额度超时")

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
                    if attempt == 1:
                        raise

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


def reset_text(epoch: int | None) -> str:
    if not epoch:
        return "重置时间未知"
    local = datetime.fromtimestamp(epoch, tz=timezone.utc).astimezone()
    return "重置 " + local.strftime("%m-%d %H:%M")


class QuotaWidget:
    def __init__(self) -> None:
        # Render at native display resolution instead of Windows bitmap scaling.
        try:
            user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except AttributeError:
            user32.SetProcessDPIAware()
        self.root = tk.Tk()
        self.root.title("Codex 剩余额度")
        self.root.configure(bg=BG)
        self.root.attributes("-topmost", True)
        self.root.attributes("-toolwindow", True)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)
        self.root.geometry(f"{WIDGET_WIDTH}x{WIDGET_HEIGHT}")
        self.root.protocol("WM_DELETE_WINDOW", self.quit)
        self.reader = AccountReader()
        self.results: queue.Queue[tuple[bool, object]] = queue.Queue()
        self.drag_origin: tuple[int, int, int, int] | None = None
        self.is_loading = False
        self.spinner_index = 0
        self.last_updated_at: float | None = None
        self.widget_visible = True
        self.last_position: tuple[int, int] | None = None

        outer = tk.Frame(self.root, bg=BG, padx=6, pady=2, highlightthickness=1,
                         highlightbackground="#3a414e")
        outer.pack(fill="both", expand=True)
        row = tk.Frame(outer, bg=BG, height=WIDGET_HEIGHT - 4)
        row.pack(fill="both", expand=True)
        row.pack_propagate(False)
        self.row = row

        def separator(parent: tk.Widget = row) -> tk.Label:
            label = tk.Label(parent, text="·", bg=BG, fg="#667080",
                             font=(FONT_FAMILY, 10))
            label.pack(side="left", padx=3)
            return label

        self.main_label = tk.Label(row, text="周额度 --%", bg=BG, fg=FG,
                                   anchor="w", font=(FONT_FAMILY, 11, "bold"))
        self.main_label.pack(side="left")
        self.progress_canvas = tk.Canvas(row, width=72, height=8, bg="#343a45",
                                         highlightthickness=0, bd=0)
        self.progress_canvas.pack(side="left", padx=(5, 4))
        self.progress_fill = self.progress_canvas.create_rectangle(
            0, 0, 0, 8, fill=ACCENT, outline=""
        )
        self.reset_label = tk.Label(row, text="重置 --", bg=BG, fg=ACCENT,
                                    font=(FONT_FAMILY, 11, "bold"))
        self.reset_label.pack(side="left")

        # Keep the separator inside the optional group so hiding it leaves no gap.
        self.short_group = tk.Frame(row, bg=BG)
        separator(self.short_group)
        self.short_label = tk.Label(self.short_group, text="5H额度 --%", bg=BG, fg=FG,
                                    font=(FONT_FAMILY, 11, "bold"))
        self.short_label.pack(side="left")
        self.short_progress_canvas = tk.Canvas(self.short_group, width=72, height=8,
                                               bg="#343a45", highlightthickness=0, bd=0)
        self.short_progress_canvas.pack(side="left", padx=(5, 4))
        self.short_progress_fill = self.short_progress_canvas.create_rectangle(
            0, 0, 0, 8, fill=ACCENT, outline=""
        )
        self.short_reset_label = tk.Label(self.short_group, text="重置 --", bg=BG,
                                          fg=ACCENT, font=(FONT_FAMILY, 11, "bold"))
        self.short_reset_label.pack(side="left")

        self.reserve_separator = separator()
        self.reserve_label = tk.Label(row, text="Reserve --%", bg=BG, fg=MUTED,
                                      font=(FONT_FAMILY, 11))
        self.reserve_label.pack(side="left")
        separator()

        self.updated_label = tk.Label(row, text="尚未更新", bg=BG, fg=MUTED,
                                      font=(FONT_FAMILY, 10))
        self.updated_label.pack(side="left")
        self.loading_label = tk.Label(row, text="", width=2, bg=BG, fg=ACCENT,
                                      anchor="w", font=(FONT_FAMILY, 10))
        self.loading_label.pack(side="left", padx=(3, 0))

        self.close_button = tk.Button(row, text="×", command=self.quit, bg=BG, fg=MUTED,
                                      activebackground=BG, activeforeground=FG,
                                      relief="flat", borderwidth=0, highlightthickness=0,
                                      padx=3, pady=0,
                                      font=("Segoe UI", 10))
        self.close_button.pack(side="right")
        self.refresh_button = tk.Button(row, text="↻", command=self.refresh, bg=BG,
                                        fg=ACCENT, activebackground=BG,
                                        activeforeground=FG, relief="flat",
                                        borderwidth=0, highlightthickness=0, padx=3, pady=0,
                                        font=("Segoe UI", 10))
        self.refresh_button.pack(side="right")

        for widget in (outer, row, self.main_label, self.progress_canvas,
                       self.short_group, self.short_label, self.short_progress_canvas,
                       self.short_reset_label, self.reserve_label, self.reset_label,
                       self.updated_label, self.loading_label):
            widget.bind("<ButtonPress-1>", self.begin_drag)
            widget.bind("<B1-Motion>", self.drag)

        self.refresh()
        self.root.after(250, self.process_results)
        self.root.after(REFRESH_MS, self.periodic_refresh)
        self.root.after(FOLLOW_MS, self.follow_codex)
        self.root.after(5000, self.update_age)
        self.fit_width()

    def fit_width(self) -> None:
        self.root.update_idletasks()
        width = 14
        for child in self.row.pack_slaves():
            padding = child.pack_info().get("padx", 0)
            padding_width = (sum(int(x) for x in padding)
                             if isinstance(padding, (tuple, list)) else int(padding) * 2)
            width += child.winfo_reqwidth() + padding_width
        width = max(600, width)
        if self.root.winfo_width() != width:
            self.root.geometry(f"{width}x{WIDGET_HEIGHT}")
            self.last_position = None

    def update_age(self) -> None:
        if self.last_updated_at is not None:
            minutes = max(0, int((time.monotonic() - self.last_updated_at) // 60))
            text = "刚刚更新" if minutes == 0 else f"{minutes}分钟前更新"
            if self.updated_label.cget("text") != text:
                self.updated_label.config(text=text)
                self.fit_width()
        self.root.after(5000, self.update_age)

    def follow_codex(self) -> None:
        target = find_codex_window()
        if target is None:
            if self.widget_visible:
                self.root.withdraw()
                self.widget_visible = False
            self.root.after(FOLLOW_MS, self.follow_codex)
            return

        hwnd, (left, top, right, _bottom) = target
        foreground = user32.GetForegroundWindow()
        foreground_root = user32.GetAncestor(foreground, GA_ROOT) if foreground else 0
        widget_root = user32.GetAncestor(self.root.winfo_id(), GA_ROOT)
        foreground_pid = wintypes.DWORD()
        if foreground:
            user32.GetWindowThreadProcessId(foreground, ctypes.byref(foreground_pid))
        codex_pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(codex_pid))

        is_codex_active = foreground_root == hwnd or foreground_pid.value == codex_pid.value
        is_widget_active = foreground_root == widget_root or foreground_pid.value == kernel32.GetCurrentProcessId()
        if user32.IsIconic(hwnd) or not (is_codex_active or is_widget_active):
            if self.widget_visible:
                self.root.withdraw()
                self.widget_visible = False
        else:
            if not self.widget_visible:
                self.root.deiconify()
                self.widget_visible = True
            x = left + max(0, (right - left - self.root.winfo_width()) // 2)
            if self.last_position != (x, top):
                self.root.geometry(f"+{x}+{top}")
                self.last_position = (x, top)
        self.root.after(FOLLOW_MS, self.follow_codex)

    def begin_drag(self, event: tk.Event) -> None:
        self.drag_origin = (event.x_root, event.y_root,
                            self.root.winfo_x(), self.root.winfo_y())

    def drag(self, event: tk.Event) -> None:
        if self.drag_origin:
            ox, oy, wx, wy = self.drag_origin
            self.root.geometry(f"+{wx + event.x_root - ox}+{wy + event.y_root - oy}")

    def refresh(self) -> None:
        if self.is_loading:
            return
        self.is_loading = True
        self.spinner_index = 0
        self.animate_loading()
        threading.Thread(target=self.fetch, daemon=True).start()

    def animate_loading(self) -> None:
        if not self.is_loading:
            return
        frame = SPINNER_FRAMES[self.spinner_index % len(SPINNER_FRAMES)]
        self.spinner_index += 1
        self.loading_label.config(text=frame, fg=ACCENT)
        self.root.after(120, self.animate_loading)

    def finish_loading(self, error: object | None = None) -> None:
        self.is_loading = False
        if error is None:
            self.loading_label.config(text="", fg=MUTED)
        else:
            self.loading_label.config(text="失败", fg=WARNING)

    def fetch(self) -> None:
        try:
            self.results.put((True, self.reader.read_limits()))
        except Exception as exc:  # surfaced in the widget, never silently presented as live
            self.results.put((False, str(exc)))

    def process_results(self) -> None:
        try:
            while True:
                ok, value = self.results.get_nowait()
                if ok:
                    try:
                        self.render(value)
                    except Exception as exc:
                        self.finish_loading(exc)
                    else:
                        self.finish_loading()
                else:
                    self.finish_loading(value)
        except queue.Empty:
            pass
        self.root.after(250, self.process_results)

    def render(self, payload: object) -> None:
        if not isinstance(payload, dict):
            raise ValueError("额度响应格式异常")
        buckets = payload.get("rateLimitsByLimitId") or {}
        codex = buckets.get("codex") or payload.get("rateLimits") or {}
        base = buckets.get("base_model_inference") or {}
        windows = [w for w in (codex.get("primary"), codex.get("secondary"))
                   if isinstance(w, dict)]
        main_window = next((w for w in windows if w.get("windowDurationMins") == 10080), {})
        # Older servers may omit durations; retain their original weekly mapping.
        if not main_window:
            main_window = next((w for w in windows if not w.get("windowDurationMins")), {})
        used = main_window.get("usedPercent")
        if used is None:
            raise ValueError("账号额度未返回；请稍后刷新或检查 Codex 登录状态")

        remaining = max(0.0, min(100.0, 100.0 - float(used)))
        self.main_label.config(text=f"周额度 {remaining:.0f}%")
        self.render_progress(self.progress_canvas, self.progress_fill, remaining)

        secondary_window = next((w for w in windows if w.get("windowDurationMins") == 300), None)
        if isinstance(secondary_window, dict) and secondary_window.get("usedPercent") is not None:
            short_remaining = max(0.0, min(100.0, 100.0 - float(secondary_window["usedPercent"])))
            self.short_label.config(text=f"5H额度 {short_remaining:.0f}%")
            self.render_progress(self.short_progress_canvas, self.short_progress_fill, short_remaining)
            self.short_reset_label.config(text=reset_text(secondary_window.get("resetsAt")))
            if not self.short_group.winfo_manager():
                self.short_group.pack(side="left", before=self.reserve_separator)
        else:
            self.short_group.pack_forget()

        reset_at = main_window.get("resetsAt")
        self.reset_label.config(text=reset_text(reset_at))

        base_window = base.get("primary") if isinstance(base, dict) else None
        if isinstance(base_window, dict) and base_window.get("usedPercent") is not None:
            reserve_remaining = max(0.0, min(100.0, 100.0 - float(base_window["usedPercent"])))
            self.reserve_label.config(text=f"Reserve {reserve_remaining:.0f}%")
        else:
            self.reserve_label.config(text="Reserve --%")
        self.last_updated_at = time.monotonic()
        self.updated_label.config(text="刚刚更新")
        self.fit_width()

    @staticmethod
    def render_progress(canvas: tk.Canvas, fill: int, remaining: float) -> None:
        width = round(int(canvas.cget("width")) * remaining / 100.0)
        color = DANGER if remaining < 20 else WARNING if remaining < 50 else ACCENT
        canvas.coords(fill, 0, 0, width, 8)
        canvas.itemconfigure(fill, fill=color)

    def periodic_refresh(self) -> None:
        self.refresh()
        self.root.after(REFRESH_MS, self.periodic_refresh)

    def quit(self) -> None:
        self.reader.close()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    QuotaWidget().run()
