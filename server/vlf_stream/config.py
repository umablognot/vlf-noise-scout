from __future__ import annotations

from dataclasses import dataclass
import os


def _as_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _device(value: str | None) -> str | int | None:
    if not value:
        return None
    return int(value) if value.isdigit() else value


@dataclass(frozen=True)
class Settings:
    device: str | int | None
    sample_rate: int
    block_size: int
    low_cut_hz: float
    high_cut_hz: float
    adapt_rate: float
    cancel_strength: float
    coherence_floor: float
    transient_freeze_ratio: float
    mp3_bitrate: str
    max_listeners: int
    mock_mode: bool
    allowed_origins: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        origins = tuple(
            item.strip()
            for item in os.getenv("VLF_ALLOWED_ORIGINS", "*").split(",")
            if item.strip()
        )
        return cls(
            device=_device(os.getenv("VLF_DEVICE")),
            sample_rate=int(os.getenv("VLF_SAMPLE_RATE", "48000")),
            block_size=int(os.getenv("VLF_BLOCK_SIZE", "512")),
            low_cut_hz=float(os.getenv("VLF_LOW_CUT_HZ", "250")),
            high_cut_hz=float(os.getenv("VLF_HIGH_CUT_HZ", "12000")),
            adapt_rate=float(os.getenv("VLF_ADAPT_RATE", "0.035")),
            cancel_strength=float(os.getenv("VLF_CANCEL_STRENGTH", "0.88")),
            coherence_floor=float(os.getenv("VLF_COHERENCE_FLOOR", "0.18")),
            transient_freeze_ratio=float(
                os.getenv("VLF_TRANSIENT_FREEZE_RATIO", "3.8")
            ),
            mp3_bitrate=os.getenv("VLF_MP3_BITRATE", "64k"),
            max_listeners=int(os.getenv("VLF_MAX_LISTENERS", "12")),
            mock_mode=_as_bool("VLF_MOCK_MODE"),
            allowed_origins=origins or ("*",),
        )
