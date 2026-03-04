# filament-calibrator

Automated filament temperature tower calibration for Prusa 3D printers.

Generates a parametric temperature tower model, slices it with PrusaSlicer,
injects per-tier temperature changes into the G-code, and optionally uploads
the result to your printer via PrusaLink.

## Installation

```bash
pip install -e .
```

Requires [CadQuery](https://cadquery.readthedocs.io/) for model generation and
[gcode-lib](https://github.com/hyiger/gcode-lib) (>= 1.7.0) for G-code
manipulation.

## Quick Start

Generate and upload a PLA temperature tower with preset defaults:

```bash
temperature-tower \
  --printer-url http://192.168.1.100 \
  --api-key YOUR_API_KEY
```

Generate without uploading:

```bash
temperature-tower --no-upload --output-dir ./output --keep-files
```

## How It Works

1. **Model generation** -- CadQuery builds a parametric temp tower STL matching
   the classic OpenSCAD design: filleted base, stacked tiers with overhang
   tests (45/35 deg), bridge holes, cones, and engraved temperature labels.

2. **Slicing** -- PrusaSlicer CLI slices the STL using either a user-supplied
   `.ini` profile or built-in defaults (0.2mm layers, 2 perimeters, 15%
   infill, no supports).

3. **Temperature insertion** -- `M104` commands are inserted at the G-code
   layer boundaries corresponding to each tier, so the printer changes
   temperature as it moves up the tower.

4. **Upload** -- The final G-code is uploaded to the printer via PrusaLink
   REST API, with optional auto-start.

## Filament Presets

The tool uses presets from `gcode-lib` to set smart defaults for each filament
type. Known presets: **ABS**, **ASA**, **HIPS**, **PA**, **PA-CF**, **PC**,
**PCTG**, **PETG**, **PETG-CF**, **PLA**, **PLA-CF**, **PP**, **PPA**, **TPU**.

Each preset provides: recommended hotend temperature, bed temperature, fan
speed, retraction distance, safe temperature range (`temp_min`/`temp_max`),
print speed, and enclosure recommendation.

When you specify `--filament-type PLA` (the default), the tool uses the
preset's `temp_max` and `temp_min` as the default high and low temperatures.
The number of tiers is computed automatically from the range and step size.

All preset values can be overridden with explicit CLI flags.

## CLI Reference

### Model Options

| Flag | Default | Description |
|------|---------|-------------|
| `--filament-type` | `PLA` | Filament type (preset name or custom) |
| `--high-temp` | from preset `temp_max` | Highest temperature (bottom tier) |
| `--low-temp` | from preset `temp_min` | Lowest temperature (top tier) |
| `--temp-jump` | `5` | Temperature decrease per tier (deg C) |
| `--brand-top` | | Optional brand label on top |
| `--brand-bottom` | | Optional brand label on bottom |

Tier count is computed automatically: `(high_temp - low_temp) / temp_jump + 1`,
validated to a maximum of 10.

### Slicer Options

| Flag | Default | Description |
|------|---------|-------------|
| `--bed-temp` | from preset | Bed temperature (deg C) |
| `--fan-speed` | from preset | Fan speed (0-100%) |
| `--config-ini` | | PrusaSlicer `.ini` config file |
| `--prusaslicer-path` | auto-detect | Path to PrusaSlicer executable |
| `--extra-slicer-args` | | Additional PrusaSlicer CLI args (must be last) |

### Printer Options

| Flag | Default | Description |
|------|---------|-------------|
| `--printer-url` | | PrusaLink URL (e.g. `http://192.168.1.100`) |
| `--api-key` | | PrusaLink API key |
| `--no-upload` | `false` | Skip uploading to printer |
| `--print-after-upload` | `false` | Start printing after upload |

### Output Options

| Flag | Default | Description |
|------|---------|-------------|
| `--output-dir` | temp dir | Directory for output files |
| `--keep-files` | `false` | Keep intermediate STL and raw G-code |

### Configuration File

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | auto-detect | Path to a TOML config file |

Commonly reused settings can be saved in a TOML config file instead of passing
them on every invocation. The tool looks for config files in this order:

1. `--config <path>` (explicit)
2. `./filament-calibrator.toml` (project-local)
3. `~/.config/filament-calibrator/config.toml` (user config)

CLI arguments always override config file values. See
`filament-calibrator.example.toml` for the supported keys:

```toml
printer-url = "http://192.168.1.100"
api-key = "your-prusalink-api-key"
prusaslicer-path = "/usr/bin/prusa-slicer"
config-ini = "/path/to/printer-profile.ini"
filament-type = "PLA"
output-dir = "./output"
```

## Examples

PETG tower with 5-degree steps:

```bash
temperature-tower --filament-type PETG --temp-jump 5 --no-upload
```

Custom range for ABS:

```bash
temperature-tower \
  --filament-type ABS \
  --high-temp 270 \
  --low-temp 240 \
  --temp-jump 5 \
  --bed-temp 110 \
  --no-upload \
  --output-dir ./abs-tower
```

Use a PrusaSlicer profile:

```bash
temperature-tower \
  --config-ini ~/PrusaSlicer/my_profile.ini \
  --no-upload
```

## Development

Run tests:

```bash
pip install -e ".[dev]"
pytest tests/ --cov=src/filament_calibrator --cov-report=term-missing
```

## License

GPL-3.0-only
