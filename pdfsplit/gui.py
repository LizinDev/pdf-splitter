"""Tkinter GUI for splitting a PDF into page ranges.

Run with:  python -m pdfsplit.gui
The heavy lifting lives in ``pdfsplit.core``; this file only handles widgets.
All user-facing text comes from ``pdfsplit.i18n`` (default language: Portuguese).
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from pypdf import PdfReader

from .core import PageRange, SplitError, split_pdf
from .i18n import t

PAD = 8


class PdfSplitApp(ttk.Frame):
    """Main application frame."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=PAD)
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # --- state -----------------------------------------------------
        self.pdf_path: Path | None = None
        self.total_pages: int = 0
        self.ranges: list[PageRange] = []

        # --- build UI --------------------------------------------------
        self._build_file_row()
        self._build_range_picker()
        self._build_range_list()
        self._build_output_row()
        self._build_actions()

        self._refresh_controls()

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_file_row(self) -> None:
        frame = ttk.LabelFrame(self, text=t("section_file"), padding=PAD)
        frame.grid(row=0, column=0, sticky="ew", pady=(0, PAD))
        frame.columnconfigure(0, weight=1)

        self.path_var = tk.StringVar(value=t("no_file"))
        ttk.Label(frame, textvariable=self.path_var, foreground="#555").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(frame, text=t("browse"), command=self.choose_file).grid(
            row=0, column=1, padx=(PAD, 0)
        )
        self.pages_var = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.pages_var).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

    def _build_range_picker(self) -> None:
        frame = ttk.LabelFrame(self, text=t("section_add"), padding=PAD)
        frame.grid(row=1, column=0, sticky="ew", pady=(0, PAD))

        ttk.Label(frame, text=t("from")).grid(row=0, column=0)
        self.from_spin = ttk.Spinbox(frame, from_=1, to=1, width=6)
        self.from_spin.grid(row=0, column=1, padx=4)

        ttk.Label(frame, text=t("to")).grid(row=0, column=2)
        self.to_spin = ttk.Spinbox(frame, from_=1, to=1, width=6)
        self.to_spin.grid(row=0, column=3, padx=4)

        ttk.Label(frame, text=t("name")).grid(row=0, column=4, padx=(PAD, 0))
        self.name_entry = ttk.Entry(frame, width=18)
        self.name_entry.grid(row=0, column=5, padx=4)

        self.add_btn = ttk.Button(frame, text=t("add_range"), command=self.add_range)
        self.add_btn.grid(row=0, column=6, padx=(PAD, 0))

        ttk.Label(frame, text=t("add_help"), foreground="#777", wraplength=560).grid(
            row=1, column=0, columnspan=7, sticky="w", pady=(6, 0)
        )

    def _build_range_list(self) -> None:
        frame = ttk.LabelFrame(self, text=t("section_list"), padding=PAD)
        frame.grid(row=2, column=0, sticky="nsew", pady=(0, PAD))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self.listbox = tk.Listbox(frame, height=6, activestyle="none")
        self.listbox.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.listbox.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=scroll.set)

        self.listbox.bind("<Double-Button-1>", lambda _event: self.rename_selected())

        btns = ttk.Frame(frame)
        btns.grid(row=0, column=2, sticky="n", padx=(PAD, 0))
        ttk.Button(btns, text=t("rename"), command=self.rename_selected).grid(
            row=0, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Button(btns, text=t("remove"), command=self.remove_selected).grid(
            row=1, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Button(btns, text=t("clear_all"), command=self.clear_ranges).grid(
            row=2, column=0, sticky="ew"
        )

    def _build_output_row(self) -> None:
        frame = ttk.LabelFrame(self, text=t("section_output"), padding=PAD)
        frame.grid(row=3, column=0, sticky="ew", pady=(0, PAD))
        frame.columnconfigure(0, weight=1)

        self.out_var = tk.StringVar(value="")
        entry = ttk.Entry(frame, textvariable=self.out_var)
        entry.grid(row=0, column=0, sticky="ew")
        ttk.Button(frame, text=t("browse"), command=self.choose_output).grid(
            row=0, column=1, padx=(PAD, 0)
        )
        ttk.Label(frame, text=t("output_help"), foreground="#777", wraplength=560).grid(
            row=1, column=0, columnspan=2, sticky="w", pady=(4, 0)
        )

    def _build_actions(self) -> None:
        frame = ttk.Frame(self)
        frame.grid(row=4, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value=t("status_start"))
        ttk.Label(frame, textvariable=self.status_var, foreground="#333").grid(
            row=0, column=0, sticky="w"
        )
        self.split_btn = ttk.Button(
            frame, text=t("split_button"), command=self.run_split
        )
        self.split_btn.grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title=t("browse"),
            filetypes=[("PDF", "*.pdf"), ("*", "*.*")],
        )
        if not path:
            return
        try:
            total = len(PdfReader(path).pages)
        except Exception as exc:
            messagebox.showerror(t("err_open_title"), str(exc))
            return

        self.pdf_path = Path(path)
        self.total_pages = total
        self.path_var.set(str(self.pdf_path))
        self.pages_var.set(t("pages_count", n=total))
        self.from_spin.configure(from_=1, to=total)
        self.to_spin.configure(from_=1, to=total)
        self.from_spin.set(1)
        self.to_spin.set(min(total, 1))
        self.name_entry.delete(0, tk.END)
        self.clear_ranges()
        self.status_var.set(t("status_added"))
        self._refresh_controls()

    def add_range(self) -> None:
        try:
            page_range = PageRange(
                int(self.from_spin.get()),
                int(self.to_spin.get()),
                self.name_entry.get(),
            )
            if page_range.end > self.total_pages:
                raise SplitError(
                    t("err_exceeds", label=page_range.label(), total=self.total_pages)
                )
        except (SplitError, ValueError) as exc:
            messagebox.showwarning(t("err_invalid_range_title"), str(exc))
            return

        self.ranges.append(page_range)
        self.name_entry.delete(0, tk.END)
        self._refresh_listbox()
        self._refresh_controls()

    def rename_selected(self) -> None:
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0]
        current = self.ranges[index]
        new_name = simpledialog.askstring(
            t("rename_title"),
            t("rename_prompt", label=current.label()),
            initialvalue=current.name or "",
            parent=self,
        )
        if new_name is None:  # user cancelled
            return
        self.ranges[index] = replace(current, name=new_name)
        self._refresh_listbox()
        self.listbox.selection_set(index)

    def remove_selected(self) -> None:
        for index in reversed(self.listbox.curselection()):
            del self.ranges[index]
        self._refresh_listbox()
        self._refresh_controls()

    def clear_ranges(self) -> None:
        self.ranges.clear()
        self._refresh_listbox()
        self._refresh_controls()

    def choose_output(self) -> None:
        folder = filedialog.askdirectory(title=t("section_output"))
        if folder:
            self.out_var.set(folder)

    def run_split(self) -> None:
        if not self.pdf_path or not self.ranges:
            return
        out_dir = self.out_var.get().strip() or None
        try:
            written = split_pdf(self.pdf_path, self.ranges, out_dir)
        except SplitError as exc:
            messagebox.showerror(t("err_split_title"), str(exc))
            self.status_var.set(t("status_failed"))
            return

        folder = written[0].parent
        self.status_var.set(t("status_done", n=len(written), folder=folder))
        messagebox.showinfo(
            t("done_title"),
            t(
                "done_body",
                n=len(written),
                files="\n".join(p.name for p in written),
                folder=folder,
            ),
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _row_text(page_range: PageRange) -> str:
        """Human-readable list entry for a range."""
        if page_range.name:
            return t(
                "row_named",
                name=page_range.name,
                label=page_range.label(),
                count=page_range.count,
            )
        return t(
            "row_unnamed", label=page_range.label(), count=page_range.count
        )

    def _refresh_listbox(self) -> None:
        """Rebuild the listbox from ``self.ranges``."""
        self.listbox.delete(0, tk.END)
        for page_range in self.ranges:
            self.listbox.insert(tk.END, self._row_text(page_range))

    def _refresh_controls(self) -> None:
        """Enable/disable controls based on current state."""
        has_file = self.pdf_path is not None
        has_ranges = bool(self.ranges)
        self.from_spin.configure(state="normal" if has_file else "disabled")
        self.to_spin.configure(state="normal" if has_file else "disabled")
        self.add_btn.configure(state="normal" if has_file else "disabled")
        self.split_btn.configure(
            state="normal" if has_file and has_ranges else "disabled"
        )


def main() -> None:
    root = tk.Tk()
    root.title(t("app_title"))
    root.minsize(600, 560)
    PdfSplitApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
