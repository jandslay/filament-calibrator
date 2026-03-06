"""Parametric cube model for extrusion multiplier calibration.

Generates a simple solid cube.  When sliced in vase mode with classic
perimeter walls, the single wall thickness can be measured with calipers
to determine the correct extrusion multiplier.  All dimensions are in
millimetres.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cadquery as cq

# ---------------------------------------------------------------------------
# Geometry constants
# ---------------------------------------------------------------------------

CUBE_SIZE = 40.0  # mm — side length of the calibration cube


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------


@dataclass
class EMCubeConfig:
    """Parameters for the extrusion multiplier test cube.

    Attributes
    ----------
    size:           Side length of the cube in mm.
    filament_type:  Label for filament type (e.g. ``"PLA"``).
    """
    size: float = CUBE_SIZE
    filament_type: str = "PLA"


# ---------------------------------------------------------------------------
# Geometry builders
# ---------------------------------------------------------------------------


def _make_cube(config: EMCubeConfig) -> cq.Workplane:
    """Build a solid cube centred at the XY origin."""
    return (
        cq.Workplane("XY")
        .rect(config.size, config.size)
        .extrude(config.size)
    )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


def generate_em_cube_stl(
    config: EMCubeConfig,
    output_path: str,
) -> str:
    """One-shot: build the EM cube and export to STL.

    Parameters
    ----------
    config:      Cube configuration.
    output_path: Where to write the ``.stl`` file.

    Returns
    -------
    str
        The *output_path* (for chaining convenience).
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    shape = _make_cube(config)
    cq.exporters.export(shape, output_path, exportType="STL")
    return output_path
