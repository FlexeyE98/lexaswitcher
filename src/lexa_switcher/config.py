from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path

from .defaults import DEFAULT_CONFIG


@dataclass
class AppConfig:
    project_root: Path
    config_path: Path
    enabled: bool = True
    notifications: bool = True
    max_buffer_length: int = 400
    excluded_apps: tuple[str, ...] = ()

    @classmethod
    def load(cls, project_root: Path | None = None) -> "AppConfig":
        if project_root is None:
            project_root = Path.cwd()
        config_path = project_root / "config.ini"

        parser = ConfigParser()
        parser.read_dict(DEFAULT_CONFIG)
        if config_path.exists():
            parser.read(config_path, encoding="utf-8")

        excluded = tuple(
            item.strip().lower()
            for item in parser.get("apps", "excluded", fallback="").split(",")
            if item.strip()
        )

        return cls(
            project_root=project_root,
            config_path=config_path,
            enabled=True,
            notifications=parser.getboolean("general", "notifications", fallback=True),
            max_buffer_length=400,
            excluded_apps=excluded,
        )
