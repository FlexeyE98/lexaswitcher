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

    def convert_layout(self, text: str) -> str:
        result: list[str] = []
        for char in text:
            if char in FORWARD_LAYOUT_MAP:
                result.append(FORWARD_LAYOUT_MAP[char])
            elif char in REVERSE_LAYOUT_MAP:
                result.append(REVERSE_LAYOUT_MAP[char])
            else:
                result.append(char)
        return "".join(result)

    def convert_preserving_case(self, text: str) -> str:
        result: list[str] = []
        token = ""
        for char in text:
            if LETTER_PATTERN.match(char):
                token += char
                continue
            if token:
                result.append(self._convert_token(token))
                token = ""
            result.append(self.convert_layout(char))
        if token:
            result.append(self._convert_token(token))
        return "".join(result)

    def _convert_token(self, token: str) -> str:
        lowered = token.lower()
        if lowered in self.exceptions_en:
            return token
        if lowered in self.autofixes:
            return self.autofixes[lowered]
        return self.convert_layout(token).lower()

    def convert_buffer(self, text: str) -> ConversionResult | None:
        source = text.strip()
        if not source:
            return None
        converted = self.convert_preserving_case(source)
        if converted == source:
            return None
        leading = re.match(r"^\s*", text).group(0)
        trailing = re.search(r"\s*$", text).group(0)
        return ConversionResult(
            source=source,
            converted=converted,
            leading_whitespace=leading,
            trailing_whitespace=trailing,
        )

    def target_layout(self, text: str) -> str | None:
        has_latin = bool(LATIN_PATTERN.search(text))
        has_cyrillic = bool(CYRILLIC_PATTERN.search(text))
        if has_cyrillic and not has_latin:
            return "ru"
        if has_latin and not has_cyrillic:
            return "en"
        return None
