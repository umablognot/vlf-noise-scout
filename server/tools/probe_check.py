#!/usr/bin/env python3
"""Diagnose the capture chain before any analog hardware is built.

Reports channel independence, level headroom, mains harmonic content and
impulse activity so the operator can tell a mono dongle, a clipped front end
and a genuinely quiet band apart.
"""

from __future__ import annotations

import argparse
import math
import sys
import wave

import numpy as np

BAND_EDGES = [
    (0.0, 250.0, "0-250 Hz (sebeke bolgesi)"),
    (250.0, 2_000.0, "250 Hz - 2 kHz"),
    (2_000.0, 6_000.0, "2-6 kHz (tweek bolgesi)"),
    (6_000.0, 12_000.0, "6-12 kHz (sferic bolgesi)"),
    (12_000.0, 20_000.0, "12-20 kHz (Alpha/ust bant)"),
    (20_000.0, 30_000.0, "20-30 kHz (MSK verici bolgesi)"),
]


def list_devices() -> None:
    import sounddevice as sd

    print(sd.query_devices())


def capture(device: str | int | None, seconds: float, rate: int, channels: int):
    import sounddevice as sd

    frames = int(seconds * rate)
    data = sd.rec(frames, samplerate=rate, channels=channels, dtype="float32", device=device)
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


def dbfs(values: np.ndarray) -> float:
    rms = math.sqrt(float(np.mean(values**2)) + 1e-20)
    return 20.0 * math.log10(max(rms, 1e-10))


def average_spectrum(channel: np.ndarray, rate: int):
    size = 1 << int(math.log2(rate * 0.25))
    if channel.size < size:
        size = 1 << int(math.log2(max(channel.size, 2)))
    window = np.hanning(size)
    hop = size // 2
    chunks = max(1, (channel.size - size) // hop + 1)
    total = np.zeros(size // 2 + 1)
    for index in range(chunks):
        start = index * hop
        segment = channel[start : start + size]
        if segment.size < size:
            break
        total += np.abs(np.fft.rfft(segment * window)) ** 2
    total /= max(chunks, 1)
    return np.fft.rfftfreq(size, 1.0 / rate), total


def band_power(freqs: np.ndarray, power: np.ndarray, low: float, high: float) -> float:
    mask = (freqs >= low) & (freqs < high)
    return float(np.sum(power[mask])) if mask.any() else 0.0


def mains_score(freqs: np.ndarray, power: np.ndarray, base: float) -> float:
    peaks = []
    for order in range(1, 13):
        target = base * order
        if target >= freqs[-1]:
            break
        index = int(np.argmin(np.abs(freqs - target)))
        window = power[max(0, index - 12) : index + 13]
        floor = float(np.median(window)) + 1e-20
        peaks.append(10.0 * math.log10((power[index] + 1e-20) / floor))
    return float(np.mean(peaks)) if peaks else 0.0


def impulse_rate(channel: np.ndarray, rate: int) -> float:
    spectrum = np.fft.rfft(channel)
    freqs = np.fft.rfftfreq(channel.size, 1.0 / rate)
    spectrum[(freqs < 2_000.0) | (freqs > 12_000.0)] = 0.0
    filtered = np.fft.irfft(spectrum, n=channel.size)
    envelope = np.abs(filtered)
    median = float(np.median(envelope))
    deviation = float(np.median(np.abs(envelope - median))) + 1e-12
    threshold = median + 8.0 * deviation
    above = envelope > threshold
    events = int(np.count_nonzero(above[1:] & ~above[:-1]))
    return events / (channel.size / rate) * 60.0


def ascii_spectrum(freqs: np.ndarray, power: np.ndarray) -> None:
    edges = np.geomspace(20.0, float(freqs[-1]), 29)
    values = []
    for low, high in zip(edges[:-1], edges[1:]):
        values.append(band_power(freqs, power, low, high))
    peak = max(values) + 1e-20
    print("\n  Ortalama spektrum (tepeye gore dB)")
    for (low, high), value in zip(zip(edges[:-1], edges[1:]), values):
        level = 10.0 * math.log10((value + 1e-20) / peak)
        bar = "#" * max(0, int((level + 60.0) / 60.0 * 40.0))
        label = f"{low:7.0f}-{high:<7.0f}"
        print(f"  {label} {level:6.1f} |{bar}")


def analyse(data: np.ndarray, rate: int, mains: float) -> None:
    channels = data.shape[1]
    print(f"\n=== Yakalama ozeti: {channels} kanal, {rate} Hz, "
          f"{data.shape[0] / rate:.1f} s ===")

    for index in range(channels):
        channel = data[:, index]
        peak = float(np.max(np.abs(channel)))
        clipped = float(np.mean(np.abs(channel) > 0.985)) * 100.0
        name = ["SOL (ana anten)", "SAG (referans prob)"][index] if channels == 2 else "MONO"
        print(f"\n[{name}]")
        if peak == 0.0:
            print("  DIJITAL SESSIZLIK - tum ornekler tam sifir.")
            print("  Aygit veri uretmiyor: giris Windows/ALSA tarafinda kapali,")
            print("  sessize alinmis veya kayit seviyesi sifir olabilir.")
            continue
        print(f"  RMS seviye     : {dbfs(channel):7.1f} dBFS")
        print(f"  Tepe seviye    : {20 * math.log10(max(peak, 1e-10)):7.1f} dBFS")
        print(f"  Kirpilan ornek : {clipped:7.2f} %")

        freqs, power = average_spectrum(channel, rate)
        for low, high, label in BAND_EDGES:
            share = band_power(freqs, power, low, high)
            total = float(np.sum(power)) + 1e-20
            print(f"  {label:<28}: {share / total * 100:5.1f} % enerji")
        print(f"  {mains:.0f} Hz harmonik belirginligi: {mains_score(freqs, power, mains):.1f} dB")
        print(f"  Darbe adayi (2-12 kHz)  : {impulse_rate(channel, rate):.1f} olay/dakika")
        if index == 0:
            ascii_spectrum(freqs, power)

    verdict(data, rate, mains)


def verdict(data: np.ndarray, rate: int, mains: float) -> None:
    print("\n=== Degerlendirme ===")
    notes: list[str] = []

    if data.shape[1] < 2:
        notes.append(
            "Kart tek kanal yakaliyor. Ikili prob mimarisi bu kartla kurulamaz; "
            "gercek stereo Line-In'li bir kart gerekiyor."
        )
    else:
        left, right = data[:, 0], data[:, 1]
        if left.std() == 0.0 or right.std() == 0.0:
            correlation = float("nan")
            print("  Kanal korelasyonu: hesaplanamadi (en az bir kanal sabit)")
        else:
            correlation = float(
                np.corrcoef(left - left.mean(), right - right.mean())[0, 1]
            )
            print(f"  Kanal korelasyonu: {correlation:+.4f}")
        if math.isnan(correlation):
            pass
        elif abs(correlation) > 0.9995 or np.allclose(left, right):
            notes.append(
                "Iki kanal neredeyse birebir ayni. Kart muhtemelen tek girisi "
                "iki kanala kopyaliyor; adaptif iptal bu kartla anlamsiz calisir."
            )
        elif abs(correlation) < 0.02:
            notes.append(
                "Kanallar tamamen bagimsiz. Ortak parazit yoksa iptal edecek bir "
                "sey de yok; referans probunu parazit kaynagina yaklastir."
            )

    left = data[:, 0]
    level = dbfs(left)
    if float(np.max(np.abs(data))) == 0.0:
        notes.append(
            "Yakalanan veri tamamen sifir. Bu bir seviye sorunu degil; aygit hic "
            "ornek uretmiyor. Isletim sistemi tarafinda girisi etkinlestirip "
            "kayit seviyesini yukseltmeden diger olculer anlamsiz."
        )
        for note in notes:
            print(f"  - {note}")
        return
    if float(np.mean(np.abs(left) > 0.985)) > 0.001:
        notes.append("Kirpilma var. Analog kazanci veya anten boyunu dusur.")
    elif level < -70.0:
        notes.append(
            f"Bant ici seviye cok dusuk ({level:.0f} dBFS). On yukselteci olmadan "
            "bu zincirden anlamli sinyal beklenmemeli."
        )
    elif level > -12.0:
        notes.append("Seviye tavana yakin. Kazanci biraz dusurmek guvenli olur.")

    freqs, power = average_spectrum(left, rate)
    if mains_score(freqs, power, mains) < 3.0 and level < -70.0:
        notes.append(
            f"{mains:.0f} Hz harmonikleri bile gorunmuyor. Anten fiziksel olarak "
            "bagli mi, dogru giris mi secili, kontrol et."
        )

    if not notes:
        notes.append("Belirgin bir sorun gorunmuyor. Kayit almaya devam edebilirsin.")
    for note in notes:
        print(f"  - {note}")


def main() -> int:
    parser = argparse.ArgumentParser(description="VLF capture chain diagnostics")
    parser.add_argument("--list", action="store_true", help="ses aygitlarini listele")
    parser.add_argument("--device", default=None, help="sounddevice aygit numarasi veya adi")
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--rate", type=int, default=48_000)
    parser.add_argument("--channels", type=int, default=2)
    parser.add_argument("--mains", type=float, default=50.0)
    parser.add_argument("--input", default=None, help="hazir 16-bit WAV dosyasini incele")
    parser.add_argument("--out", default=None, help="yakalanan sesi WAV olarak kaydet")
    args = parser.parse_args()

    if args.list:
        list_devices()
        return 0

    if args.input:
        data, rate = read_wav(args.input)
    else:
        device: str | int | None = args.device
        if isinstance(device, str) and device.isdigit():
            device = int(device)
        try:
            data, rate = capture(device, args.seconds, args.rate, args.channels)
        except Exception as exc:
            if args.channels > 1:
                print(f"Iki kanal acilamadi ({exc}); tek kanala dusuluyor.", file=sys.stderr)
                data, rate = capture(device, args.seconds, args.rate, 1)
            else:
                raise
        if args.out:
            write_wav(args.out, data, rate)
            print(f"Kayit yazildi: {args.out}")

    analyse(data, rate, args.mains)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
