"""Core PDF-splitting logic.

This module is intentionally free of any UI code so it can be reused from a
GUI, a command-line script, or automated tests. It exposes:

    * PageRange           - a validated, inclusive 1-based page range
    * parse_ranges        - turn user text ("1-3, 5, 7-9") into PageRanges
    * split_pdf           - write one output PDF per range
    * SplitError          - raised for any user-facing problem

All page numbers in the public API are 1-based and inclusive, matching what a
person sees in a PDF viewer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from pypdf import PdfReader, PdfWriter

from .i18n import t


class SplitError(Exception):
    """Raised for problems that should be shown to the user."""


_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def sanitize_filename(name: str) -> str:
    """Make ``name`` safe to use as a Windows/macOS/Linux file stem."""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name).strip()
    return cleaned.rstrip(". ")  # trailing dots/spaces are invalid on Windows


@dataclass(frozen=True)
class PageRange:
    """An inclusive, 1-based range of pages. A single page has start == end.

    An optional ``name`` sets a custom output file name for this range; when
    omitted, a name is derived from the source file and the page numbers.
    """

    start: int
    end: int
    name: str | None = None

    def __post_init__(self) -> None:
        if self.start < 1:
            raise SplitError(t("err_page_start", n=self.start))
        if self.end < self.start:
            raise SplitError(t("err_backwards", start=self.start, end=self.end))
        # Normalise blank names to None so the default naming kicks in.
        if self.name is not None and not self.name.strip():
            object.__setattr__(self, "name", None)

    @property
    def count(self) -> int:
        return self.end - self.start + 1

    def zero_based_indices(self) -> range:
        """Page indices for pypdf (0-based, end exclusive)."""
        return range(self.start - 1, self.end)

    def label(self) -> str:
        return str(self.start) if self.start == self.end else f"{self.start}-{self.end}"

    @classmethod
    def parse(cls, token: str) -> "PageRange":
        """Parse a single token like '5' or '1-3' into a PageRange."""
        token = token.strip()
        if not token:
            raise SplitError(t("err_empty_range"))
        try:
            if "-" in token:
                start_str, end_str = token.split("-", 1)
                return cls(int(start_str), int(end_str))
            page = int(token)
            return cls(page, page)
        except ValueError:
            raise SplitError(t("err_invalid_token", token=token))


def parse_ranges(text: str) -> list[PageRange]:
    """Parse free-form text into a list of PageRanges.

    Accepts commas, whitespace, and/or newlines as separators, so all of
    "1-3, 5, 7-9", "1-3 5 7-9" and "1-3\n5\n7-9" are equivalent.
    """
    tokens = re.split(r"[,\s]+", text.strip())
    ranges = [PageRange.parse(token) for token in tokens if token]
    if not ranges:
        raise SplitError(t("err_no_ranges"))
    return ranges


def validate_against(ranges: Iterable[PageRange], total_pages: int) -> None:
    """Raise SplitError if any range falls outside a document of total_pages."""
    for r in ranges:
        if r.end > total_pages:
            raise SplitError(t("err_exceeds", label=r.label(), total=total_pages))


def output_path_for(source: Path, out_dir: Path, page_range: PageRange) -> Path:
    """Build the output file path for a given range.

    Uses the range's custom ``name`` when set, otherwise falls back to
    "<source stem>_pages_<range>".
    """
    if page_range.name:
        stem = sanitize_filename(page_range.name) or page_range.label()
    else:
        stem = f"{source.stem}_pages_{page_range.label()}"
    return out_dir / f"{stem}.pdf"


def _dedupe(path: Path, taken: set[Path]) -> Path:
    """Return ``path`` or, if already taken, the same name with a _2/_3 suffix."""
    if path not in taken:
        return path
    counter = 2
    while True:
        candidate = path.with_name(f"{path.stem}_{counter}{path.suffix}")
        if candidate not in taken:
            return candidate
        counter += 1


def split_pdf(
    input_path: str | Path,
    ranges: Sequence[PageRange],
    output_dir: str | Path | None = None,
    reader: PdfReader | None = None,
) -> list[Path]:
    """Split ``input_path`` into one PDF per range.

    Args:
        input_path:  Path to the source PDF.
        ranges:      Page ranges to extract (1-based, inclusive). May overlap.
        output_dir:  Where to write results. Defaults to a "<name>_split"
                     folder next to the source file.
        reader:      An already-open PdfReader for ``input_path``. Passing one
                     avoids loading the whole file into memory a second time;
                     the trade-off is that changes made to the file on disk
                     since it was opened are not picked up.

    Returns:
        The list of written file paths.

    Raises:
        SplitError: If the file is missing/unreadable, a range is invalid, or
            an output file cannot be written.
    """
    source = Path(input_path)
    if not source.is_file():
        raise SplitError(t("err_not_found", path=source))

    if not ranges:
        raise SplitError(t("err_no_ranges"))

    try:
        if reader is None:
            reader = PdfReader(source)
        total = len(reader.pages)
    except Exception as exc:  # pypdf raises a variety of errors
        raise SplitError(t("err_cannot_read", name=source.name, error=exc)) from exc

    validate_against(ranges, total)

    out_dir = Path(output_dir) if output_dir else source.parent / f"{source.stem}_split"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise SplitError(t("err_out_dir", path=out_dir, error=exc)) from exc

    written: list[Path] = []
    taken: set[Path] = set()
    for page_range in ranges:
        try:
            writer = PdfWriter()
            # pypdf parses page content lazily, so corrupt pages surface here.
            for index in page_range.zero_based_indices():
                writer.add_page(reader.pages[index])

            destination = _dedupe(output_path_for(source, out_dir, page_range), taken)
            taken.add(destination)
            with open(destination, "wb") as handle:
                writer.write(handle)
        except SplitError:
            raise
        except Exception as exc:
            raise SplitError(
                t("err_write", label=page_range.label(), error=exc)
            ) from exc
        written.append(destination)

    return written
