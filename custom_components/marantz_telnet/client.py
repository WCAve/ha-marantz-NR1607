"""Async push client for the Denon/Marantz telnet protocol (port 23)."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
import logging
import time
from typing import Any

from .const import (
    FAST_POLL_INTERVAL,
    FAST_QUERIES,
    FULL_POLL_INTERVAL,
    IDENTITY_QUERIES,
    MODE_QUERIES,
    NET_SOURCES,
    STATE_QUERIES,
)
from .protocol import parse_line

_LOGGER = logging.getLogger(__name__)

# Commands that make the receiver busy for a moment; anything sent right after is dropped.
_SLOW_PREFIXES = ("SI", "PW", "ZM", "MS")
_MODE_KEYS = {"SI", "MS", "SD", "PW", "ZM"}

Listener = Callable[[str], None]


class AVRClient:
    """Keeps one telnet connection open and mirrors the receiver state."""

    def __init__(self, host: str, port: int = 23) -> None:
        self.host = host
        self.port = port
        self.state: dict[str, str] = {}
        self.connected = False
        self._listeners: dict[str, list[Listener]] = defaultdict(list)
        self._new_key_listeners: list[Listener] = []
        self._conn_listeners: list[Listener] = []
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._task: asyncio.Task | None = None
        self._closing = False
        self._last_rx = 0.0
        self._followup: asyncio.TimerHandle | None = None

    # ----------------------------------------------------------------- lifecycle
    def start(
        self, create_task: Callable[[Coroutine[Any, Any, None]], asyncio.Task] | None = None
    ) -> None:
        """Start the connection loop."""
        self._closing = False
        coro = self._run()
        self._task = create_task(coro) if create_task else asyncio.create_task(coro)

    async def stop(self) -> None:
        """Close the connection and stop reconnecting."""
        self._closing = True
        if self._followup:
            self._followup.cancel()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._task = None
        self._set_connected(False)

    async def wait_for(self, keys: list[str], timeout: float) -> bool:
        """Wait until all keys are known (or timeout)."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if all(k in self.state for k in keys):
                return True
            await asyncio.sleep(0.1)
        return all(k in self.state for k in keys)

    # ----------------------------------------------------------------- listeners
    def add_listener(self, key: str, cb: Listener) -> Callable[[], None]:
        self._listeners[key].append(cb)
        return lambda: self._listeners[key].remove(cb)

    def add_new_key_listener(self, cb: Listener) -> Callable[[], None]:
        self._new_key_listeners.append(cb)
        return lambda: self._new_key_listeners.remove(cb)

    def add_connection_listener(self, cb: Listener) -> Callable[[], None]:
        self._conn_listeners.append(cb)
        return lambda: self._conn_listeners.remove(cb)

    # ----------------------------------------------------------------- commands
    def send(self, command: str) -> None:
        """Queue a raw command (without the trailing CR)."""
        if not self.connected:
            raise ConnectionError(f"Not connected to {self.host}")
        self._queue.put_nowait(command.strip())

    def send_many(self, commands: list[str]) -> None:
        if self._queue.qsize() > 300:  # receiver gone quiet; don't grow forever
            return
        seen: set[str] = set()
        for cmd in commands:
            if cmd not in seen:
                seen.add(cmd)
                self._queue.put_nowait(cmd)

    def poll(self, full: bool = False) -> None:
        cmds = [*IDENTITY_QUERIES, *STATE_QUERIES, *FAST_QUERIES] if full else list(FAST_QUERIES)
        cmds += self._context_queries()
        self.send_many(cmds)

    def _context_queries(self) -> list[str]:
        src = self.state.get("SI", "")
        if src == "TUNER":
            return ["TFAN?", "TPAN?", "TMAN?"]
        if src in NET_SOURCES:
            return ["NSE"]
        return []

    # ----------------------------------------------------------------- internals
    def _set_connected(self, value: bool) -> None:
        if self.connected == value:
            return
        self.connected = value
        for cb in list(self._conn_listeners):
            cb("")

    def _set(self, key: str, value: str) -> None:
        new = key not in self.state
        if not new and self.state[key] == value:
            return
        self.state[key] = value
        if new:
            for cb in list(self._new_key_listeners):
                cb(key)
        for cb in list(self._listeners.get(key, ())) + list(self._listeners.get("*", ())):
            cb(key)
        if not new and key in _MODE_KEYS:
            self._schedule_followup()

    def _schedule_followup(self) -> None:
        if self._followup:
            self._followup.cancel()
        loop = asyncio.get_running_loop()
        self._followup = loop.call_later(
            3, lambda: self.send_many([*MODE_QUERIES, *self._context_queries()])
        )

    def handle_line(self, line: str) -> None:
        """Process one line received from the receiver."""
        parsed = parse_line(line)
        if parsed is None:
            return
        key, value = parsed
        if key == "UNKNOWN":
            _LOGGER.debug("Unrecognized message from %s: %r", self.host, line)
        self._set("LAST", line.strip())
        self._set(key, value)

    async def _run(self) -> None:
        backoff = 5
        while not self._closing:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), 10
                )
            except (OSError, asyncio.TimeoutError) as err:
                _LOGGER.debug("Connect to %s:%s failed: %s", self.host, self.port, err)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
                continue
            backoff = 5
            _LOGGER.info("Connected to %s:%s", self.host, self.port)
            self._queue = asyncio.Queue()
            self._last_rx = time.monotonic()
            self._set_connected(True)
            self.poll(full=True)
            tasks = [
                asyncio.create_task(self._read_loop(reader)),
                asyncio.create_task(self._write_loop(writer)),
                asyncio.create_task(self._poll_loop()),
            ]
            try:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    if not task.cancelled() and (exc := task.exception()):
                        _LOGGER.warning("Connection to %s lost: %s", self.host, exc)
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), 2)
                except (OSError, asyncio.TimeoutError, asyncio.CancelledError):
                    pass
                self._set_connected(False)
            if not self._closing:
                await asyncio.sleep(5)

    async def _read_loop(self, reader: asyncio.StreamReader) -> None:
        buf = b""
        while True:
            data = await reader.read(4096)
            if not data:
                raise ConnectionError("connection closed by receiver")
            self._last_rx = time.monotonic()
            buf += data
            while b"\r" in buf:
                raw, buf = buf.split(b"\r", 1)
                self.handle_line(raw.decode("utf-8", "replace"))

    async def _write_loop(self, writer: asyncio.StreamWriter) -> None:
        while True:
            cmd = await self._queue.get()
            writer.write((cmd + "\r").encode("utf-8"))
            await writer.drain()
            slow = cmd[:2] in _SLOW_PREFIXES and "?" not in cmd and not cmd.startswith("MSSMART")
            await asyncio.sleep(1.2 if slow else 0.08)

    async def _poll_loop(self) -> None:
        last_full = time.monotonic()
        while True:
            await asyncio.sleep(FAST_POLL_INTERVAL)
            if time.monotonic() - self._last_rx > FAST_POLL_INTERVAL * 2 + 15:
                raise TimeoutError("receiver stopped responding")
            if time.monotonic() - last_full > FULL_POLL_INTERVAL:
                last_full = time.monotonic()
                self.poll(full=True)
            else:
                self.poll()


async def probe(host: str, port: int, timeout: float = 8) -> dict[str, str]:
    """Open a short connection and return identity info. Raises on failure."""
    reader, writer = await asyncio.wait_for(asyncio.open_connection(host, port), timeout)
    found: dict[str, str] = {}
    try:
        for cmd in ("PW?", "SYMO", "NSFRN ?"):
            writer.write((cmd + "\r").encode())
            await writer.drain()
            await asyncio.sleep(0.1)
        end = time.monotonic() + timeout
        buf = b""
        while time.monotonic() < end and not {"PW", "SYMO", "NSFRN"} <= found.keys():
            try:
                data = await asyncio.wait_for(reader.read(4096), max(0.1, end - time.monotonic()))
            except asyncio.TimeoutError:
                break
            if not data:
                break
            buf += data
            while b"\r" in buf:
                raw, buf = buf.split(b"\r", 1)
                if parsed := parse_line(raw.decode("utf-8", "replace")):
                    found[parsed[0]] = parsed[1]
    finally:
        writer.close()
    if "PW" not in found:
        raise ConnectionError("no response to PW?")
    return found
