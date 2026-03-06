from __future__ import annotations

from .base import PlatformBackend


class LinuxBackend(PlatformBackend):
    def __init__(self, app: object) -> None:
        self.app = app

    def start(self) -> None:
        raise NotImplementedError("Linux backend is not implemented yet")

    def stop(self) -> None:
        return None

    def get_active_window_id(self) -> str | None:
        return None

    def get_active_process_name(self) -> str | None:
        return None

    def send_backspaces(self, count: int) -> None:
        return None

    def send_text(self, text: str) -> None:
        return None

    def switch_layout(self, layout: str) -> None:
        return None

    def modifiers_pressed(self) -> bool:
        return False

    def wait(self) -> None:
        return None
