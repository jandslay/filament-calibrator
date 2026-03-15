"""
Internationalization (i18n) setup for filament-calibrator.

Usage:
    from filament_calibrator.i18n import setup
    setup("de")   # explicit language
    setup()       # use system language

After setup(), the built-in _() function is available everywhere.
"""

from __future__ import annotations

import builtins
import gettext
import locale
import logging
from pathlib import Path

LOCALE_DIR = Path(__file__).parent / "locale"
DOMAIN = "filament_calibrator"

log = logging.getLogger(__name__)


def setup(language: str | None = None) -> None:
    """Install the _() translation function into builtins.

    Args:
        language: BCP-47 language tag, e.g. "de", "de_DE", "en".
                  None → auto-detect from OS locale.
    """
    lang = _resolve_language(language)

    try:
        translation = gettext.translation(
            DOMAIN,
            localedir=LOCALE_DIR,
            languages=[lang] if lang else None,
        )
        translation.install()
        log.debug("i18n: loaded language '%s' from %s", lang, LOCALE_DIR)
    except FileNotFoundError:
        # No .mo file found — fall back to English (identity translation)
        gettext.install(DOMAIN)
        log.debug("i18n: no translation for '%s', falling back to English", lang)


def _resolve_language(language: str | None) -> str | None:
    """Return language string to use, normalising locale codes."""
    if language:
        return language.replace("-", "_")  # "de-DE" → "de_DE"
    try:
        sys_locale, _ = locale.getdefaultlocale()
        return sys_locale  # e.g. "de_DE" or None
    except ValueError:
        return None


def get_available_languages() -> list[str]:
    """Return list of languages that have a compiled .mo file."""
    if not LOCALE_DIR.exists():
        return ["en"]
    langs = [
        p.parent.parent.name
        for p in LOCALE_DIR.glob("*/LC_MESSAGES/*.mo")
    ]
    return sorted(langs) or ["en"]
