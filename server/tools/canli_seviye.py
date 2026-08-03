#!/usr/bin/env python3
"""Canli seviye monitoru: trimpotu cevirirken ekrana bakarak ayarla.

Her 0.2 saniyede bir RMS, tepe ve kirpilma yuzdesini gunceller. Terminal
kapanana kadar (Ctrl+C) calisir; test komutu tekrar tekrar calistirmaya
gerek kalmaz.

Kullanim:
  python canli_seviye.py --device 1
  python canli_seviye.py --device 1 --rate 96000
"""

from __future__ import annotations

import argparse
import math
import sys
import time

import numpy as np

# Hedef bantlar (mod secimine gore)
TARGETS = {
    "dinleme": (-30.0, -20.0),
    "av": (-28.0, -22.0),
}


def dbfs(values: np.ndarray) -> float:
    rms = math.sqrt(float(np.mean(values**2)) + 1e-20)
    return 20.0 * math.log10(max(rms, 1e-10))


def bar(level: float, low: float = -70.0, high: float = 0.0, width: int = 34) -> str:
    """Seviye cubugu: -70..0 dBFS araligini karakterlere yayar."""
    frac = (level - low) / (high - low)
    filled = max(0, min(width, int(frac * width)))
    return "#" * filled + "-" * (width - filled)


def verdict(rms: float, clip: float, target: tuple[float, float]) -> str:
    low, high = target
    if clip > 0.001:
        return "KIRPILMA VAR  -> trimpotu KIS"
    if rms < low - 8:
        return "cok dusuk      -> trimpotu AC"
    if rms < low:
        return "biraz dusuk    -> trimpotu biraz AC"
    if rms > high + 6:
        return "cok yuksek     -> trimpotu KIS"
    if rms > high:
        return "biraz yuksek   -> trimpotu biraz KIS"
    return "HEDEFTE  <<< bu ayarda birak"


def main() -> int:
    parser = argparse.ArgumentParser(description="Canli seviye/kirpilma monitoru")
    parser.add_argument("--device", default=None, help="sounddevice aygit numarasi")
    parser.add_argument("--rate", type=int, default=48_000)
    parser.add_argument("--channels", type=int, default=2)
    parser.add_argument("--mode", choices=sorted(TARGETS), default="dinleme",
                        help="hedef bant: dinleme (-30..-20) veya av (-28..-22)")
    parser.add_argument("--block", type=float, default=0.2,
                        help="guncelleme araligi (saniye)")
    args = parser.parse_args()

    import sounddevice as sd

    device = args.device
    if isinstance(device, str) and device.isdigit():
        device = int(device)

    target = TARGETS[args.mode]
    frames = int(args.rate * args.block)

    # Kirpilma gecmisi: son 5 saniyede kirpilan ornek orani
    history: list[float] = []
    history_len = max(1, int(5.0 / args.block))
    peak_hold = -200.0
    peak_hold_until = 0.0

    print(f"Aygit {device} · {args.rate} Hz · mod: {args.mode} "
          f"(hedef {target[0]:.0f}..{target[1]:.0f} dBFS)")
    print("Trimpotu cevirirken asagiya bak. Cikis: Ctrl+C\n")

    try:
        with sd.InputStream(samplerate=args.rate, channels=args.channels,
                            dtype="float32", device=device,
                            blocksize=frames) as stream:
            while True:
                data, overflowed = stream.read(frames)
                block = np.asarray(data, dtype=np.float64)
                left = block[:, 0]
                right = block[:, 1] if block.shape[1] > 1 else None

                rms = dbfs(left)
                peak = float(np.max(np.abs(left)))
                peak_db = 20.0 * math.log10(max(peak, 1e-10))
                clip = float(np.mean(np.abs(left) > 0.985))
                history.append(clip)
                if len(history) > history_len:
                    history.pop(0)
                clip5 = float(np.mean(history)) * 100.0

                now = time.time()
                if peak_db > peak_hold or now > peak_hold_until:
                    peak_hold = peak_db
                    peak_hold_until = now + 3.0

                right_txt = ""
                if right is not None:
                    right_txt = f" | SAG {dbfs(right):6.1f}"

                flag = "!" if clip > 0 else " "
                line = (f"\rSOL {rms:6.1f} dBFS [{bar(rms)}] "
                        f"tepe {peak_hold:5.1f}{flag} "
                        f"kirp {clip5:5.2f}%{right_txt}  {verdict(rms, clip5 / 100.0, target):<38}")
                sys.stdout.write(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\nBitti. Son ayar:")
        print(f"  SOL {rms:.1f} dBFS · tepe {peak_hold:.1f} dBFS · kirpilma {clip5:.2f} %")
        print("Bu ayar iyiyse trimpotun konumunu isaretle.")
        return 0
    except Exception as exc:
        print(f"\nHata: {exc}", file=sys.stderr)
        print("Sunucu calisiyorsa once Ctrl+C ile durdur; iki program ayni "
              "aygiti acamaz.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
