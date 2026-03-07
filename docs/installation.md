# Installation

## Prerequisites

- **Python 3.10 or 3.12** (see [note on Python versions](#python-version-compatibility)
  below)
- **PrusaSlicer** installed and available on your `PATH` (or provide
  `--prusaslicer-path`). Download from
  [prusa3d.com](https://www.prusa3d.com/page/prusaslicer_424/).
- A Prusa printer with **PrusaLink** enabled (only needed for uploading).

## Install

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

The `temperature-tower`, `extrusion-multiplier`, `volumetric-flow`,
`pressure-advance`, and `retraction-test` commands are available whenever the
venv is active. To reactivate later, run `source .venv/bin/activate` from the
project directory.

## Python version compatibility

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

## Conda alternative

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
