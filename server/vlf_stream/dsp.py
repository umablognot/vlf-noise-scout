from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass
class DSPMetrics:
    coherence: float = 0.0
    cancellation_db: float = 0.0
    band_reject_db: float = 0.0
    transient_frozen: bool = False


class SpectralNLMS:
    """Two-channel frequency-domain normalized LMS canceller.

    Channel 0 is the main antenna. Channel 1 is the local-noise reference.
    A sqrt-Hann overlap/add pair reconstructs one cleaned mono block for every
    input block. Adaptation freezes during large main-channel transients so a
    sferic is less likely to be learned as interference.
    """

    def __init__(
        self,
        sample_rate: int = 48_000,
        hop_size: int = 512,
        low_cut_hz: float = 250.0,
        high_cut_hz: float = 12_000.0,
        adapt_rate: float = 0.035,
        cancel_strength: float = 0.88,
        coherence_floor: float = 0.18,
        transient_freeze_ratio: float = 3.8,
    ) -> None:
        self.sample_rate = sample_rate
        self.hop_size = hop_size
        self.frame_size = hop_size * 2
        self.low_cut_hz = low_cut_hz
        self.high_cut_hz = min(high_cut_hz, sample_rate / 2 - 1)
        self.adapt_rate = adapt_rate
        self.cancel_strength = cancel_strength
        self.coherence_floor = coherence_floor
        self.transient_freeze_ratio = transient_freeze_ratio

        self.window = np.sqrt(np.hanning(self.frame_size) + 1e-12).astype(
            np.float64
        )
        frequencies = np.fft.rfftfreq(self.frame_size, 1.0 / sample_rate)
        self.band = (frequencies >= low_cut_hz) & (frequencies <= self.high_cut_hz)
        bins = frequencies.size
        self.transfer = np.zeros(bins, dtype=np.complex128)
        self.pxx = np.full(bins, 1e-8, dtype=np.float64)
        self.pdd = np.full(bins, 1e-8, dtype=np.float64)
        self.pdx = np.zeros(bins, dtype=np.complex128)
        self.previous_main = np.zeros(hop_size, dtype=np.float64)
        self.previous_reference = np.zeros(hop_size, dtype=np.float64)
        self.overlap_tail = np.zeros(hop_size, dtype=np.float64)
        self.main_rms_ema = 1e-4
        self.frames_seen = 0
        self.metrics = DSPMetrics()

    def reset(self) -> None:
        self.__init__(
            sample_rate=self.sample_rate,
            hop_size=self.hop_size,
            low_cut_hz=self.low_cut_hz,
            high_cut_hz=self.high_cut_hz,
            adapt_rate=self.adapt_rate,
            cancel_strength=self.cancel_strength,
            coherence_floor=self.coherence_floor,
            transient_freeze_ratio=self.transient_freeze_ratio,
        )

    def process(self, stereo_block: np.ndarray) -> np.ndarray:
        block = np.asarray(stereo_block, dtype=np.float64)
        if block.shape != (self.hop_size, 2):
            raise ValueError(
                f"expected {(self.hop_size, 2)}, received {block.shape}"
            )

        main = np.clip(block[:, 0], -1.0, 1.0)
        reference = np.clip(block[:, 1], -1.0, 1.0)
        main_rms = float(np.sqrt(np.mean(main * main) + 1e-14))
        reference_rms = float(np.sqrt(np.mean(reference * reference) + 1e-14))
        transient = (
            self.frames_seen > 12
            and main_rms > self.transient_freeze_ratio * self.main_rms_ema
        )

        main_frame = np.concatenate((self.previous_main, main))
        reference_frame = np.concatenate((self.previous_reference, reference))
        desired = np.fft.rfft(main_frame * self.window)
        noise = np.fft.rfft(reference_frame * self.window)

        smoothing = 0.025
        noise_power = np.abs(noise) ** 2
        desired_power = np.abs(desired) ** 2
        self.pxx = (1.0 - smoothing) * self.pxx + smoothing * noise_power
        self.pdd = (1.0 - smoothing) * self.pdd + smoothing * desired_power
        self.pdx = (1.0 - smoothing) * self.pdx + smoothing * (
            desired * np.conjugate(noise)
        )

        error = desired - self.transfer * noise
        if not transient and reference_rms > 1e-6:
            step = (
                self.adapt_rate
                * np.conjugate(noise)
                * error
                / (self.pxx + 1e-9)
            )
            self.transfer[self.band] += step[self.band]
            magnitude = np.abs(self.transfer)
            too_large = magnitude > 12.0
            self.transfer[too_large] *= 12.0 / magnitude[too_large]

        coherence = np.clip(
            np.abs(self.pdx) ** 2 / (self.pxx * self.pdd + 1e-12), 0.0, 1.0
        )
        weight = np.clip(
            (coherence - self.coherence_floor)
            / max(1.0 - self.coherence_floor, 1e-6),
            0.0,
            1.0,
        )
        cleaned_spectrum = desired - (
            self.cancel_strength * weight * self.transfer * noise
        )
        cleaned_spectrum[~self.band] = 0.0

        cleaned_frame = np.fft.irfft(
            cleaned_spectrum, n=self.frame_size
        ).real * self.window
        output = cleaned_frame[: self.hop_size] + self.overlap_tail
        self.overlap_tail = cleaned_frame[self.hop_size :]
        self.previous_main = main.copy()
        self.previous_reference = reference.copy()
        self.frames_seen += 1
        self.main_rms_ema = 0.99 * self.main_rms_ema + 0.01 * main_rms

        output = np.clip(output, -0.98, 0.98).astype(np.float32)
        in_band = coherence[self.band]
        mean_coherence = float(np.mean(in_band)) if in_band.size else 0.0

        total_power = float(np.sum(desired_power))
        band_input_power = float(np.sum(desired_power[self.band]))
        band_output_power = float(np.sum(np.abs(cleaned_spectrum[self.band]) ** 2))
        cancellation_db = 10.0 * math.log10(
            max(band_input_power, 1e-18) / max(band_output_power, 1e-18)
        )
        band_reject_db = 10.0 * math.log10(
            max(total_power, 1e-18) / max(band_input_power, 1e-18)
        )

        self.metrics = DSPMetrics(
            coherence=mean_coherence,
            cancellation_db=float(np.clip(cancellation_db, -6.0, 48.0)),
            band_reject_db=float(np.clip(band_reject_db, 0.0, 60.0)),
            transient_frozen=transient,
        )
        return output
