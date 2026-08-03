import numpy as np

from vlf_stream.streaming import BroadcastHub, MP3Encoder


class _Sink:
    def __init__(self) -> None:
        self.payloads: list[bytes] = []

    def write(self, payload: bytes) -> None:
        self.payloads.append(payload)


class _Process:
    def __init__(self, sink: _Sink) -> None:
        self.stdin = sink


def test_encoder_stays_idle_without_listeners() -> None:
    hub = BroadcastHub(max_listeners=2)
    encoder = MP3Encoder(hub, sample_rate=48_000, bitrate="64k", name="test")
    sink = _Sink()
    encoder.process = _Process(sink)  # type: ignore[assignment]
    samples = np.zeros(512, dtype=np.float32)

    encoder.write(samples)
    assert sink.payloads == []

    hub.subscribe()
    encoder.write(samples)
    assert len(sink.payloads) == 1
    assert len(sink.payloads[0]) == samples.size * 4
