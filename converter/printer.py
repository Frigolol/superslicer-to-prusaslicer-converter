"""Printer settings: SuperSlicer -> PrusaSlicer 2.9."""
import os

from .common import Conversion

# Start G-code proposed for Klipper printers driven by a PRINT_START macro (PrusaSlicer placeholders).
PRINT_START_GCODE = (
    "M104 S0 ; Cancel slicer-injected heating so PRINT_START controls it\\n"
    "M140 S0 ; Cancel slicer-injected heating so PRINT_START controls it\\n"
    "print_start EXTRUDER=[first_layer_temperature[initial_extruder]] BED=[first_layer_bed_temperature]"
)

# Same name, same meaning in both slicers.
DIRECT_KEYS = [
    "bed_shape", "before_layer_gcode", "between_objects_gcode", "binary_gcode", "color_change_gcode",
    "cooling_tube_length", "cooling_tube_retraction", "default_filament_profile", "default_print_profile",
    "deretract_speed", "end_gcode", "extra_loading_move", "extruder_colour", "extruder_offset",
    "high_current_on_filament_swap", "layer_gcode",
    "machine_max_acceleration_e", "machine_max_acceleration_extruding", "machine_max_acceleration_retracting",
    "machine_max_acceleration_travel", "machine_max_acceleration_x", "machine_max_acceleration_y",
    "machine_max_acceleration_z", "machine_max_feedrate_e", "machine_max_feedrate_x", "machine_max_feedrate_y",
    "machine_max_feedrate_z", "machine_max_jerk_e", "machine_max_jerk_x", "machine_max_jerk_y",
    "machine_max_jerk_z", "machine_max_junction_deviation", "machine_min_extruding_rate",
    "machine_min_travel_rate", "max_print_height", "multimaterial_purging", "nozzle_diameter",
    "nozzle_high_flow", "parking_pos_retraction", "pause_print_gcode", "prefer_clockwise_movements",
    "print_host", "printer_notes", "printer_technology", "printhost_apikey", "printhost_cafile",
    "retract_before_travel", "retract_before_wipe", "retract_layer_change", "retract_length",
    "retract_length_toolchange", "retract_lift", "retract_lift_above", "retract_lift_below",
    "retract_restart_extra", "retract_restart_extra_toolchange", "retract_speed", "silent_mode",
    "single_extruder_multi_material", "template_custom_gcode", "toolchange_gcode",
    "travel_lift_before_obstacle", "travel_max_lift", "travel_ramping_lift", "travel_slope",
    "use_firmware_retraction", "use_relative_e_distances", "use_volumetric_e", "variable_layer_height",
    "wipe", "z_offset", "extruder_clearance_height", "extruder_clearance_radius",
]

# PrusaSlicer 2.9.6 defaults for keys missing from the SuperSlicer profile.
# "@" = one value per extruder.
PRUSA_DEFAULTS = {
    "binary_gcode": "0",
    "custom_parameters_printer": "",
    "extruder_clearance_height": "20",
    "extruder_clearance_radius": "20",
    "machine_max_junction_deviation": "0,0",
    "multimaterial_purging": "140",
    "nozzle_high_flow": "@0",
    "prefer_clockwise_movements": "0",
    "travel_lift_before_obstacle": "@0",
    "travel_max_lift": "@0",
    "travel_ramping_lift": "@0",
    "travel_slope": "@0",
}

GCODE_FLAVORS = ["klipper", "marlin2", "marlin", "reprapfirmware", "repetier", "teacup", "makerware",
                 "sailfish", "mach3", "machinekit", "smoothie", "no-extrusion"]
HOST_TYPES = ["prusalink", "prusaconnect", "octoprint", "moonraker", "duet", "flashair", "astrobox",
              "repetier", "mks"]
HOST_MAP = {"klipper": "moonraker"}
LIMITS_USAGE = ["emit_to_gcode", "time_estimate_only", "ignore"]
THUMB_FORMATS = ["PNG", "JPG", "QOI", "BTT_TFT"]

IGNORED_NOTES = {
    "arc_fitting": "PrusaSlicer has `arc_fitting` in the print settings",
    "arc_fitting_tolerance": "PrusaSlicer has `arc_fitting` in the print settings",
    "retract_lift_top": "PrusaSlicer lifts on every surface",
    "printer_custom_variables": "PrusaSlicer uses `custom_parameters_printer` (JSON), set it by hand if needed",
    "start_gcode_manual": "converted to `autoemit_temperature_commands`",
}


class PrinterConversion(Conversion):
    kind = "printer"

    def run(self):
        ss = self.ss
        n = len(ss.get("nozzle_diameter", "0.4").split(","))
        nozzles = [float(x) for x in ss.get("nozzle_diameter", "0.4").split(",")]

        # identity / inheritance: SuperSlicer vendor profiles do not exist in PrusaSlicer
        for k in ("inherits", "printer_model", "printer_vendor", "printer_variant", "printer_settings_id"):
            v = self.get(k, "")
            if v.strip('"'):
                self.set(k, "", "converted", f"was `{v}`: refers to SuperSlicer, cleared")
            else:
                self.set(k, "")

        for k in DIRECT_KEYS:
            if k in ss:
                v = self.get(k)
                if self.disabled(v):
                    self.set(k, v[1:], "converted", "SuperSlicer disabled value (`!`), value kept")
                else:
                    self.set(k, v)

        # bed model / texture: absolute paths, maybe from another computer
        for k in ("bed_custom_model", "bed_custom_texture"):
            v = self.get(k, "")
            path = v.replace("\\\\", "\\")
            if v and not os.path.isfile(path):
                self.doubt(k, "", [v], f"file not found on this computer: `{path}`", closed=True,
                           labels={"": "None (PrusaSlicer default bed)", v: f"Keep {os.path.basename(path)}"})
            else:
                self.set(k, v)

        # gcode flavor
        v = self.get("gcode_flavor", "marlin2")
        if v in GCODE_FLAVORS:
            self.set("gcode_flavor", v)
        else:
            self.doubt("gcode_flavor", "marlin2", GCODE_FLAVORS,
                       f"`{v}` does not exist in PrusaSlicer", closed=True)

        # host type
        v = self.get("host_type", "prusalink")
        if v in HOST_MAP:
            self.set("host_type", HOST_MAP[v], "converted", f"SuperSlicer `{v}` = PrusaSlicer `{HOST_MAP[v]}`")
        elif v in HOST_TYPES:
            self.set("host_type", v)
        else:
            self.doubt("host_type", "octoprint", HOST_TYPES, f"`{v}` does not exist in PrusaSlicer", closed=True)

        # machine limits
        v = self.get("machine_limits_usage", "time_estimate_only")
        if v in LIMITS_USAGE:
            self.set("machine_limits_usage", v)
        else:
            self.doubt("machine_limits_usage", "time_estimate_only", LIMITS_USAGE,
                       f"`{v}` does not exist in PrusaSlicer", closed=True)

        # layer height limits: % of nozzle -> mm
        for k, dflt in (("max_layer_height", "0"), ("min_layer_height", "0.07")):
            raw = self.get(k)
            if raw is None:
                self.set(k, ",".join([dflt] * n), "default")
                continue
            vals = raw.split(",")
            if any(x.endswith("%") for x in vals):
                mm = [fmt(float(x[:-1]) / 100 * nozzles[min(i, len(nozzles) - 1)]) if x.endswith("%") else x
                      for i, x in enumerate(vals)]
                self.set(k, ",".join(mm), "converted", f"`{raw}` of the nozzle diameter -> mm")
            else:
                self.set(k, raw)

        # thumbnails: "32x32,400x300" + thumbnails_format -> "32x32/PNG, 400x300/PNG"
        fmt_ = self.get("thumbnails_format", "PNG")
        if fmt_ not in THUMB_FORMATS:
            self.doubt("thumbnails_format", "PNG", THUMB_FORMATS, f"`{fmt_}` does not exist in PrusaSlicer",
                       closed=True)
            fmt_ = "PNG"
        else:
            self.set("thumbnails_format", fmt_)
        raw = self.get("thumbnails", "")
        sizes = [s.strip() for s in raw.split(",") if s.strip()]
        if sizes and not all("/" in s for s in sizes):
            new = ", ".join(s if "/" in s else f"{s}/{fmt_}" for s in sizes)
            self.set("thumbnails", new, "converted", f"`{raw}` + format {fmt_}")
        else:
            self.set("thumbnails", raw)

        # temperatures emitted by the slicer before the start G-code
        if "autoemit_temperature_commands" in ss:
            self.set("autoemit_temperature_commands", self.get("autoemit_temperature_commands"))
        else:
            manual = self.get("start_gcode_manual", "0")
            v = "0" if manual == "1" else "1"
            self.set("autoemit_temperature_commands", v, "converted", f"from `start_gcode_manual = {manual}`")

        # remaining times
        self.set("remaining_times", self.get("remaining_times", "0"))
        rt = self.get("remaining_times_type", "m73")
        if rt != "m73" and self.out["remaining_times"] == "1":
            self.note("ignored", "remaining_times_type", rt, "PrusaSlicer always emits M73")

        # start G-code
        start = self.get("start_gcode", "")
        if start.strip() == PRINT_START_GCODE:
            self.set("start_gcode", start)
        else:
            self.doubt("start_gcode", PRINT_START_GCODE, [start],
                       "adapt the start G-code for PrusaSlicer (PRINT_START macro with PrusaSlicer placeholders) "
                       "or keep the SuperSlicer one unchanged",
                       closed=True,
                       labels={PRINT_START_GCODE: "PrusaSlicer print_start (M104 S0, M140 S0, print_start "
                                                  "EXTRUDER=... BED=...)",
                               start: "Keep the SuperSlicer start G-code"})

        # PrusaSlicer-only keys
        for k, v in PRUSA_DEFAULTS.items():
            if k not in self.out:
                self.set(k, ",".join([v[1:]] * n) if v.startswith("@") else v, "default")

        for k, why in IGNORED_NOTES.items():
            if k in ss:
                self.get(k)
                self.note("ignored", k, ss[k], why)
        self.log_unused()
        self.apply_overrides()
        return self


def fmt(x):
    return f"{round(x, 4):g}"
