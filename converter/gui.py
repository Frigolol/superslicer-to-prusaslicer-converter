"""Window (tkinter): choose what to transfer, pick profiles, confirm doubtful settings."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .batch import Options, convert, destination, save
from .common import (KINDS, app_dir, default_overrides_path, list_profiles, parse_overrides,
                     slicer_dir, valid_choice)
from .theme import FONT, MONO, Theme, dark_title_bar

TITLES = {"print": "Print settings", "filament": "Filaments", "printer": "Printers"}
_theme = None   # Theme of the running window, used by dialogs


def _card(parent, padding=14):
    """White (or dark) rounded-looking panel."""
    outer = ttk.Frame(parent, style="Card.TFrame")
    inner = ttk.Frame(outer, style="Inner.TFrame", padding=padding)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


def _prepare_dialog(win):
    if _theme:
        win.configure(bg=_theme.c["bg"])
        dark_title_bar(win, _theme.mode == "dark")


# ---------------------------------------------------------------------------
# Doubts dialog
# ---------------------------------------------------------------------------
def ask_doubts(parent, doubts, title):
    """Modal window: one drop-down per doubt. Returns {key: value}, or None if skipped."""
    win = tk.Toplevel(parent)
    win.title("Please confirm these settings")
    win.transient(parent)
    win.resizable(False, False)
    _prepare_dialog(win)
    frm = ttk.Frame(win, padding=(20, 16))
    frm.pack(fill="both", expand=True)
    ttk.Label(frm, text=title, font=(FONT, 13, "bold")).pack(anchor="w")
    ttk.Label(frm, text="These settings could not be converted with certainty. "
                        "Keep the proposed value or choose another one.",
              style="Sub.TLabel", wraplength=620, justify="left").pack(anchor="w", pady=(2, 12))

    vars_ = {}
    for d in doubts:
        outer, card = _card(frm, padding=(14, 10))
        outer.pack(fill="x", pady=4)
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text=d["key"], style="CardHead.TLabel", font=(MONO, 10, "bold")).grid(
            row=0, column=0, sticky="w")
        ttk.Label(card, text=d["note"], style="CardMuted.TLabel", wraplength=600, justify="left").grid(
            row=1, column=0, sticky="w", pady=(1, 6))
        labels = d.get("labels") or {}
        shown = [labels.get(o, o) for o in d["options"]]
        v = tk.StringVar(value=shown[0])
        ttk.Combobox(card, textvariable=v, values=shown, width=max(24, min(78, max(len(x) for x in shown))),
                     state="readonly" if d["closed"] else "normal").grid(row=2, column=0, sticky="w")
        v.back = dict(zip(shown, d["options"]))
        vars_[d["key"]] = v

    result = {}

    def value(k):
        v = vars_[k]
        return v.back.get(v.get(), v.get().strip())

    def ok():
        bad = [d["key"] for d in doubts if not valid_choice(d, value(d["key"]))]
        if bad:
            messagebox.showerror("Invalid value", "A number is expected for:\n" + "\n".join(bad), parent=win)
            return
        result.update({k: value(k) for k in vars_})
        win.destroy()

    btns = ttk.Frame(frm)
    btns.pack(fill="x", pady=(14, 0))
    ttk.Button(btns, text="OK", style="Accent.TButton", command=ok).pack(side="right")
    ttk.Button(btns, text="Skip this profile", style="Ghost.TButton", command=win.destroy).pack(
        side="right", padx=8)
    win.bind("<Return>", lambda e: ok())
    win.bind("<Escape>", lambda e: win.destroy())
    win.update_idletasks()
    if parent.winfo_viewable():
        x = parent.winfo_rootx() + (parent.winfo_width() - win.winfo_width()) // 2
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - win.winfo_height()) // 3)
        win.geometry(f"+{max(0, x)}+{max(0, y)}")
    win.grab_set()
    parent.wait_window(win)
    return result or None


# ---------------------------------------------------------------------------
# Conversion of a list of files (window and drag-and-drop)
# ---------------------------------------------------------------------------
def process(parent, items, opts, ask=True, log=print):
    """items: [(path, output folder or None)]. Returns (converted, skipped, errors)."""
    convs = []
    errors = 0
    for path, out_dir in items:
        try:
            conv = convert(path, opts)
            convs.append((conv, destination(conv, out_dir)))
        except Exception as e:  # shown to the user
            errors += 1
            log(f"ERROR    {os.path.basename(path)}: {e}")

    existing = [d for _, d in convs if os.path.exists(d)]
    if existing:
        names = "\n".join(f"  {os.path.basename(d)}" for d in existing[:15])
        more = f"\n  ... and {len(existing) - 15} more" if len(existing) > 15 else ""
        ans = messagebox.askyesnocancel(
            "Profiles already exist",
            f"{len(existing)} profile(s) already exist in the destination:\n{names}{more}\n\n"
            "Yes: replace them (the old versions are backed up)\nNo: skip them\nCancel: stop",
            parent=parent)
        if ans is None:
            log("Cancelled.")
            return 0, len(convs), errors
        if not ans:
            for d in existing:
                log(f"SKIPPED  {os.path.basename(d)} (already exists)")
            convs = [(c, d) for c, d in convs if d not in existing]

    done = skipped = 0
    skipped += len(existing) if existing and not ans else 0
    for conv, dest in convs:
        name = os.path.basename(conv.src_path)
        if ask and conv.doubts:
            choices = ask_doubts(parent, conv.doubts, f"{TITLES[conv.kind]}: {name}")
            if choices is None:
                skipped += 1
                log(f"SKIPPED  {name} (doubts not confirmed)")
                continue
            conv.apply_choices(choices)
        try:
            _, bak = save(conv, dest)
        except Exception as e:  # shown to the user
            errors += 1
            log(f"ERROR    {name}: {e}")
            continue
        done += 1
        extra = f", old version backed up in {bak}" if bak else ""
        log(f"OK       {TITLES[conv.kind].lower()}: {name} -> {dest}{extra}")
    return done, skipped, errors


def drop_mode(paths):
    """Files dropped onto the exe: convert them into the slicer folders, then show a summary."""
    global _theme
    root = tk.Tk()
    root.withdraw()
    _theme = Theme(root)
    lines = []
    o = default_overrides_path()
    try:
        opts = Options(overrides=parse_overrides(o) if o else {}, overrides_path=o or "")
    except Exception as e:  # shown to the user
        messagebox.showerror("Overrides file", str(e))
        return
    done, skipped, errors = process(root, [(p, None) for p in paths], opts, log=lines.append)
    lines.append(f"\nDone: {done} converted, {skipped} skipped, {errors} error(s).")
    if done:
        lines.append("Restart PrusaSlicer to see the new profiles.")
    messagebox.showinfo("Conversion", "\n".join(lines))
    root.destroy()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------
class ProfileSection:
    """Card for one kind: enable checkbox, profile checklist, and (advanced) source / destination folders."""

    COLUMNS = 3

    def __init__(self, parent, kind, on_change=None, theme=None):
        self.kind = kind
        self.on_change = on_change
        self.enabled = tk.BooleanVar(value=True)
        self.src = tk.StringVar(value=slicer_dir("super", kind) or "")
        self.dst = tk.StringVar(value=slicer_dir("prusa", kind) or "")
        self.checks = {}

        self.frame, card = _card(parent)
        card.columnconfigure(0, weight=1)

        head = ttk.Frame(card, style="Inner.TFrame")
        head.grid(row=0, column=0, sticky="ew")
        ttk.Checkbutton(head, text=TITLES[kind], variable=self.enabled, style="Head.TCheckbutton",
                        command=self._toggle).pack(side="left")
        self.count = ttk.Label(head, text="", style="CardMuted.TLabel")
        self.count.pack(side="left", padx=10)
        self.widgets = []
        for t, s in (("Select none", False), ("Select all", True)):
            b = ttk.Button(head, text=t, style="Link.TButton", command=lambda s=s: self.set_all(s))
            b.pack(side="right")
            self.widgets.append(b)

        # folders (advanced)
        self.folders = ttk.Frame(card, style="Inner.TFrame")
        self.folders.columnconfigure(1, weight=1)
        for r, (label, var) in enumerate((("From SuperSlicer", self.src), ("To PrusaSlicer", self.dst))):
            ttk.Label(self.folders, text=label, style="CardMuted.TLabel").grid(row=r, column=0, sticky="w")
            e = ttk.Entry(self.folders, textvariable=var)
            e.grid(row=r, column=1, sticky="ew", padx=8, pady=2)
            b = ttk.Button(self.folders, text="Browse", command=lambda v=var, s=(r == 0): self._browse(v, s))
            b.grid(row=r, column=2)
            self.widgets += [e, b]

        # profile checklist
        box = ttk.Frame(card, style="Inner.TFrame")
        box.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        card.rowconfigure(2, weight=1)
        self.canvas = tk.Canvas(box, height=60, highlightthickness=0, borderwidth=0)
        if theme:
            theme.track(self.canvas, bg="card")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.canvas.yview, style="Thin.Vertical.TScrollbar")
        self.inner = ttk.Frame(self.canvas, style="Inner.TFrame")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(win, width=e.width))

        def sb_set(first, last):
            if float(first) <= 0 and float(last) >= 1:
                sb.pack_forget()      # everything visible: no scrollbar
            else:
                sb.pack(side="right", fill="y", padx=(6, 0), before=self.canvas)
            sb.set(first, last)

        self.canvas.configure(yscrollcommand=sb_set)
        self.canvas.pack(side="left", fill="both", expand=True)
        for w in (self.canvas, self.inner):
            w.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
            w.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))
        self.refresh()

    def _wheel(self, e):
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-e.delta / 120), "units")

    def show_folders(self, show):
        if show:
            self.folders.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        else:
            self.folders.grid_remove()

    def _browse(self, var, is_src):
        d = filedialog.askdirectory(initialdir=var.get() or os.path.expanduser("~"))
        if d:
            var.set(d)
            if is_src:
                self.refresh()

    def refresh(self):
        for w in self.inner.winfo_children():
            w.destroy()
        self.checks.clear()
        profiles = list_profiles(self.src.get().strip())
        if not profiles:
            ttk.Label(self.inner, text="No profile found in the SuperSlicer folder (see Advanced).",
                      style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
        for c in range(self.COLUMNS):
            self.inner.columnconfigure(c, weight=1, uniform="col")
        for i, p in enumerate(profiles):
            v = tk.BooleanVar(value=False)
            self.checks[p] = v
            ttk.Checkbutton(self.inner, text=os.path.splitext(os.path.basename(p))[0], variable=v,
                            style="Card.TCheckbutton", command=self._update_count).grid(
                row=i // self.COLUMNS, column=i % self.COLUMNS, sticky="w", padx=(0, 8))
        self._toggle()

    def set_all(self, state):
        for v in self.checks.values():
            v.set(state)
        self._update_count()

    def selected(self):
        if not self.enabled.get():
            return []
        return [p for p, v in self.checks.items() if v.get()]

    def _update_count(self):
        n = len(self.selected())
        self.count.configure(text=f"{n} of {len(self.checks)} selected" if self.enabled.get() else "not transferred")
        if self.on_change:
            self.on_change()

    def _toggle(self):
        state = "normal" if self.enabled.get() else "disabled"
        for w in self.widgets + list(self.inner.winfo_children()):
            try:
                w.configure(state=state)
            except tk.TclError:
                pass
        self._update_count()


def main_window():
    global _theme
    root = tk.Tk()
    root.title(f"SuperSlicer to PrusaSlicer converter {__version__}")
    root.geometry("940x900")
    root.minsize(760, 640)
    theme = _theme = Theme(root)

    # header
    header = ttk.Frame(root, padding=(22, 18, 22, 8))
    header.pack(fill="x")
    titles = ttk.Frame(header)
    titles.pack(side="left")
    ttk.Label(titles, text="SuperSlicer  →  PrusaSlicer", style="Title.TLabel").pack(anchor="w")
    ttk.Label(titles, text="Choose what to transfer, tick the profiles, then convert.",
              style="Sub.TLabel").pack(anchor="w")
    mode_btn = ttk.Button(header, style="Ghost.TButton")
    mode_btn.pack(side="right", anchor="n")
    ttk.Label(header, text=f"v{__version__}", style="Sub.TLabel").pack(side="right", anchor="n", padx=10, pady=5)

    def set_mode_text():
        mode_btn.configure(text="☾  Dark mode" if theme.mode == "light" else "☀  Light mode")

    set_mode_text()

    body = ttk.Frame(root, padding=(22, 0))
    body.pack(fill="both", expand=True)

    footer_status = tk.StringVar()
    footer = ttk.Frame(body)        # packed below the options
    convert_btn = ttk.Button(footer, text="Convert and install into PrusaSlicer", style="Accent.TButton")

    def update_status():
        n = sum(len(s.selected()) for s in sections)
        footer_status.set(f"{n} profile{'s' if n != 1 else ''} selected" if n else "No profile selected")
        convert_btn.configure(state="normal" if n else "disabled")

    sections = []
    for k in KINDS:
        s = ProfileSection(body, k, on_change=lambda: update_status() if len(sections) == len(KINDS) else None,
                           theme=theme)
        sections.append(s)

    # options
    opts_outer, opts = _card(body)
    opts.columnconfigure(3, weight=1)
    nozzle = tk.StringVar(value="0.4")
    ovr = tk.StringVar(value=default_overrides_path() or "")
    ask = tk.BooleanVar(value=True)
    adv = tk.BooleanVar(value=False)
    ttk.Label(opts, text="Options", style="CardHead.TLabel").grid(row=0, column=0, columnspan=4, sticky="w")
    ttk.Label(opts, text="Nozzle diameter", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(opts, textvariable=nozzle, width=6).grid(row=1, column=1, sticky="w", padx=(8, 4), pady=(8, 0))
    ttk.Label(opts, text="mm  (turns print widths in % into mm)", style="CardMuted.TLabel").grid(
        row=1, column=2, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Checkbutton(opts, text="Ask me about doubtful settings (otherwise the proposed values are kept)",
                    variable=ask, style="Card.TCheckbutton").grid(row=2, column=0, columnspan=4, sticky="w",
                                                                  pady=(6, 0))

    ovr_row = ttk.Frame(opts, style="Inner.TFrame")
    ovr_row.columnconfigure(1, weight=1)
    ttk.Label(ovr_row, text="Overrides file", style="CardMuted.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Entry(ovr_row, textvariable=ovr).grid(row=0, column=1, sticky="ew", padx=8)

    def pick_ovr():
        p = filedialog.askopenfilename(title="Overrides file (optional)", initialdir=app_dir(),
                                       filetypes=[(".ini files", "*.ini"), ("All files", "*.*")])
        if p:
            ovr.set(p)

    ttk.Button(ovr_row, text="Browse", command=pick_ovr).grid(row=0, column=2)

    def toggle_adv():
        for s in sections:
            s.show_folders(adv.get())
        if adv.get():
            ovr_row.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        else:
            ovr_row.grid_remove()
        # grow the window so the profile lists keep some room (within the screen)
        root.update_idletasks()
        want = root.winfo_reqheight() + (3 * 50 if adv.get() else 0)
        if root.winfo_height() > 1 and want > root.winfo_height():
            h = min(want, root.winfo_screenheight() - 80)
            root.geometry(f"{root.winfo_width()}x{h}+{root.winfo_x()}+{max(0, min(root.winfo_y(), root.winfo_screenheight() - 80 - h))}")

    ttk.Checkbutton(opts, text="Advanced: show folders and overrides file", variable=adv,
                    style="Card.TCheckbutton", command=toggle_adv).grid(row=3, column=0, columnspan=4, sticky="w")

    # footer
    ttk.Label(footer, textvariable=footer_status, style="Sub.TLabel").pack(side="left")
    convert_btn.pack(side="right")

    # log
    log_outer, log_card = _card(body, padding=(12, 8))
    log_box = tk.Text(log_card, height=5, state="disabled", wrap="word", relief="flat", borderwidth=0,
                      font=(MONO, 9), highlightthickness=0)
    log_box.pack(fill="both", expand=True)
    theme.track(log_box, bg="card", fg="fg", insertbackground="fg", selectbackground="select")
    tags = {"OK": "ok", "ERROR": "err", "SKIPPED": "muted", "Cancelled": "muted"}

    def color_tags():
        for t in ("ok", "err", "muted"):
            log_box.tag_configure(t, foreground=theme.c[t])

    color_tags()

    def log(msg):
        log_box.configure(state="normal")
        tag = next((t for p, t in tags.items() if msg.startswith(p)), "")
        log_box.insert("end", msg + "\n", tag)
        log_box.see("end")
        log_box.configure(state="disabled")
        root.update_idletasks()

    def toggle_mode():
        theme.toggle()
        set_mode_text()
        color_tags()

    mode_btn.configure(command=toggle_mode)

    def go():
        items = [(p, s.dst.get().strip() or None) for s in sections for p in s.selected()]
        if not items:
            messagebox.showinfo("Nothing to do", "Tick at least one profile.")
            return
        try:
            n = float(nozzle.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Error", "Invalid nozzle diameter.")
            return
        o = ovr.get().strip()
        try:
            overrides = parse_overrides(o) if o else {}
        except Exception as e:  # shown to the user
            messagebox.showerror("Overrides file", str(e))
            return
        opts_ = Options(nozzle=n, overrides=overrides, overrides_path=o, target="prusa")
        convert_btn.configure(state="disabled")
        try:
            done, skipped, errors = process(root, items, opts_, ask.get(), log)
        finally:
            update_status()
        log(f"Done: {done} converted, {skipped} skipped, {errors} error(s).")
        if done:
            log("Restart PrusaSlicer to see the new profiles.\n")

    convert_btn.configure(command=go)

    # bottom first, so options, button and log stay visible; the profile lists share what is left
    log_outer.pack(side="bottom", fill="x", pady=(4, 18))
    footer.pack(side="bottom", fill="x", pady=(10, 6))
    opts_outer.pack(side="bottom", fill="x", pady=5)
    for s in sections:
        s.frame.pack(fill="both", expand=True, pady=5)
    update_status()

    missing = [TITLES[s.kind] for s in sections if not s.src.get() or not s.dst.get()]
    if missing:
        log("Some SuperSlicer / PrusaSlicer folders were not found automatically "
            f"({', '.join(missing)}): tick Advanced and pick them with Browse.")
        adv.set(True)
        toggle_adv()
    else:
        log("SuperSlicer and PrusaSlicer folders found. Tick the profiles to transfer.")
    root.mainloop()
