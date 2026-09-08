import unittest

from pathlib import Path
from tempfile import TemporaryDirectory

from pypdf import PdfWriter

from pdfsplit.core import PageRange, split_pdf


class SplitPdfTest(unittest.TestCase):
    def test_split_does_not_overwrite_preexisting_output(self):
        with TemporaryDirectory() as directory:
            tmp_path = Path(directory)
            source = tmp_path / "document.pdf"
            source_writer = PdfWriter()
            source_writer.add_blank_page(width=72, height=72)
            with source.open("wb") as handle:
                source_writer.write(handle)

            output_dir = tmp_path / "output"
            output_dir.mkdir()
            existing = output_dir / "document_pages_1.pdf"
            existing_writer = PdfWriter()
            existing_writer.add_blank_page(width=144, height=144)
            with existing.open("wb") as handle:
                existing_writer.write(handle)
            original = existing.read_bytes()

            written = split_pdf(source, [PageRange(1, 1)], output_dir)

            self.assertEqual(written, [output_dir / "document_pages_1_2.pdf"])
            self.assertEqual(existing.read_bytes(), original)
