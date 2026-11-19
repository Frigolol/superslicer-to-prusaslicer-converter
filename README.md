# SuperSlicer to PrusaSlicer converter

Move your **SuperSlicer profiles to PrusaSlicer 2.9**: print settings, filaments and printers, in one Windows program.
Pick what you want to transfer, tick the profiles, click **Convert**: the profiles are installed straight into PrusaSlicer, each one with a report explaining every setting.

> Not affiliated with Prusa Research or the SuperSlicer project.
> Always check a converted profile in PrusaSlicer and test-print before relying on it.

This project replaces two earlier tools:
[superslicer-to-prusaslicer-print-settings-converter](https://github.com/Frigolol/superslicer-to-prusaslicer-print-settings-converter) and
[superslicer-prusaslicer-filament-converter](https://github.com/Frigolol/superslicer-prusaslicer-filament-converter).

---

## Features

- **Print settings, filaments and printers** in the same program, many profiles at once.
- **Your SuperSlicer and PrusaSlicer folders are found automatically**; converted profiles are installed directly into PrusaSlicer.
- **Converts meaning, not just names**, for example:
  - print: extrusion widths in `%` of nozzle → mm, `bridge_flow_ratio` `80%` → `0.8`, `first_layer_size_compensation` → `elefant_foot_compensation`, SuperSlicer-only fill patterns → closest PrusaSlicer pattern, `only_one_perimeter_top` → `top_one_perimeter_type`, …
  - printer: `max_layer_height` in `%` → mm, thumbnails `32x32,400x300` → `32x32/PNG, 400x300/PNG`, host `klipper` → `moonraker`, `start_gcode_manual` → `autoemit_temperature_commands`, …
  - filament: renamed settings (`default_fan_speed` → `min_fan_speed`, `filament_seam_gap` → `filament_seam_gap_distance`, …), shrinkage (`filament_shrink` 99.5% → compensation 0.5%), SuperSlicer disabled values (`!`) → `nil` (inherited), …
- **You decide on doubtful settings**: when a setting has no certain equivalent, the program shows the proposed value with the alternatives, and you keep it or pick another one.
- **Start G-code adapted for PrusaSlicer** (printers): keep your SuperSlicer start G-code, or replace it with a `print_start` call using PrusaSlicer placeholders (see [Start G-code](#start-g-code)).
- **A report for every profile** (`<name> - report.md`, next to the profile), grouping settings by status:

  | status | meaning |
  |---|---|
  | `doubt` | no certain conversion: you confirmed or changed the value |
  | `override` | value forced by your overrides file |
  | `converted` | converted (unit / name / meaning) |
  | `default` | setting that only exists in PrusaSlicer: default value used |
  | `ignored` | SuperSlicer setting with no PrusaSlicer equivalent |
  | `direct` | same name, same meaning, copied as is |

- **Overrides file**: force your own values on every conversion (e.g. `gcode_label_objects = firmware` for Klipper).
- **Nothing is lost**: an existing PrusaSlicer profile is only replaced after you agree, and the old version is backed up.
- Command line too, including filament conversion **PrusaSlicer → SuperSlicer**.

## Download

Get `ss2ps.exe` from the [Releases](../../releases) page. No installation, no Python needed.

Windows may show a SmartScreen warning because the exe is not signed: *More info* → *Run anyway*.

## Usage

### Window

1. Double-click `ss2ps.exe`.
2. For each type (**Print settings**, **Filaments**, **Printers**), keep the box ticked to transfer it or untick it to leave it out. The SuperSlicer and PrusaSlicer folders are filled in automatically (change them with **...** if needed).
3. Tick the profiles to convert (**Select all** / **Select none**).
4. Options: nozzle diameter (used to turn `%` widths into mm), overrides file, and whether you want to be asked about doubtful settings.
5. Click **Convert and install into PrusaSlicer**.
   - If some profiles already exist in PrusaSlicer, you choose: replace them (old versions backed up), skip them, or cancel.
   - For each profile with doubtful settings, a window lists them: keep the proposed value or choose another one, then **OK** (**Skip this profile** leaves it out).
6. Restart PrusaSlicer: the profiles are in the print settings, filament and printer lists, under the same names as in SuperSlicer.

You can also drag `.ini` profiles (or a folder) onto `ss2ps.exe`: they are converted with the same questions, and a summary is shown at the end.

Backups of replaced profiles go to `%APPDATA%\PrusaSlicer\print_backups\`, `...\filament_backups\` and `...\printer_backups\`.

### Command line

```
ss2ps.exe <profiles or folders> [options]
```

or with Python 3.8+ (no dependencies): `python ss2ps.py <profiles or folders> [options]`

| option | meaning |
|---|---|
| `-d`, `--outdir` | output folder (default: PrusaSlicer's `print` / `filament` / `printer` folder) |
| `-o`, `--out` | output file (one input profile only) |
| `--kind print\|filament\|printer` | profile type (default: auto-detected) |
| `--to prusa\|super` | target slicer (default: the other one; print and printer profiles: PrusaSlicer only) |
| `--nozzle` | nozzle diameter for print widths (default `0.4`) |
| `--overrides FILE` | overrides file (default: `overrides.ini` next to the program, if present) |
| `--no-overrides` | ignore `overrides.ini` |
| `--keep-phony` | filament: keep SuperSlicer `!` values as real values instead of `nil` |
| `-y`, `--yes` | keep the proposed values for doubtful settings without asking |
| `-f`, `--force` | replace existing profiles (old version backed up); otherwise they are skipped |

Examples:

```
ss2ps.exe "%APPDATA%\SuperSlicer\print\my print.ini"
ss2ps.exe "%APPDATA%\SuperSlicer\filament" -y
ss2ps.exe "%APPDATA%\SuperSlicer\printer\my printer.ini"
ss2ps.exe "%APPDATA%\PrusaSlicer\filament\Generic ASA.ini" --to super
```

In a terminal, each doubtful setting is asked with its options; press Enter to keep the proposed value.

## Start G-code

For each printer profile, you choose between:

1. **PrusaSlicer `print_start`** (proposed), for Klipper printers whose `PRINT_START` macro handles heating:

   ```
   M104 S0 ; Cancel slicer-injected heating so PRINT_START controls it
   M140 S0 ; Cancel slicer-injected heating so PRINT_START controls it
   print_start EXTRUDER=[first_layer_temperature[initial_extruder]] BED=[first_layer_bed_temperature]
   ```

2. **Keep the SuperSlicer start G-code** unchanged.

With `-y` (command line) or with *Ask me about doubtful settings* unticked, the proposed `print_start` version is used.
To always use your own start G-code instead, put it in the `[printer]` section of the overrides file (on one line, with `\n` between G-code lines).

## Overrides

Some differences are a matter of preference rather than conversion (for example, PrusaSlicer applies `small_perimeter_speed` to *every* small perimeter, whereas SuperSlicer ramps it between two lengths). Put your choices in an overrides file, by section:

```ini
[print]
# Klipper: exclude objects through the firmware
gcode_label_objects = firmware

# 10 mm/s is too slow in PrusaSlicer
small_perimeter_speed = 50

[filament]
filament_max_volumetric_speed = 20

[printer]
host_type = moonraker
```

- one `prusaslicer_key = value` per line, in a `[print]`, `[filament]` or `[printer]` section (lines before any section count as `[print]`);
- the `#` comment directly above a line is copied to the report as the reason;
- a setting set in the overrides file is never asked as a doubt;
- name it `overrides.ini` and place it next to `ss2ps.exe` / `ss2ps.py` to apply it automatically, or pick it in the window.

See [`overrides.example.ini`](overrides.example.ini).

## Where are the profiles?

| OS | folders |
|---|---|
| Windows | `%APPDATA%\SuperSlicer\print`, `...\filament`, `...\printer`; `%APPDATA%\PrusaSlicer\print`, `...\filament`, `...\printer` |
| macOS | `~/Library/Application Support/SuperSlicer/...`, `.../PrusaSlicer/...` |
| Linux | `~/.config/SuperSlicer/...`, `~/.config/PrusaSlicer/...` |

## Build the exe yourself

```
pip install pyinstaller
build.bat
```

The exe is created in `dist\ss2ps.exe`.

## Tests

```
python -m unittest discover tests
```

## Limitations

- Built and checked with SuperSlicer 2.7.61.10 and PrusaSlicer 2.9.6. Other versions may add or rename settings; unknown ones are listed as `ignored`.
- Print settings: SuperSlicer → PrusaSlicer only. Many SuperSlicer-only features (`infill_connection`, `perimeter_direction`, `gap_fill_*` details, seam costs, per-feature accelerations, milling, …) have no PrusaSlicer equivalent.
- Filaments: dynamic overhang fan speeds are not translated. The meaning of SuperSlicer's `!` prefix (disabled / inherited value) was inferred from sample files; use `--keep-phony` if it does not fit your profiles.
- Printers: SuperSlicer → PrusaSlicer only. SuperSlicer-only settings (advanced wipe, fan offsets, G-code precision, milling, time estimates, …) are listed as `ignored`. Custom G-code other than the start G-code is copied as is: check the placeholders it uses. A bed model or texture that is not found on the computer is proposed as empty.
- SuperSlicer physical printers (print host connections) are not transferred.

Issues and pull requests are welcome, especially sample profiles from other versions. If a conversion looks wrong, please attach the source `.ini` and the report.

## License

[MIT](LICENSE)
