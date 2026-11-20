"""Command line and program entry point."""
import argparse
import os
import sys

from . import __version__
from .batch import Options, convert, destination, save
from .common import ask_console, default_overrides_path, list_profiles, parse_overrides

USAGE = """examples:
  ss2ps                                       open the window
  ss2ps "my print.ini"                        convert into PrusaSlicer's folder (type auto-detected)
  ss2ps %APPDATA%\\SuperSlicer\\filament        convert every profile of a folder
  ss2ps "my print.ini" -o out.ini --nozzle 0.6
  ss2ps "Generic ASA.ini" --to super          filament PrusaSlicer -> SuperSlicer
"""


def run_cli(argv):
    ap = argparse.ArgumentParser(prog="ss2ps", description="SuperSlicer -> PrusaSlicer profile converter "
                                 "(print settings, filaments and printers).", epilog=USAGE,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help=".ini profiles or folders of profiles")
    ap.add_argument("-o", "--out", help="output file (single input)")
    ap.add_argument("-d", "--outdir", help="output folder (default: the target slicer's folder for that type)")
    ap.add_argument("--kind", choices=["print", "filament", "printer"], help="profile type (default: auto-detected)")
    ap.add_argument("--to", choices=["prusa", "super"],
                    help="target slicer (default: the other one; print and printer profiles: prusa only)")
    ap.add_argument("--nozzle", type=float, default=0.4, help="nozzle diameter, to convert %% widths to mm (print)")
    ap.add_argument("--overrides", help="overrides file (default: overrides.ini next to the program, if present)")
    ap.add_argument("--no-overrides", action="store_true", help="ignore overrides.ini")
    ap.add_argument("--keep-phony", action="store_true",
                    help="filament: keep SuperSlicer '!' values as real values instead of nil")
    ap.add_argument("-y", "--yes", action="store_true", help="keep the proposed values for doubtful settings")
    ap.add_argument("-f", "--force", action="store_true",
                    help="replace existing profiles (the old version is backed up)")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)

    files = []
    for i in args.inputs:
        files += list_profiles(i) if os.path.isdir(i) else [i]
    if args.out and len(files) != 1:
        ap.error("-o needs exactly one input profile (use -d for several)")
    ovr_path = None if args.no_overrides else (args.overrides or default_overrides_path())
    opts = Options(nozzle=args.nozzle, overrides=parse_overrides(ovr_path) if ovr_path else {},
                   overrides_path=ovr_path or "", kind=args.kind or "", target=args.to or "",
                   keep_phony=args.keep_phony)
    interactive = not args.yes and sys.stdin is not None and sys.stdin.isatty()

    errors = 0
    for f in files:
        name = os.path.basename(f)
        try:
            conv = convert(f, opts)
            dest = args.out or destination(conv, args.outdir)
            if os.path.exists(dest) and not args.force:
                print(f"SKIPPED  {name}: {dest} already exists (use -f to replace it)")
                continue
            if interactive and conv.doubts:
                conv.apply_choices(ask_console(conv.doubts, f"[{conv.kind}] {name}: "))
            report, bak = save(conv, dest)
        except Exception as e:  # reported, next file
            errors += 1
            print(f"ERROR    {name}: {e}", file=sys.stderr)
            continue
        counts = ", ".join(f"{k}: {v}" for k, v in conv.counts().items())
        print(f"OK       [{conv.kind}] {name} -> {dest}\n         report: {report}\n         {counts}")
        if bak:
            print(f"         old version backed up in {bak}")
    return 1 if errors else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    argv = [a for a in argv if not a.startswith("-psn_")]   # old macOS adds this when opening an .app
    frozen = getattr(sys, "frozen", False)
    if not argv:
        from .gui import main_window
        main_window()
        return 0
    # Files dropped onto the exe (no console): convert them with dialogs
    if frozen and sys.stdout is None and all(not a.startswith("-") for a in argv):
        from .gui import drop_mode
        drop_mode([p for a in argv for p in (list_profiles(a) if os.path.isdir(a) else [a])])
        return 0
    return run_cli(argv)
