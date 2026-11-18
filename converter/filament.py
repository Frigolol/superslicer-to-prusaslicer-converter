"""Filament profiles: SuperSlicer <-> PrusaSlicer.

How it works: start from a template profile of the target slicer (embedded below,
taken from two sample exports: SuperSlicer 2.7.61.10, PrusaSlicer 2.9.6), then
overwrite every parameter that has an equivalent in the source profile.

SuperSlicer convention: a value prefixed with "!" is disabled (inherited from the
printer / print profile). It becomes "nil" in PrusaSlicer when the parameter accepts it.
"""
import re

from .common import Conversion, parse_ini

# Embedded template profiles (values for parameters with no source value)
SUPER_TEMPLATE = r"""
bed_temperature = 110
bridge_fan_speed = !100
chamber_temperature = 50
compatible_printers =
compatible_printers_condition =
compatible_prints =
compatible_prints_condition =
default_fan_speed = 50
disable_fan_first_layers = 1
end_filament_gcode = "; Filament-specific end gcode \n;END gcode for filament\n"
external_perimeter_fan_speed = !100
extrusion_multiplier = 0.96
fan_below_layer_time = 0
filament_colour = #FF00FF
filament_cooling_final_speed = 3.4
filament_cooling_initial_speed = 2.2
filament_cooling_moves = 4
filament_cooling_zone_pause = 0
filament_cost = 22
filament_custom_variables = ""
filament_density = 1.03
filament_deretract_speed = !0
filament_diameter = 1.75
filament_dip_extraction_speed = 70
filament_dip_insertion_speed = 33
filament_enable_toolchange_part_fan = 0
filament_enable_toolchange_temp = 0
filament_fill_top_flow_ratio = 100%
filament_first_layer_flow_ratio = 100%
filament_load_time = 0
filament_loading_speed = 28
filament_loading_speed_start = 3
filament_max_overlap = 100%
filament_max_speed = 0
filament_max_volumetric_speed = 0
filament_max_wipe_tower_speed = 0
filament_melt_zone_pause = 0
filament_minimal_purge_on_wipe_tower = 15
filament_multitool_ramming = 0
filament_multitool_ramming_flow = 10
filament_multitool_ramming_volume = 10
filament_notes = ""
filament_pressure_advance = !0.02
filament_ramming_parameters = "120 100 6.6 6.8 7.2 7.6 7.9 8.2 8.7 9.4 9.9 10.0| 0.05 6.6 0.45 6.8 0.95 7.8 1.45 8.3 1.95 9.7 2.45 10 2.95 7.6 3.45 7.6 3.95 7.6 4.45 7.6 4.95 7.6"
filament_retract_before_travel = !2
filament_retract_before_wipe = !0%
filament_retract_layer_change = !0
filament_retract_length = !2
filament_retract_length_toolchange = !10
filament_retract_lift = !0
filament_retract_lift_above = !0
filament_retract_lift_before_travel = !2
filament_retract_lift_below = !0
filament_retract_restart_extra = !0
filament_retract_restart_extra_toolchange = !0
filament_retract_speed = !40
filament_seam_gap = !15%
filament_settings_id = "ABS - KVP"
filament_shrink = 100%
filament_skinnydip_distance = 31
filament_soluble = 0
filament_spool_weight = 1000
filament_toolchange_delay = 0
filament_toolchange_part_fan_speed = 50
filament_toolchange_temp = 200
filament_travel_lift_before_obstacle = !0
filament_travel_ramping_lift = !0
filament_travel_slope = !0
filament_type = ABS
filament_unload_time = 0
filament_unloading_speed = 90
filament_unloading_speed_start = 100
filament_use_fast_skinnydip = 0
filament_use_skinnydip = 0
filament_vendor = (Unknown)
filament_wipe = !0
filament_wipe_advanced_pigment = 0.5
filament_wipe_extra_perimeter = !0
filament_wipe_inside_depth = !50%
filament_wipe_inside_end = !1
filament_wipe_inside_start = !0
filament_wipe_lift = !0
filament_wipe_lift_length = !50%
filament_wipe_min = !150%
filament_wipe_only_crossing = !1
filament_wipe_speed = !0
first_layer_bed_temperature = 110
first_layer_temperature = 255
full_fan_speed_layer = 0
gap_fill_fan_speed = !100
idle_temperature = !30
infill_fan_speed = !100
inherits =
internal_bridge_fan_speed = !100
max_fan_speed = 100
max_speed_reduction = 90%
min_print_speed = 10
overhangs_dynamic_fan_speed = !0:5:1:0x100:25x80:50x60:75x40:100x20
overhangs_fan_speed = !100
perimeter_fan_speed = !100
slowdown_below_layer_time = 15
solid_infill_fan_speed = !100
start_filament_gcode = "; Filament gcode\n"
support_material_fan_speed = !100
support_material_interface_fan_speed = !100
temperature = 255
top_fan_speed = !100
"""

PRUSA_TEMPLATE = r"""
bed_temperature = 110
bridge_fan_speed = 50
chamber_minimal_temperature = 40
chamber_temperature = 55
compatible_printers =
compatible_printers_condition = printer_model=~/(V2_250|V2_300|V2_350|VT_250|VT_300|VT_350|V0_120|VS_MK52)/ and nozzle_high_flow[0] and nozzle_diameter[0]==0.4
compatible_prints =
compatible_prints_condition =
cooling = 1
cooling_perimeter_transition_distance = 10
cooling_slowdown_logic = uniform_cooling
custom_parameters_filament = ""
disable_fan_first_layers = 1
enable_dynamic_fan_speeds = 0
end_filament_gcode = "; Filament-specific end gcode"
extrusion_multiplier = 0.92
fan_always_on = 1
fan_below_layer_time = 0
filament_abrasive = 0
filament_colour = #FF3232
filament_cooling_final_speed = 3.4
filament_cooling_initial_speed = 2.2
filament_cooling_moves = 4
filament_cost = 0
filament_density = 1.07
filament_deretract_speed = nil
filament_diameter = 1.75
filament_flush_speed = 0
filament_flush_volume = 0
filament_infill_max_crossing_speed = 0
filament_infill_max_speed = 0
filament_load_time = 0
filament_loading_speed = 28
filament_loading_speed_start = 3
filament_max_volumetric_speed = 25
filament_minimal_purge_on_wipe_tower = 15
filament_multitool_ramming = 0
filament_multitool_ramming_flow = 10
filament_multitool_ramming_volume = 10
filament_notes = ""
filament_purge_multiplier = 100%
filament_ramming_parameters = "120 100 5.70968 6.03226 7 8.25806 9 9.19355 9.3871 9.77419 10.129 10.3226 10.4516 10.5161| 0.05 5.69677 0.45 6.15484 0.95 8.76774 1.45 9.20323 1.95 9.95806 2.45 10.3871 2.95 10.5677 3.45 7.6 3.95 7.6 4.45 7.6 4.95 7.6"
filament_retract_before_travel = nil
filament_retract_before_wipe = nil
filament_retract_layer_change = nil
filament_retract_length = nil
filament_retract_length_toolchange = nil
filament_retract_lift = nil
filament_retract_lift_above = nil
filament_retract_lift_below = nil
filament_retract_restart_extra = nil
filament_retract_restart_extra_toolchange = nil
filament_retract_speed = nil
filament_seam_gap_distance = nil
filament_settings_id = ""
filament_shrinkage_compensation_xy = 0%
filament_shrinkage_compensation_z = 0%
filament_soluble = 0
filament_spool_weight = 0
filament_stamping_distance = 0
filament_stamping_loading_speed = 20
filament_toolchange_delay = 0
filament_travel_lift_before_obstacle = nil
filament_travel_max_lift = nil
filament_travel_ramping_lift = nil
filament_travel_slope = nil
filament_type = ASA
filament_unload_time = 0
filament_unloading_speed = 90
filament_unloading_speed_start = 100
filament_vendor = Generic
filament_wipe = nil
first_layer_bed_temperature = 110
first_layer_temperature = 255
full_fan_speed_layer = 0
idle_temperature = nil
inherits = Generic ASA @Voron HF0.4
max_fan_speed = 50
min_fan_speed = 50
min_print_speed = 10
overhang_fan_speed_0 = 0
overhang_fan_speed_1 = 0
overhang_fan_speed_2 = 0
overhang_fan_speed_3 = 0
slowdown_below_layer_time = 10
start_filament_gcode = "; Filament-specific start gcode"
temperature = 255
"""

# Renamed parameters (SuperSlicer -> PrusaSlicer)
RENAME_SUPER_TO_PRUSA = {
    "default_fan_speed": "min_fan_speed",
    "filament_custom_variables": "custom_parameters_filament",
    "filament_seam_gap": "filament_seam_gap_distance",
}
RENAME_PRUSA_TO_SUPER = {v: k for k, v in RENAME_SUPER_TO_PRUSA.items()}

# Profile/machine-specific parameters
RESET_KEYS = ("inherits", "compatible_printers", "compatible_printers_condition",
              "compatible_prints", "compatible_prints_condition")


def pct(value):
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*%?\s*$", value.strip('"'))
    return float(m.group(1)) if m else None


def fmt_pct(x):
    return f"{x:g}%"


def to_number(value):
    try:
        return float(value.lstrip("!"))
    except ValueError:
        return None


class FilamentConversion(Conversion):
    """SuperSlicer -> PrusaSlicer (default) or PrusaSlicer -> SuperSlicer (target='super')."""
    kind = "filament"

    def __init__(self, src_text, overrides=None, src_path="", target="prusa", keep_phony=False):
        super().__init__(src_text, overrides if target == "prusa" else None, src_path)
        self.target = target
        self.keep_phony = keep_phony

    def run(self):
        if self.target == "prusa":
            self._super_to_prusa()
        else:
            self._prusa_to_super()
        return self

    # -- SuperSlicer -> PrusaSlicer ----------------------------------------------
    def _super_to_prusa(self):
        tmpl = parse_ini(PRUSA_TEMPLATE)
        src = self.ss
        for k, v in src.items():
            if k == "filament_shrink":
                continue  # handled below
            tk = RENAME_SUPER_TO_PRUSA.get(k, k)
            if tk not in tmpl or k in RESET_KEYS:
                continue
            self.used.add(k)
            renamed = f" (renamed from {k})" if tk != k else ""
            if self.disabled(v):
                val = v[1:]
                if tmpl[tk] == "nil" and not self.keep_phony:
                    self.set(tk, "nil", "converted", f"`{v}` disabled in SuperSlicer -> nil (inherited){renamed}")
                elif tmpl[tk] == "nil":
                    self.set(tk, val, "converted", f"`{v}` disabled in SuperSlicer, kept as a real value{renamed}")
                else:
                    # A disabled fan speed falls back to the default fan speed in SuperSlicer
                    alt = src.get("default_fan_speed", "").lstrip("!") if tk.endswith("fan_speed") else ""
                    self.doubt(tk, val, [alt] if alt else [],
                               f"`{v}` is disabled in SuperSlicer but PrusaSlicer has no 'inherited' value here: "
                               f"value kept" + (f" (or {alt} = default fan speed)" if alt else "") + renamed)
            elif renamed:
                self.set(tk, v, "converted", renamed.strip(" ()"))
            else:
                self.set(tk, v)

        # Shrinkage: SuperSlicer stores the size after cooling (99.5% = shrinks 0.5%),
        # PrusaSlicer the compensation (0.5%).
        if "filament_shrink" in src:
            s = pct(self.get("filament_shrink").lstrip("!"))
            if s is not None:
                comp = fmt_pct(round(100 - s, 6))
                self.set("filament_shrinkage_compensation_xy", comp, "converted",
                         f"filament_shrink `{src['filament_shrink']}` -> compensation {comp}")

        for k in RESET_KEYS:
            self.set(k, self.get(k, ""))

        fan_min = to_number(self.out.get("min_fan_speed", "0")) or 0
        self.set("fan_always_on", "1" if fan_min > 0 else "0", "converted",
                 f"min_fan_speed {fan_min:g} -> fan {'always on' if fan_min > 0 else 'not always on'}")

        if self.out.get("filament_vendor") == "(Unknown)":
            self.set("filament_vendor", "Generic", "converted", "`(Unknown)` -> Generic")

        self.apply_overrides()
        for k, v in sorted(tmpl.items()):
            if k not in self.out:
                self.set(k, v, "default", "no SuperSlicer equivalent, template value")
        self.log_unused()

    # -- PrusaSlicer -> SuperSlicer ----------------------------------------------
    def _prusa_to_super(self):
        tmpl = parse_ini(SUPER_TEMPLATE)
        src = self.ss
        for k, v in src.items():
            if k in ("filament_shrinkage_compensation_xy", "filament_shrinkage_compensation_z") or k in RESET_KEYS:
                continue
            tk = RENAME_PRUSA_TO_SUPER.get(k, k)
            if tk not in tmpl:
                continue
            self.used.add(k)
            renamed = f" (renamed from {k})" if tk != k else ""
            if v == "nil":
                d = tmpl[tk]
                self.set(tk, d if d.startswith("!") else "!" + d, "converted", f"nil -> disabled value{renamed}")
            elif renamed:
                self.set(tk, v, "converted", renamed.strip(" ()"))
            else:
                self.set(tk, v)

        if "filament_shrinkage_compensation_xy" in src:
            c = pct(self.get("filament_shrinkage_compensation_xy"))
            if c is not None:
                s = fmt_pct(round(100 - c, 6))
                self.set("filament_shrink", s, "converted", f"compensation `{src['filament_shrinkage_compensation_xy']}` -> {s}")

        for k in RESET_KEYS:
            v = self.get(k, "")
            self.set(k, "", "converted" if v else "direct",
                     f"PrusaSlicer-specific expression not carried over: {v[:60]}" if v else "")

        for k, v in sorted(tmpl.items()):
            if k not in self.out:
                self.set(k, v, "default", "no PrusaSlicer equivalent, template value")
        self.log_unused("no SuperSlicer equivalent")
