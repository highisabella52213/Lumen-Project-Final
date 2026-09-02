"""Uvicorn WebSocket data-plane tuned for bulk VLESS/WS transfers.

Inbound parsing, masking checks, close/ping handling and protocol state stay on
Uvicorn's supported Sans-I/O ``websockets`` engine. The only outbound shortcut
is an RFC 6455 server-binary header followed by the existing payload object when
compression is disabled; this removes a full multi-MiB BytesIO copy. Queue
watermarks, accepted-socket tuning and direct relay hooks remove the remaining
per-frame ASGI overhead while preserving bounded backpressure.

The implementation is pinned to Uvicorn 0.52.4 in requirements.txt.  If this
module cannot be imported, main.py falls back to Uvicorn's stock protocol.
"""

from __future__ import annotations

import asyncio
import os
import socket
import struct
from typing import Any

from uvicorn.protocols.utils import ClientDisconnected
from uvicorn.protocols.websockets.websockets_sansio_impl import (
    WebSocketsSansIOProtocol,
)


def _env_int(name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


# A stock Uvicorn Sans-I/O connection pauses transport reading after *every*
# complete message. Xray sends many binary messages while downloading/uploading;
# pause/resume on each one becomes an avoidable syscall/event-loop bottleneck.
RX_QUEUE_HIGH = _env_int("WS_TURBO_QUEUE_HIGH", 256, 8, 2048)
RX_QUEUE_LOW = _env_int("WS_TURBO_QUEUE_LOW", 64, 1, RX_QUEUE_HIGH - 1)
RX_QUEUE_BYTES_HIGH = _env_int(
    "WS_TURBO_QUEUE_BYTES_HIGH", 64 * 1024 * 1024, 4 * 1024 * 1024, 512 * 1024 * 1024
)
RX_QUEUE_BYTES_LOW = min(
    _env_int("WS_TURBO_QUEUE_BYTES_LOW", 16 * 1024 * 1024, 1024 * 1024, 128 * 1024 * 1024),
    RX_QUEUE_BYTES_HIGH // 2,
)

SOCKET_BUFFER = _env_int(
    "WS_TURBO_SOCKET_BUFFER", 32 * 1024 * 1024, 256 * 1024, 128 * 1024 * 1024
)
WRITE_BUFFER_HIGH = _env_int(
    "WS_TURBO_WRITE_HIGH", 16 * 1024 * 1024, 256 * 1024, 64 * 1024 * 1024
)
WRITE_BUFFER_LOW = min(
    _env_int("WS_TURBO_WRITE_LOW", 2 * 1024 * 1024, 64 * 1024, 16 * 1024 * 1024),
    WRITE_BUFFER_HIGH // 2,
)
PREFERRED_CC = (b"bbr", b"cubic")


def _tune_accepted_socket(transport: asyncio.Transport) -> None:
    """Tune the actual accepted client socket, not merely the listen socket."""
    try:
        transport.set_write_buffer_limits(high=WRITE_BUFFER_HIGH, low=WRITE_BUFFER_LOW)
    except Exception:
        pass

    try:
        sock = transport.get_extra_info("socket")
    except Exception:
        sock = None
    if sock is None:
        return

    for level, option, value in (
        (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
        (socket.SOL_SOCKET, socket.SO_SNDBUF, SOCKET_BUFFER),
        (socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_BUFFER),
    ):
        try:
            sock.setsockopt(level, option, value)
        except OSError:
            pass

    quickack = getattr(socket, "TCP_QUICKACK", None)
    if quickack is not None:
        try:
            sock.setsockopt(socket.IPPROTO_TCP, quickack, 1)
        except OSError:
            pass

    congestion = getattr(socket, "TCP_CONGESTION", None)
    if congestion is not None:
        for algorithm in PREFERRED_CC:
            try:
                sock.setsockopt(socket.IPPROTO_TCP, congestion, algorithm)
                break
            except OSError:
                continue

    # Low-delay DSCP hint; unsupported/container-restricted kernels simply ignore it.
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)
    except OSError:
        pass
    ipv6_tclass = getattr(socket, "IPV6_TCLASS", None)
    if ipv6_tclass is not None:
        try:
            sock.setsockopt(socket.IPPROTO_IPV6, ipv6_tclass, 0x10)
        except OSError:
            pass


def _binary_header(length: int) -> bytes:
    """RFC 6455 FIN+binary header for an unmasked server frame."""
    if length < 126:
        return bytes((0x82, length))
    if length < 65536:
        return struct.pack("!BBH", 0x82, 126, length)
    return struct.pack("!BBQ", 0x82, 127, length)


class TurboWebSocketsSansIOProtocol(WebSocketsSansIOProtocol):
    """Sans-I/O WebSocket protocol with bulk-transfer queueing and fast I/O hooks."""

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        super().connection_made(transport)
        self._turbo_queue_bytes = 0
        _tune_accepted_socket(self.transport)

    def send_receive_event_to_app(self) -> None:
        """Queue bursts and pause only at a real high-water mark.

        Uvicorn 0.52.4's stock implementation pauses socket reading for every
        individual message. Here, up to ``RX_QUEUE_HIGH`` complete messages may
        be queued. This preserves bounded backpressure while removing thousands
        of pause/resume transitions during a large transfer.
        """
        data = self.frames[0] if len(self.frames) == 1 else b"".join(self.frames)
        self.frames = []

        if self.close_sent:
            return

        if self.curr_msg_data_type == "text":
            try:
                message = {"type": "websocket.receive", "text": data.decode()}
            except UnicodeDecodeError:
                self.logger.exception("Invalid UTF-8 sequence received from client.")
                self.conn.send_close(1007)
                self.handle_parser_exception()
                return
        else:
            # Keep the single-frame object unchanged. websockets/Uvicorn 0.50+
            # specifically avoids copying this payload.
            message = {"type": "websocket.receive", "bytes": data}

        self.queue.put_nowait(message)  # type: ignore[arg-type]
        self._turbo_queue_bytes = getattr(self, "_turbo_queue_bytes", 0) + len(data)
        if not self.read_paused and (
            self.queue.qsize() >= RX_QUEUE_HIGH
            or self._turbo_queue_bytes >= RX_QUEUE_BYTES_HIGH
        ):
            self.read_paused = True
            self.transport.pause_reading()

    def _after_receive(self, message):
        payload = message.get("bytes")
        if payload is None:
            payload = message.get("text") or ""
        self._turbo_queue_bytes = max(
            0, getattr(self, "_turbo_queue_bytes", 0) - len(payload)
        )
        if self.read_paused and (
            self.queue.qsize() <= RX_QUEUE_LOW
            and self._turbo_queue_bytes <= RX_QUEUE_BYTES_LOW
        ):
            self.read_paused = False
            self.transport.resume_reading()
        return message

    async def receive(self):
        return self._after_receive(await self.queue.get())

    async def turbo_receive(self):
        """Direct receive hook used by relay_vless after Starlette accepted WS."""
        return await self.receive()

    def turbo_receive_nowait(self):
        """Take another queued frame without a coroutine/await in upload bursts."""
        try:
            message = self.queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
        return self._after_receive(message)

    async def turbo_send_bytes(self, data: bytes | bytearray | memoryview) -> None:
        """Send an uncompressed server binary frame without copying its payload.

        Uvicorn/websockets normally serializes the entire frame through BytesIO,
        which duplicates every multi-MiB download chunk. Compression is disabled
        in main.py, so a legal server frame is just a small unmasked header followed
        by the existing payload object. There is no await between the two writes,
        therefore ping/close frames cannot interleave with this frame.
        """
        if not self.writable.is_set():
            await self.writable.wait()
        if (
            self.disconnected
            or self.close_sent
            or not self.handshake_complete
            or self.transport.is_closing()
        ):
            raise ClientDisconnected()

        # Safety fallback if someone later enables per-message compression.
        if self.config.ws_per_message_deflate:
            await self.send({"type": "websocket.send", "bytes": bytes(data)})
            return

        self.transport.write(_binary_header(len(data)))
        self.transport.write(data)

    async def turbo_flush(self) -> None:
        """Wait until transport backpressure has dropped below its low watermark."""
        if not self.writable.is_set() and not self.disconnected:
            await self.writable.wait()


__all__ = ["TurboWebSocketsSansIOProtocol"]
