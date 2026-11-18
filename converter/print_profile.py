"""Print settings: SuperSlicer -> PrusaSlicer 2.9."""
from .common import Conversion


# ---------------------------------------------------------------------------
# PrusaSlicer 2.9.x defaults for keys that have NO SuperSlicer equivalent.
# Every PrusaSlicer 2.9.6 print key is either here or produced by PrintConversion.run().
# ---------------------------------------------------------------------------
PRUSA_ONLY_DEFAULTS = {
    "arc_fitting": "disabled",
    "automatic_extrusion_widths": "0",
    "automatic_infill_combination": "0",
    "automatic_infill_combination_max_layer_height": "100%",
    "bed_temperature_extruder": "0",
    "brim_type": "outer_only",
    "custom_parameters_print": "",
    "enable_dynamic_overhang_speeds": "0",
    "gcode_resolution": "0.0125",
    "interlocking_beam": "0",
    "interlocking_beam_layer_count": "2",
    "interlocking_beam_width": "0.8",
    "interlocking_boundary_avoidance": "2",
    "interlocking_depth": "2",
    "interlocking_orientation": "22.5",
    "overhang_speed_0": "15",
    "overhang_speed_1": "15",
    "overhang_speed_2": "20",
    "overhang_speed_3": "25",
    "scarf_seam_entire_loop": "0",
    "scarf_seam_length": "20",
    "scarf_seam_max_segment_length": "1",
    "scarf_seam_on_inner_perimeters": "0",
    "scarf_seam_only_on_smooth": "1",
    "scarf_seam_placement": "nowhere",
    "scarf_seam_start_height": "0%",
    "seam_gap_distance": "15%",
    "toolchange_ordering": "optimized",
    "travel_short_distance_acceleration": "250",
    "wipe_tower_acceleration": "0",
    "wipe_tower_extra_flow": "100%",
}

# Keys whose name AND meaning are identical in both slicers.
DIRECT_KEYS = [
    "avoid_crossing_curled_overhangs", "avoid_crossing_perimeters",
    "avoid_crossing_perimeters_max_detour", "bottom_solid_layers",
    "bottom_solid_min_thickness", "bridge_acceleration", "bridge_speed",
    "brim_separation", "brim_width", "compatible_printers",
    "compatible_printers_condition", "complete_objects", "default_acceleration",
    "dont_support_bridges", "draft_shield", "external_perimeter_acceleration",
    "external_perimeter_speed", "external_perimeters_first", "extra_perimeters",
    "extra_perimeters_on_overhangs", "fill_angle", "fill_density", "fill_pattern",
    "first_layer_acceleration", "first_layer_acceleration_over_raft",
    "first_layer_height", "first_layer_infill_speed", "first_layer_speed",
    "first_layer_speed_over_raft", "fuzzy_skin", "gap_fill_enabled",
    "gap_fill_speed", "gcode_comments", "gcode_label_objects",
    "gcode_substitutions", "infill_acceleration", "infill_anchor",
    "infill_anchor_max", "infill_every_layers", "infill_extruder", "infill_first",
    "infill_overlap", "infill_speed", "inherits", "interface_shells", "ironing",
    "ironing_flowrate", "ironing_spacing", "ironing_speed", "ironing_type",
    "layer_height", "max_print_speed",
    "max_volumetric_extrusion_rate_slope_negative",
    "max_volumetric_extrusion_rate_slope_positive", "max_volumetric_speed",
    "min_bead_width", "min_feature_size", "min_skirt_length",
    "mmu_segmented_region_interlocking_depth", "mmu_segmented_region_max_width",
    "notes", "only_one_perimeter_first_layer",
    "only_retract_when_crossing_perimeters", "ooze_prevention",
    "output_filename_format", "perimeter_acceleration", "perimeter_extruder",
    "perimeter_generator", "perimeter_speed", "perimeters", "post_process",
    "raft_contact_distance", "raft_expansion", "raft_first_layer_density",
    "raft_first_layer_expansion", "raft_layers", "seam_position",
    "single_extruder_multi_material_priming", "skirt_distance", "skirt_height",
    "skirts", "slice_closing_radius", "slicing_mode", "small_perimeter_speed",
    "solid_infill_acceleration", "solid_infill_below_area",
    "solid_infill_every_layers", "solid_infill_extruder", "solid_infill_speed",
    "spiral_vase", "staggered_inner_seams", "standby_temperature_delta",
    "support_material", "support_material_angle", "support_material_auto",
    "support_material_buildplate_only", "support_material_closing_radius",
    "support_material_enforce_layers", "support_material_extruder",
    "support_material_interface_contact_loops",
    "support_material_interface_extruder", "support_material_interface_layers",
    "support_material_interface_spacing", "support_material_interface_speed",
    "support_material_pattern", "support_material_spacing",
    "support_material_speed", "support_material_style",
    "support_material_synchronize_layers", "support_material_threshold",
    "support_material_with_sheath", "support_material_xy_spacing",
    "support_tree_angle", "support_tree_angle_slow", "support_tree_branch_diameter",
    "support_tree_branch_diameter_angle", "support_tree_branch_diameter_double_wall",
    "support_tree_branch_distance", "support_tree_tip_diameter",
    "support_tree_top_rate", "thin_walls", "top_solid_infill_acceleration",
    "top_solid_infill_speed", "top_solid_layers", "top_solid_min_thickness",
    "travel_acceleration", "travel_speed", "travel_speed_z",
    "wall_distribution_count", "wall_transition_angle",
    "wall_transition_filter_deviation", "wall_transition_length", "wipe_tower",
    "wipe_tower_bridging", "wipe_tower_brim_width", "wipe_tower_cone_angle",
    "wipe_tower_extra_spacing", "wipe_tower_extruder",
    "wipe_tower_no_sparse_layers", "wipe_tower_width", "xy_size_compensation",
]

# Extrusion widths: SuperSlicer % (of nozzle) -> absolute mm.
WIDTH_KEYS = {
    # PrusaSlicer key: SuperSlicer key
    "extrusion_width": "extrusion_width",
    "external_perimeter_extrusion_width": "external_perimeter_extrusion_width",
    "perimeter_extrusion_width": "perimeter_extrusion_width",
    "infill_extrusion_width": "infill_extrusion_width",
    "solid_infill_extrusion_width": "solid_infill_extrusion_width",
    "top_infill_extrusion_width": "top_infill_extrusion_width",
    "first_layer_extrusion_width": "first_layer_extrusion_width",
    "support_material_extrusion_width": "support_material_extrusion_width",
}


FILL_PATTERN_MAP = {
    # SuperSlicer -> PrusaSlicer
    "monotonicgapfill": "monotoniclines",
    "rectilineargapfill": "rectilinear",
    "concentricgapfill": "concentric",
    "smooth": "monotonic",
    "smoothtriple": "monotonic",
    "smoothhilbert": "monotonic",
    "sawtooth": "rectilinear",
    "rectiwithperimeter": "rectilinear",
    "scatteredrectilinear": "rectilinear",
}
PRUSA_TOP_BOTTOM_PATTERNS = {"rectilinear", "monotonic", "monotoniclines", "alignedrectilinear",
                             "concentric", "hilbertcurve", "archimedeanchords", "octagramspiral"}


class PrintConversion(Conversion):
    kind = "print"

    def __init__(self, src_text, overrides=None, src_path="", nozzle=0.4):
        super().__init__(src_text, overrides, src_path)
        self.nozzle = nozzle
        self.info.append(f"Nozzle: {nozzle} mm")

    def width_mm(self, v):
        """SuperSlicer: % = percentage of nozzle diameter. Returns absolute mm."""
        if v is None or v == "" or self.disabled(v):
            return "0"
        if v.endswith("%"):
            return fmt(float(v[:-1]) / 100 * self.nozzle)
        return v

    def run(self):
        g = self.get

        for k in DIRECT_KEYS:
            if k in self.ss:
                v = g(k)
                if self.disabled(v):
                    self.doubt(k, v[1:], [], f"value disabled in SuperSlicer (`{v}`), copied as is")
                else:
                    self.set(k, v)

        # Extrusion widths: % of nozzle -> mm
        for pk, sk in WIDTH_KEYS.items():
            v = g(sk, "")
            mm = self.width_mm(v)
            self.set(pk, mm, "converted",
                     f"SS `{v}` -> {mm} mm (nozzle {self.nozzle} mm)" if v else "SS empty = auto -> 0 (auto)")
        g("first_layer_infill_extrusion_width")  # no equivalent
        for k in ("external_perimeter_extrusion_spacing", "perimeter_extrusion_spacing",
                  "infill_extrusion_spacing", "solid_infill_extrusion_spacing",
                  "top_infill_extrusion_spacing", "first_layer_extrusion_spacing",
                  "first_layer_infill_extrusion_spacing", "extrusion_spacing"):
            g(k)  # spacing = SuperSlicer's alternative form of width, redundant

        # Bridge flow: 80% -> 0.8
        v = g("bridge_flow_ratio", "100%")
        r = fmt(float(v.rstrip("%")) / 100) if v.endswith("%") else v
        self.set("bridge_flow_ratio", r, "converted", f"`{v}` -> ratio {r}")

        # Thick bridges
        bt = g("bridge_type", "nozzle")
        self.set("thick_bridges", "1" if bt == "nozzle" else "0", "converted",
                 f"bridge_type=`{bt}`: 'nozzle' (nozzle-diameter bridges) ~ thick_bridges=1 in PrusaSlicer")

        # Bridge angle
        v = g("bridge_angle", "0")
        self.set("bridge_angle", "0" if self.disabled(v) else v, "converted",
                 f"`{v}` -> disabled = 0 (auto)" if self.disabled(v) else "")

        # Top / bottom patterns
        for k in ("top_fill_pattern", "bottom_fill_pattern"):
            v = g(k, "monotonic")
            nv = FILL_PATTERN_MAP.get(v, v)
            if nv not in PRUSA_TOP_BOTTOM_PATTERNS:
                self.doubt(k, "monotoniclines", sorted(PRUSA_TOP_BOTTOM_PATTERNS),
                           f"unknown SuperSlicer pattern `{v}`", closed=True)
                continue
            st = "direct" if nv == v else "converted"
            self.set(k, nv, st, "" if nv == v else f"`{v}` does not exist in PrusaSlicer -> `{nv}`")
        v = g("solid_fill_pattern")
        if v:
            self.note("ignored", "solid_fill_pattern", v,
                      "PrusaSlicer has no pattern setting for internal solid infill")

        # Vertical shell
        v = g("ensure_vertical_shell_thickness", "enabled")
        m = {"enabled_old": "enabled", "enabled": "enabled", "partial": "partial",
             "disabled": "disabled", "1": "enabled", "0": "disabled"}
        if v in ("enabled", "partial", "disabled"):
            self.set("ensure_vertical_shell_thickness", v)
        else:
            self.doubt("ensure_vertical_shell_thickness", m.get(v, "enabled"), ["enabled", "partial", "disabled"],
                       f"`{v}` has no exact PrusaSlicer equivalent (partial = PrusaSlicer default, lighter)",
                       closed=True)

        # Elephant foot compensation
        v = g("first_layer_size_compensation", "0")
        g("first_layer_size_compensation_layers"); g("first_layer_size_compensation_no_collapse")
        efc = fmt(abs(float(v))) if float(v) <= 0 else "0"
        self.set("elefant_foot_compensation", efc, "converted",
                 f"first_layer_size_compensation `{v}` -> elefant_foot_compensation {efc} (sign inverted)")

        # Resolution
        v = g("resolution", "0")
        self.doubt("resolution", v, ["0"], "slice simplification copied as is (0 = no simplification, PrusaSlicer default)")
        g("resolution_internal")

        # Single perimeter on top surfaces
        v = g("only_one_perimeter_top", "0")
        g("only_one_perimeter_top_other_algo")
        self.set("top_one_perimeter_type", "top" if v == "1" else "none", "converted",
                 f"only_one_perimeter_top={v} -> {'top (all top surfaces)' if v == '1' else 'none'}")

        # Overhangs
        ow = g("overhangs_width", "75%")
        g("overhangs_width_speed"); g("overhangs_dynamic_speed"); g("overhangs_speed")
        g("overhangs_speed_enforce"); g("overhangs_bridge_threshold"); g("overhangs_bridge_upper_layers")
        g("overhangs_max_slope"); g("overhangs_reverse"); g("overhangs_reverse_threshold")
        on = "0" if self.disabled(ow) or ow in ("0", "0%") else "1"
        self.set("overhangs", on, "converted",
                 f"overhangs_width=`{ow}` -> overhang perimeter detection {'enabled' if on == '1' else 'disabled'}")

        # Speed over internal bridges
        v = g("internal_bridge_speed", "100%")
        self.set("over_bridge_speed", v, "converted",
                 f"internal_bridge_speed `{v}` -> over_bridge_speed")
        g("over_bridge_flow_ratio")

        # Supports
        v = g("support_material_contact_distance", "0.2")
        g("support_material_contact_distance_type")
        self.set("support_material_contact_distance", v)
        v = g("support_material_bottom_contact_distance", "0")
        self.set("support_material_bottom_contact_distance", v)
        v = g("support_material_bottom_interface_layers", "-1")
        self.set("support_material_bottom_interface_layers", "-1" if self.disabled(v) else v, "converted",
                 f"`{v}` disabled -> -1 (same as top)" if self.disabled(v) else "")
        v = g("support_material_top_interface_pattern", "rectilinear")
        g("support_material_bottom_interface_pattern")
        self.set("support_material_interface_pattern", v, "converted", "from support_material_top_interface_pattern")

        # Fuzzy skin : % -> mm
        for k in ("fuzzy_skin_point_dist", "fuzzy_skin_thickness"):
            v = g(k, "0.3")
            mm = self.width_mm(v)
            self.set(k, mm, "converted", f"`{v}` -> {mm} mm")

        # print_custom_variables: not transferred (listed as ignored)

        self.apply_overrides()

        # Keys with no equivalent: PrusaSlicer defaults
        for k, v in PRUSA_ONLY_DEFAULTS.items():
            if k not in self.out:
                self.set(k, v, "default", "no SuperSlicer equivalent, PrusaSlicer default")

        self.set("print_settings_id", "")
        g("print_settings_id"); g("print_version")

        self.log_unused()
        return self


def fmt(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s or "0"
