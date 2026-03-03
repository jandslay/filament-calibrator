"""Parametric temperature tower 3D model generation using CadQuery.

Recreates the geometry from the customizable-temp-tower.scad template
without any OpenSCAD dependency.  All dimensions are in millimetres.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cadquery as cq

# ---------------------------------------------------------------------------
# Geometry constants (matching the OpenSCAD template)
# ---------------------------------------------------------------------------

BASE_LENGTH = 89.3
BASE_WIDTH = 20.0
BASE_HEIGHT = 1.0
BASE_FILLET = 4.0

TIER_LENGTH = 79.0
TIER_WIDTH = 10.0
TIER_HEIGHT = 10.0

TEXT_DEPTH = 0.6

# Overhang dimensions
OVERHANG_45_X = 10.0
OVERHANG_35_X = 14.281

# Central cutout
CUTOUT_LENGTH = 30.0
CUTOUT_HEIGHT = 9.0
CUTOUT_OFFSET = 15.0

# Cones
CONE_HEIGHT = 5.0
SM_CONE_DIAM = 3.0
SM_CONE_OFFSET = 5.0
LG_CONE_DIAM = 5.0
LG_CONE_OFFSET = 25.0

# Holes
HOLE_DIAM = 3.0
HOLE_45_OFFSET = 3.671
HOLE_35_OFFSET = 75.0
HORIZ_HOLE_LEN = 5.0

# Test cutout / protrusion
TEST_CUTOUT_H_OFFSET = 47.0
TEST_CUTOUT_V_OFFSET = 0.3
TEST_CUTOUT_DEPTH = 8.0
PROTRUSION_LENGTH = 16.0
PROTRUSION_HEIGHT = 0.7
PROTRUSION_DEPTH = 0.5

# Temperature label
TEMP_LABEL_SIZE = 6.0
TEMP_LABEL_DEPTH = 1.0
TEMP_LABEL_V_OFFSET = 6.0
TEMP_LABEL_H_OFFSET = 25.0

# Overhang label
OH_LABEL_SIZE = 3.0
OH_LABEL_DEPTH = 0.6


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class TowerConfig:
    """Parameters for the temperature tower.

    Attributes
    ----------
    high_temp:    Highest temperature (bottom tier), in °C.
    temp_jump:    Temperature decrease per tier, in °C.
    num_tiers:    Number of temperature tiers.
    filament_type: Label for filament type (e.g. ``"PLA"``).
    brand_top:    Optional brand label on top of tower.
    brand_bottom: Optional brand label on bottom of base.
    """
    high_temp: int = 220
    temp_jump: int = 10
    num_tiers: int = 9
    filament_type: str = "PLA"
    brand_top: str = ""
    brand_bottom: str = ""


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def tier_temperature(config: TowerConfig, tier_index: int) -> int:
    """Return the temperature for *tier_index* (0 = bottom = hottest)."""
    return config.high_temp - tier_index * config.temp_jump


def total_height(config: TowerConfig) -> float:
    """Return the total tower height including base."""
    return BASE_HEIGHT + config.num_tiers * TIER_HEIGHT


# ---------------------------------------------------------------------------
# Geometry builders
# ---------------------------------------------------------------------------


def _make_filleted_base_plate() -> cq.Workplane:
    """Create the base plate with filleted corners, centred at XY origin."""
    return (
        cq.Workplane("XY")
        .rect(BASE_LENGTH, BASE_WIDTH)
        .extrude(BASE_HEIGHT)
        .edges("|Z")
        .fillet(BASE_FILLET)
    )


def _make_tier_block() -> cq.Workplane:
    """Create the raw tier block (before cuts), origin at its bottom-left."""
    return (
        cq.Workplane("XY")
        .box(TIER_LENGTH, TIER_WIDTH, TIER_HEIGHT, centered=False)
    )


def _make_45_overhang() -> cq.Workplane:
    """Create the 45° overhang cut solid (triangular prism)."""
    pts = [(0, 0), (OVERHANG_45_X, 0), (0, TIER_HEIGHT)]
    return (
        cq.Workplane("XZ")
        .polyline(pts).close()
        .extrude(TIER_WIDTH)
    )


def _make_35_overhang() -> cq.Workplane:
    """Create the 35° overhang cut solid (triangular prism)."""
    pts = [(0, 0), (OVERHANG_35_X, 0), (OVERHANG_35_X, TIER_HEIGHT)]
    return (
        cq.Workplane("XZ")
        .moveTo(TIER_LENGTH - OVERHANG_35_X, 0)
        .polyline([
            (TIER_LENGTH - OVERHANG_35_X, 0),
            (TIER_LENGTH, 0),
            (TIER_LENGTH, TIER_HEIGHT),
        ]).close()
        .extrude(TIER_WIDTH)
    )


def _make_central_cutout() -> cq.Workplane:
    """Create the central rectangular cutout solid."""
    return (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(
            CUTOUT_OFFSET + CUTOUT_LENGTH / 2,
            TIER_WIDTH / 2,
            CUTOUT_HEIGHT / 2,
        ))
        .box(CUTOUT_LENGTH, TIER_WIDTH + 1, CUTOUT_HEIGHT, centered=True)
    )


def _make_vertical_hole(x_offset: float) -> cq.Workplane:
    """Create a vertical cylinder for hole subtraction."""
    return (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(x_offset, TIER_WIDTH / 2, 0))
        .circle(HOLE_DIAM / 2)
        .extrude(TIER_HEIGHT)
    )


def _make_horizontal_hole() -> cq.Workplane:
    """Create the horizontal hole through the bridge area."""
    return (
        cq.Workplane("YZ")
        .transformed(offset=cq.Vector(
            TIER_WIDTH / 2,
            TIER_HEIGHT / 2,
        ))
        .circle(HOLE_DIAM / 2)
        .extrude(HORIZ_HOLE_LEN)
        .translate(cq.Vector(
            CUTOUT_OFFSET + CUTOUT_LENGTH,
            0,
            0,
        ))
    )


def _make_cone(x_offset: float, diameter: float) -> cq.Workplane:
    """Create a cone (positive feature) at the given offset."""
    return (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(
            CUTOUT_OFFSET + x_offset,
            TIER_WIDTH / 2,
            0,
        ))
        .circle(diameter / 2)
        .workplane(offset=CONE_HEIGHT)
        .circle(0.01)  # near-zero top radius for cone
        .loft()
    )


def _make_test_cutout_profile() -> cq.Workplane:
    """Create the 2D test cutout shape.

    Approximation of the OpenSCAD sieve pattern: a half-circle on top of a
    rectangle, with a notch cut from the upper-right corner.
    """
    r_main = 6.0
    rect_w = 10.0
    rect_h = 6.0
    r_notch = 4.0

    # Build a simplified version of the test shape:
    # Main body = half-circle (top) + rectangle (bottom)
    main_circle = (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(6, 1.7, 0))
        .circle(r_main)
    )
    main_rect = (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(6 + rect_w / 2, 1.7 + rect_h / 2, 0))
        .rect(rect_w, rect_h)
    )
    # Bottom cut to make half-circle
    bottom_cut = (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(6, 1.7 - 6, 0))
        .rect(12, 12)
    )
    # Notch in upper right
    notch_circle = (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(16, 6.7, 0))
        .circle(r_notch)
    )
    notch_cut = (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(16, 6.7 + 4, 0))
        .rect(8, 8)
    )

    # Extrude each and do CSG
    depth = TEST_CUTOUT_DEPTH + 0.01
    main_c = main_circle.extrude(depth)
    main_r = main_rect.extrude(depth)
    bot_c = bottom_cut.extrude(depth)
    notch_c = notch_circle.extrude(depth)
    notch_top = notch_cut.extrude(depth)

    union_shape = main_c.union(main_r)
    union_shape = union_shape.cut(bot_c)
    notch = notch_c.cut(notch_top)
    result = union_shape.cut(notch)

    return result.translate(cq.Vector(
        TEST_CUTOUT_H_OFFSET,
        TEST_CUTOUT_DEPTH,
        TEST_CUTOUT_V_OFFSET,
    ))


def _make_test_protrusion() -> cq.Workplane:
    """Create the small protrusion bar on the front face."""
    return (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(
            TEST_CUTOUT_H_OFFSET + PROTRUSION_LENGTH / 2,
            PROTRUSION_DEPTH / 2,
            TEST_CUTOUT_V_OFFSET + PROTRUSION_HEIGHT / 2,
        ))
        .box(PROTRUSION_LENGTH, PROTRUSION_DEPTH, PROTRUSION_HEIGHT,
             centered=True)
        .translate(cq.Vector(0, -PROTRUSION_DEPTH, 0))
    )


def _make_temp_label(text: str) -> cq.Workplane:
    """Create 3D text for a temperature label on the back face of a tier.

    The text is positioned on the back face (Y = TIER_WIDTH) of the tier,
    engraved into the surface.
    """
    return (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(
            TIER_LENGTH - TEMP_LABEL_H_OFFSET,
            TIER_HEIGHT - TEMP_LABEL_V_OFFSET,
            0,
        ))
        .text(
            text,
            fontsize=TEMP_LABEL_SIZE,
            distance=-TEMP_LABEL_DEPTH,
            halign="center",
            valign="center",
        )
        .translate(cq.Vector(0, TIER_WIDTH, 0))
    )


def _make_overhang_label_45() -> cq.Workplane:
    """Create the '45' degree label on the first tier."""
    return (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(8, TIER_HEIGHT - 4, 0))
        .text("45", fontsize=OH_LABEL_SIZE, distance=-OH_LABEL_DEPTH,
              halign="center", valign="center")
        .translate(cq.Vector(0, TIER_WIDTH, 0))
    )


def _make_overhang_label_35() -> cq.Workplane:
    """Create the '35' degree label on the first tier."""
    return (
        cq.Workplane("XZ")
        .transformed(offset=cq.Vector(TIER_LENGTH - 11, TIER_HEIGHT - 3, 0))
        .text("35", fontsize=OH_LABEL_SIZE, distance=-OH_LABEL_DEPTH,
              halign="center", valign="center")
        .translate(cq.Vector(0, TIER_WIDTH, 0))
    )


def _make_filament_type_label(text: str) -> cq.Workplane:
    """Create the filament type label on top of the base plate."""
    return (
        cq.Workplane("XY")
        .transformed(
            offset=cq.Vector(-BASE_LENGTH / 2 + 5, 0, BASE_HEIGHT),
            rotate=cq.Vector(0, 0, -90),
        )
        .text(text, fontsize=8, distance=TEXT_DEPTH,
              halign="center", valign="center")
    )


def _make_brand_top_label(text: str, config: TowerConfig) -> cq.Workplane:
    """Create the brand label on top of the tower."""
    z = BASE_HEIGHT + config.num_tiers * TIER_HEIGHT
    return (
        cq.Workplane("XY")
        .transformed(offset=cq.Vector(0, 0, z))
        .text(text, fontsize=5, distance=TEXT_DEPTH,
              halign="center", valign="center")
    )


def _make_brand_bottom_label(text: str) -> cq.Workplane:
    """Create the brand label on the bottom of the base plate."""
    return (
        cq.Workplane("XY")
        .transformed(
            offset=cq.Vector(0, 0, 0),
            rotate=cq.Vector(180, 0, 0),
        )
        .text(text, fontsize=6, distance=TEXT_DEPTH,
              halign="center", valign="center")
    )


# ---------------------------------------------------------------------------
# Tier assembly
# ---------------------------------------------------------------------------


def make_tier(config: TowerConfig, tier_index: int) -> cq.Workplane:
    """Build a single tier with all features.

    The tier is created at local origin (0, 0, 0), then translated to its
    final stacked position.
    """
    block = _make_tier_block()

    # Subtractive features
    block = block.cut(_make_45_overhang())
    block = block.cut(_make_35_overhang())
    block = block.cut(_make_central_cutout())
    block = block.cut(_make_vertical_hole(HOLE_45_OFFSET))
    block = block.cut(_make_vertical_hole(HOLE_35_OFFSET))
    block = block.cut(_make_horizontal_hole())

    # Temperature label (engraved)
    temp_text = str(tier_temperature(config, tier_index))
    block = block.cut(_make_temp_label(temp_text))

    # Overhang labels on first tier only
    if tier_index == 0:
        block = block.cut(_make_overhang_label_45())
        block = block.cut(_make_overhang_label_35())

    # Test cutout
    block = block.cut(_make_test_cutout_profile())

    # Additive features
    block = block.union(_make_test_protrusion())
    block = block.union(_make_cone(SM_CONE_OFFSET, SM_CONE_DIAM))
    block = block.union(_make_cone(LG_CONE_OFFSET, LG_CONE_DIAM))

    # Translate to stacked position (centred in X/Y like the base)
    z_offset = BASE_HEIGHT + tier_index * TIER_HEIGHT
    return block.translate(cq.Vector(
        -TIER_LENGTH / 2,
        -TIER_WIDTH / 2,
        z_offset,
    ))


# ---------------------------------------------------------------------------
# Full tower assembly
# ---------------------------------------------------------------------------


def make_base(config: TowerConfig) -> cq.Workplane:
    """Create the base plate with filament type label."""
    base = _make_filleted_base_plate()

    # Add filament type label on top
    if config.filament_type:
        base = base.union(_make_filament_type_label(config.filament_type))

    # Bottom brand label (engraved)
    if config.brand_bottom:
        base = base.cut(_make_brand_bottom_label(config.brand_bottom))

    return base


def make_tower(config: TowerConfig) -> cq.Workplane:
    """Assemble the complete temperature tower: base + all tiers + labels."""
    tower = make_base(config)

    for i in range(config.num_tiers):
        tier = make_tier(config, i)
        tower = tower.union(tier)

    # Top brand label
    if config.brand_top:
        tower = tower.union(_make_brand_top_label(config.brand_top, config))

    return tower


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def export_stl(shape: cq.Workplane, path: str) -> None:
    """Export a CadQuery shape to an STL file.

    Parameters
    ----------
    shape: CadQuery workplane/shape to export.
    path:  Output file path (should end in ``.stl``).
    """
    cq.exporters.export(shape, path, exportType="STL")


def generate_tower_stl(config: TowerConfig, output_path: str) -> str:
    """One-shot: build the tower and export to STL.

    Parameters
    ----------
    config:      Tower configuration.
    output_path: Where to write the ``.stl`` file.

    Returns
    -------
    str
        The *output_path* (for chaining convenience).
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    tower = make_tower(config)
    export_stl(tower, output_path)
    return output_path
