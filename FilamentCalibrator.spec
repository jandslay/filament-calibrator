# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for FilamentCalibrator
# Bundles: Streamlit GUI + locale files (i18n) + all data files
#
# Build with:
#   pyinstaller FilamentCalibrator.spec

import sys
from pathlib import Path
import streamlit
import altair

# --- Paths ---
streamlit_dir = Path(streamlit.__file__).parent
altair_dir    = Path(altair.__file__).parent

block_cipher = None

a = Analysis(
    # Entry point: launches Streamlit with our gui.py
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Streamlit static web assets (HTML, JS, CSS)
        (str(streamlit_dir / "static"),       "streamlit/static"),
        (str(streamlit_dir / "runtime"),      "streamlit/runtime"),
        # Altair Vega schemas
        (str(altair_dir / "vega"),            "altair/vega"),
        # Our locale files (German translation)
        ("src/filament_calibrator/locale",    "filament_calibrator/locale"),
    ],
    hiddenimports=[
        "streamlit",
        "streamlit.web.cli",
        "streamlit.runtime.scriptrunner",
        "filament_calibrator.gui",
        "filament_calibrator.i18n",
        "filament_calibrator.cli",
        "filament_calibrator.config",
        "filament_calibrator.ini_writer",
        "filament_calibrator.model",
        "filament_calibrator.slicer",
        "filament_calibrator.tempinsert",
        "cadquery",
        "gcode_lib",
        "altair",
        "pydeck",
        "pyarrow",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FilamentCalibrator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add .ico path here if you have one
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FilamentCalibrator',
)
