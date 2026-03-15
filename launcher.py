"""
Launcher for the FilamentCalibrator GUI.

PyInstaller entry point — starts Streamlit with gui.py
and sets up i18n before the app loads.
"""
import sys
import threading
import webbrowser
import time
from pathlib import Path


def _fix_paths() -> None:
    """Add the bundled package directory to sys.path when running as .exe."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        sys.path.insert(0, str(base))


def _find_gui_script() -> Path:
    """Locate gui.py whether running as .exe bundle or from source."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        candidate = base / "filament_calibrator" / "gui.py"
        if candidate.exists():
            return candidate
        matches = list(base.rglob("gui.py"))
        if matches:
            return matches[0]
        raise FileNotFoundError(f"gui.py not found in bundle at {base}")
    else:
        here = Path(__file__).parent
        for p in [
            here / "src" / "filament_calibrator" / "gui.py",
            here / "filament_calibrator" / "gui.py",
        ]:
            if p.exists():
                return p
        raise FileNotFoundError("gui.py not found in source tree")


def main() -> None:
    _fix_paths()

    try:
        from filament_calibrator.i18n import setup
        setup()
    except Exception as exc:
        print(f"[i18n] Warning: {exc}")

    try:
        gui_script = _find_gui_script()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        input("Press Enter to exit...")
        sys.exit(1)

    print(f"[launcher] gui.py: {gui_script}")

    try:
        from streamlit.web import cli as stcli
    except ImportError as exc:
        print(f"ERROR: Cannot import Streamlit: {exc}")
        input("Press Enter to exit...")
        sys.exit(1)

    sys.argv = [
        "streamlit", "run", str(gui_script),
        "--global.developmentMode", "false",
        "--server.headless", "true",
        "--server.port", "8501",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]

    # Open browser automatically after short delay (Streamlit needs ~2s to start)
    def _open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:8501")

    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        stcli.main()
    except SystemExit:
        pass
    except Exception as exc:
        import traceback
        print(f"ERROR: Streamlit failed: {exc}")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
