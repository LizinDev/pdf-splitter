#!/usr/bin/env bash
# Build PDFSplitter.app locally on a Mac (optional; CI does this automatically).
#
# Usage on a Mac:
#   chmod +x build_mac.sh
#   ./build_mac.sh
# Output: dist/PDFSplitter.app
set -euo pipefail
cd "$(dirname "$0")"

python3 -m pip install --upgrade pip pyinstaller pypdf
pyinstaller --noconfirm --clean --windowed --name PDFSplitter run_gui.pyw

echo
echo "Done. App is at: dist/PDFSplitter.app"
