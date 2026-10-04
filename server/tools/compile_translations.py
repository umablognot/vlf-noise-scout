#!/usr/bin/env python3
"""gettext toolchain for the VLF Noise Scout web UI.

Reads flat per-language JSON catalogs (scripts/translations/<code>.json),
emits standard gettext sources and web-ready bundles:

    <out>/<code>/LC_MESSAGES/messages.po    human-editable gettext source
    <out>/<code>/LC_MESSAGES/messages.mo    compiled GNU MO catalog
    <out>/<code>.json                       flat key->string map for the web UI

The web frontend fetches <code>.json at runtime; the .po/.mo files are the
canonical localization source for translators and any Python-side tooling.
A messages.pot template is emitted next to the catalogs.

Usage:
    python3 compile_translations.py <src_json_dir> <out_dir>
    python3 compile_translations.py <out_dir> --check      # CI validation
    python3 compile_translations.py <out_dir> --sync-po    # .po edits -> .mo + .json
"""

from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

# Language metadata: code -> (native name for the UI dropdown, plural-forms)
LANGUAGES: dict[str, tuple[str, str]] = {
    "tr": ("Türkçe", "nplurals=2; plural=(n != 1);"),
    "en": ("English", "nplurals=2; plural=(n != 1);"),
    "es": ("Español", "nplurals=2; plural=(n != 1);"),
    "zh": ("中文", "nplurals=1; plural=0;"),
    "ja": ("日本語", "nplurals=1; plural=0;"),
    "vi": ("Tiếng Việt", "nplurals=1; plural=0;"),
    "de": ("Deutsch", "nplurals=2; plural=(n != 1);"),
    "fr": ("Français", "nplurals=2; plural=(n != 1);"),
    "ru": ("Русский", "nplurals=4; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2);"),
    "az": ("Azərbaycanca", "nplurals=2; plural=(n != 1);"),
    "kk": ("Қазақша", "nplurals=2; plural=(n != 1);"),
    "mn": ("Монгол", "nplurals=2; plural=(n != 1);"),
    "ta": ("தமிழ்", "nplurals=2; plural=(n != 1);"),
    "ku": ("Kurmancî", "nplurals=2; plural=(n != 1);"),
    "zza": ("Zazakî", "nplurals=2; plural=(n != 1);"),
    "yua": ("Maya t'aan", "nplurals=2; plural=(n != 1);"),
    "fa": ("فارسی", "nplurals=2; plural=(n > 1);"),
}

PROJECT = "VLF Noise Scout"
VERSION = "1.0.0"
BUGS = "https://github.com/altunsumerve/vlf-noise-scout/issues"

PO_HEADER = """\
msgid ""
msgstr ""
"Project-Id-Version: {project} {version}\\n"
"Report-Msgid-Bugs-To: {bugs}\\n"
"POT-Creation-Date: 2026-10-04 12:00+0000\\n"
"PO-Revision-Date: 2026-10-04 12:00+0000\\n"
"Last-Translator: VLF Noise Scout contributors\\n"
"Language-Team: {team}\\n"
"Language: {code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: {plural}\\n"
"X-Generator: compile_translations.py\\n"
"""


def _po_escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def _po_wrap(text: str) -> str:
    """Emit long msgstr values as multi-line strings (80-col friendly)."""
    limit = 76
    if len(text) <= limit and "\n" not in text:
        return f'"{_po_escape(text)}"'
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > limit and current:
            lines.append(current + " ")   # ayırıcı boşluk satır sonunda taşınır
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    quoted = "\n".join(f'"{_po_escape(line)}"' for line in lines)
    return f'""\n{quoted}'


def build_po(code: str, catalog: dict[str, str]) -> str:
    name, plural = LANGUAGES[code]
    chunks = [
        PO_HEADER.format(
            project=PROJECT, version=VERSION, bugs=BUGS,
            team=f"{name} <https://github.com/altunsumerve/vlf-noise-scout>",
            code=code, plural=plural,
        )
    ]
    for key, value in catalog.items():
        comment = f"#. UI string “{key}”\n" if not key.startswith(("guide", "station")) else f"#. UI string {key}\n"
        chunks.append(f"{comment}msgid \"{_po_escape(key)}\"\nmsgstr {_po_wrap(value)}\n")
    return "\n".join(chunks)


def mo_header_entry(code: str) -> str:
    """Metadata entry (msgid "") every GNU MO catalog must carry."""
    _name, plural = LANGUAGES[code]
    return (
        f"Project-Id-Version: {PROJECT} {VERSION}\n"
        f"Report-Msgid-Bugs-To: {BUGS}\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
        "Content-Transfer-Encoding: 8bit\n"
        f"Plural-Forms: {plural}\n"
        f"Language: {code}\n"
    )


def build_mo(code: str, catalog: dict[str, str]) -> bytes:
    """Serialize a GNU MO file (same layout as GNU msgfmt output)."""
    catalog = {**catalog, "": mo_header_entry(code)}
    entries = sorted((key.encode("utf-8"), value.encode("utf-8")) for key, value in catalog.items())
    n = len(entries)
    orig_off = 28                # 7 x uint32 header
    trans_off = orig_off + 8 * n
    data_off = trans_off + 8 * n
    header = struct.pack("<IIIIIII", 0x950412DE, 0, n, orig_off, trans_off, 0, 0)
    orig_table = b""
    trans_table = b""
    offset = data_off
    for msgid, _msgstr in entries:
        orig_table += struct.pack("<II", len(msgid), offset)
        offset += len(msgid) + 1
    for _msgid, msgstr in entries:
        trans_table += struct.pack("<II", len(msgstr), offset)
        offset += len(msgstr) + 1
    body_ids = b"".join(msgid + b"\x00" for msgid, _msgstr in entries)
    body_strs = b"".join(msgstr + b"\x00" for _msgid, msgstr in entries)
    return header + orig_table + trans_table + body_ids + body_strs


def load_catalog(src: Path, code: str) -> dict[str, str]:
    data = json.loads((src / f"{code}.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{code}.json: expected a JSON object")
    bad = [k for k, v in data.items() if not isinstance(v, str) or not v.strip()]
    if bad:
        raise ValueError(f"{code}.json: empty or non-string values: {bad}")
    return data


def compile_all(src: Path, out: Path) -> None:
    reference = load_catalog(src, "en")
    for code in LANGUAGES:
        catalog = load_catalog(src, code)
        missing = set(reference) - set(catalog)
        extra = set(catalog) - set(reference)
        if missing or extra:
            raise ValueError(f"{code}.json: missing={sorted(missing)} extra={sorted(extra)}")
        lc = out / code / "LC_MESSAGES"
        lc.mkdir(parents=True, exist_ok=True)
        (lc / "messages.po").write_text(build_po(code, catalog), encoding="utf-8")
        (lc / "messages.mo").write_bytes(build_mo(code, catalog))
        (out / f"{code}.json").write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  {code}: {len(catalog)} strings -> po + mo + json")
    pot = {k: "" for k in reference}
    (out / "messages.pot").write_text(build_po("en", pot), encoding="utf-8")
    print(f"  template: messages.pot ({len(reference)} msgids)")


def parse_po(text: str) -> dict[str, str]:
    """Minimal .po reader for catalogs generated by this tool.

    Handles single/multi-line quoted msgid/msgstr pairs and the usual
    escapes (\\n, \\t, \\\", \\\\). Entries written by external tools that
    use the same plain format parse fine too; comments are ignored.
    """
    def unescape(value: str) -> str:
        out: list[str] = []
        i = 0
        while i < len(value):
            ch = value[i]
            if ch == "\\" and i + 1 < len(value):
                nxt = value[i + 1]
                out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                i += 2
            else:
                out.append(ch)
                i += 1
        return "".join(out)

    catalog: dict[str, str] = {}
    msgid: str | None = None
    msgstr: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("msgid "):
            if msgid is not None and msgstr is not None and msgid:
                catalog[msgid] = msgstr
            msgid, msgstr = "", ""
            msgid += unescape(line[6:].strip().strip('"'))
        elif line.startswith("msgstr "):
            if msgid is None:
                msgid = ""
            msgstr = unescape(line[7:].strip().strip('"'))
        elif line.startswith('"') and msgstr is not None:
            # devam satırı: hangi alana ait olduğunu takip et
            if msgid is not None:
                msgstr += unescape(line.strip('"'))
    if msgid is not None and msgstr is not None and msgid:
        catalog[msgid] = msgstr
    return catalog


def sync_from_po(bundle: Path) -> None:
    """Round-trip for translators: edited .po files refresh .mo and .json.

    Usage: python compile_translations.py web/locales --sync-po
    The .po files are the human-editable source; the JSON bundles that the
    web UI fetches and the binary MO catalogs are regenerated from them.
    """
    reference = json.loads((bundle / "en.json").read_text(encoding="utf-8"))
    for code in LANGUAGES:
        po_path = bundle / code / "LC_MESSAGES" / "messages.po"
        if not po_path.is_file():
            raise FileNotFoundError(po_path)
        catalog = parse_po(po_path.read_text(encoding="utf-8"))
        missing = set(reference) - set(catalog)
        if missing:
            raise ValueError(f"{code}: .po is missing keys: {sorted(missing)}")
        catalog = {k: catalog[k] for k in reference}
        bad = [k for k, v in catalog.items() if not v.strip()]
        if bad:
            raise ValueError(f"{code}: empty translations: {bad}")
        (bundle / code / "LC_MESSAGES" / "messages.mo").write_bytes(build_mo(code, catalog))
        (bundle / f"{code}.json").write_text(
            json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"  {code}: synced from .po ({len(catalog)} keys)")


def check(out: Path) -> int:
    """CI mode: verify every language ships .po, .mo and .json and MO parses."""
    import gettext as gt

    failures = 0
    reference = json.loads((out / "en.json").read_text(encoding="utf-8"))
    for code in LANGUAGES:
        try:
            lc = out / code / "LC_MESSAGES"
            for name in ("messages.po", "messages.mo"):
                if not (lc / name).is_file():
                    raise FileNotFoundError(f"{code}/LC_MESSAGES/{name}")
            js = json.loads((out / f"{code}.json").read_text(encoding="utf-8"))
            if set(js) != set(reference):
                raise ValueError("key set differs from en.json")
            if any(not v.strip() for v in js.values()):
                raise ValueError("empty translation present")
            with (lc / "messages.mo").open("rb") as fh:
                catalog = gt.GNUTranslations(fh)
            for key in ("tagline", "guideTitle", "txTitle"):
                if catalog.gettext(key) not in (js[key], ""):
                    raise ValueError(f"MO mismatch for {key}")
            print(f"  {code}: OK ({len(js)} keys)")
        except Exception as exc:
            failures += 1
            print(f"  {code}: FAIL — {exc}")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[2] == "--check":
        return check(Path(argv[1]))
    if len(argv) >= 3 and argv[2] == "--sync-po":
        sync_from_po(Path(argv[1]))
        return 0
    if len(argv) < 3:
        print(__doc__)
        return 2
    compile_all(Path(argv[1]), Path(argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
