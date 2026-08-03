from __future__ import annotations

import asyncio
import queue
import subprocess
import threading
from collections.abc import AsyncIterator

import numpy as np


class ListenerLimitReached(RuntimeError):
    pass


class BroadcastHub:
    def __init__(self, max_listeners: int) -> None:
        self.max_listeners = max_listeners
        self._loop: asyncio.AbstractEventLoop | None = None
        self._clients: set[asyncio.Queue[bytes]] = set()

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    @property
    def listener_count(self) -> int:
        return len(self._clients)

    def subscribe(self) -> asyncio.Queue[bytes]:
        if len(self._clients) >= self.max_listeners:
            raise ListenerLimitReached
        client: asyncio.Queue[bytes] = asyncio.Queue(maxsize=96)
        self._clients.add(client)
        return client

    async def stream(self, client: asyncio.Queue[bytes]) -> AsyncIterator[bytes]:
        try:
            while True:
                yield await client.get()
                await asyncio.sleep(0)
        finally:
            self._clients.discard(client)

    def publish_threadsafe(self, chunk: bytes) -> None:
        if self._loop and not self._loop.is_closed():
            self._loop.call_soon_threadsafe(self._publish, chunk)

    def _publish(self, chunk: bytes) -> None:
        for client in tuple(self._clients):
            if client.full():
                try:
                    client.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                client.put_nowait(chunk)
            except asyncio.QueueFull:
                pass


class MP3Encoder:
    def __init__(
        self,
        hub: BroadcastHub,
        sample_rate: int,
        bitrate: str,
        name: str,
    ) -> None:
        self.hub = hub
        self.sample_rate = sample_rate
        self.bitrate = bitrate
        self.name = name
        self.process: subprocess.Popen[bytes] | None = None
        self.reader: threading.Thread | None = None
        self.stderr_reader: threading.Thread | None = None
        self.last_error: str | None = None
        self._write_lock = threading.Lock()

    def start(self) -> None:
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "warning",
            "-f",
            "f32le",
            "-ar",
            str(self.sample_rate),
            "-ac",
            "1",
            "-channel_layout",
            "mono",
            "-i",
            "pipe:0",
            "-vn",
            "-ar",
            str(min(self.sample_rate, 48_000)),
            "-c:a",
            "libmp3lame",
            "-b:a",
            self.bitrate,
            "-write_xing",
            "0",
            "-f",
            "mp3",
            "pipe:1",
        ]
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        self.reader = threading.Thread(
            target=self._read_output, name=f"{self.name}-mp3-reader", daemon=True
        )
        self.stderr_reader = threading.Thread(
            target=self._read_errors, name=f"{self.name}-ffmpeg-log", daemon=True
        )
        self.reader.start()
        self.stderr_reader.start()

    def write(self, samples: np.ndarray) -> None:
        # Leave each encoder idle until somebody requests its stream.
        # The capture/DSP pipeline keeps running, so a new listener still gets
        # fresh audio immediately without paying for two always-on encoders.
        if self.hub.listener_count == 0:
            return
        if not self.process or not self.process.stdin:
            return
        payload = np.asarray(samples, dtype="<f4").tobytes()
        try:
            with self._write_lock:
                self.process.stdin.write(payload)
        except (BrokenPipeError, OSError) as exc:
            self.last_error = f"{self.name} encoder pipe: {exc}"

    def _read_output(self) -> None:
        if not self.process or not self.process.stdout:
            return
        while True:
            chunk = self.process.stdout.read(4096)
            if not chunk:
                return
            self.hub.publish_threadsafe(chunk)

    def _read_errors(self) -> None:
        if not self.process or not self.process.stderr:
            return
        for line in iter(self.process.stderr.readline, b""):
            text = line.decode("utf-8", errors="replace").strip()
            if text:
                self.last_error = text[-500:]

    def stop(self) -> None:
        if not self.process:
            return
        try:
            if self.process.stdin:
                self.process.stdin.close()
            self.process.terminate()
            self.process.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            self.process.kill()
        self.process = None
