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

# Build the .icns from assets/icon.png
mkdir -p icon.iconset
for pair in "16:icon_16x16" "32:icon_16x16@2x" "32:icon_32x32" "64:icon_32x32@2x" \
            "128:icon_128x128" "256:icon_128x128@2x" "256:icon_256x256" \
            "512:icon_256x256@2x" "512:icon_512x512" "1024:icon_512x512@2x"; do
    sz="${pair%%:*}"; name="${pair##*:}"
    sips -z "$sz" "$sz" assets/icon.png --out "icon.iconset/${name}.png" >/dev/null
done
iconutil -c icns icon.iconset -o assets/icon.icns
rm -rf icon.iconset

pyinstaller --noconfirm --clean --windowed \
    --icon assets/icon.icns --name PDFSplitter run_gui.pyw

echo
echo "Done. App is at: dist/PDFSplitter.app"
