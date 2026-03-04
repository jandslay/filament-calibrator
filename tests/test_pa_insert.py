"""Tests for filament_calibrator.pa_insert — pressure advance G-code insertion."""
from __future__ import annotations

import pytest

import gcode_lib as gl

from filament_calibrator.pa_insert import (
    PALevel,
    compute_pa_levels,
    insert_pa_commands,
    pa_command,
    _level_for_z,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _lines(text: str):
    return gl.parse_lines(text)


def _raw_texts(lines):
    return [line.raw for line in lines]


# ---------------------------------------------------------------------------
# PALevel
# ---------------------------------------------------------------------------


class TestPALevel:
    def test_attributes(self):
        lv = PALevel(pa_value=0.05, z_start=1.0, z_end=2.0)
        assert lv.pa_value == 0.05
        assert lv.z_start == 1.0
        assert lv.z_end == 2.0


# ---------------------------------------------------------------------------
# pa_command
# ---------------------------------------------------------------------------


class TestPACommand:
    def test_marlin_format(self):
        result = pa_command(0.05, "marlin")
        assert result == "M900 K0.0500 ; PA calibration level"

    def test_klipper_format(self):
        result = pa_command(0.05, "klipper")
        assert result == "SET_PRESSURE_ADVANCE ADVANCE=0.0500 ; PA calibration level"

    def test_four_decimal_places(self):
        result = pa_command(0.1, "marlin")
        assert "K0.1000" in result

    def test_zero_value(self):
        result = pa_command(0.0, "marlin")
        assert "K0.0000" in result


# ---------------------------------------------------------------------------
# compute_pa_levels
# ---------------------------------------------------------------------------


class TestComputePALevels:
    def test_basic_levels(self):
        levels = compute_pa_levels(0.0, 0.05, 3, 1.0)
        assert len(levels) == 3
        assert levels[0].pa_value == pytest.approx(0.0)
        assert levels[0].z_start == pytest.approx(0.0)
        assert levels[0].z_end == pytest.approx(1.0)
        assert levels[1].pa_value == pytest.approx(0.05)
        assert levels[2].pa_value == pytest.approx(0.1)
        assert levels[2].z_start == pytest.approx(2.0)
        assert levels[2].z_end == pytest.approx(3.0)

    def test_single_level(self):
        levels = compute_pa_levels(0.04, 0.01, 1, 2.0)
        assert len(levels) == 1
        assert levels[0].pa_value == pytest.approx(0.04)
        assert levels[0].z_start == pytest.approx(0.0)
        assert levels[0].z_end == pytest.approx(2.0)

    def test_zero_levels(self):
        levels = compute_pa_levels(0.0, 0.05, 0, 1.0)
        assert levels == []

    def test_custom_level_height(self):
        levels = compute_pa_levels(0.0, 0.01, 3, 2.0)
        assert levels[0].z_end == pytest.approx(2.0)
        assert levels[1].z_start == pytest.approx(2.0)
        assert levels[2].z_start == pytest.approx(4.0)

    def test_rounding_prevents_drift(self):
        """PA values are rounded to 4 decimals to prevent float drift."""
        levels = compute_pa_levels(0.0, 0.1, 10, 1.0)
        # Without rounding, 0.1 * 3 = 0.30000000000000004
        assert levels[3].pa_value == pytest.approx(0.3)
        assert levels[9].pa_value == pytest.approx(0.9)


# ---------------------------------------------------------------------------
# _level_for_z
# ---------------------------------------------------------------------------


class TestLevelForZ:
    def test_in_first_level(self):
        levels = compute_pa_levels(0.0, 0.05, 3, 1.0)
        assert _level_for_z(0.5, levels).pa_value == pytest.approx(0.0)

    def test_in_second_level(self):
        levels = compute_pa_levels(0.0, 0.05, 3, 1.0)
        assert _level_for_z(1.5, levels).pa_value == pytest.approx(0.05)

    def test_at_boundary(self):
        levels = compute_pa_levels(0.0, 0.05, 3, 1.0)
        # z_start is inclusive
        assert _level_for_z(1.0, levels).pa_value == pytest.approx(0.05)

    def test_below_range(self):
        # Levels start at z=0, so nothing is below
        levels = compute_pa_levels(0.0, 0.05, 3, 1.0)
        assert _level_for_z(-0.5, levels) is None

    def test_above_range(self):
        levels = compute_pa_levels(0.0, 0.05, 3, 1.0)
        assert _level_for_z(3.5, levels) is None

    def test_empty_levels(self):
        assert _level_for_z(0.5, []) is None


# ---------------------------------------------------------------------------
# insert_pa_commands
# ---------------------------------------------------------------------------


class TestInsertPACommands:
    def test_basic_marlin_insertion(self):
        """M900 commands are inserted at level boundaries."""
        gcode = (
            "G28\n"
            "G1 Z0.2 F1000\n"
            "G1 X10 E1\n"
            "G1 Z1.2 F1000\n"
            "G1 X20 E2\n"
        )
        lines = _lines(gcode)
        levels = compute_pa_levels(0.0, 0.05, 2, 1.0)
        result = insert_pa_commands(lines, levels, firmware="marlin")
        texts = _raw_texts(result)

        m900_lines = [t for t in texts if t.startswith("M900")]
        assert len(m900_lines) == 2
        assert "K0.0000" in m900_lines[0]
        assert "K0.0500" in m900_lines[1]

    def test_klipper_insertion(self):
        """SET_PRESSURE_ADVANCE commands are inserted for klipper firmware."""
        gcode = (
            "G1 Z0.2 F1000\n"
            "G1 X10 E1\n"
            "G1 Z1.2 F1000\n"
            "G1 X20 E2\n"
        )
        lines = _lines(gcode)
        levels = compute_pa_levels(0.0, 0.05, 2, 1.0)
        result = insert_pa_commands(lines, levels, firmware="klipper")
        texts = _raw_texts(result)

        pa_lines = [t for t in texts if t.startswith("SET_PRESSURE_ADVANCE")]
        assert len(pa_lines) == 2
        assert "ADVANCE=0.0000" in pa_lines[0]
        assert "ADVANCE=0.0500" in pa_lines[1]

    def test_no_duplicate_commands(self):
        """Same-level layers don't get duplicate PA commands."""
        gcode = (
            "G1 Z0.2 F1000\n"
            "G1 X10 E1\n"
            "G1 Z0.4 F1000\n"
            "G1 X20 E2\n"
            "G1 Z0.6 F1000\n"
            "G1 X30 E3\n"
        )
        lines = _lines(gcode)
        levels = compute_pa_levels(0.0, 0.05, 1, 1.0)
        result = insert_pa_commands(lines, levels, firmware="marlin")
        texts = _raw_texts(result)

        m900_lines = [t for t in texts if t.startswith("M900")]
        assert len(m900_lines) == 1

    def test_empty_levels_no_modification(self):
        gcode = "G28\nG1 X10 E1\n"
        lines = _lines(gcode)
        result = insert_pa_commands(lines, [])
        assert len(result) == len(lines)

    def test_empty_lines(self):
        result = insert_pa_commands([], compute_pa_levels(0.0, 0.05, 3, 1.0))
        assert result == []

    def test_above_last_level_keeps_pa(self):
        """Layers above the last level don't generate new PA commands."""
        gcode = (
            "G1 Z0.2 F1000\n"
            "G1 X10 E1\n"
            "G1 Z100.0 F1000\n"
            "G1 X30 E3\n"
        )
        lines = _lines(gcode)
        levels = compute_pa_levels(0.0, 0.05, 1, 1.0)  # single level: z=0-1
        result = insert_pa_commands(lines, levels, firmware="marlin")
        texts = _raw_texts(result)

        m900_lines = [t for t in texts if t.startswith("M900")]
        assert len(m900_lines) == 1
        assert "K0.0000" in m900_lines[0]

    def test_command_order_in_output(self):
        """PA command appears before the first line of the new-level layer."""
        gcode = (
            "G1 Z0.2 F1000\n"
            "G1 X10 E1\n"
            "G1 Z1.2 F1000\n"
            "G1 X20 E2\n"
        )
        lines = _lines(gcode)
        levels = compute_pa_levels(0.0, 0.05, 2, 1.0)
        result = insert_pa_commands(lines, levels, firmware="marlin")
        texts = _raw_texts(result)

        idx_m900_0 = next((i for i, t in enumerate(texts) if "K0.0000" in t), -1)
        idx_z0_2 = next((i for i, t in enumerate(texts) if "Z0.2" in t), -1)
        assert idx_m900_0 != -1
        assert idx_z0_2 != -1
        assert idx_m900_0 < idx_z0_2

        idx_m900_1 = next((i for i, t in enumerate(texts) if "K0.0500" in t), -1)
        idx_z1_2 = next((i for i, t in enumerate(texts) if "Z1.2" in t), -1)
        assert idx_m900_1 != -1
        assert idx_z1_2 != -1
        assert idx_m900_1 < idx_z1_2

    def test_immutable_input(self):
        """Original list is not mutated."""
        gcode = (
            "G1 Z0.2 F1000\n"
            "G1 X10 E1\n"
        )
        lines = _lines(gcode)
        original_len = len(lines)
        levels = compute_pa_levels(0.0, 0.05, 1, 1.0)
        insert_pa_commands(lines, levels, firmware="marlin")
        assert len(lines) == original_len
