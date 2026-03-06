# Filament Calibrator — Session Context

## Project State (2026-03-03)

**All code is committed, merged to main, and pushed.** 103 tests passing, 100% statement coverage.

Working in git worktree: `/Users/rlewis/git/filament-calibrator/.claude/worktrees/amazing-solomon` (branch `claude/amazing-solomon`, merged to main).

## Repos

| Repo | Location | Role |
|------|----------|------|
| **filament-calibrator** | `/Users/rlewis/git/filament-calibrator` | Main CLI tool |
| **gcode-lib** | `/Users/rlewis/git/gcode-lib` | G-code parsing, PrusaSlicer integration, PrusaLink API, filament presets |

## Architecture

```
src/filament_calibrator/
  __init__.py       # __version__ = "0.1.0"
  __main__.py       # python -m filament_calibrator
  cli.py            # argparse CLI, pipeline orchestration
  model.py          # CadQuery parametric 3D model (temp tower geometry)
  slicer.py         # PrusaSlicer CLI wrapper with defaults
  tempinsert.py     # G-code temperature command insertion (M104)
tests/
  conftest.py       # shared fixtures (empty)
  test_cli.py       # 36 tests
  test_model.py     # 30 tests
  test_slicer.py    # 18 tests
  test_tempinsert.py # 19 tests
```

Entry point: `temperature-tower` → `filament_calibrator.cli:main`

## Pipeline Flow

`cli.run()` orchestrates:
1. `resolve_preset(args)` → resolve high_temp, low_temp, bed_temp, fan_speed from filament presets
2. `_compute_num_tiers(high, low, jump)` → validate and compute tier count
3. `generate_tower_stl(config, path)` → CadQuery model → STL
4. `slice_tower(stl, gcode, ...)` → PrusaSlicer CLI
5. `gl.load()` → parse G-code
6. `insert_temperatures(lines, tiers)` → inject M104 at tier boundaries
7. `gl.save()` → write final G-code
8. `gl.prusalink_upload()` → send to printer (optional)

## CLI Arguments

```
temperature-tower \
  --filament-type PLA          # Known presets auto-set defaults
  --high-temp 230              # From preset temp_max (optional)
  --low-temp 190               # From preset temp_min (optional)
  --temp-jump 5                # Default: 5°C per tier
  --brand-top "MyBrand"        # Label on tower top
  --brand-bottom "MyBrand"     # Label on base bottom
  --bed-temp 60                # From preset (optional)
  --fan-speed 100              # From preset (optional)
  --config-ini profile.ini     # PrusaSlicer config (optional)
  --prusaslicer-path /path     # Auto-detected if omitted
  --extra-slicer-args ...      # Must be last
  --printer-url http://...     # PrusaLink URL
  --api-key xxxxxxxx           # PrusaLink API key
  --no-upload                  # Skip uploading
  --print-after-upload         # Start printing after upload
  --output-dir ./output        # Default: temp dir
  --keep-files                 # Keep intermediate STL/raw gcode
```

`--num-tiers` is computed automatically: `(high_temp - low_temp) / temp_jump + 1`. Validated: high > low, range divisible by jump, max 10 tiers.

## Key Design Details

### _UNSET Sentinel Pattern
`_UNSET = object()` distinguishes "user didn't set" from None/0 in argparse. Used for --high-temp, --low-temp, --bed-temp, --fan-speed.

### Filament Presets (gcode-lib)
`gl.FILAMENT_PRESETS` dict with 14 presets. Keys: hotend, bed, fan, retract, temp_min, temp_max, speed, enclosure. Lookup is case-insensitive (`.upper()`). Unknown filaments fallback: high=230, low=190, bed=60, fan=100.

Key preset values:
- PLA: temp_min=190, temp_max=230, hotend=215, bed=60, fan=100
- PETG: temp_min=220, temp_max=260, hotend=240, bed=80, fan=40
- ABS: temp_min=230, temp_max=270, hotend=255, bed=100, fan=20

### CadQuery Workplane Gotchas
- `Workplane("XZ")` has normal **-Y** (right-hand rule). `.extrude(d)` goes Y=0 → Y=-d. Must `.translate(Vector(0, TIER_WIDTH, 0))` to position inside tier.
- Back-face text must be `.mirror("YZ", basePointVector=(x_center, 0, 0))` to read correctly when viewed from +Y.

### Slicer Integration
- `slice_tower()` passes `--temperature` and `--first-layer-temperature` to PrusaSlicer so start G-code uses the correct initial temp (high_temp). Without this, PrusaSlicer defaults override M104 insertion.
- `DEFAULT_SLICER_ARGS` used when no --config-ini: 0.2mm layers, 2 perimeters, 15% infill, no support.

### Temperature Insertion
- `compute_temp_tiers()` creates Z-range → temp mappings
- `insert_temperatures()` walks layers via `gl.iter_layers()`, inserts `M104 S{temp}` at tier boundaries
- Base plate layers get first tier temp; above last tier keeps previous temp

## Model Geometry (per tier, from OpenSCAD reference)
- Base: 89.3 × 20 × 1mm, filleted corners (4mm)
- Tier block: 79 × 10 × 10mm
- Left 45° overhang, right 35° overhang (triangular prisms)
- Central cutout: 30 × 9mm with horizontal bridge hole (Ø3mm)
- Two vertical holes (Ø3mm) at specific offsets
- Two cones: Ø3mm and Ø5mm base, 5mm tall
- Test cutout (D-shaped profile) + protrusion bar
- Temperature label on back face, overhang labels ("45", "35") on tier 0

## TowerConfig Dataclass
```python
@dataclass
class TowerConfig:
    high_temp: int = 220
    temp_jump: int = 10
    num_tiers: int = 9
    filament_type: str = "PLA"
    brand_top: str = ""
    brand_bottom: str = ""
```

## Testing Conventions
- 100% statement coverage enforced: `pytest --cov-fail-under=100`
- CadQuery mocked in model tests (geometry ops verified via call assertions)
- PrusaSlicer and PrusaLink mocked in slicer/CLI tests
- G-code insertion tests use synthetic inline G-code strings
- `unittest.mock.patch` for all external dependencies
- Python 3.10+, `from __future__ import annotations` everywhere

## gcode-lib Changes (commit ae48a8d)
Added to `/Users/rlewis/git/gcode-lib/gcode_lib.py`:
- `FILAMENT_PRESETS` dict (14 filament types)
- PrusaLink API client: `PrusaLinkError`, `PrusaLinkInfo`, `PrusaLinkStatus`, `PrusaLinkJob`
- Functions: `_prusalink_request()`, `prusalink_get_version()`, `prusalink_get_status()`, `prusalink_get_job()`, `prusalink_upload()`
- Tests: `/Users/rlewis/git/gcode-lib/tests/test_gcode_lib_prusalink.py`

## Commit History (main, newest first)
```
641df34 Merge branch 'claude/amazing-solomon'
9d08633 feat: replace --num-tiers with --low-temp, compute tiers automatically
886ee79 Merge branch 'claude/amazing-solomon'
dc25c4d chore: remove unused import and add missing constant tests
183d805 Merge branch 'claude/amazing-solomon'
08638bb fix: pass nozzle temperature to PrusaSlicer start G-code
46bccf9 Merge branch 'claude/amazing-solomon'
ff9c446 fix: mirror back-face text labels so they read correctly
891faa8 Merge branch 'claude/amazing-solomon'
b8cb89b fix: correct XZ workplane -Y normal direction for all tier features
653e6ba Merge branch 'claude/amazing-solomon'
3315cb4 fix: rewrite test cutout profile and fix Y-axis translation
ccaf5e7 Merge branch 'claude/amazing-solomon'
e2c0ddb fix: use --key=value format for PrusaSlicer args and remove support-material
```

## Issues Resolved
1. **PrusaSlicer --support-material 0**: Not a valid value — removed from defaults (PrusaSlicer default is already no support)
2. **XZ workplane -Y normal**: All tier features built on XZ plane needed +Y translation to position correctly
3. **Test cutout profile**: Rewritten with correct D-shaped geometry matching OpenSCAD
4. **Mirrored text**: Back-face text needed `.mirror("YZ")` to read correctly from +Y
5. **Bottom tier wrong temp**: PrusaSlicer start G-code overrode M104 — fixed by passing `--temperature` and `--first-layer-temperature`
6. **--num-tiers replaced**: Now uses --high-temp/--low-temp/--temp-jump with auto-computed tiers
