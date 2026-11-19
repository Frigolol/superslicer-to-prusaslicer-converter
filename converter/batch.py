"""Turns profile files into conversions and writes them (shared by the window and the command line)."""
import os
from dataclasses import dataclass, field

from .common import (SLICERS, backup, detect_kind, detect_slicer, parse_ini, read_text, slicer_dir)
from .filament import FilamentConversion
from .print_profile import PrintConversion
from .printer import PrinterConversion


@dataclass
class Options:
    nozzle: float = 0.4
    overrides: dict = field(default_factory=dict)   # {"print": {...}, "filament": {...}, "printer": {...}}
    overrides_path: str = ""
    kind: str = ""          # "" = auto-detected
    target: str = ""        # "" = the other slicer
    keep_phony: bool = False


def convert(path, opts):
    """Reads and converts one profile. Returns the Conversion (doubts still to be confirmed)."""
    text = read_text(path)
    data = parse_ini(text)
    kind = opts.kind or detect_kind(data)
    source = detect_slicer(text, data)
    target = opts.target or ("prusa" if source == "super" else "super")
    if target == source:
        raise ValueError(f"already a {SLICERS[source]} profile")
    ovr = opts.overrides.get(kind, {})
    if kind in ("print", "printer"):
        if target != "prusa":
            raise ValueError(f"{kind} profiles can only be converted from SuperSlicer to PrusaSlicer")
        conv = (PrintConversion(text, ovr, path, opts.nozzle) if kind == "print"
                else PrinterConversion(text, ovr, path))
    else:
        conv = FilamentConversion(text, ovr, path, target, opts.keep_phony)
    if opts.overrides_path and ovr:
        conv.info.append(f"Overrides: {opts.overrides_path}")
    return conv.run()


def destination(conv, out_dir=None):
    """Same file name, in `out_dir`, else the target slicer's folder, else next to the source."""
    folder = out_dir or slicer_dir(conv.target, conv.kind) or os.path.dirname(os.path.abspath(conv.src_path))
    dest = os.path.join(folder, os.path.basename(conv.src_path))
    if os.path.abspath(dest) == os.path.abspath(conv.src_path):
        raise ValueError("the output would overwrite the source profile: choose another output folder")
    return dest


def save(conv, dest):
    """Writes the profile (backing up an existing one). Returns (report path, backup folder or None)."""
    os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
    bak = backup(dest, conv.kind) if os.path.exists(dest) else None
    return conv.write(dest), bak
