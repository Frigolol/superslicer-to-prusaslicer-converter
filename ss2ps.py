"""SuperSlicer -> PrusaSlicer profile converter (print settings and filaments).

Run without arguments to open the window, or see `python ss2ps.py --help`.
"""
import sys

from converter.cli import main

if __name__ == "__main__":
    sys.exit(main())
