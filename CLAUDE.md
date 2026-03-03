# CLAUDE.md

## Project Overview

**filament-calibrator** is a CLI tool suite for 3D printer filament calibration.
The first tool is `temperature-tower`, which generates, slices, and uploads
temperature tower prints. The repo will eventually contain additional
calibration scripts.

## Architecture

```
src/filament_calibrator/
  __init__.py       # Package init, __version__
  __main__.py       # python -m filament_calibrator support
  cli.py            # argparse CLI, pipeline orchestration
  model.py          # CadQuery parametric 3D model generation
  slicer.py         # PrusaSlicer CLI wrapper with defaults
  tempinsert.py     # G-code temperature command insertion
```

### Key Dependencies

- **cadquery** (>= 2.4): Parametric CAD model generation (OCCT kernel)
- **gcode-lib** (>= 1.7.0): G-code parsing, PrusaSlicer integration,
  PrusaLink API, filament presets. Located at `/Users/rlewis/git/gcode-lib`.

### Pipeline Flow

`cli.run()` orchestrates: resolve_preset -> generate_tower_stl -> slice_tower
-> load G-code -> insert_temperatures -> save -> optional PrusaLink upload.

## Code Conventions

- Python 3.10+, `from __future__ import annotations` in every module
- Type hints on all function signatures
- Immutable transforms (return new data, don't mutate inputs) following
  gcode-lib patterns
- `_UNSET = object()` sentinel for distinguishing "user didn't set" from None
  in argparse
- Filament preset lookup is case-insensitive (`.upper()`)

## Testing

```bash
pytest tests/ --cov=src/filament_calibrator --cov-report=term-missing --cov-fail-under=100
```

- 100% statement coverage is required and enforced
- CadQuery is mocked in model tests (geometry ops verified via call assertions)
- PrusaSlicer and PrusaLink are mocked in slicer/CLI tests
- G-code insertion tests use synthetic inline G-code strings
- Tests use `unittest.mock.patch` for external dependencies

## Build & Install

```bash
pip install -e .                    # editable install
pip install -e /path/to/gcode-lib   # if gcode-lib not on PyPI
```

Entry point: `temperature-tower` -> `filament_calibrator.cli:main`

## Common Tasks

- **Add a new filament preset**: Add to `FILAMENT_PRESETS` in
  `gcode-lib/gcode_lib.py`. Required keys: hotend, bed, fan, retract,
  temp_min, temp_max, speed, enclosure.
- **Change tower geometry**: Edit constants in `model.py` (BASE_*, TIER_*).
- **Change slicer defaults**: Edit `DEFAULT_SLICER_ARGS` in `slicer.py`.
- **Add a new calibration tool**: Create a new module + CLI entry point in
  `pyproject.toml [project.scripts]`.
