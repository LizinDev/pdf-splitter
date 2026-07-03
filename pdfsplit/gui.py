"""Tkinter GUI for splitting a PDF into page ranges.

Run with:  python -m pdfsplit.gui
The heavy lifting lives in ``pdfsplit.core``; this file only handles widgets.
All user-facing text comes from ``pdfsplit.i18n`` (default language: Portuguese).
"""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from tkinter import font as tkfont

from pypdf import PdfReader

from .core import PageRange, SplitError, split_pdf
from .i18n import t

PAD = 10
GAP = 6

# --------------------------------------------------------------------------- #
# Design tokens — dark theme (deep green-grey surfaces, teal/orange/lilac)
# --------------------------------------------------------------------------- #
INK = "#E9ECE8"       # primary text (light on dark)
PAPER = "#151E1A"     # app surface (deep green-grey)
PANEL = "#1D2823"     # inset panel (list, page-map viewer)
INPUT = "#111A16"     # entry & spinbox fields
MUTED = "#8C978F"     # help / secondary text
BORDER = "#2C3A33"    # hairlines
ACCENT = "#3DAA9F"    # primary action (teal)
ACCENT_ACTIVE = "#329089"
SELECT_BG = "#284039"  # treeview selection
TIP_BG = "#0C130F"     # tooltip bubble

# teal / orange / lilac lead — distinguishable band hues for ranges (cycled)
BANDS = ["#3DAA9F", "#E08A4B", "#A98BD6", "#7FB069", "#D07EA6"]


class Tooltip:
    """Simple hover tooltip: a dark bubble shown next to ``widget``."""

    def __init__(self, widget: tk.Widget, text: str, font: tkfont.Font) -> None:
        self.widget = widget
        self.text = text
        self.font = font
        self.tip: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event: object = None) -> None:
        if self.tip is not None:
            return
        x = self.widget.winfo_rootx() + self.widget.winfo_width() + 8
        y = self.widget.winfo_rooty() - 2
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(
            tw, text=self.text, justify="left", background=TIP_BG, foreground=INK,
            font=self.font, wraplength=320, padx=10, pady=7, bd=0,
        ).pack()

    def _hide(self, _event: object = None) -> None:
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


class PdfSplitApp(ttk.Frame):
    """Main application frame."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=(PAD + 4, PAD + 2), style="App.TFrame")
        self.grid(sticky="nsew")
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # fonts prepared by _install_styles for the canvas + help badges
        self.f_tick = master._f_tick
        self.f_band = master._f_band
        self.f_badge = master._f_badge
        self.f_tip = master._f_tip

        # --- state -----------------------------------------------------
        self.pdf_path: Path | None = None
        self.total_pages: int = 0
        self.ranges: list[PageRange] = []
        self.selected_index: int | None = None  # highlighted band in the map
        self._tooltips: list[Tooltip] = []
        self._reader: PdfReader | None = None  # kept so the split reuses it
        self._result_queue: queue.Queue | None = None  # worker -> Tk thread

        # --- build UI --------------------------------------------------
        self._build_header()
        self._build_file()
        self._build_pagemap()
        self._build_picker()
        self._build_list()
        self._build_output()
        self._build_footer()

        self._refresh_tree()
        self._refresh_controls()
        self._draw_map()

    # ------------------------------------------------------------------ #
    # Small UI helpers
    # ------------------------------------------------------------------ #
    def _help_badge(self, parent: tk.Widget, text: str) -> tk.Canvas:
        """A small circular '?' that reveals ``text`` on hover."""
        size = 15
        cv = tk.Canvas(parent, width=size, height=size, bg=PAPER,
                       highlightthickness=0, cursor="question_arrow")
        cv.create_oval(1, 1, size - 1, size - 1, fill=ACCENT, outline="")
        cv.create_text(size / 2 + 0.5, size / 2, text="?", fill="white",
                       font=self.f_badge)
        self._tooltips.append(Tooltip(cv, text, self.f_tip))
        return cv

    def _eyebrow(self, row: int, text: str, help: str | None = None) -> None:
        """An uppercase section label, optionally with a '?' help badge."""
        if help is None:
            ttk.Label(self, text=text.upper(), style="Eyebrow.TLabel").grid(
                row=row, column=0, sticky="w", pady=(PAD, 2)
            )
            return
        fr = ttk.Frame(self, style="App.TFrame")
        fr.grid(row=row, column=0, sticky="w", pady=(PAD, 2))
        ttk.Label(fr, text=text.upper(), style="Eyebrow.TLabel").grid(row=0, column=0)
        self._help_badge(fr, help).grid(row=0, column=1, padx=(6, 0))

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_header(self) -> None:
        head = ttk.Frame(self, style="App.TFrame")
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(0, weight=1)
        # no sticky -> the brand name centers within the weighted column
        ttk.Label(head, text="PDFSplitter", style="Title.TLabel").grid(
            row=0, column=0, pady=(2, 0)
        )
        ttk.Label(head, text=t("app_subtitle"), style="Sub.TLabel").grid(
            row=1, column=0, pady=(1, 0)
        )
        ttk.Separator(head, orient="horizontal").grid(
            row=2, column=0, sticky="ew", pady=(PAD, 2)
        )

    def _build_file(self) -> None:
        self._eyebrow(1, t("section_file"))
        row = ttk.Frame(self, style="App.TFrame")
        row.grid(row=2, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.path_var = tk.StringVar(value=t("no_file"))
        ttk.Label(row, textvariable=self.path_var, style="Path.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(row, text=t("browse"), command=self.choose_file).grid(
            row=0, column=1, padx=(GAP, 0)
        )
        self.pages_var = tk.StringVar(value="")
        ttk.Label(row, textvariable=self.pages_var, style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )

    def _build_pagemap(self) -> None:
        self._eyebrow(3, t("section_map"))
        wrap = tk.Frame(self, bg=BORDER, bd=0)
        wrap.grid(row=4, column=0, sticky="ew")
        wrap.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            wrap, height=self._map_height(), bg=PANEL, highlightthickness=1,
            highlightbackground=BORDER,
        )
        self.canvas.grid(row=0, column=0, sticky="ew", padx=1, pady=1)
        self.canvas.bind("<Configure>", lambda _e: self._draw_map())

    def _build_picker(self) -> None:
        self._eyebrow(5, t("section_add"), help=t("add_help"))
        row = ttk.Frame(self, style="App.TFrame")
        row.grid(row=6, column=0, sticky="ew")

        def field(col: int, label: str) -> ttk.Frame:
            cell = ttk.Frame(row, style="App.TFrame")
            cell.grid(row=0, column=col, sticky="w", padx=(0, GAP + 4))
            ttk.Label(cell, text=label, style="Field.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            return cell

        cell = field(0, t("from"))
        self.from_spin = ttk.Spinbox(cell, from_=1, to=1, width=6)
        self.from_spin.grid(row=1, column=0, pady=(1, 0))

        cell = field(1, t("to"))
        self.to_spin = ttk.Spinbox(cell, from_=1, to=1, width=6)
        self.to_spin.grid(row=1, column=0, pady=(1, 0))

        cell = field(2, t("name_optional"))
        self.name_entry = ttk.Entry(cell, width=22)
        self.name_entry.grid(row=1, column=0, pady=(1, 0))

        add = ttk.Frame(row, style="App.TFrame")
        add.grid(row=0, column=3, sticky="e")
        row.columnconfigure(3, weight=1)
        ttk.Label(add, text=" ", style="Field.TLabel").grid(row=0, column=0)
        self.add_btn = ttk.Button(add, text=t("add_range"), command=self.add_range)
        self.add_btn.grid(row=1, column=0, sticky="e", pady=(1, 0))

    def _build_list(self) -> None:
        self._eyebrow(8, t("section_list"))
        wrap = ttk.Frame(self, style="App.TFrame")
        wrap.grid(row=9, column=0, sticky="nsew")
        self.rowconfigure(9, weight=1)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        cols = ("nome", "paginas", "qtd")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=5)
        self.tree.heading("nome", text=t("col_name"))
        self.tree.heading("paginas", text=t("col_pages"))
        self.tree.heading("qtd", text=t("col_count"))
        self.tree.column("nome", width=280, anchor="w")
        self.tree.column("paginas", width=90, anchor="center")
        self.tree.column("qtd", width=60, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.tag_configure("odd", background="#22302A")
        self.tree.tag_configure("even", background=PANEL)
        self.tree.bind("<Double-Button-1>", lambda _e: self.rename_selected())
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)

        btns = ttk.Frame(wrap, style="App.TFrame")
        btns.grid(row=0, column=2, sticky="n", padx=(GAP, 0))
        ttk.Button(btns, text=t("rename"), width=12, command=self.rename_selected).grid(
            row=0, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Button(btns, text=t("remove"), width=12, command=self.remove_selected).grid(
            row=1, column=0, sticky="ew", pady=(0, 4)
        )
        ttk.Button(btns, text=t("clear_all"), width=12, command=self.clear_ranges).grid(
            row=2, column=0, sticky="ew"
        )

    def _build_output(self) -> None:
        self._eyebrow(10, t("section_output"), help=t("output_help"))
        row = ttk.Frame(self, style="App.TFrame")
        row.grid(row=11, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)

        self.out_var = tk.StringVar(value="")
        ttk.Entry(row, textvariable=self.out_var).grid(row=0, column=0, sticky="ew")
        ttk.Button(row, text=t("browse"), command=self.choose_output).grid(
            row=0, column=1, padx=(GAP, 0)
        )

    def _build_footer(self) -> None:
        ttk.Separator(self, orient="horizontal").grid(
            row=13, column=0, sticky="ew", pady=(PAD + 2, PAD)
        )
        foot = ttk.Frame(self, style="App.TFrame")
        foot.grid(row=14, column=0, sticky="ew")
        foot.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value=t("status_start"))
        ttk.Label(foot, textvariable=self.status_var, style="Muted.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        self.split_btn = ttk.Button(
            foot, text=t("split_button"), style="Accent.TButton", command=self.run_split
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
            reader = PdfReader(path)
            total = len(reader.pages)
        except Exception as exc:
            messagebox.showerror(t("err_open_title"), str(exc))
            return

        self._reader = reader
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
        self._refresh_tree()
        self._refresh_controls()
        self._draw_map()

    def rename_selected(self) -> None:
        index = self._selected_index()
        if index is None:
            return
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
        self._refresh_tree()
        self._select_index(index)

    def remove_selected(self) -> None:
        for index in sorted(self._selected_indices(), reverse=True):
            del self.ranges[index]
        self.selected_index = None
        self._refresh_tree()
        self._refresh_controls()
        self._draw_map()

    def clear_ranges(self) -> None:
        self.ranges.clear()
        self.selected_index = None
        self._refresh_tree()
        self._refresh_controls()
        self._draw_map()

    def choose_output(self) -> None:
        folder = filedialog.askdirectory(title=t("section_output"))
        if folder:
            self.out_var.set(folder)

    def run_split(self) -> None:
        if not self.pdf_path or not self.ranges:
            return
        out_dir = self.out_var.get().strip() or None

        # Run the split in a worker thread so the window stays responsive;
        # results come back through a queue polled with ``after``.
        self.split_btn.configure(state="disabled")
        self.status_var.set(t("status_working"))
        self._result_queue = queue.Queue(maxsize=1)
        threading.Thread(
            target=self._split_worker,
            args=(self.pdf_path, list(self.ranges), out_dir, self._reader),
            daemon=True,
        ).start()
        self.after(100, self._poll_split_result)

    def _split_worker(
        self,
        pdf_path: Path,
        ranges: list[PageRange],
        out_dir: str | None,
        reader: PdfReader | None,
    ) -> None:
        """Background thread: no widget access allowed in here."""
        try:
            written = split_pdf(pdf_path, ranges, out_dir, reader=reader)
            self._result_queue.put(("done", written))
        except SplitError as exc:
            self._result_queue.put(("error", str(exc)))
        except Exception as exc:  # last resort — a failure must never be silent
            self._result_queue.put(("error", f"{type(exc).__name__}: {exc}"))

    def _poll_split_result(self) -> None:
        try:
            kind, payload = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_split_result)
            return

        self._refresh_controls()
        if kind == "error":
            messagebox.showerror(t("err_split_title"), payload)
            self.status_var.set(t("status_failed"))
            return

        written = payload
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
    # Selection helpers (Treeview rows carry their range index as the iid)
    # ------------------------------------------------------------------ #
    def _selected_indices(self) -> list[int]:
        return [int(iid) for iid in self.tree.selection()]

    def _selected_index(self) -> int | None:
        selection = self._selected_indices()
        return selection[0] if selection else None

    def _select_index(self, index: int) -> None:
        iid = str(index)
        if self.tree.exists(iid):
            self.tree.selection_set(iid)

    def _on_select(self, _event: object = None) -> None:
        self.selected_index = self._selected_index()
        self._draw_map()

    # ------------------------------------------------------------------ #
    # List rendering
    # ------------------------------------------------------------------ #
    def _row_name(self, page_range: PageRange) -> str:
        """The file name that would be produced for ``page_range``."""
        if page_range.name:
            return page_range.name
        if self.pdf_path is not None:
            return f"{self.pdf_path.stem}_pages_{page_range.label()}"
        return page_range.label()

    def _refresh_tree(self) -> None:
        """Rebuild the Treeview from ``self.ranges`` (iid == list index)."""
        self.tree.delete(*self.tree.get_children())
        for i, page_range in enumerate(self.ranges):
            tag = "odd" if i % 2 else "even"
            self.tree.insert(
                "", "end", iid=str(i),
                values=(self._row_name(page_range), page_range.label(), page_range.count),
                tags=(tag,),
            )

    def _refresh_controls(self) -> None:
        """Enable/disable controls based on current state."""
        has_file = self.pdf_path is not None
        has_ranges = bool(self.ranges)
        state = "normal" if has_file else "disabled"
        self.from_spin.configure(state=state)
        self.to_spin.configure(state=state)
        self.add_btn.configure(state=state)
        self.split_btn.configure(
            state="normal" if has_file and has_ranges else "disabled"
        )

    # ------------------------------------------------------------------ #
    # Page map
    # ------------------------------------------------------------------ #
    def _map_height(self) -> int:
        lanes = max(1, len(self.ranges))
        return 34 + 22 * lanes + 12

    @staticmethod
    def _tick_step(total: int) -> int:
        """Choose a ruler step giving at most ~8 labels."""
        for step in (1, 2, 5, 10, 20, 25, 50, 100, 200, 500, 1000):
            if total / step <= 8:
                return step
        return total

    def _draw_map(self) -> None:
        canvas = self.canvas
        desired = self._map_height()
        if int(canvas.cget("height")) != desired:
            # Resizing re-fires <Configure>, which redraws — avoid a double draw.
            canvas.configure(height=desired)
            return

        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1:
            return
        left, right = 14, w - 14

        if self.total_pages <= 0:
            canvas.create_text(
                w / 2, desired / 2, text=t("map_empty"), fill=MUTED, font=self.f_band
            )
            return

        span = right - left

        def x(page_boundary: float) -> float:
            return left + span * (page_boundary / self.total_pages)

        # ruler ticks + labels
        base_y = 22
        step = self._tick_step(self.total_pages)
        canvas.create_line(left, base_y, right, base_y, fill=BORDER)
        for p in range(0, self.total_pages + 1):
            xp = x(p)
            major = p == 0 or p == self.total_pages or p % step == 0
            canvas.create_line(
                xp, base_y - (6 if major else 3), xp, base_y, fill=BORDER
            )
            if major:
                canvas.create_text(
                    xp, base_y - 9, text=str(p if p else 1), fill=MUTED,
                    font=self.f_tick, anchor="s",
                )

        # range bands, one lane each
        lane_top = base_y + 8
        lane_h = 22
        for i, page_range in enumerate(self.ranges):
            s, e, name = page_range.start, page_range.end, page_range.name or ""
            color = BANDS[i % len(BANDS)]
            y0 = lane_top + i * lane_h
            y1 = y0 + lane_h - 6
            x0, x1 = x(s - 1) + 1, x(e) - 1
            selected = i == self.selected_index
            canvas.create_rectangle(
                x0, y0, x1, y1, fill=color, outline=INK if selected else color,
                width=2 if selected else 1,
            )
            label = str(s) if s == e else f"{s}–{e}"
            text = f"{label}  {name}".strip()
            cy = (y0 + y1) / 2
            if self.f_band.measure(text) + 12 <= x1 - x0:
                canvas.create_text(x0 + 6, cy, text=text, fill="white",
                                   font=self.f_band, anchor="w")
            elif self.f_band.measure(label) + 12 <= x1 - x0:
                canvas.create_text(x0 + 6, cy, text=label, fill="white",
                                   font=self.f_band, anchor="w")
                if name:
                    canvas.create_text(x1 + 6, cy, text=name, fill=MUTED,
                                       font=self.f_band, anchor="w")
            else:
                canvas.create_text(x1 + 6, cy, text=text, fill=MUTED,
                                   font=self.f_band, anchor="w")


def _install_styles(root: tk.Tk) -> None:
    """Apply the dark theme and prepare fonts used by the canvas + badges."""
    style = ttk.Style(root)
    style.theme_use("clam")

    base = tkfont.nametofont("TkDefaultFont").actual("family")
    f_title = tkfont.Font(family=base, size=22, weight="bold")
    f_sub = tkfont.Font(family=base, size=10)
    f_eyebrow = tkfont.Font(family=base, size=8, weight="bold")
    f_body = tkfont.Font(family=base, size=10)
    f_path = tkfont.Font(family=base, size=11)

    root.configure(bg=PAPER)
    style.configure(".", background=PAPER, foreground=INK, font=f_body)
    style.configure("App.TFrame", background=PAPER)
    style.configure("Title.TLabel", font=f_title, background=PAPER, foreground=ACCENT)
    style.configure("Sub.TLabel", font=f_sub, background=PAPER, foreground=MUTED)
    style.configure("Eyebrow.TLabel", font=f_eyebrow, background=PAPER, foreground=MUTED)
    style.configure("Field.TLabel", font=f_eyebrow, background=PAPER, foreground=MUTED)
    style.configure("Muted.TLabel", font=f_sub, background=PAPER, foreground=MUTED)
    style.configure("Path.TLabel", font=f_path, background=PAPER, foreground=INK)

    style.configure(
        "TButton", background="#26332D", foreground=INK, bordercolor=BORDER,
        borderwidth=1, padding=(12, 5),
    )
    style.map(
        "TButton",
        background=[("active", "#2F3E37"), ("pressed", "#2F3E37")],
        bordercolor=[("active", "#3A4A42")],
        foreground=[("disabled", "#5C685F")],
    )
    style.configure(
        "Accent.TButton", background=ACCENT, foreground="#0C130F",
        padding=(18, 7), font=tkfont.Font(family=base, size=10, weight="bold"),
        borderwidth=0,
    )
    style.map(
        "Accent.TButton",
        background=[("active", ACCENT_ACTIVE), ("pressed", ACCENT_ACTIVE),
                    ("disabled", "#26332D")],
        foreground=[("disabled", "#5C685F")],
    )

    style.configure(
        "TEntry", fieldbackground=INPUT, foreground=INK, insertcolor=INK,
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
    )
    style.configure(
        "TSpinbox", fieldbackground=INPUT, foreground=INK, insertcolor=INK,
        bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
        arrowcolor=INK, arrowsize=12,
    )
    style.map(
        "TSpinbox",
        fieldbackground=[("disabled", PANEL)],
        arrowcolor=[("disabled", MUTED)],
    )

    style.configure(
        "Treeview", background=PANEL, fieldbackground=PANEL, foreground=INK,
        rowheight=26, borderwidth=1, bordercolor=BORDER,
    )
    style.configure(
        "Treeview.Heading", font=f_eyebrow, foreground=MUTED,
        background=PAPER, relief="flat", padding=(6, 6),
    )
    style.map(
        "Treeview",
        background=[("selected", SELECT_BG)],
        foreground=[("selected", INK)],
    )
    style.configure("TSeparator", background=BORDER)
    style.configure(
        "Vertical.TScrollbar", background="#26332D", troughcolor=PAPER,
        bordercolor=BORDER, arrowcolor=MUTED,
    )
    style.map("Vertical.TScrollbar", background=[("active", "#2F3E37")])

    # fonts the page-map canvas and help badges reach for via ``master``
    root._f_tick = tkfont.Font(family=base, size=8)
    root._f_band = tkfont.Font(family=base, size=9, weight="bold")
    root._f_badge = tkfont.Font(family=base, size=9, weight="bold")
    root._f_tip = tkfont.Font(family=base, size=9)


def main() -> None:
    root = tk.Tk()
    root.title(t("app_title"))
    root.minsize(680, 720)
    root.geometry("720x760")
    _install_styles(root)
    PdfSplitApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
