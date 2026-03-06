#!/usr/bin/env python3
"""Cross-platform keyboard layout switcher (EN<->RU).

Hotkeys:
- Right Shift release: convert the currently typed phrase.
- Ctrl+Alt+Pause: toggle on/off (Ctrl+Alt+P fallback on keyboards without Pause).
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
from dataclasses import dataclass
from typing import Dict

from pynput import keyboard

FORWARD_LAYOUT_MAP: Dict[str, str] = {
    "`": "ё",
    "~": "Ё",
    "q": "й",
    "Q": "Й",
    "w": "ц",
    "W": "Ц",
    "e": "у",
    "E": "У",
    "r": "к",
    "R": "К",
    "t": "е",
    "T": "Е",
    "y": "н",
    "Y": "Н",
    "u": "г",
    "U": "Г",
    "i": "ш",
    "I": "Ш",
    "o": "щ",
    "O": "Щ",
    "p": "з",
    "P": "З",
    "[": "х",
    "{": "Х",
    "]": "ъ",
    "}": "Ъ",
    "a": "ф",
    "A": "Ф",
    "s": "ы",
    "S": "Ы",
    "d": "в",
    "D": "В",
    "f": "а",
    "F": "А",
    "g": "п",
    "G": "П",
    "h": "р",
    "H": "Р",
    "j": "о",
    "J": "О",
    "k": "л",
    "K": "Л",
    "l": "д",
    "L": "Д",
    ";": "ж",
    ":": "Ж",
    "'": "э",
    '"': "Э",
    "z": "я",
    "Z": "Я",
    "x": "ч",
    "X": "Ч",
    "c": "с",
    "C": "С",
    "v": "м",
    "V": "М",
    "b": "и",
    "B": "И",
    "n": "т",
    "N": "Т",
    "m": "ь",
    "M": "Ь",
    ",": "б",
    "<": "Б",
    ".": "ю",
    ">": "Ю",
    "/": ".",
    "?": ",",
}

REVERSE_LAYOUT_MAP: Dict[str, str] = {v: k for k, v in FORWARD_LAYOUT_MAP.items()}

CLEAR_KEYS = {
    keyboard.Key.delete,
    keyboard.Key.left,
    keyboard.Key.right,
    keyboard.Key.up,
    keyboard.Key.down,
    keyboard.Key.home,
    keyboard.Key.end,
    keyboard.Key.page_up,
    keyboard.Key.page_down,
    keyboard.Key.esc,
    keyboard.Key.enter,
    keyboard.Key.tab,
}

MOD_CTRL = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
MOD_ALT = {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r, keyboard.Key.alt_gr}


@dataclass
class SwitcherState:
    enabled: bool = True
    internal_send_until: float = 0.0
    internal_send_active: bool = False
    synthetic_backspace_pending: int = 0
    synthetic_text_pending: str = ""
    synthetic_pending_until: float = 0.0
    typed_buffer: str = ""
    max_buffer_len: int = 400
    ctrl_pressed: bool = False
    alt_pressed: bool = False


class LexaSwitcher:
    def __init__(self) -> None:
        self.state = SwitcherState()
        self.controller = keyboard.Controller()
        self._send_lock = threading.Lock()

    def _is_internal_send(self) -> bool:
        return self.state.internal_send_active or (time.monotonic() < self.state.internal_send_until)

    def _begin_internal_send(self) -> None:
        self.state.internal_send_active = True

    def _end_internal_send(self) -> None:
        self.state.internal_send_active = False
        self.state.internal_send_until = time.monotonic() + 0.45

    def _register_synthetic_sequence(self, backspaces: int, payload: str) -> None:
        self.state.synthetic_backspace_pending = backspaces
        self.state.synthetic_text_pending = payload
        self.state.synthetic_pending_until = time.monotonic() + 1.5

    def _clear_synthetic_sequence(self) -> None:
        self.state.synthetic_backspace_pending = 0
        self.state.synthetic_text_pending = ""
        self.state.synthetic_pending_until = 0.0

    def _consume_synthetic_event(self, key: keyboard.Key | keyboard.KeyCode) -> bool:
        now = time.monotonic()
        if now > self.state.synthetic_pending_until:
            self._clear_synthetic_sequence()
            return False

        if key == keyboard.Key.backspace and self.state.synthetic_backspace_pending > 0:
            self.state.synthetic_backspace_pending -= 1
            return True

        if isinstance(key, keyboard.KeyCode) and key.char and self.state.synthetic_text_pending:
            expected = self.state.synthetic_text_pending[0]
            if key.char == expected:
                self.state.synthetic_text_pending = self.state.synthetic_text_pending[1:]
                return True

            # Sequence diverged: stop suppressing old synthetic chars.
            self._clear_synthetic_sequence()

        return False

    def _convert_layout(self, text: str) -> str:
        out = []
        for ch in text:
            if ch in FORWARD_LAYOUT_MAP:
                out.append(FORWARD_LAYOUT_MAP[ch])
            elif ch in REVERSE_LAYOUT_MAP:
                out.append(REVERSE_LAYOUT_MAP[ch])
            else:
                out.append(ch)
        return "".join(out)

    def _convert_preserving_case(self, text: str) -> str:
        result = []
        token = []

        def flush_token() -> None:
            if token:
                converted = self._convert_layout("".join(token)).lower()
                result.append(converted)
                token.clear()

        for ch in text:
            if ch.isalpha():
                token.append(ch)
            else:
                flush_token()
                result.append(self._convert_layout(ch))

        flush_token()
        return "".join(result)

    @staticmethod
    def _leading_ws(text: str) -> str:
        i = 0
        while i < len(text) and text[i].isspace():
            i += 1
        return text[:i]

    @staticmethod
    def _trailing_ws(text: str) -> str:
        i = len(text)
        while i > 0 and text[i - 1].isspace():
            i -= 1
        return text[i:]

    def _clear_buffer(self) -> None:
        self.state.typed_buffer = ""

    def _append_char(self, ch: str) -> None:
        if not ch:
            return

        self.state.typed_buffer += ch
        if ch in ".!?":
            self._clear_buffer()
            return

        if len(self.state.typed_buffer) > self.state.max_buffer_len:
            self.state.typed_buffer = self.state.typed_buffer[-200:]

    def _delete_last_char(self) -> None:
        if self.state.typed_buffer:
            self.state.typed_buffer = self.state.typed_buffer[:-1]

    def _toggle_enabled(self) -> None:
        self.state.enabled = not self.state.enabled
        status = "ENABLED" if self.state.enabled else "DISABLED"
        print(f"[{status}]", flush=True)

    def convert_typed_sentence(self) -> None:
        if not self.state.enabled or self._is_internal_send():
            return

        source = self.state.typed_buffer.strip()
        if not source:
            return

        converted = self._convert_preserving_case(source)
        if converted == source:
            return

        leading = self._leading_ws(self.state.typed_buffer)
        trailing = self._trailing_ws(self.state.typed_buffer)
        payload = f"{leading}{converted}{trailing}"

        to_erase = len(self.state.typed_buffer)
        self._clear_buffer()
        self._register_synthetic_sequence(to_erase, payload)

        with self._send_lock:
            self._begin_internal_send()
            try:
                for _ in range(to_erase):
                    self.controller.press(keyboard.Key.backspace)
                    self.controller.release(keyboard.Key.backspace)

                self.controller.type(payload)
            finally:
                self._end_internal_send()

        print(f"[CONVERT] {converted}", flush=True)

    def on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key in MOD_CTRL:
            self.state.ctrl_pressed = True
        if key in MOD_ALT:
            self.state.alt_pressed = True

        if self._consume_synthetic_event(key):
            return

        if self._is_internal_send():
            return

        if self.state.ctrl_pressed and self.state.alt_pressed:
            if key == keyboard.Key.pause:
                self._toggle_enabled()
                return
            if isinstance(key, keyboard.KeyCode) and key.char and key.char.lower() == "p":
                self._toggle_enabled()
                return

        if key == keyboard.Key.backspace:
            self._delete_last_char()
            return

        if key in CLEAR_KEYS:
            self._clear_buffer()
            return

        if isinstance(key, keyboard.KeyCode) and key.char:
            self._append_char(key.char)

    def on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key in MOD_CTRL:
            self.state.ctrl_pressed = False
        if key in MOD_ALT:
            self.state.alt_pressed = False

        if self._is_internal_send():
            return

        if key == keyboard.Key.shift_r:
            self.convert_typed_sentence()


def run_switcher() -> int:
    switcher = LexaSwitcher()
    print("LEXA_SWITCHER started: Right Shift converts phrase, Ctrl+Alt+Pause toggles", flush=True)

    with keyboard.Listener(on_press=switcher.on_press, on_release=switcher.on_release) as listener:
        listener.join()

    return 0


def run_self_test() -> int:
    switcher = LexaSwitcher()
    sample = "ghbdtn blbjn"
    print(switcher._convert_preserving_case(sample))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true", help="Run a quick conversion check and exit")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.self_test:
        return run_self_test()
    return run_switcher()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
