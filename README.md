# PDF Splitter

[![⬇️ Download for macOS](https://img.shields.io/badge/⬇️_Download_for-macOS-blue?style=for-the-badge&logo=apple&logoColor=white)](https://github.com/LizinDev/pdf-splitter/releases/latest/download/PDFSplitter-macos.zip)
[![⬇️ Download for Windows](https://img.shields.io/badge/⬇️_Download_for-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/LizinDev/pdf-splitter/releases/latest/download/PDFSplitter.exe)
[![Latest release](https://img.shields.io/github/v/release/LizinDev/pdf-splitter?style=for-the-badge&label=version)](https://github.com/LizinDev/pdf-splitter/releases/latest)

Split one PDF into several smaller PDFs by page range. Each range can be given
its own file name. A simple graphical app, available in **Portuguese** (default)
and **English**.

- Inclusive page ranges that **may overlap** (e.g. `1-3`, `3-8`, `5-20`)
- Optional custom name per output file
- Colliding output names are kept unique automatically (`_2`, `_3`, …)
- The original PDF is never modified

---

## 📥 For users — download the app

You **don't need to install Python**. Just download the ready-made app from the
**[Releases](../../releases)** page (or use the buttons above).

**On macOS:**
1. Download **`PDFSplitter-macos.zip`**.
2. Unzip it and move **`PDFSplitter.app`** to your *Applications* folder.
3. The **first time**, right-click the app → **Open** → **Open** (needed only
   once, because the app is not signed with a paid Apple certificate; it is
   safe).

**On Windows:**
1. Download **`PDFSplitter.exe`**.
2. Double-click to open it. If Windows shows a blue *SmartScreen* warning,
   click **More info** → **Run anyway** (only the first time; the app is safe).

### How to use
1. **Document** → *Browse* and pick the PDF (the total page count is shown).
2. **Add a page range**: choose *From* / *To*, an optional *Name*, and click
   **Add range**. Repeat for each part — ranges may overlap. The **Page map**
   shows each range as a colored band over the document.
3. **Ranges**: use *Rename* (or double-click), *Remove*, or *Clear all* to edit
   the list.
4. **Output folder** (optional): if left blank, a `<name>_split` folder is
   created next to the PDF.
5. Click **Split PDF**.

---

## 🛠️ For developers

### Run from source
```bash
pip install pypdf
python -m pdfsplit.gui                          # graphical app
python -m pdfsplit.cli file.pdf 1-3 3-8 5-20    # command line
```

The CLI accepts commas, spaces, or newlines as separators and single pages too,
so `"1-3, 5, 7-9"` and `1-3 5 7-9` are equivalent. Use `--out <folder>` to set
the destination (defaults to `<name>_split` next to the PDF):

```bash
python -m pdfsplit.cli file.pdf "1-3, 5, 7-9" --out ./exports
```

### Install as a package
```bash
pip install .
pdfsplit                         # launches the GUI (entry point)
pdfsplit-cli file.pdf 1-3 5 7-9
```

### Build a standalone app
PyInstaller cannot cross-compile, so each app must be built on its own OS:

- **macOS:** run `./build_mac.sh` on a Mac → `dist/PDFSplitter.app`.
- **Windows:** run `powershell -File build_windows.ps1` → `dist\PDFSplitter.exe`.

You usually don't need to build by hand: every push to `main` builds both apps
in GitHub Actions (a macOS runner and a Windows runner) and uploads them as
downloadable artifacts. See [`.github/workflows/build.yml`](.github/workflows/build.yml).

### Publishing a downloadable release
Push a version tag and the same workflow builds both apps and attaches them to a
GitHub Release, giving permanent download links for macOS and Windows:
```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 🌍 Language
The interface defaults to Portuguese. To switch to English, set
`LANG = "en"` in [`pdfsplit/i18n.py`](pdfsplit/i18n.py). All user-facing text
lives in that one file.

## 📂 Project layout
```
pdfsplit/
├── __init__.py
├── core.py     # PDF logic (no UI) — parse ranges, split, dedupe names
├── gui.py      # tkinter interface
├── cli.py      # command-line interface
└── i18n.py     # all translatable text (PT/EN)
run_gui.pyw           # entry point used by the app builders
build_mac.sh          # local macOS build
build_windows.ps1     # local Windows build
assets/               # app icons (icon.png/.ico) + make_icon.py
.github/workflows/    # CI: builds the macOS and Windows apps
```

## License
MIT — see [LICENSE](LICENSE).
