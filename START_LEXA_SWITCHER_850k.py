#!/usr/bin/env python3
"""Universal launcher for LEXA_SWITCHER_850k.

Routes execution by OS:
- Windows -> windows/START_LEXA_SWITCHER_850k.ps1
- Linux/macOS -> ubuntu-macos/START_LEXA_SWITCHER_850k.sh
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    os_name = platform.system().lower()

    if os_name == "windows":
        script = root / "windows" / "START_LEXA_SWITCHER_850k.ps1"
        if not script.exists():
            print(f"Missing script: {script}", file=sys.stderr)
            return 1

        cmd = [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script),
            "-ProjectRoot",
            str(root),
        ]
    elif os_name in {"linux", "darwin"}:
        script = root / "ubuntu-macos" / "START_LEXA_SWITCHER_850k.sh"
        if not script.exists():
            print(f"Missing script: {script}", file=sys.stderr)
            return 1

        cmd = ["bash", str(script)]
    else:
        print(f"Unsupported OS: {platform.system()}", file=sys.stderr)
        return 1

    completed = subprocess.run(cmd, cwd=root)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
