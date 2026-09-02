#!/usr/bin/env python3
"""Real-socket WS/VLESS correctness and stress test without third-party packages.

It implements only the small RFC 6455 subset required by this test. Both the
client <-> WS gateway and gateway <-> echo target are real loopback TCP sockets.
Usage:
    python tests/ws_hyper_stress.py [project-root] [clients] [MiB-per-client]
"""

from __future__ import annotations

import asyncio
import base64
import collections
import hashlib
import logging
import os
import struct
import sys
import time
import types
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1])
CLIENTS = int(sys.argv[2]) if len(sys.argv) > 2 else 16
MIB_PER_CLIENT = int(sys.argv[3]) if len(sys.argv) > 3 else 8
UID = "11111111-2222-3333-4444-555555555555"
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

# Project stubs: the relay is tested unchanged, while panel dependencies aren't needed.
fastapi = types.ModuleType("fastapi")
class WebSocketDisconnect(Exception):
    def __init__(self, code=1000): self.code = code
class WebSocket: pass
fastapi.WebSocket = WebSocket
fastapi.WebSocketDisconnect = WebSocketDisconnect
sys.modules["fastapi"] = fastapi

main_stub = types.ModuleType("main")
main_stub.LINKS = {UID: {
    "label": "stress", "used_bytes": 0, "limit_bytes": 0,
    "speed_limit_bytes": 0, "active": True,
}}
main_stub.LINKS_LOCK = asyncio.Lock()
main_stub.stats = collections.defaultdict(int)
main_stub.hourly_traffic = collections.defaultdict(int)
main_stub.connections = {}
main_stub.error_logs = []
main_stub.logger = logging.getLogger("ws-stress")
main_stub.is_link_allowed = lambda link: bool(link and link.get("active", True))
main_stub.is_ip_allowed = lambda *args: True
async def _save(): pass
main_stub.save_state = _save
main_stub.log_activity = lambda *args, **kwargs: None
import datetime as _datetime
main_stub.now_ir = _datetime.datetime.now
sys.modules["main"] = main_stub
sys.path.insert(0, str(ROOT))

import relay_vless as relay  # noqa: E402


def ws_header(length: int, masked: bool, opcode: int = 2) -> bytes:
    second = 0x80 if masked else 0
    if length < 126:
        return bytes((0x80 | opcode, second | length))
    if length < 65536:
        return bytes((0x80 | opcode, second | 126)) + struct.pack("!H", length)
    return bytes((0x80 | opcode, second | 127)) + struct.pack("!Q", length)


async def read_ws_frame(reader: asyncio.StreamReader):
    first, second = await reader.readexactly(2)
    opcode = first & 0x0F
    masked = bool(second & 0x80)
    length = second & 0x7F
    if length == 126:
        length = struct.unpack("!H", await reader.readexactly(2))[0]
    elif length == 127:
        length = struct.unpack("!Q", await reader.readexactly(8))[0]
    mask = await reader.readexactly(4) if masked else b""
    payload = await reader.readexactly(length)
    if masked and mask != b"\0\0\0\0":
        data = bytearray(payload)
        for index in range(length):
            data[index] ^= mask[index & 3]
        payload = bytes(data)
    return opcode, payload


class NetworkWebSocket:
    def __init__(self, reader, writer, headers):
        self.reader = reader
        self.writer = writer
        self.headers = headers
        peer = writer.get_extra_info("peername") or ("127.0.0.1", 0)
        self.client = types.SimpleNamespace(host=peer[0])
        self.scope = {}
        self.accepted = False
        self.closed = False

    async def accept(self, subprotocol=None):
        key = self.headers["sec-websocket-key"]
        accept = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
        lines = [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Accept: {accept}",
        ]
        if subprotocol:
            lines.append(f"Sec-WebSocket-Protocol: {subprotocol}")
        self.writer.write(("\r\n".join(lines) + "\r\n\r\n").encode())
        await self.writer.drain()
        self.accepted = True

    async def receive(self):
        try:
            while True:
                opcode, payload = await read_ws_frame(self.reader)
                if opcode == 2:
                    return {"type": "websocket.receive", "bytes": payload}
                if opcode == 8:
                    return {"type": "websocket.disconnect", "code": 1000}
                if opcode == 9:
                    self.writer.write(ws_header(len(payload), False, 10))
                    self.writer.write(payload)
                    await self.writer.drain()
        except (asyncio.IncompleteReadError, ConnectionError):
            return {"type": "websocket.disconnect", "code": 1006}

    async def send_bytes(self, payload):
        self.writer.write(ws_header(len(payload), False, 2))
        self.writer.write(payload)
        if self.writer.transport.get_write_buffer_size() >= 8 * 1024 * 1024:
            await self.writer.drain()

    async def close(self, code=1000, reason=""):
        if self.closed:
            return
        self.closed = True
        payload = struct.pack("!H", code) + reason.encode()
        try:
            self.writer.write(ws_header(len(payload), False, 8))
            self.writer.write(payload)
            await self.writer.drain()
        except Exception:
            pass


def vless_header(port: int, payload=b"") -> bytes:
    return (
        b"\0" + bytes(16) + b"\0" + b"\1" + port.to_bytes(2, "big")
        + b"\1\x7f\0\0\1" + payload
    )


async def echo_server():
    async def echo(reader, writer):
        try:
            while data := await reader.read(2 * 1024 * 1024):
                writer.write(data)
                if writer.transport.get_write_buffer_size() >= 8 * 1024 * 1024:
                    await writer.drain()
            await writer.drain()
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            writer.close()
            try: await writer.wait_closed()
            except Exception: pass
    server = await asyncio.start_server(echo, "127.0.0.1", 0, limit=16 * 1024 * 1024)
    return server, server.sockets[0].getsockname()[1]


async def gateway_server():
    async def gateway(reader, writer):
        try:
            request = await reader.readuntil(b"\r\n\r\n")
            lines = request.decode("latin-1").split("\r\n")
            path = lines[0].split()[1]
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()
            uid = path.split("/ws/", 1)[1].split("?", 1)[0]
            ws = NetworkWebSocket(reader, writer, headers)
            await relay.websocket_tunnel(ws, uid)
        except Exception as exc:
            main_stub.error_logs.append({"gateway": repr(exc)})
        finally:
            writer.close()
            try: await writer.wait_closed()
            except Exception: pass
    server = await asyncio.start_server(gateway, "127.0.0.1", 0, limit=16 * 1024 * 1024)
    return server, server.sockets[0].getsockname()[1]


async def handshake(port: int, early: bytes = b""):
    reader, writer = await asyncio.open_connection("127.0.0.1", port, limit=16 * 1024 * 1024)
    key = base64.b64encode(os.urandom(16)).decode()
    request = [
        f"GET /ws/{UID}?ed=4096 HTTP/1.1",
        f"Host: 127.0.0.1:{port}",
        "Upgrade: websocket",
        "Connection: Upgrade",
        f"Sec-WebSocket-Key: {key}",
        "Sec-WebSocket-Version: 13",
    ]
    if early:
        request.append("Sec-WebSocket-Protocol: " + base64.urlsafe_b64encode(early).decode().rstrip("="))
    writer.write(("\r\n".join(request) + "\r\n\r\n").encode())
    await writer.drain()
    response = await reader.readuntil(b"\r\n\r\n")
    assert response.startswith(b"HTTP/1.1 101"), response[:100]
    return reader, writer


async def client_case(gateway_port: int, target_port: int, size: int, token: int, mode="normal"):
    prefix = b"seed-" + bytes((token,))
    header = vless_header(target_port, prefix)
    reader, writer = await handshake(gateway_port, header if mode == "early" else b"")
    if mode != "early":
        if mode == "split":
            for part in (header[:7], header[7:19], header[19:]):
                writer.write(ws_header(len(part), True) + b"\0\0\0\0" + part)
        else:
            writer.write(ws_header(len(header), True) + b"\0\0\0\0" + header)

    chunk = bytes((token,)) * (256 * 1024)
    expected = len(prefix) + size

    async def upload():
        remaining = size
        while remaining:
            payload = chunk if remaining >= len(chunk) else chunk[:remaining]
            writer.write(ws_header(len(payload), True))
            writer.write(b"\0\0\0\0")
            writer.write(payload)
            remaining -= len(payload)
            if writer.transport.get_write_buffer_size() >= 8 * 1024 * 1024:
                await writer.drain()
        await writer.drain()

    async def download():
        opcode, response_header = await read_ws_frame(reader)
        assert opcode == 2 and response_header == b"\0\0"
        received = 0
        prefix_left = prefix
        while received < expected:
            opcode, payload = await read_ws_frame(reader)
            assert opcode == 2
            if prefix_left:
                take = min(len(prefix_left), len(payload))
                assert payload[:take] == prefix_left[:take]
                prefix_left = prefix_left[take:]
                payload = payload[take:]
            if payload:
                assert payload == bytes((token,)) * len(payload)
            received += len(payload) + (take if 'take' in locals() else 0)
            if 'take' in locals(): del take
        return received

    await asyncio.gather(upload(), download())
    writer.write(ws_header(2, True, 8) + b"\0\0\0\0" + b"\x03\xe8")
    await writer.drain()
    writer.close()
    try: await writer.wait_closed()
    except Exception: pass
    return expected


async def correctness(gateway_port, target_port):
    for index, mode in enumerate(("normal", "split", "early"), 1):
        got = await asyncio.wait_for(
            client_case(gateway_port, target_port, 1024 * 1024, index, mode),
            timeout=20,
        )
        print(f"correctness {mode:6}: {got} bytes OK")


async def stress(gateway_port, target_port):
    size = MIB_PER_CLIENT * 1024 * 1024
    start = time.perf_counter()
    totals = await asyncio.wait_for(
        asyncio.gather(*[
            client_case(gateway_port, target_port, size, (index % 250) + 1)
            for index in range(CLIENTS)
        ]),
        timeout=max(60, CLIENTS * MIB_PER_CLIENT * 2),
    )
    elapsed = time.perf_counter() - start
    total_mib = sum(totals) / (1024 * 1024)
    print(
        f"stress {CLIENTS}x{MIB_PER_CLIENT}MiB: {total_mib:.1f} MiB round-trip "
        f"in {elapsed:.3f}s = {total_mib / elapsed:.1f} MiB/s each way"
    )
    return total_mib / elapsed


async def main():
    target, target_port = await echo_server()
    gateway, gateway_port = await gateway_server()
    try:
        await correctness(gateway_port, target_port)
        speed = await stress(gateway_port, target_port)
        await asyncio.sleep(0.1)
        assert not main_stub.connections, main_stub.connections
        assert not main_stub.error_logs, main_stub.error_logs
        print(
            f"final: speed={speed:.1f} MiB/s, active={len(main_stub.connections)}, "
            f"errors={len(main_stub.error_logs)}, used={main_stub.LINKS[UID]['used_bytes']}"
        )
    finally:
        gateway.close(); target.close()
        await gateway.wait_closed(); await target.wait_closed()


if __name__ == "__main__":
    asyncio.run(main())
