from __future__ import annotations

from dataclasses import dataclass, field
import re
import time

LETTER_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё]")


@dataclass
class TypedBuffer:
    max_length: int = 400
    text: str = ""
    last_window_id: str | None = None
    last_input_ts: float = 0.0

    def reset(self) -> None:
        self.text = ""
        self.last_input_ts = 0.0

    def track_window(self, window_id: str | None) -> None:
        if not window_id:
            self.reset()
            return
        if self.last_window_id != window_id:
            self.last_window_id = window_id
            self.reset()

    def add_char(self, char: str, window_id: str | None) -> None:
        if not char:
            return
        self.track_window(window_id)
        self.text += char
        self.last_input_ts = time.monotonic()
        if len(self.text) > self.max_length:
            self.text = self.text[-200:]

    def handle_backspace(self, window_id: str | None) -> None:
        self.track_window(window_id)
        if self.text:
            self.text = self.text[:-1]

    def clear_for_navigation(self, window_id: str | None) -> None:
        self.track_window(window_id)
        self.reset()

    def is_recent(self, max_age_seconds: float = 3.0) -> bool:
        if not self.last_input_ts:
            return False
        return (time.monotonic() - self.last_input_ts) <= max_age_seconds

    def has_letters(self) -> bool:
        return bool(LETTER_PATTERN.search(self.text))

    def replace(self, new_text: str) -> None:
        self.text = new_text
        self.last_input_ts = time.monotonic()

    @property
    def stripped(self) -> str:
        return self.text.strip()

    def leading_whitespace(self) -> str:
        match = re.match(r"^\s+", self.text)
        return match.group(0) if match else ""

    def trailing_whitespace(self) -> str:
        match = re.search(r"\s+$", self.text)
        return match.group(0) if match else ""
