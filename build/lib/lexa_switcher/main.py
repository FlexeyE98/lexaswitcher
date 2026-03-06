from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .app import LexaSwitcherApp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Background layout switcher")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root containing config.ini and data/",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = LexaSwitcherApp.create(args.project_root)
    try:
        app.run()
    except NotImplementedError as exc:
        logging.getLogger(__name__).error(str(exc))
        return 2
    except KeyboardInterrupt:
        app.stop()
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
