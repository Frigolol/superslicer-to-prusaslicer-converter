import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from converter.batch import Options, convert, destination, save  # noqa: E402
from converter.common import parse_ini, parse_overrides, read_text, valid_choice  # noqa: E402
from converter.filament import FilamentConversion  # noqa: E402
from converter.print_profile import PrintConversion  # noqa: E402
from converter.printer import PRINT_START_GCODE, PrinterConversion  # noqa: E402

EX = ROOT / "examples"
SUPER_FIL = read_text(EX / "superslicer_abs.ini")
PRUSA_FIL = read_text(EX / "prusaslicer_asa.ini")
SUPER_PRINT = read_text(EX / "superslicer_print.ini")
SUPER_PRINTER = read_text(EX / "superslicer_printer.ini")


# ---------------------------------------------------------------------------
# Filament
# ---------------------------------------------------------------------------
class FilamentSuperToPrusa(unittest.TestCase):
    def setUp(self):
        self.c = FilamentConversion(SUPER_FIL).run()
        self.out, self.src = self.c.out, parse_ini(SUPER_FIL)
        self.ignored = {r[1] for r in self.c.log if r[0] == "ignored"}

    def test_common_values_copied(self):
        for key in ("temperature", "first_layer_temperature", "bed_temperature",
                    "extrusion_multiplier", "filament_cost", "filament_density",
                    "filament_diameter", "filament_type", "slowdown_below_layer_time"):
            self.assertEqual(self.out[key], self.src[key], key)

    def test_renamed_parameters(self):
        self.assertEqual(self.out["min_fan_speed"], self.src["default_fan_speed"])
        self.assertIn("custom_parameters_filament", self.out)
        self.assertIn("filament_seam_gap_distance", self.out)

    def test_phony_values_become_nil(self):
        self.assertEqual(self.out["filament_retract_length"], "nil")
        self.assertEqual(self.out["filament_wipe"], "nil")

    def test_no_phony_prefix_left(self):
        self.assertFalse([k for k, v in self.out.items() if v.startswith("!")])

    def test_superslicer_only_parameters_ignored(self):
        for key in ("filament_pressure_advance", "infill_fan_speed"):
            self.assertNotIn(key, self.out)
            self.assertIn(key, self.ignored)

    def test_no_leaked_compatibility_condition(self):
        self.assertEqual(self.out["inherits"], "")
        self.assertEqual(self.out["compatible_printers_condition"], "")

    def test_disabled_fan_speed_is_a_doubt(self):
        d = {x["key"]: x for x in self.c.doubts}
        self.assertIn("bridge_fan_speed", d)
        self.assertEqual(d["bridge_fan_speed"]["options"], ["100", self.src["default_fan_speed"]])


class FilamentPrusaToSuper(unittest.TestCase):
    def setUp(self):
        self.c = FilamentConversion(PRUSA_FIL, target="super").run()
        self.out, self.src = self.c.out, parse_ini(PRUSA_FIL)

    def test_common_values_copied(self):
        for key in ("temperature", "bed_temperature", "extrusion_multiplier",
                    "filament_density", "filament_type", "filament_max_volumetric_speed"):
            self.assertEqual(self.out[key], self.src[key], key)

    def test_renamed_parameters(self):
        self.assertEqual(self.out["default_fan_speed"], self.src["min_fan_speed"])

    def test_nil_becomes_phony(self):
        self.assertTrue(self.out["filament_retract_length"].startswith("!"))

    def test_prusa_only_parameters_ignored(self):
        self.assertNotIn("filament_abrasive", self.out)
        self.assertIn("filament_abrasive", {r[1] for r in self.c.log if r[0] == "ignored"})


# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------
class Print(unittest.TestCase):
    def setUp(self):
        self.c = PrintConversion(SUPER_PRINT, nozzle=0.4).run()
        self.out = self.c.out

    def test_widths_in_mm(self):
        self.assertEqual(self.out["perimeter_extrusion_width"], "0.444")
        self.assertEqual(self.out["solid_infill_extrusion_width"], "0.524")

    def test_conversions(self):
        self.assertEqual(self.out["bridge_flow_ratio"], "0.8")
        self.assertEqual(self.out["elefant_foot_compensation"], "0.07")
        self.assertEqual(self.out["top_fill_pattern"], "monotoniclines")
        self.assertEqual(self.out["top_one_perimeter_type"], "top")

    def test_doubts(self):
        self.assertEqual(sorted(d["key"] for d in self.c.doubts),
                         ["ensure_vertical_shell_thickness", "resolution"])

    def test_choice_applied(self):
        self.c.apply_choices({"ensure_vertical_shell_thickness": "partial"})
        self.assertEqual(self.c.out["ensure_vertical_shell_thickness"], "partial")

    def test_choice_validation(self):
        d = {x["key"]: x for x in self.c.doubts}
        self.assertFalse(valid_choice(d["ensure_vertical_shell_thickness"], "foo"))
        self.assertTrue(valid_choice(d["resolution"], "0.01"))
        self.assertFalse(valid_choice(d["resolution"], "abc"))

    def test_no_phony_prefix_left(self):
        self.assertFalse([k for k, v in self.out.items() if v.startswith("!")])


# ---------------------------------------------------------------------------
# Printer
# ---------------------------------------------------------------------------
class Printer(unittest.TestCase):
    def setUp(self):
        self.c = PrinterConversion(SUPER_PRINTER).run()
        self.out, self.src = self.c.out, parse_ini(SUPER_PRINTER)

    def test_direct_values(self):
        for key in ("bed_shape", "nozzle_diameter", "retract_length", "machine_max_acceleration_x",
                    "end_gcode", "toolchange_gcode", "gcode_flavor"):
            self.assertEqual(self.out[key], self.src[key], key)

    def test_conversions(self):
        self.assertEqual(self.out["max_layer_height"], ",".join(["0.3"] * 5))
        self.assertEqual(self.out["thumbnails"], "32x32/PNG, 400x300/PNG")
        self.assertEqual(self.out["printer_settings_id"], "")
        self.assertEqual(self.out["nozzle_high_flow"], "0,0,0,0,0")

    def test_host_klipper_is_moonraker(self):
        c = PrinterConversion(SUPER_PRINTER.replace("host_type = octoprint", "host_type = klipper")).run()
        self.assertEqual(c.out["host_type"], "moonraker")

    def test_start_gcode_proposed_and_kept(self):
        d = {x["key"]: x for x in self.c.doubts}["start_gcode"]
        self.assertEqual(self.out["start_gcode"], PRINT_START_GCODE)
        self.assertEqual(d["options"], [PRINT_START_GCODE, self.src["start_gcode"]])
        self.assertIn(self.src["start_gcode"], d["labels"])
        self.c.apply_choices({"start_gcode": self.src["start_gcode"]})
        self.assertEqual(self.c.out["start_gcode"], self.src["start_gcode"])

    def test_start_gcode_already_adapted(self):
        text = SUPER_PRINTER.replace(self.src["start_gcode"], PRINT_START_GCODE)
        c = PrinterConversion(text).run()
        self.assertNotIn("start_gcode", [d["key"] for d in c.doubts])

    def test_missing_bed_model_is_a_doubt(self):
        keys = [d["key"] for d in self.c.doubts]
        self.assertIn("bed_custom_model", keys)
        self.assertEqual(self.out["bed_custom_model"], "")


# ---------------------------------------------------------------------------
# Overrides, detection, writing
# ---------------------------------------------------------------------------
class Batch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_overrides_sections(self):
        o = parse_overrides(ROOT / "overrides.example.ini")
        self.assertEqual(o["print"]["fill_angle"][0], "45")
        self.assertEqual(o["filament"], {})

    def test_overrides_without_section_are_print(self):
        p = os.path.join(self.tmp, "o.ini")
        Path(p).write_text("# reason\nfill_angle = 45\n", encoding="utf-8")
        self.assertEqual(parse_overrides(p)["print"]["fill_angle"], ("45", "reason"))

    def test_override_removes_doubt(self):
        c = PrintConversion(SUPER_PRINT, {"resolution": ("0", "test")}).run()
        self.assertEqual([d["key"] for d in c.doubts], ["ensure_vertical_shell_thickness"])
        self.assertEqual(c.out["resolution"], "0")

    def test_kind_detected_and_written_with_report(self):
        opts = Options(overrides=parse_overrides(ROOT / "overrides.example.ini"))
        for f, kind in (("superslicer_print.ini", "print"), ("superslicer_abs.ini", "filament"),
                        ("superslicer_printer.ini", "printer")):
            c = convert(str(EX / f), opts)
            self.assertEqual(c.kind, kind)
            dest = destination(c, self.tmp)
            self.assertEqual(os.path.basename(dest), f)
            report, bak = save(c, dest)
            self.assertTrue(os.path.isfile(dest) and os.path.isfile(report))
            self.assertIsNone(bak)

    def test_existing_profile_backed_up(self):
        c = convert(str(EX / "superslicer_abs.ini"), Options())
        dest = destination(c, os.path.join(self.tmp, "filament"))
        save(c, dest)
        _, bak = save(c, dest)
        self.assertTrue(os.path.isfile(os.path.join(bak, "superslicer_abs.ini")))

    def test_print_to_superslicer_rejected(self):
        with self.assertRaises(ValueError):
            convert(str(EX / "superslicer_print.ini"), Options(target="super"))

    def test_printer_overrides_section(self):
        p = os.path.join(self.tmp, "o.ini")
        Path(p).write_text("[printer]\n# my macro\nstart_gcode = PRINT_START\n", encoding="utf-8")
        o = parse_overrides(p)
        c = convert(str(EX / "superslicer_printer.ini"), Options(overrides=o))
        self.assertEqual(c.out["start_gcode"], "PRINT_START")
        self.assertNotIn("start_gcode", [d["key"] for d in c.doubts])

    def test_same_target_rejected(self):
        with self.assertRaises(ValueError):
            convert(str(EX / "superslicer_abs.ini"), Options(target="super"))


if __name__ == "__main__":
    unittest.main()
