# PDF Splitter / Divisor de PDF

Split one PDF into several smaller PDFs by page range. Each range can be given
its own file name. Simple graphical app, available in **Portuguese** (default)
and **English**.

- Inclusive page ranges that **may overlap** (e.g. `1-3`, `3-8`, `5-20`)
- Optional custom name per output file
- The original PDF is never modified

---

## 📥 Para a usuária — baixar o aplicativo (macOS)

Você **não precisa instalar o Python**. Basta baixar o aplicativo pronto:

1. Abra a página de **[Releases](../../releases)** deste repositório.
2. Baixe o arquivo **`PDFSplitter-macos.zip`**.
3. Descompacte e mova **`PDFSplitter.app`** para a pasta *Aplicativos*.
4. Na **primeira vez**, clique com o botão direito no app → **Abrir** →
   **Abrir** (isso é necessário só uma vez porque o app não tem assinatura
   paga da Apple; ele é seguro).

### Como usar
1. **Arquivo PDF** → *Procurar* e escolha o PDF (mostra o total de páginas).
2. **Adicionar um intervalo de páginas**: escolha *De* / *Até*, um *Nome*
   opcional, e clique em **Adicionar intervalo**. Repita para cada trecho —
   os intervalos podem se sobrepor.
3. **Intervalos a exportar**: use *Renomear* (ou duplo clique) e *Remover*.
4. **Pasta de destino** (opcional): em branco, cria uma pasta `<nome>_split`
   ao lado do PDF.
5. Clique em **Dividir PDF**.

---

## 🛠️ For developers

### Run from source
```bash
pip install pypdf
python -m pdfsplit.gui        # graphical app
python -m pdfsplit.cli file.pdf 1-3 3-8 5-20   # command line
```

### Install as a package
```bash
pip install .
pdfsplit        # launches the GUI (entry point)
pdfsplit-cli file.pdf 1-3 5 7-9
```

### Build a standalone app
- **macOS:** handled automatically by GitHub Actions on every push (see below),
  or run `./build_mac.sh` on a Mac → `dist/PDFSplitter.app`.
- **Windows:** run `powershell -File build_windows.ps1` → `dist\PDFSplitter.exe`.

> PyInstaller cannot cross-compile: a Mac app must be built on macOS, a Windows
> exe on Windows. That is why the macOS build runs in CI on a macOS runner.

### Releasing a downloadable Mac app
Push a version tag and the workflow builds the `.app` and attaches it to a
GitHub Release:
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
├── core.py     # PDF logic (no UI) — parse ranges, split
├── gui.py      # tkinter interface
├── cli.py      # command-line interface
└── i18n.py     # all translatable text (PT/EN)
run_gui.pyw            # entry point used by the app builders
build_mac.sh          # local macOS build
build_windows.ps1     # local Windows build
.github/workflows/    # CI: builds the macOS app
```

## License
MIT — see [LICENSE](LICENSE).
