from __future__ import annotations

from dataclasses import dataclass
import re
from pathlib import Path
from importlib import resources

from .layout_map import FORWARD_LAYOUT_MAP, REVERSE_LAYOUT_MAP

LETTER_PATTERN = re.compile(r"[A-Za-zА-Яа-яЁё]")
LATIN_PATTERN = re.compile(r"[A-Za-z]")
CYRILLIC_PATTERN = re.compile(r"[А-Яа-яЁё]")


@dataclass
class ConversionResult:
    source: str
    converted: str
    leading_whitespace: str
    trailing_whitespace: str
    direction: str

    @property
    def final_text(self) -> str:
        return f"{self.leading_whitespace}{self.converted}{self.trailing_whitespace}"


class Converter:
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root
        self.autofixes = self._load_word_set("autofixes.txt", key_value=True)
        self.exceptions_en = self._load_word_set("exceptions-en.txt")

    def _load_word_set(self, name: str, *, key_value: bool = False) -> dict[str, str] | set[str]:
        path = None
        if self.project_root:
            candidate = self.project_root / "data" / name
            if candidate.exists():
                path = candidate

        if path is None:
            package_file = resources.files("lexa_switcher.data").joinpath(name)
            content = package_file.read_text(encoding="utf-8")
        else:
            content = path.read_text(encoding="utf-8")

        if key_value:
            mapping: dict[str, str] = {}
            for raw_line in content.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=>" not in line:
                    continue
                left, right = line.split("=>", 1)
                mapping[left.strip().lower()] = right.strip()
            return mapping

        words: set[str] = set()
        for raw_line in content.splitlines():
            line = raw_line.strip().lower()
            if not line or line.startswith("#"):
                continue
            words.add(line)
        return words

    def detect_direction(self, text: str) -> str | None:
        has_latin = bool(LATIN_PATTERN.search(text))
        has_cyrillic = bool(CYRILLIC_PATTERN.search(text))
        if has_latin and not has_cyrillic:
            return "en_to_ru"
        if has_cyrillic and not has_latin:
            return "ru_to_en"
        return None

    def convert_layout(self, text: str, direction: str) -> str:
        result: list[str] = []
        mapping = FORWARD_LAYOUT_MAP if direction == "en_to_ru" else REVERSE_LAYOUT_MAP
        for char in text:
            result.append(mapping.get(char, char))
        return "".join(result)

    def convert_preserving_case(self, text: str, direction: str) -> str:
        result: list[str] = []
        token = ""
        for char in text:
            if LETTER_PATTERN.match(char):
                token += char
                continue
            if token:
                result.append(self._convert_token(token, direction))
                token = ""
            result.append(self.convert_layout(char, direction))
        if token:
            result.append(self._convert_token(token, direction))
        return "".join(result)

    def _convert_token(self, token: str, direction: str) -> str:
        lowered = token.lower()
        if direction == "en_to_ru":
            if lowered in self.exceptions_en:
                return token
            if lowered in self.autofixes:
                return self.autofixes[lowered]
            return self.convert_layout(token, direction).lower()
        return self.convert_layout(token, direction).lower()

    def convert_buffer(self, text: str) -> ConversionResult | None:
        source = text.strip()
        if not source:
            return None

        direction = self.detect_direction(source)
        if direction is None:
            return None

        converted = self.convert_preserving_case(source, direction)
        if converted == source:
            return None

        leading = re.match(r"^\s*", text).group(0)
        trailing = re.search(r"\s*$", text).group(0)
        return ConversionResult(
            source=source,
            converted=converted,
            leading_whitespace=leading,
            trailing_whitespace=trailing,
            direction=direction,
        )

    def target_layout(self, result: ConversionResult) -> str:
        return "ru" if result.direction == "en_to_ru" else "en"
