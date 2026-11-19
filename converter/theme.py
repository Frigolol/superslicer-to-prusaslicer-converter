"""Light / dark look for the tkinter window, built on ttk's 'clam' theme (no extra dependency)."""
import sys
import tkinter as tk
from tkinter import ttk

PALETTES = {
    "light": {
        "bg": "#f3f4f6", "card": "#ffffff", "fg": "#1f2328", "muted": "#656d76", "border": "#d8dce1",
        "accent": "#2563eb", "accent_hover": "#1d4ed8", "accent_fg": "#ffffff", "field": "#ffffff",
        "hover": "#eef1f5", "select": "#dbe7ff", "disabled": "#a0a7b0", "ok": "#1a7f37", "err": "#cf222e",
    },
    "dark": {
        "bg": "#1b1d21", "card": "#25282d", "fg": "#e6e8eb", "muted": "#9aa1a9", "border": "#3a3f46",
        "accent": "#3b82f6", "accent_hover": "#60a5fa", "accent_fg": "#ffffff", "field": "#1e2025",
        "hover": "#30343a", "select": "#29406b", "disabled": "#5d636b", "ok": "#3fb950", "err": "#f85149",
    },
}
FONT = "Segoe UI" if sys.platform == "win32" else "TkDefaultFont"
MONO = "Consolas" if sys.platform == "win32" else "TkFixedFont"


def system_mode():
    """'dark' or 'light', from the Windows app setting (light elsewhere)."""
    if sys.platform != "win32":
        return "light"
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return "light" if winreg.QueryValueEx(k, "AppsUseLightTheme")[0] else "dark"
    except OSError:
        return "light"


class Theme:
    """Applies a palette to ttk styles and to the plain tk widgets registered with `track`."""

    def __init__(self, root, mode=None):
        self.root = root
        self.mode = mode or system_mode()
        self.tracked = []      # (widget, {option: palette key})
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.apply()

    @property
    def c(self):
        return PALETTES[self.mode]

    def toggle(self):
        self.mode = "light" if self.mode == "dark" else "dark"
        self.apply()

    def track(self, widget, **opts):
        """Recolors a plain tk widget on every theme change: track(w, bg="card", fg="fg")."""
        self.tracked.append((widget, opts))
        self._color(widget, opts)
        return widget

    def _color(self, w, opts):
        try:
            w.configure(**{o: self.c[k] for o, k in opts.items()})
        except tk.TclError:
            pass

    def apply(self):
        c, s = self.c, self.style
        f = (FONT, 10)
        s.configure(".", background=c["bg"], foreground=c["fg"], font=f, bordercolor=c["border"],
                    lightcolor=c["border"], darkcolor=c["border"], troughcolor=c["bg"],
                    fieldbackground=c["field"], selectbackground=c["select"], selectforeground=c["fg"],
                    insertcolor=c["fg"], focuscolor=c["accent"])
        s.map(".", foreground=[("disabled", c["disabled"])])
        s.configure("TFrame", background=c["bg"])
        s.configure("Card.TFrame", background=c["card"], relief="solid", borderwidth=1)
        s.configure("Inner.TFrame", background=c["card"])
        s.configure("TLabel", background=c["bg"], foreground=c["fg"])
        s.configure("Title.TLabel", font=(FONT, 17, "bold"))
        s.configure("Sub.TLabel", foreground=c["muted"])
        for base in ("Card", "CardMuted", "CardHead"):
            s.configure(f"{base}.TLabel", background=c["card"])
        s.configure("CardMuted.TLabel", foreground=c["muted"], font=(FONT, 9))
        s.configure("CardHead.TLabel", font=(FONT, 11, "bold"))

        for name, bg in (("TCheckbutton", c["bg"]), ("Card.TCheckbutton", c["card"]),
                         ("Head.TCheckbutton", c["card"])):
            s.configure(name, background=bg, foreground=c["fg"], indicatorbackground=c["field"],
                        indicatorforeground=c["accent_fg"], indicatorrelief="flat", padding=(2, 3),
                        upperbordercolor=c["border"], lowerbordercolor=c["border"])
            s.map(name, background=[("active", bg)],
                  indicatorbackground=[("selected", c["accent"]), ("active", c["hover"])],
                  foreground=[("disabled", c["disabled"])])
        s.configure("Head.TCheckbutton", font=(FONT, 11, "bold"))

        s.configure("TButton", background=c["card"], foreground=c["fg"], padding=(12, 5), relief="flat",
                    borderwidth=1, focusthickness=0)
        s.map("TButton", background=[("disabled", c["card"]), ("pressed", c["select"]), ("active", c["hover"])],
              bordercolor=[("active", c["accent"])])
        s.configure("Link.TButton", background=c["card"], foreground=c["accent"], padding=(6, 1),
                    borderwidth=0, font=(FONT, 9))
        s.map("Link.TButton", background=[("active", c["hover"]), ("disabled", c["card"])],
              foreground=[("disabled", c["disabled"])])
        s.configure("Accent.TButton", background=c["accent"], foreground=c["accent_fg"], bordercolor=c["accent"],
                    padding=(22, 9), font=(FONT, 10, "bold"))
        s.map("Accent.TButton", background=[("pressed", c["accent_hover"]), ("active", c["accent_hover"])],
              bordercolor=[("active", c["accent_hover"])])
        s.configure("Ghost.TButton", background=c["bg"], padding=(10, 4), borderwidth=1)
        s.map("Ghost.TButton", background=[("active", c["hover"])])

        s.configure("TEntry", fieldbackground=c["field"], foreground=c["fg"], padding=(6, 4),
                    bordercolor=c["border"], lightcolor=c["field"], darkcolor=c["field"])
        s.map("TEntry", bordercolor=[("focus", c["accent"])], lightcolor=[("focus", c["accent"])],
              fieldbackground=[("disabled", c["card"])])
        s.configure("TCombobox", fieldbackground=c["field"], foreground=c["fg"], background=c["card"],
                    arrowcolor=c["fg"], padding=(6, 3), bordercolor=c["border"],
                    lightcolor=c["field"], darkcolor=c["field"])
        s.map("TCombobox", fieldbackground=[("readonly", c["field"])], foreground=[("readonly", c["fg"])],
              selectbackground=[("readonly", c["field"])], selectforeground=[("readonly", c["fg"])],
              bordercolor=[("focus", c["accent"])], background=[("active", c["hover"])])
        self.root.option_add("*TCombobox*Listbox.background", c["field"])
        self.root.option_add("*TCombobox*Listbox.foreground", c["fg"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", c["select"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", c["fg"])
        self.root.option_add("*TCombobox*Listbox.font", f)

        s.layout("Thin.Vertical.TScrollbar", [("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})]})])
        s.configure("Thin.Vertical.TScrollbar", background=c["border"], troughcolor=c["card"],
                    bordercolor=c["card"], lightcolor=c["border"], darkcolor=c["border"], gripcount=0,
                    arrowsize=7, width=7)
        s.map("Thin.Vertical.TScrollbar", background=[("active", c["muted"])])

        self.root.configure(bg=c["bg"])
        for w, opts in list(self.tracked):
            if w.winfo_exists():
                self._color(w, opts)
        for w in self._toplevels(self.root):
            w.configure(bg=c["bg"])
            dark_title_bar(w, self.mode == "dark")

    @staticmethod
    def _toplevels(w):
        yield w
        for ch in w.winfo_children():
            if isinstance(ch, tk.Toplevel):
                yield ch


def dark_title_bar(win, dark):
    """Windows 10/11: dark or light title bar to match the window."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        win.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
        val = ctypes.c_int(1 if dark else 0)
        for attr in (20, 19):  # DWMWA_USE_IMMERSIVE_DARK_MODE (new / old builds)
            if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(val), ctypes.sizeof(val)) == 0:
                break
    except Exception:  # cosmetic only
        pass
