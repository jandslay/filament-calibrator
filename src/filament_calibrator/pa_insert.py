"""Pressure advance G-code insertion for PA calibration prints.

Uses ``gcode_lib.iter_layers()`` to identify Z-level boundaries and inserts
firmware-specific pressure advance commands at the start of each PA level.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import gcode_lib as gl


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class PALevel:
    """One pressure advance level's Z range and target PA value.

    Attributes
    ----------
    pa_value: Pressure advance value for this level.
    z_start:  Bottom of level (inclusive), in mm.
    z_end:    Top of level (exclusive), in mm.
    """
    pa_value: float
    z_start: float
    z_end: float


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def pa_command(pa_value: float, firmware: str) -> str:
    """Return the G-code command to set pressure advance.

    Parameters
    ----------
    pa_value: The pressure advance value.
    firmware: ``"marlin"`` or ``"klipper"``.

    Returns
    -------
    str
        The G-code command string.
    """
    if firmware == "klipper":
        return f"SET_PRESSURE_ADVANCE ADVANCE={pa_value:.4f} ; PA calibration level"
    # Default: Marlin (also used by Prusa firmware)
    return f"M900 K{pa_value:.4f} ; PA calibration level"


def compute_pa_levels(
    start_pa: float,
    pa_step: float,
    num_levels: int,
    level_height: float,
) -> List[PALevel]:
    """Calculate the Z ranges and PA values for each level.

    Level 0 (bottom) gets *start_pa*.  Each subsequent level increases
    by *pa_step*.

    Parameters
    ----------
    start_pa:     Lowest PA value (bottom level).
    pa_step:      PA value increase per level.
    num_levels:   Number of levels.
    level_height: Height of each level in mm.

    Returns
    -------
    List[PALevel]
        One entry per level, ordered bottom to top.
    """
    levels: List[PALevel] = []
    for i in range(num_levels):
        z_start = i * level_height
        z_end = z_start + level_height
        pa_value = round(start_pa + i * pa_step, 4)
        levels.append(PALevel(
            pa_value=pa_value,
            z_start=z_start,
            z_end=z_end,
        ))
    return levels


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _level_for_z(z: float, levels: List[PALevel]) -> PALevel | None:
    """Return the level that contains height *z*, or ``None``."""
    for level in levels:
        if level.z_start <= z < level.z_end:
            return level
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def insert_pa_commands(
    lines: List[gl.GCodeLine],
    levels: List[PALevel],
    firmware: str = "marlin",
) -> List[gl.GCodeLine]:
    """Insert pressure advance commands at level boundaries.

    Walks the G-code layer by layer using :func:`gcode_lib.iter_layers`.
    When a layer's Z height crosses into a new PA level, a PA command
    is inserted before that layer's first line.

    Returns a new list of :class:`gcode_lib.GCodeLine` (following the
    immutable-input convention from gcode-lib).

    Parameters
    ----------
    lines:    Parsed G-code lines.
    levels:   PA levels from :func:`compute_pa_levels`.
    firmware: ``"marlin"`` or ``"klipper"``.
    """
    if not levels:
        return list(lines)

    result: List[gl.GCodeLine] = []
    prev_pa: float | None = None

    for z_height, layer_lines in gl.iter_layers(lines):
        level = _level_for_z(z_height, levels)
        if level is not None:
            target_pa = level.pa_value
        else:
            # Above the last level — keep previous PA
            target_pa = prev_pa

        if target_pa is not None and target_pa != prev_pa:
            cmd = pa_command(target_pa, firmware)
            result.append(gl.parse_line(cmd))
            prev_pa = target_pa

        result.extend(layer_lines)

    return result
