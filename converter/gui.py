"""Window (tkinter): choose what to transfer, pick profiles, confirm doubtful settings."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .batch import Options, convert, destination, save
from .common import (KINDS, app_dir, default_overrides_path, list_profiles, parse_overrides,
                     slicer_dir, valid_choice)

TITLES = {"print": "Print settings", "filament": "Filaments"}


# ---------------------------------------------------------------------------
# Doubts dialog
# ---------------------------------------------------------------------------
def ask_doubts(parent, doubts, title):
    """Modal window: one drop-down per doubt. Returns {key: value}, or None if skipped."""
    win = tk.Toplevel(parent)
    win.title("Please confirm these settings")
    win.transient(parent)
    win.grab_set()
    frm = ttk.Frame(win, padding=12)
    frm.grid(sticky="nsew")
    ttk.Label(frm, text=title, font=("", 10, "bold")).grid(row=0, column=0, columnspan=3, sticky="w")
    ttk.Label(frm, text="These settings could not be converted with certainty.\n"
                        "Keep the proposed value or choose another one (you can also type a number).",
              justify="left").grid(row=1, column=0, columnspan=3, sticky="w", pady=(2, 10))
    for c, t in enumerate(("Setting", "Value", "Why")):
        ttk.Label(frm, text=t, font=("", 9, "bold")).grid(row=2, column=c, sticky="w", padx=(0, 8))
    vars_ = {}
    for i, d in enumerate(doubts, start=3):
        ttk.Label(frm, text=d["key"]).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 8))
        v = tk.StringVar(value=d["value"])
        ttk.Combobox(frm, textvariable=v, values=d["options"], width=18,
                     state="readonly" if d["closed"] else "normal").grid(row=i, column=1, padx=(0, 8))
        ttk.Label(frm, text=d["note"], wraplength=420, justify="left").grid(row=i, column=2, sticky="w")
        vars_[d["key"]] = v

    result = {}

    def ok():
        bad = [d["key"] for d in doubts if not valid_choice(d, vars_[d["key"]].get().strip())]
        if bad:
            messagebox.showerror("Invalid value", "A number is expected for:\n" + "\n".join(bad), parent=win)
            return
        result.update({k: v.get().strip() for k, v in vars_.items()})
        win.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=len(doubts) + 3, column=0, columnspan=3, pady=(12, 0))
    ttk.Button(btns, text="OK", command=ok).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text="Skip this profile", command=win.destroy).grid(row=0, column=1, padx=4)
    win.bind("<Return>", lambda e: ok())
    win.bind("<Escape>", lambda e: win.destroy())
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
    root = tk.Tk()
    root.withdraw()
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
    """Frame for one kind: enable checkbox, source / destination folders, profile checklist."""

    def __init__(self, parent, kind, on_change=None):
        self.kind = kind
        self.enabled = tk.BooleanVar(value=True)
        self.src = tk.StringVar(value=slicer_dir("super", kind) or "")
        self.dst = tk.StringVar(value=slicer_dir("prusa", kind) or "")
        self.checks = {}

        self.frame = ttk.LabelFrame(parent, padding=8)
        hdr = ttk.Checkbutton(self.frame, text=f"Transfer {TITLES[kind].lower()}", variable=self.enabled,
                              command=self._toggle)
        self.frame.configure(labelwidget=hdr)
        self.frame.columnconfigure(1, weight=1)
        self.widgets = []
        for r, (label, var) in enumerate((("SuperSlicer folder", self.src), ("PrusaSlicer folder", self.dst))):
            ttk.Label(self.frame, text=label).grid(row=r, column=0, sticky="w")
            e = ttk.Entry(self.frame, textvariable=var)
            e.grid(row=r, column=1, sticky="ew", padx=6, pady=2)
            b = ttk.Button(self.frame, text="...", width=4, command=lambda v=var, s=(r == 0): self._browse(v, s))
            b.grid(row=r, column=2)
            self.widgets += [e, b]

        box = ttk.Frame(self.frame)
        box.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(6, 0))
        self.frame.rowconfigure(2, weight=1)
        self.canvas = tk.Canvas(box, height=130, highlightthickness=0)
        sb = ttk.Scrollbar(box, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        btns = ttk.Frame(self.frame)
        btns.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))
        for t, s in (("Select all", True), ("Select none", False)):
            b = ttk.Button(btns, text=t, command=lambda s=s: self.set_all(s))
            b.pack(side="left", padx=(0, 6))
            self.widgets.append(b)
        self.count = ttk.Label(btns, text="")
        self.count.pack(side="left", padx=8)
        self.refresh()

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
            ttk.Label(self.inner, text="No .ini profile in this folder.").pack(anchor="w")
        for p in profiles:
            v = tk.BooleanVar(value=False)
            self.checks[p] = v
            cb = ttk.Checkbutton(self.inner, text=os.path.splitext(os.path.basename(p))[0], variable=v,
                                 command=self._update_count)
            cb.pack(anchor="w")
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
        self.count.configure(text=f"{len(self.selected())} / {len(self.checks)} selected")

    def _toggle(self):
        state = "normal" if self.enabled.get() else "disabled"
        for w in self.widgets + list(self.inner.winfo_children()):
            try:
                w.configure(state=state)
            except tk.TclError:
                pass
        self._update_count()


def main_window():
    root = tk.Tk()
    root.title(f"SuperSlicer -> PrusaSlicer converter {__version__}")
    root.geometry("860x780")
    root.minsize(640, 600)
    pad = {"padx": 10, "pady": 4}

    ttk.Label(root, text="Choose what to transfer, tick the profiles, then click Convert.",
              font=("", 10, "bold")).pack(anchor="w", **pad)

    sections = [ProfileSection(root, k) for k in KINDS]
    for s in sections:
        s.frame.pack(fill="both", expand=True, **pad)

    opts_frm = ttk.LabelFrame(root, text="Options", padding=8)
    opts_frm.pack(fill="x", **pad)
    opts_frm.columnconfigure(1, weight=1)
    nozzle = tk.StringVar(value="0.4")
    ovr = tk.StringVar(value=default_overrides_path() or "")
    ask = tk.BooleanVar(value=True)
    ttk.Label(opts_frm, text="Nozzle diameter (mm), for print widths").grid(row=0, column=0, sticky="w")
    ttk.Entry(opts_frm, textvariable=nozzle, width=8).grid(row=0, column=1, sticky="w", padx=6)
    ttk.Label(opts_frm, text="Overrides file (optional)").grid(row=1, column=0, sticky="w")
    ttk.Entry(opts_frm, textvariable=ovr).grid(row=1, column=1, sticky="ew", padx=6, pady=2)

    def pick_ovr():
        p = filedialog.askopenfilename(title="Overrides file (optional)", initialdir=app_dir(),
                                       filetypes=[(".ini files", "*.ini"), ("All files", "*.*")])
        if p:
            ovr.set(p)

    ttk.Button(opts_frm, text="...", width=4, command=pick_ovr).grid(row=1, column=2)
    ttk.Checkbutton(opts_frm, text="Ask me about doubtful settings (otherwise the proposed values are kept)",
                    variable=ask).grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

    bottom = ttk.Frame(root)
    bottom.pack(fill="x", **pad)
    log_box = tk.Text(root, height=8, state="disabled", wrap="word")
    log_box.pack(fill="both", **pad)

    def log(msg):
        log_box.configure(state="normal")
        log_box.insert("end", msg + "\n")
        log_box.see("end")
        log_box.configure(state="disabled")
        root.update_idletasks()

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
        opts = Options(nozzle=n, overrides=overrides, overrides_path=o, target="prusa")
        done, skipped, errors = process(root, items, opts, ask.get(), log)
        log(f"Done: {done} converted, {skipped} skipped, {errors} error(s).")
        if done:
            log("Restart PrusaSlicer to see the new profiles.\n")

    ttk.Button(bottom, text="Convert and install into PrusaSlicer", command=go).pack(side="right")

    missing = [TITLES[s.kind] for s in sections if not s.src.get() or not s.dst.get()]
    if missing:
        log("Some SuperSlicer / PrusaSlicer folders were not found automatically "
            f"({', '.join(missing)}): pick them with \"...\".")
    root.mainloop()
