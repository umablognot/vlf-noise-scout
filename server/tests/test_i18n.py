"""Locale bundle sanity: 17 languages, identical key sets, parseable .mo files.

The web UI fetches web/locales/<code>.json at runtime; the .po/.mo gettext
files under web/locales/<code>/LC_MESSAGES/ are the editable sources. These
tests keep every language complete and in sync.
"""

import gettext
import json
from pathlib import Path

LOCALES = Path(__file__).resolve().parents[2] / "web" / "locales"

LANGUAGES = [
    "tr", "en", "es", "zh", "ja", "vi", "de", "fr", "ru",
    "az", "kk", "mn", "ta", "ku", "zza", "yua", "fa",
]


def test_every_language_ships_po_mo_and_json() -> None:
    for code in LANGUAGES:
        lc = LOCALES / code / "LC_MESSAGES"
        assert (lc / "messages.po").is_file(), f"missing .po for {code}"
        assert (lc / "messages.mo").is_file(), f"missing .mo for {code}"
        assert (LOCALES / f"{code}.json").is_file(), f"missing .json for {code}"


def test_key_sets_match_english() -> None:
    en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    assert len(en) >= 90, "catalog unexpectedly small"
    for code in LANGUAGES:
        data = json.loads((LOCALES / f"{code}.json").read_text(encoding="utf-8"))
        assert set(data) == set(en), f"{code}: key set differs from en.json"
        assert all(str(v).strip() for v in data.values()), f"{code}: empty value"


def test_placeholders_and_markup_survive() -> None:
    for code in LANGUAGES:
        data = json.loads((LOCALES / f"{code}.json").read_text(encoding="utf-8"))
        assert "{d}" in data["scanAt"], f"{code}: scanAt lost the {{d}} placeholder"
        for key in ("wfNote", "lxNote", "txNote"):
            assert "<b>" in data[key], f"{code}: {key} lost its <b> markup"
        assert "https://www.blitzortung.org/" in data["lxNote"], (
            f"{code}: lxNote lost the Blitzortung link"
        )


def test_mo_files_parse_with_gettext() -> None:
    en = json.loads((LOCALES / "en.json").read_text(encoding="utf-8"))
    for code in LANGUAGES:
        js = json.loads((LOCALES / f"{code}.json").read_text(encoding="utf-8"))
        with (LOCALES / code / "LC_MESSAGES" / "messages.mo").open("rb") as fh:
            catalog = gettext.GNUTranslations(fh)
        assert catalog.gettext("tagline") == js["tagline"], f"{code}: MO out of sync"
        assert catalog.gettext("guide0_d") == js["guide0_d"], f"{code}: MO out of sync"
        assert en is not js  # dosyalar birbirine referans değil
