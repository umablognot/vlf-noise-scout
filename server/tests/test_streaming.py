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


def test_encoder_feeds_pipe_without_listeners() -> None:
    hub = BroadcastHub(max_listeners=2)
    encoder = MP3Encoder(hub, sample_rate=48_000, bitrate="64k", name="test")
    sink = _Sink()
    encoder.process = _Process(sink)  # type: ignore[assignment]
    samples = np.zeros(512, dtype=np.float32)

    encoder.write(samples)
    assert len(sink.payloads) == 1
    assert len(sink.payloads[0]) == samples.size * 4


def test_subscribe_replays_backlog_burst() -> None:
    hub = BroadcastHub(max_listeners=2, burst_bytes=8)
    hub._publish(b"aaaa")
    hub._publish(b"bbbb")
    hub._publish(b"cccc")  # evicts "aaaa" (backlog cap 8 bytes)

    client = hub.subscribe()
    assert client.get_nowait() == b"bbbb"
    assert client.get_nowait() == b"cccc"
    assert client.empty()

    hub._publish(b"dddd")
    assert client.get_nowait() == b"dddd"
