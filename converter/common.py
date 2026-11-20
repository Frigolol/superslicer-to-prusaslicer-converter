"""Shared building blocks: .ini parsing, conversion log, doubts, overrides, report, slicer folders."""
import datetime
import os
import shutil
import sys

from . import __version__

KINDS = ("print", "filament", "printer")
SLICERS = {"super": "SuperSlicer", "prusa": "PrusaSlicer"}
REPORT_ORDER = ["doubt", "override", "converted", "default", "ignored", "direct"]


# ---------------------------------------------------------------------------
# .ini files
# ---------------------------------------------------------------------------
def parse_ini(text):
    """`key = value` lines -> dict. Comments and blank lines are skipped."""
    data = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if sep:
            data[key.strip()] = value.strip()
    return data


def read_text(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def detect_kind(data):
    """'print', 'filament' or 'printer', from the keys of a profile."""
    if "bed_shape" in data and "nozzle_diameter" in data:
        return "printer"
    if "perimeters" in data and "layer_height" in data:
        return "print"
    if "filament_type" in data or ("temperature" in data and "filament_diameter" in data):
        return "filament"
    raise ValueError("not a print, filament or printer profile")


def detect_slicer(text, data):
    """'super' or 'prusa', from the header line or from slicer-specific keys."""
    head = text.lstrip().splitlines()[0] if text.strip() else ""
    if "SuperSlicer" in head:
        return "super"
    if "PrusaSlicer" in head:
        return "prusa"
    if any(k in data for k in ("default_fan_speed", "filament_shrink", "print_version", "perimeter_loop")):
        return "super"
    if any(k in data for k in ("min_fan_speed", "filament_shrinkage_compensation_xy", "scarf_seam_placement")):
        return "prusa"
    raise ValueError("cannot tell whether this is a SuperSlicer or a PrusaSlicer profile")


# ---------------------------------------------------------------------------
# Overrides
# ---------------------------------------------------------------------------
def parse_overrides(path):
    """Overrides file -> {"print": {key: (value, reason)}, "filament": {...}, "printer": {...}}.

    Lines before any [section] belong to [print] (format of v1.x).
    The `# ...` comment right above a line is used as the reason in the report.
    """
    res = {k: {} for k in KINDS}
    section, why = "print", ""
    for line in read_text(path).splitlines():
        line = line.strip()
        if not line:
            why = ""
        elif line.startswith("[") and line.endswith("]"):
            name = line[1:-1].strip().lower()
            if name not in res:
                raise ValueError(f"{os.path.basename(path)}: unknown section [{name}] (use [print], [filament] or [printer])")
            section, why = name, ""
        elif line.startswith("#"):
            why = line.lstrip("# ").strip()
        elif "=" in line:
            k, _, v = line.partition("=")
            res[section][k.strip()] = (v.strip(), why or "user override")
            why = ""
    return res


def app_dir():
    """Folder of the exe (PyInstaller) or of the project."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def default_overrides_path():
    """overrides.ini next to the program (on macOS also next to the .app bundle)."""
    folders = [app_dir()]
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        app = os.path.abspath(os.path.join(app_dir(), "..", ".."))   # ss2ps.app/Contents/MacOS -> ss2ps.app
        folders.append(os.path.dirname(app))
    for folder in folders:
        p = os.path.join(folder, "overrides.ini")
        if os.path.isfile(p):
            return p
    return None


# ---------------------------------------------------------------------------
# Slicer folders
# ---------------------------------------------------------------------------
def config_root():
    home = os.path.expanduser("~")
    if os.name == "nt":
        return os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
    if sys.platform == "darwin":
        return os.path.join(home, "Library", "Application Support")
    return os.path.join(home, ".config")


def slicer_dir(slicer, kind):
    """Profile folder of a slicer ('super' / 'prusa') for a kind, or None if missing."""
    p = os.path.join(config_root(), SLICERS[slicer], kind)
    return p if os.path.isdir(p) else None


def list_profiles(folder):
    if not folder or not os.path.isdir(folder):
        return []
    return sorted((os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".ini")),
                  key=lambda p: os.path.basename(p).lower())


def backup(path, kind):
    """Copies an existing profile to <slicer config>/<kind>_backups/<timestamp>/ before it is replaced."""
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(path))), f"{kind}_backups", stamp)
    os.makedirs(folder, exist_ok=True)
    shutil.copy2(path, os.path.join(folder, os.path.basename(path)))
    return folder


# ---------------------------------------------------------------------------
# Conversion base class
# ---------------------------------------------------------------------------
class Conversion:
    """Result of a conversion: output values, a log for the report, and doubts for the user.

    Subclasses implement run(). Statuses: see REPORT_ORDER.
    """
    kind = ""

    def __init__(self, src_text, overrides=None, src_path=""):
        self.text = src_text
        self.ss = parse_ini(src_text)
        self.src_path = src_path
        self.overrides = overrides or {}   # {key: (value, reason)}
        self.target = "prusa"
        self.used = set()                  # source keys consumed
        self.out = {}                      # target key -> value
        self.log = []                      # (status, key, value, note)
        self.doubts = []                   # [{key, value, options, note, closed}]
        self.info = []                     # extra header lines for the report

    # -- helpers ---------------------------------------------------------------
    def get(self, key, default=None):
        self.used.add(key)
        return self.ss.get(key, default)

    @staticmethod
    def disabled(v):
        return v is not None and v.startswith("!")

    def set(self, key, value, status="direct", note=""):
        self.out[key] = value
        self.log.append((status, key, value, note))

    def note(self, status, key, value, note):
        """Report line without output value (e.g. ignored keys)."""
        self.log.append((status, key, value, note))

    def doubt(self, key, value, options, note, closed=False, labels=None):
        """Proposed value the user should confirm. `options` = suggested alternatives.
        closed=True: only the listed options are valid; otherwise any number is accepted.
        labels: {value: text shown instead of the value} (for long values such as G-code)."""
        opts = [value] + [o for o in options if o != value]
        self.set(key, value, "doubt", note)
        self.doubts.append({"key": key, "value": value, "options": opts, "note": note, "closed": closed,
                            "labels": labels or {}})

    def apply_overrides(self):
        for k, (v, why) in self.overrides.items():
            old = self.out.get(k)
            self.log = [r for r in self.log if not (r[0] == "doubt" and r[1] == k)]
            self.set(k, v, "override", f"{old} -> {v}: {why}")
        self.doubts = [d for d in self.doubts if d["key"] not in self.overrides]

    def log_unused(self, note="no PrusaSlicer equivalent"):
        for k in sorted(self.ss):
            if k not in self.used:
                self.note("ignored", k, self.ss[k], note)

    def apply_choices(self, choices):
        """Applies the user's answers to the doubts: {key: value}."""
        for d in self.doubts:
            v = choices.get(d["key"], d["value"]).strip()
            if v == d["value"]:
                continue
            self.out[d["key"]] = v
            lab = d.get("labels", {})
            chose = lab.get(v, f"`{v}`")
            prop = lab.get(d["value"], f"`{d['value']}`")
            self.log = [(st, k, v, f"{n} -- user chose {chose} (proposed {prop})")
                        if st == "doubt" and k == d["key"] else (st, k, val, n)
                        for st, k, val, n in self.log]

    # -- output ----------------------------------------------------------------
    def counts(self):
        return {st: sum(1 for r in self.log if r[0] == st) for st in REPORT_ORDER}

    def write(self, out_path):
        """Writes the profile and `<name> - report.md` next to it. Returns the report path."""
        stamp = f"{datetime.datetime.now():%Y-%m-%d %H:%M}"
        with open(out_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# converted for {SLICERS[self.target]} by ss2ps {__version__} on {stamp}\n")
            for k in sorted(self.out):
                f.write(f"{k} = {self.out[k]}\n")

        rep_path = os.path.splitext(out_path)[0] + " - report.md"
        with open(rep_path, "w", encoding="utf-8") as f:
            f.write(f"# Conversion report: {os.path.basename(self.src_path) or 'profile'}\n\n"
                    f"Type: {self.kind}  \nTarget: {SLICERS[self.target]}  \n")
            for line in self.info:
                f.write(f"{line}  \n")
            for st in REPORT_ORDER:
                rows = [r for r in self.log if r[0] == st]
                if not rows:
                    continue
                f.write(f"\n## {st} ({len(rows)})\n\n| key | value | note |\n|---|---|---|\n")
                for _, k, v, n in rows:
                    v = str(v).replace("|", "\\|")
                    f.write(f"| {k} | `{v}` | {n} |\n")
        return rep_path


# ---------------------------------------------------------------------------
# Doubts: validation and terminal prompts
# ---------------------------------------------------------------------------
def valid_choice(d, v):
    """True if `v` is an acceptable answer for doubt `d`."""
    if d["closed"]:
        return v in d["options"]
    try:
        float(v.rstrip("%"))
        return True
    except ValueError:
        return v in d["options"]


def ask_console(doubts, title=""):
    """Asks each doubt in the terminal. Enter = keep the proposed value."""
    print(f"\n{title}{len(doubts)} setting(s) need your confirmation (Enter = keep proposed value):")
    res = {}
    for d in doubts:
        print(f"\n  {d['key']}: {d['note']}")
        if d.get("labels"):
            for i, o in enumerate(d["options"], 1):
                print(f"    {i}) {d['labels'].get(o, o)}")
            while True:
                a = input("    choice [1]: ").strip() or "1"
                if a.isdigit() and 1 <= int(a) <= len(d["options"]):
                    break
                print("    type the number of an option")
            res[d["key"]] = d["options"][int(a) - 1]
            continue
        print("    options: " + ", ".join(d["options"]))
        while True:
            a = input(f"    value [{d['value']}]: ").strip() or d["value"]
            if valid_choice(d, a):
                break
            print("    invalid value, choose one of the options" if d["closed"] else "    a number is expected")
        res[d["key"]] = a
    print()
    return res
