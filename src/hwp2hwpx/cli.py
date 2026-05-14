"""CLI entry point: ``hwp2hwpx document.hwp``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .converter import convert


def _collect_files(raw_paths: list[str]) -> list[Path]:
    """Expand globs and directories into a flat list of .hwp files."""
    files: list[Path] = []
    for raw in raw_paths:
        p = Path(raw)
        if "*" in raw or "?" in raw:
            # Windows shell doesn't expand globs
            parent = p.parent if str(p.parent) != "." else Path.cwd()
            files.extend(sorted(parent.glob(p.name)))
        elif p.is_dir():
            files.extend(sorted(p.glob("*.hwp")))
        else:
            files.append(p)
    return files


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="hwp2hwpx",
        description="Convert HWP files to HWPX format.",
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="HWP file(s), glob pattern, or directory",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="DIR",
        help="Output directory (default: same as input file)",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories (when input is a directory)",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    args = parser.parse_args(argv)

    # Collect files
    files: list[Path] = []
    for raw in args.input:
        p = Path(raw)
        if "*" in raw or "?" in raw:
            parent = p.parent if str(p.parent) != "." else Path.cwd()
            files.extend(sorted(parent.glob(p.name)))
        elif p.is_dir():
            pattern = "**/*.hwp" if args.recursive else "*.hwp"
            files.extend(sorted(p.glob(pattern)))
        else:
            files.append(p)

    if not files:
        print("No HWP files found.", file=sys.stderr)
        sys.exit(1)

    print(f"hwp2hwpx {__version__}: {len(files)} file(s)")

    ok = 0
    fail = 0
    for f in files:
        try:
            out_path = None
            if args.output_dir:
                out_path = Path(args.output_dir) / (f.stem + ".hwpx")
            result = convert(f, out_path)
            kb = result.stat().st_size / 1024
            print(f"  OK  {kb:.1f}KB | {f.name}")
            ok += 1
        except Exception as exc:
            print(f"  FAIL | {f.name}: {exc}", file=sys.stderr)
            fail += 1

    print(f"\nDone: {ok} OK, {fail} failed")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
