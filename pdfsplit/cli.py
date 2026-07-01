"""Command-line interface for splitting a PDF by page range.

Examples:
    python -m pdfsplit.cli myfile.pdf 1-3 3-8 5-20
    python -m pdfsplit.cli myfile.pdf "1-3, 5, 7-9" --out /path/to/exports

Prefer the graphical app? Run:  python -m pdfsplit.gui
"""

from __future__ import annotations

import argparse
import sys

from .core import SplitError, parse_ranges, split_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split a PDF into page ranges.")
    parser.add_argument("pdf", help="Path to the source PDF.")
    parser.add_argument(
        "ranges",
        nargs="+",
        help="Inclusive ranges, e.g. 1-3 3-8 5-20 (may overlap).",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output folder (default: '<name>_split' next to the PDF).",
    )
    args = parser.parse_args(argv)

    try:
        ranges = parse_ranges(" ".join(args.ranges))
        written = split_pdf(args.pdf, ranges, args.out)
    except SplitError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Created {len(written)} file(s) in {written[0].parent}:")
    for path in written:
        print(f"  {path.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
