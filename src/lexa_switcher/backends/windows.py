from __future__ import annotations

import ctypes
from ctypes import wintypes
from pathlib import Path
import threading

import keyboard

from .base import PlatformBackend

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_INPUTLANGCHANGEREQUEST = 0x0050
KLF_ACTIVATE = 0x00000001
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

GetForegroundWindow = user32.GetForegroundWindow
GetWindowThreadProcessId = user32.GetWindowThreadProcessId
PostMessageW = user32.PostMessageW
LoadKeyboardLayoutW = user32.LoadKeyboardLayoutW
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle
QueryFullProcessImageNameW = kernel32.QueryFullProcessImageNameW


class WindowsBackend(PlatformBackend):
    EN_HKL = "00000409"
    RU_HKL = "00000419"

    def __init__(self, app: "LexaSwitcherApp") -> None:
        self.app = app
        self._running = threading.Event()
        self._hooks: list[object] = []
        self._internal_send = False

    def start(self) -> None:
        self._running.set()
        self._hooks.append(keyboard.on_press(self._on_press))
        self._hooks.append(keyboard.on_release_key("right shift", self._on_right_shift_release))

    def stop(self) -> None:
        self._running.clear()
        keyboard.unhook_all()

    def wait(self) -> None:
        self._running.wait()
        try:
            while self._running.is_set():
                self._running.wait(timeout=1.0)
        except KeyboardInterrupt:
            self.stop()

    def get_active_window_id(self) -> str | None:
        hwnd = GetForegroundWindow()
        return str(hwnd) if hwnd else None

    def get_active_process_name(self) -> str | None:
        hwnd = GetForegroundWindow()
        if not hwnd:
            return None

        pid = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        handle = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
        if not handle:
            return None

        try:
            buffer_length = wintypes.DWORD(260)
            buffer = ctypes.create_unicode_buffer(buffer_length.value)
            if not QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(buffer_length)):
                return None
            return Path(buffer.value).name.lower()
        finally:
            CloseHandle(handle)

    def send_backspaces(self, count: int) -> None:
        if count <= 0:
            return
        self._internal_send = True
        try:
            for _ in range(count):
                keyboard.send("backspace")
        finally:
            self._internal_send = False

    def send_text(self, text: str) -> None:
        if not text:
            return
        self._internal_send = True
        try:
            keyboard.write(text, delay=0, exact=True)
        finally:
            self._internal_send = False

    def switch_layout(self, layout: str) -> None:
        hkl_hex = self.RU_HKL if layout == "ru" else self.EN_HKL
        hwnd = GetForegroundWindow()
        if not hwnd:
            return
        hkl = LoadKeyboardLayoutW(hkl_hex, KLF_ACTIVATE)
        if hkl:
            PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, hkl)

    def modifiers_pressed(self) -> bool:
        return any(
            keyboard.is_pressed(name)
            for name in ("ctrl", "alt", "left windows", "right windows")
        )

    def _on_press(self, event: keyboard.KeyboardEvent) -> None:
        if self._internal_send or event.event_type != "down":
            return
        self.app.handle_key_event(event.name)

    def _on_right_shift_release(self, _: keyboard.KeyboardEvent) -> None:
        if self._internal_send:
            return
        self.app.handle_convert_request()
