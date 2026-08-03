"""Bilinen VLF vericilerinin son tarama sonucunu web arayuzune sunar.

`tools/verici_avi.py --json <yol>` ile uretilen dosyayi okur. Dosya yoksa
statik verici listesini "henuz taranmadi" durumuyla dondurur; arayuz yine de
istasyon listesini gosterebilir.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# (frekans Hz, cagri, ulke kodu, aciklama TR, aciklama EN)
CATALOG: list[tuple[float, str, str, str, str]] = [
    (11_905.0, "Alpha F1", "RU", "RSDN-20 seyrüsefer", "RSDN-20 navigation"),
    (12_649.0, "Alpha F2", "RU", "RSDN-20 seyrüsefer", "RSDN-20 navigation"),
    (14_881.0, "Alpha F3", "RU", "RSDN-20 seyrüsefer", "RSDN-20 navigation"),
    (19_580.0, "GBZ", "GB", "Anthorn deniz üssü", "Anthorn naval station"),
    (20_270.0, "ICV", "IT", "Tavolara deniz üssü", "Tavolara naval station"),
    (21_750.0, "HWU", "FR", "Rosnay deniz üssü", "Rosnay naval station"),
    (23_400.0, "DHO38", "DE", "Rhauderfehn deniz üssü", "Rhauderfehn naval station"),
    (24_000.0, "NAA", "US", "Cutler, Maine", "Cutler, Maine"),
    (26_700.0, "TBB", "TR", "Bafa — Türkiye vericisi", "Bafa — Turkish transmitter"),
    (37_500.0, "TFK/NRK", "IS", "Grindavík", "Grindavík"),
]


def _results_path() -> Path:
    override = os.getenv("VLF_SCAN_FILE")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data" / "son_tarama.json"


def _verdict(snr: float) -> str:
    if snr >= 10.0:
        return "seen"
    if snr >= 5.0:
        return "trace"
    return "none"


def load() -> dict[str, Any]:
    """Son tarama sonucunu (varsa) katalogla birlestirip dondurur."""
    path = _results_path()
    scanned: dict[str, float] = {}
    meta: dict[str, Any] = {}
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            meta = {
                "scanned_at": payload.get("scanned_at"),
                "seconds": payload.get("seconds"),
                "sample_rate": payload.get("sample_rate"),
            }
            for item in payload.get("results", []):
                scanned[str(item.get("call"))] = float(item.get("snr", 0.0))
        except Exception as exc:  # bozuk dosya arayuzu dusurmesin
            meta = {"error": str(exc)}

    stations = []
    for freq, call, country, note_tr, note_en in CATALOG:
        snr = scanned.get(call)
        stations.append(
            {
                "call": call,
                "freq_hz": freq,
                "country": country,
                "note_tr": note_tr,
                "note_en": note_en,
                "snr_db": snr,
                "verdict": _verdict(snr) if snr is not None else "unknown",
            }
        )
    return {"meta": meta, "stations": stations}
