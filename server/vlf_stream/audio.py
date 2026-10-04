from __future__ import annotations

import queue
import threading
import time
from typing import Any

import numpy as np

from .config import Settings
from .dsp import SpectralNLMS
from .streaming import BroadcastHub, MP3Encoder


def _dbfs(samples: np.ndarray) -> float:
    rms = float(np.sqrt(np.mean(np.asarray(samples, dtype=np.float64) ** 2) + 1e-14))
    return float(np.clip(20.0 * np.log10(max(rms, 1e-9)), -120.0, 0.0))


class AudioPipeline:
    def __init__(
        self,
        settings: Settings,
        raw_hub: BroadcastHub,
        clean_hub: BroadcastHub,
    ) -> None:
        self.settings = settings
        self.raw_hub = raw_hub
        self.clean_hub = clean_hub
        self.dsp = SpectralNLMS(
            sample_rate=settings.sample_rate,
            hop_size=settings.block_size,
            low_cut_hz=settings.low_cut_hz,
            high_cut_hz=settings.high_cut_hz,
            adapt_rate=settings.adapt_rate,
            cancel_strength=settings.cancel_strength,
            coherence_floor=settings.coherence_floor,
            transient_freeze_ratio=settings.transient_freeze_ratio,
        )
        self.raw_encoder = MP3Encoder(
            raw_hub, settings.sample_rate, settings.mp3_bitrate, "raw"
        )
        self.clean_encoder = MP3Encoder(
            clean_hub, settings.sample_rate, settings.mp3_bitrate, "clean"
        )
        self.blocks: queue.Queue[np.ndarray] = queue.Queue(maxsize=48)
        self._residual = np.zeros((0, 2), dtype=np.float32)
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.source_thread: threading.Thread | None = None
        self.input_stream: Any | None = None
        self.started_at = time.monotonic()
        self._status_lock = threading.Lock()
        self._status: dict[str, Any] = {
            "online": False,
            "mode": "mock" if settings.mock_mode else "live",
            "input_dbfs": -120.0,
            "output_dbfs": -120.0,
            "cancellation_db": 0.0,
            "band_reject_db": 0.0,
            "coherence": 0.0,
            "clipping": False,
            "transient_frozen": False,
            "dropped_blocks": 0,
            "error": None,
        }

    def start(self) -> None:
        try:
            # Kodlayıcılardan biri başlamazsa (ör. ffmpeg kurulu değil) tüm
            # boru hattını öldürme: yakalama + DSP + metrikler çalışmaya devam
            # etsin, arayüz hatayı durum satırında göstersin.
            encoder_error: str | None = None
            for encoder in (self.raw_encoder, self.clean_encoder):
                try:
                    encoder.start()
                except Exception as exc:
                    encoder.last_error = str(exc)
                    encoder_error = encoder_error or f"MP3 encoder: {exc}"
            self.worker = threading.Thread(
                target=self._process_loop, name="vlf-dsp", daemon=True
            )
            self.worker.start()
            if self.settings.mock_mode:
                self.source_thread = threading.Thread(
                    target=self._mock_loop, name="vlf-mock-source", daemon=True
                )
                self.source_thread.start()
            else:
                self._start_sounddevice()
            self._set_status(online=True, error=encoder_error)
        except Exception as exc:
            self._set_status(online=False, error=str(exc))

    def _start_sounddevice(self) -> None:
        import sounddevice as sd

        def callback(
            indata: np.ndarray,
            _frames: int,
            _time_info: Any,
            status: Any,
        ) -> None:
            if status:
                self._set_status(error=str(status))
            self._accumulate(np.array(indata, dtype=np.float32, copy=True))

        self.input_stream = sd.InputStream(
            device=self.settings.device,
            channels=2,
            samplerate=self.settings.sample_rate,
            blocksize=self.settings.block_size,
            dtype="float32",
            callback=callback,
        )
        self.input_stream.start()

    def _accumulate(self, chunk: np.ndarray) -> None:
        size = self.settings.block_size
        self._residual = np.concatenate((self._residual, chunk))
        while self._residual.shape[0] >= size:
            self._enqueue(self._residual[:size].copy())
            self._residual = self._residual[size:]

    def _enqueue(self, block: np.ndarray) -> None:
        try:
            self.blocks.put_nowait(block)
        except queue.Full:
            try:
                self.blocks.get_nowait()
                self.blocks.put_nowait(block)
            except (queue.Empty, queue.Full):
                pass
            with self._status_lock:
                self._status["dropped_blocks"] += 1

    def _process_loop(self) -> None:
        while not self.stop_event.is_set():
            try:
                block = self.blocks.get(timeout=0.5)
            except queue.Empty:
                continue
            if block.shape != (self.settings.block_size, 2):
                self._set_status(error=f"unexpected audio shape {block.shape}")
                continue
            main = block[:, 0]
            clean = self.dsp.process(block)
            self.raw_encoder.write(main)
            self.clean_encoder.write(clean)
            self._set_status(
                input_dbfs=_dbfs(main),
                output_dbfs=_dbfs(clean),
                cancellation_db=self.dsp.metrics.cancellation_db,
                band_reject_db=self.dsp.metrics.band_reject_db,
                coherence=self.dsp.metrics.coherence,
                clipping=bool(np.max(np.abs(main)) >= 0.985),
                transient_frozen=self.dsp.metrics.transient_frozen,
                error=self.raw_encoder.last_error or self.clean_encoder.last_error,
            )

    def _mock_loop(self) -> None:
        rng = np.random.default_rng(240724)
        phase = 0
        while not self.stop_event.is_set():
            count = self.settings.block_size
            index = np.arange(count, dtype=np.float64) + phase
            seconds = index / self.settings.sample_rate
            reference = (
                0.12 * np.sin(2 * np.pi * 50 * seconds)
                + 0.055 * np.sin(2 * np.pi * 350 * seconds)
                + 0.025 * np.sin(2 * np.pi * 1_250 * seconds)
                + 0.005 * rng.normal(size=count)
            )
            natural = 0.006 * rng.normal(size=count)
            if rng.random() < 0.025:
                start = int(rng.integers(0, max(1, count - 96)))
                length = min(96, count - start)
                envelope = np.exp(-np.arange(length) / 18.0)
                natural[start : start + length] += 0.45 * envelope * rng.normal(
                    size=length
                )
            main_noise = 0.76 * np.roll(reference, 7)
            main = np.clip(main_noise + natural, -0.95, 0.95)
            stereo = np.column_stack((main, reference)).astype(np.float32)
            self._enqueue(stereo)
            phase += count
            time.sleep(count / self.settings.sample_rate)

    def _set_status(self, **updates: Any) -> None:
        with self._status_lock:
            self._status.update(updates)

    def status(self) -> dict[str, Any]:
        with self._status_lock:
            result = dict(self._status)
        result.update(
            {
                "uptime_seconds": int(time.monotonic() - self.started_at),
                "listeners": self.raw_hub.listener_count
                + self.clean_hub.listener_count,
                "sample_rate": self.settings.sample_rate,
                "band_hz": [
                    int(self.settings.low_cut_hz),
                    int(self.settings.high_cut_hz),
                ],
            }
        )
        return result

    def stop(self) -> None:
        self.stop_event.set()
        if self.input_stream is not None:
            try:
                self.input_stream.stop()
                self.input_stream.close()
            except Exception:
                pass
        self.raw_encoder.stop()
        self.clean_encoder.stop()
        self._set_status(online=False)
