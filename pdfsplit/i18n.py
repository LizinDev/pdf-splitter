"""Lightweight translations for pdfsplit.

All user-facing text lives here so the app can be translated without touching
logic or UI code. Switch the whole app's language with one constant::

    from pdfsplit import i18n
    i18n.LANG = "en"   # or "pt"

Usage:  i18n.t("split_button")  ->  the string for the current language.
"""

from __future__ import annotations

# Default language for the app. "pt" = Portuguese, "en" = English.
LANG = "pt"

TEXTS: dict[str, dict[str, str]] = {
    "pt": {
        # --- window / sections ---
        "app_title": "Divisor de PDF",
        "app_subtitle": "Divida PDFs por intervalo de páginas",
        "section_file": "Documento",
        "section_map": "Mapa de páginas",
        "section_add": "Adicionar intervalo",
        "section_list": "Intervalos",
        "section_output": "Pasta de destino",
        "map_empty": "Selecione um PDF para ver o mapa de páginas.",
        # --- file row ---
        "no_file": "Nenhum arquivo selecionado",
        "browse": "Procurar…",
        "pages_count": "{n} páginas",
        # --- add row ---
        "from": "De",
        "to": "Até",
        "name": "Nome",
        "name_optional": "Nome (opcional)",
        "add_range": "Adicionar intervalo",
        # --- list columns ---
        "col_name": "Nome do arquivo",
        "col_pages": "Páginas",
        "col_count": "Qtd",
        "add_help": (
            "Os intervalos incluem as duas páginas e podem se sobrepor "
            "(ex.: 1-3, 3-8, 5-20). O nome é opcional — em branco, usa um "
            "nome de arquivo automático."
        ),
        # --- list buttons ---
        "rename": "Renomear",
        "remove": "Remover",
        "clear_all": "Limpar tudo",
        # --- output row ---
        "output_help": (
            "Deixe em branco para criar uma pasta '<nome>_split' ao lado do PDF."
        ),
        # --- actions / status ---
        "status_start": "Selecione um PDF para começar.",
        "status_added": "Adicione os intervalos desejados e clique em Dividir PDF.",
        "status_failed": "A divisão falhou.",
        "status_done": "{n} arquivo(s) criado(s) em {folder}",
        "split_button": "Dividir PDF",
        # --- dialogs ---
        "err_open_title": "Não foi possível abrir o PDF",
        "err_invalid_range_title": "Intervalo inválido",
        "err_split_title": "Falha na divisão",
        "rename_title": "Renomear intervalo",
        "rename_prompt": "Nome do arquivo para as páginas {label}:",
        "done_title": "Concluído",
        "done_body": (
            "{n} arquivo(s) criado(s):\n\n{files}\n\nLocal:\n{folder}"
        ),
        # --- core errors ---
        "err_page_start": "As páginas começam em 1 (recebido {n}).",
        "err_backwards": (
            "O intervalo {start}-{end} está invertido "
            "(o fim deve ser maior ou igual ao início)."
        ),
        "err_empty_range": "Intervalo vazio.",
        "err_invalid_token": "'{token}' não é uma página ou intervalo válido.",
        "err_no_ranges": "Nenhum intervalo de páginas foi informado.",
        "err_exceeds": "O intervalo {label} ultrapassa o documento ({total} páginas).",
        "err_not_found": "Arquivo não encontrado: {path}",
        "err_cannot_read": "Não foi possível ler '{name}': {error}",
    },
    "en": {
        "app_title": "PDF Splitter",
        "app_subtitle": "Split PDFs by page range",
        "section_file": "Document",
        "section_map": "Page map",
        "section_add": "Add a page range",
        "section_list": "Ranges",
        "section_output": "Output folder",
        "map_empty": "Select a PDF to see the page map.",
        "no_file": "No file selected",
        "browse": "Browse…",
        "pages_count": "{n} pages",
        "from": "From",
        "to": "To",
        "name": "Name",
        "name_optional": "Name (optional)",
        "add_range": "Add range",
        "col_name": "File name",
        "col_pages": "Pages",
        "col_count": "Count",
        "add_help": (
            "Ranges are inclusive and may overlap (e.g. 1-3, 3-8, 5-20). "
            "Name is optional — blank uses an automatic file name."
        ),
        "rename": "Rename",
        "remove": "Remove",
        "clear_all": "Clear all",
        "output_help": (
            "Leave blank to create a '<name>_split' folder next to the PDF."
        ),
        "status_start": "Select a PDF to begin.",
        "status_added": "Add the ranges you want, then click Split PDF.",
        "status_failed": "Split failed.",
        "status_done": "Created {n} file(s) in {folder}",
        "split_button": "Split PDF",
        "err_open_title": "Cannot open PDF",
        "err_invalid_range_title": "Invalid range",
        "err_split_title": "Split failed",
        "rename_title": "Rename range",
        "rename_prompt": "File name for pages {label}:",
        "done_title": "Done",
        "done_body": "Created {n} file(s):\n\n{files}\n\nLocation:\n{folder}",
        "err_page_start": "Page numbers start at 1 (got {n}).",
        "err_backwards": "Range {start}-{end} is backwards (end must be >= start).",
        "err_empty_range": "Empty range.",
        "err_invalid_token": "'{token}' is not a valid page or range.",
        "err_no_ranges": "No page ranges were provided.",
        "err_exceeds": "Range {label} exceeds the document ({total} pages).",
        "err_not_found": "File not found: {path}",
        "err_cannot_read": "Could not read '{name}': {error}",
    },
}


def t(key: str, **kwargs: object) -> str:
    """Return the translated string for ``key`` in the current LANG.

    Falls back to English, then to the key itself, so a missing translation
    never crashes the app.
    """
    template = TEXTS.get(LANG, {}).get(key) or TEXTS["en"].get(key) or key
    return template.format(**kwargs) if kwargs else template
