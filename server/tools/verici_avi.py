#!/usr/bin/env python3
"""Bilinen VLF vericilerini arar: zincirin "garantili hedef" sinamasi.

96 kHz orneklemede TBB (26.7 kHz, TURKIYE), NAA, DHO38 gibi MSK vericileri
ve Rus Alpha seyrusefer hatlari icin dar bant SNR olcer. Sferic beklemeden
"bu duzenek gokyuzunu duyuyor mu?" sorusuna dakikalar icinde cevap verir.

Kullanim:
  python verici_avi.py --device 1                # 30 sn, 96 kHz
  python verici_avi.py --device 1 --out av.wav   # kaydi da sakla
  python verici_avi.py --input av.wav            # hazir kaydi incele
"""

from __future__ import annotations

import argparse
import math
import sys
import wave

import numpy as np

# (frekans Hz, ad, not)
TRANSMITTERS = [
    (11_905.0, "Alpha F1", "RSDN-20 seyrusefer, Rusya"),
    (12_649.0, "Alpha F2", "RSDN-20 seyrusefer, Rusya"),
    (14_881.0, "Alpha F3", "RSDN-20 seyrusefer, Rusya"),
    (19_580.0, "GBZ", "Anthorn, Birlesik Krallik"),
    (20_270.0, "ICV", "Tavolara, Italya"),
    (21_750.0, "HWU", "Rosnay, Fransa"),
    (23_400.0, "DHO38", "Rhauderfehn, Almanya"),
    (24_000.0, "NAA", "Cutler, ABD"),
    (26_700.0, "TBB", "Bafa, TURKIYE - bizim verici"),
    (37_500.0, "TFK/NRK", "Grindavik, Izlanda"),
]


def capture(device, seconds: float, rate: int, channels: int):
    import sounddevice as sd

    frames = int(seconds * rate)
    data = sd.rec(frames, samplerate=rate, channels=channels,
                  dtype="float32", device=device)
    sd.wait()
    return np.asarray(data, dtype=np.float64), rate


def read_wav(path: str):
    with wave.open(path, "rb") as handle:
        rate = handle.getframerate()
        width = handle.getsampwidth()
        channels = handle.getnchannels()
        raw = handle.readframes(handle.getnframes())
    if width != 2:
        raise ValueError("yalnizca 16-bit WAV destekleniyor")
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    return samples.reshape(-1, channels), rate


def write_wav(path: str, data: np.ndarray, rate: int) -> None:
    clipped = np.clip(data, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(path, "wb") as handle:
        handle.setnchannels(data.shape[1])
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm.tobytes())


def average_spectrum(channel: np.ndarray, rate: int):
    size = 1 << int(math.log2(rate * 0.25))
    if channel.size < size:
        size = 1 << int(math.log2(max(channel.size, 2)))
    window = np.hanning(size)
    hop = size // 2
    chunks = max(1, (channel.size - size) // hop + 1)
    total = np.zeros(size // 2 + 1)
    used = 0
    for index in range(chunks):
        start = index * hop
        segment = channel[start:start + size]
        if segment.size < size:
            break
        total += np.abs(np.fft.rfft(segment * window)) ** 2
        used += 1
    total /= max(used, 1)
    return np.fft.rfftfreq(size, 1.0 / rate), total


def narrow_snr(freqs: np.ndarray, power: np.ndarray, target: float,
               half_signal: float = 150.0, half_noise: float = 1_500.0):
    """target +-150 Hz icindeki tepe / cevre +-1.5 kHz medyani (dB)."""
    sig = (freqs >= target - half_signal) & (freqs <= target + half_signal)
    ring = ((freqs >= target - half_noise) & (freqs <= target + half_noise)) & ~sig
    if not sig.any() or not ring.any():
        return None, None
    peak_idx = int(np.argmax(np.where(sig, power, 0.0)))
    floor = float(np.median(power[ring])) + 1e-20
    snr = 10.0 * math.log10((float(power[peak_idx]) + 1e-20) / floor)
    return snr, float(freqs[peak_idx])


def top_peaks(freqs: np.ndarray, power: np.ndarray, low: float, high: float,
              count: int = 5):
    """Kesif modu: en guclu dar tepeleri listele (beklenmedik tasiyicilar)."""
    mask = (freqs >= low) & (freqs <= high)
    idx = np.where(mask)[0]
    if idx.size < 32:
        return []
    smooth = np.convolve(power, np.ones(9) / 9.0, mode="same")
    prominence = power[idx] / (smooth[idx] + 1e-20)
    order = np.argsort(prominence)[::-1]
    results = []
    taken: list[float] = []
    for j in order:
        f = float(freqs[idx[j]])
        if any(abs(f - t) < 250.0 for t in taken):
            continue
        results.append((f, 10.0 * math.log10(float(prominence[j]) + 1e-20)))
        taken.append(f)
        if len(results) >= count:
            break
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Bilinen VLF vericilerini ara")
    parser.add_argument("--device", default=None)
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument("--rate", type=int, default=96_000)
    parser.add_argument("--channels", type=int, default=2)
    parser.add_argument("--input", default=None, help="hazir 16-bit WAV incele")
    parser.add_argument("--out", default=None, help="yakalanani WAV kaydet")
    parser.add_argument("--json", default=None,
                        help="sonuclari JSON yaz (web arayuzu icin)")
    args = parser.parse_args()

    if args.input:
        data, rate = read_wav(args.input)
    else:
        device = args.device
        if isinstance(device, str) and device.isdigit():
            device = int(device)
        try:
            data, rate = capture(device, args.seconds, args.rate, args.channels)
        except Exception as exc:
            print(f"Iki kanal acilamadi ({exc}); tek kanala dusuluyor.",
                  file=sys.stderr)
            data, rate = capture(device, args.seconds, args.rate, 1)
        if args.out:
            write_wav(args.out, data, rate)
            print(f"Kayit yazildi: {args.out}")

    left = data[:, 0]
    nyquist = rate / 2.0
    print(f"\n=== Verici avi: {rate} Hz orneklem, tavan {nyquist/1000:.1f} kHz, "
          f"{left.size / rate:.1f} s ===")
    if rate < 88_200:
        print("UYARI: 96000 Hz onerilir; bu oranla ust vericiler menzil disi.")

    freqs, power = average_spectrum(left, rate)

    collected = []
    print(f"\n{'Verici':<10}{'Frekans':>9}  {'SNR':>6}  Durum")
    print("-" * 62)
    for target, name, note in TRANSMITTERS:
        if target >= nyquist - 500.0:
            print(f"{name:<10}{target/1000:>7.2f}k  {'—':>6}  "
                  f"orneklem tavani disinda")
            continue
        snr, peak_f = narrow_snr(freqs, power, target)
        if snr is None:
            continue
        if snr >= 10.0:
            verdict = "GORULDU"
        elif snr >= 5.0:
            verdict = "zayif iz"
        else:
            verdict = "yok"
        collected.append({"call": name, "freq_hz": target, "snr": round(snr, 2)})
        bar = "#" * max(0, min(30, int(snr)))
        print(f"{name:<10}{target/1000:>7.2f}k  {snr:>5.1f}d  "
              f"{verdict:<9} {bar}  ({note})")

    print("\nKesif modu — 10 kHz uzerindeki en belirgin 5 dar tepe:")
    for f, prom in top_peaks(freqs, power, 10_000.0, nyquist - 500.0):
        match = next((n for t, n, _ in TRANSMITTERS if abs(f - t) < 250.0), "")
        tag = f"  <-- {match}" if match else ""
        print(f"  {f/1000:7.3f} kHz  belirginlik {prom:5.1f} dB{tag}")

    if args.json:
        import datetime, json as _json, pathlib as _pl
        payload = {
            "scanned_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "seconds": args.seconds,
            "sample_rate": rate,
            "results": collected,
        }
        out_path = _pl.Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(_json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON yazildi: {out_path}")

    print("\nNot: MSK vericileri 7/24 yayindadir ama bakima girebilirler;")
    print("tek olcumle 'yok' demeden farkli saatlerde tekrar dene. Gece,")
    print("uzak vericiler (NAA, TFK) icin belirgin avantajdir; TBB ic hat")
    print("oldugu icin gunduz de gorulebilir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
