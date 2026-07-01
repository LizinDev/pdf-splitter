"""pdfsplit - split a PDF into multiple files by page range.

Public API lives in ``pdfsplit.core``; the tkinter interface is in
``pdfsplit.gui``.
"""

from .core import (
    PageRange,
    SplitError,
    parse_ranges,
    sanitize_filename,
    split_pdf,
    validate_against,
)

__all__ = [
    "PageRange",
    "SplitError",
    "parse_ranges",
    "sanitize_filename",
    "split_pdf",
    "validate_against",
]

__version__ = "1.0.0"
