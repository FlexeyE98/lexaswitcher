from __future__ import annotations

from abc import ABC, abstractmethod


class PlatformBackend(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_active_window_id(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def get_active_process_name(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def send_backspaces(self, count: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def send_text(self, text: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def switch_layout(self, layout: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def modifiers_pressed(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def wait(self) -> None:
        raise NotImplementedError
