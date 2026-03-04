# filament-calibrator

Automated filament temperature tower calibration for Prusa 3D printers.

Generates a parametric temperature tower model, slices it with PrusaSlicer,
injects per-tier temperature changes into the G-code, and optionally uploads
the result to your printer via PrusaLink.

## Prerequisites

- **Python 3.10 or 3.12** (see [note on Python versions](#python-version-compatibility)
  below)
- **PrusaSlicer** installed and available on your `PATH` (or provide
  `--prusaslicer-path`). Download from
  [prusa3d.com](https://www.prusa3d.com/page/prusaslicer_424/).
- A Prusa printer with **PrusaLink** enabled (only needed for uploading).

## Installation

Create a virtual environment and install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This pulls all Python dependencies from PyPI automatically:
[CadQuery](https://cadquery.readthedocs.io/) for model generation and
[gcode-lib](https://github.com/hyiger/gcode-lib) (>= 1.0.0) for G-code
manipulation.

The `temperature-tower` command is available whenever the venv is active.
To reactivate later, run `source .venv/bin/activate` from the project
directory.

### Python version compatibility

CadQuery depends on [cadquery-ocp](https://pypi.org/project/cadquery-ocp/),
which ships pre-built binary wheels for specific Python versions. Wheels are
available for **Python 3.10 and 3.12** on all major platforms (Linux x86-64,
macOS x86-64 / ARM64, Windows x86-64). Other Python versions (3.11, 3.13,
3.14) have limited or no wheel coverage.

If `pip install` fails with a dependency resolution error mentioning
`cadquery-ocp`, create a venv with a supported Python version:

```bash
# macOS with Homebrew
brew install python@3.12
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Conda alternative

If pip installation doesn't work for your platform, CadQuery can be installed
via conda-forge:

```bash
conda create -n filament-cal python=3.12
conda activate filament-cal
mamba install -c conda-forge cadquery
pip install -e .
```

> **Note:** Install conda packages first, then pip packages. See the
> [Anaconda docs](https://www.anaconda.com/blog/using-pip-in-a-conda-environment)
> for details on mixing conda and pip.

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

## Configuration

Save commonly reused settings in a TOML file so you don't have to pass them
on every run. To get started, copy the example file:

```bash
cp filament-calibrator.example.toml filament-calibrator.toml
```

Then edit it with your printer and slicer details:

```toml
# Printer connection (required for uploading)
printer-url = "http://192.168.1.100"
api-key = "your-prusalink-api-key"

# Slicer setup (prusaslicer-path is only needed if PrusaSlicer is not
# installed in a standard location — the tool auto-detects it on PATH)
# prusaslicer-path = "/usr/bin/prusa-slicer"
# config-ini = "/path/to/printer-profile.ini"

# Bed centre in mm — default is 125,105 (Prusa MK-series).
# For Prusa MINI, use 90,90.
# bed-center = "125,105"

# Defaults
filament-type = "PLA"
output-dir = "./output"
```

All keys are optional — include only what you need. In particular,
`prusaslicer-path` can be omitted if PrusaSlicer is installed in a standard
location (e.g. `/usr/bin/prusa-slicer`, `/Applications/PrusaSlicer.app`, or
anywhere on your `PATH`).

### Config file locations

The tool looks for a config file in this order (first found wins):

| Priority | Location | Use case |
|----------|----------|----------|
| 1 | `--config <path>` | Explicit override |
| 2 | `./filament-calibrator.toml` | Per-project settings |
| 3 | `~/.config/filament-calibrator/config.toml` | User-wide defaults |

CLI arguments always override config file values, so you can set your usual
defaults in the file and override individual flags as needed.

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
| `--start-temp` | from preset `temp_max` | Highest temperature (bottom tier) |
| `--end-temp` | from preset `temp_min` | Lowest temperature (top tier) |
| `--temp-step` | `5` | Temperature decrease per tier (deg C) |
| `--brand-top` | | Optional brand label on top |
| `--brand-bottom` | | Optional brand label on bottom |

Tier count is computed automatically: `(start_temp - end_temp) / temp_step + 1`,
validated to a maximum of 10. Temperatures must be within 150–350°C,
`--start-temp` must be at least `--end-temp + --temp-step`, and the range
must be evenly divisible by `--temp-step`.

### Slicer Options

| Flag | Default | Description |
|------|---------|-------------|
| `--bed-temp` | from preset | Bed temperature (deg C) |
| `--fan-speed` | from preset | Fan speed (0-100%) |
| `--config-ini` | | PrusaSlicer `.ini` config file |
| `--prusaslicer-path` | auto-detect | Path to PrusaSlicer executable |
| `--bed-center` | `125,105` | Bed centre as X,Y in mm |
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

### General Options

| Flag | Default | Description |
|------|---------|-------------|
| `--config` | auto-detect | Path to a TOML config file |
| `-v`, `--verbose` | `false` | Show detailed debug output |

See the [Configuration](#configuration) section above for config file setup
and supported keys.

## Examples

PETG tower with 5-degree steps:

```bash
temperature-tower --filament-type PETG --temp-step 5 --no-upload
```

Custom range for ABS:

```bash
temperature-tower \
  --filament-type ABS \
  --start-temp 270 \
  --end-temp 240 \
  --temp-step 5 \
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
