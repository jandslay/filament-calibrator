"""
Launcher for the FilamentCalibrator GUI.

PyInstaller entry point — starts Streamlit with gui.py
and sets up i18n before the app loads.
"""
import os
import sys
from pathlib import Path


def _fix_paths() -> None:
    """Add the bundled package directory to sys.path when running as .exe."""
    if getattr(sys, "frozen", False):
        # Running inside PyInstaller bundle
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        sys.path.insert(0, str(base))


def main() -> None:
    _fix_paths()

    # Setup i18n (auto-detects system language, falls back to English)
    try:
        from filament_calibrator.i18n import setup
        setup()
    except Exception:
        pass  # Non-fatal: GUI works in English without translation

    # Launch Streamlit
    try:
        from streamlit.web.cli import main as st_main
    except ImportError:
        sys.exit(
            "Error: Streamlit is not installed.\n"
            "Run: pip install 'filament-calibrator[gui]'"
        )

    gui_script = Path(__file__).parent / "filament_calibrator" / "gui.py"
    if not gui_script.exists():
        # Fallback for development (running from repo root)
        gui_script = (
            Path(__file__).parent / "src" / "filament_calibrator" / "gui.py"
        )

    sys.argv = [
        "streamlit", "run", str(gui_script),
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false",
    ]
    st_main()


if __name__ == "__main__":
    main()
