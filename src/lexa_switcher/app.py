from __future__ import annotations

from dataclasses import dataclass
import logging
import platform
from pathlib import Path

from .buffer import TypedBuffer
from .config import AppConfig
from .converter import Converter
from .backends.base import PlatformBackend

LOG = logging.getLogger(__name__)
NAVIGATION_KEYS = {
    "delete",
    "left",
    "right",
    "up",
    "down",
    "home",
    "end",
    "page up",
    "page down",
    "esc",
    "enter",
    "tab",
    "ctrl",
    "left ctrl",
    "right ctrl",
    "alt",
    "left alt",
    "right alt",
    "windows",
    "left windows",
    "right windows",
    "menu",
}
SPECIAL_CHAR_MAP = {
    "space": " ",
}


@dataclass
class LexaSwitcherApp:
    config: AppConfig
    converter: Converter
    buffer: TypedBuffer
    backend: PlatformBackend | None = None
    enabled: bool = True

    @classmethod
    def create(cls, project_root: Path | None = None) -> "LexaSwitcherApp":
        config = AppConfig.load(project_root)
        converter = Converter(config.project_root)
        buffer = TypedBuffer(max_length=config.max_buffer_length)
        app = cls(config=config, converter=converter, buffer=buffer, enabled=config.enabled)
        app.backend = _create_backend(app)
        return app

    def run(self) -> None:
        if self.backend is None:
            raise RuntimeError("Backend was not initialized")
        LOG.info("Starting Lexa Switcher backend: %s", self.backend.__class__.__name__)
        self.backend.start()
        self.backend.wait()

    def stop(self) -> None:
        if self.backend is not None:
            self.backend.stop()

    def handle_key_event(self, key_name: str | None) -> None:
        if not self.enabled or self.backend is None or not key_name:
            return

        if self._is_excluded_process():
            self.buffer.reset()
            return

        window_id = self.backend.get_active_window_id()
        if key_name == "backspace":
            self.buffer.handle_backspace(window_id)
            return

        if key_name in NAVIGATION_KEYS:
            self.buffer.clear_for_navigation(window_id)
            return

        text = SPECIAL_CHAR_MAP.get(key_name, key_name if len(key_name) == 1 else None)
        if text is not None:
            self.buffer.add_char(text, window_id)

    def handle_convert_request(self) -> None:
        if not self.enabled or self.backend is None:
            return

        if self._is_excluded_process() or self.backend.modifiers_pressed():
            return

        window_id = self.backend.get_active_window_id()
        self.buffer.track_window(window_id)
        if not self.buffer.text or not self.buffer.has_letters() or not self.buffer.is_recent():
            return

        result = self.converter.convert_buffer(self.buffer.text)
        if result is None:
            return

        self.backend.send_backspaces(len(self.buffer.text))
        self.backend.send_text(result.final_text)
        self.buffer.replace(result.final_text)

        target_layout = self.converter.target_layout(result.converted)
        if target_layout:
            self.backend.switch_layout(target_layout)

    def _is_excluded_process(self) -> bool:
        if self.backend is None:
            return False
        process_name = self.backend.get_active_process_name()
        return bool(process_name and process_name in self.config.excluded_apps)


def _create_backend(app: LexaSwitcherApp) -> PlatformBackend:
    system = platform.system()
    if system == "Windows":
        from .backends.windows import WindowsBackend

        return WindowsBackend(app)
    if system == "Darwin":
        from .backends.macos import MacOSBackend

        return MacOSBackend(app)
    if system == "Linux":
        from .backends.linux import LinuxBackend

        return LinuxBackend(app)
    raise NotImplementedError(f"Unsupported platform: {system}")
