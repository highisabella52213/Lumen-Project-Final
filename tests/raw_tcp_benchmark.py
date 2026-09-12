#!/usr/bin/env python3
"""Controlled loopback benchmark for the native TLS VLESS Raw TCP listener.

This is deliberately a local transport benchmark, not a Railway performance
claim.  It uses the same 1 MiB payload for each client at 1/10/50/100
concurrency and reports handshake-plus-transfer latency, aggregate duplex
throughput, process CPU, RSS, file descriptors, and asyncio task cleanup.
"""
from __future__ import annotations

import asyncio
import json
import os
import resource
import socket
import ssl
import statistics
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PAYLOAD_MIB = int(sys.argv[1]) if len(sys.argv) > 1 else 1
PAYLOAD_SIZE = PAYLOAD_MIB * 1024 * 1024


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def rss_kib() -> int:
    # Linux ru_maxrss is KiB.  It is intentionally reported as a high-water
    # mark, not misrepresented as per-connection retained memory.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss


def fd_count() -> int:
    return len(list(Path("/proc/self/fd").iterdir()))


TMP = tempfile.TemporaryDirectory(prefix="lumen-raw-benchmark-")
WORK = Path(TMP.name)
PORT = free_port()
CERT, KEY = WORK / "cert.pem", WORK / "key.pem"
subprocess.run(
    [
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
        "-subj", "/CN=tcp.test", "-addext", "subjectAltName=DNS:tcp.test",
        "-keyout", str(KEY), "-out", str(CERT),
    ],
    check=True,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
os.environ.update(
    {
        "DATA_DIR": str(WORK / "state"),
        "RAILWAY_TCP_APPLICATION_PORT": str(PORT),
        "RAILWAY_TCP_PROXY_DOMAIN": "127.0.0.1",
        "RAILWAY_TCP_PROXY_PORT": str(PORT),
        "VLESS_TCP_LISTEN_HOST": "127.0.0.1",
        "VLESS_TCP_LISTEN_PORT": str(PORT),
        "VLESS_TCP_TLS_CERT_FILE": str(CERT),
        "VLESS_TCP_TLS_KEY_FILE": str(KEY),
        "VLESS_TCP_URI_NETWORK": "tcp",
        "VLESS_TCP_DEFAULT_SNI": "tcp.test",
        "VLESS_TCP_SNI_MAP": json.dumps({"tcp.test": ""}),
        "VLESS_TCP_MAX_CONNECTIONS": "128",
    }
)

import main  # noqa: E402
from raw_tcp import RAW_TCP_LISTENER  # noqa: E402


def vless_header(uid: str, port: int) -> bytes:
    return (
        b"\x00" + uuid.UUID(uid).bytes + b"\x00\x01" + port.to_bytes(2, "big")
        + b"\x01\x7f\x00\x00\x01"
    )


async def echo_server() -> tuple[asyncio.AbstractServer, int]:
    async def echo(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            while data := await reader.read(1024 * 1024):
                writer.write(data)
                if writer.transport.get_write_buffer_size() >= 8 * 1024 * 1024:
                    await writer.drain()
        except (ConnectionError, asyncio.CancelledError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(echo, "127.0.0.1", 0, limit=16 * 1024 * 1024)
    return server, server.sockets[0].getsockname()[1]


async def client(uid: str, target_port: int, token: int) -> float:
    tls = ssl.create_default_context(cafile=str(CERT))
    started = time.perf_counter()
    reader, writer = await asyncio.open_connection(
        "127.0.0.1", PORT, ssl=tls, server_hostname="tcp.test",
        limit=16 * 1024 * 1024,
    )
    payload = bytes((token,)) * min(256 * 1024, PAYLOAD_SIZE)

    async def upload() -> None:
        writer.write(vless_header(uid, target_port))
        remaining = PAYLOAD_SIZE
        while remaining:
            chunk = payload if remaining >= len(payload) else payload[:remaining]
            writer.write(chunk)
            remaining -= len(chunk)
            if writer.transport.get_write_buffer_size() >= 8 * 1024 * 1024:
                await writer.drain()
        await writer.drain()

    async def download() -> None:
        assert await reader.readexactly(2) == b"\x00\x00"
        remaining = PAYLOAD_SIZE
        while remaining:
            data = await reader.read(min(1024 * 1024, remaining))
            if not data:
                raise AssertionError(f"short echo: {remaining} bytes left")
            assert data == bytes((token,)) * len(data)
            remaining -= len(data)

    try:
        await asyncio.wait_for(asyncio.gather(upload(), download()), timeout=30)
        return (time.perf_counter() - started) * 1000
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


def quantile(values: list[float], value: float) -> float:
    return values[min(len(values) - 1, int(len(values) * value))]


async def wait_for_cleanup(timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while main.connections or RAW_TCP_LISTENER._tasks:
        if time.monotonic() >= deadline:
            raise AssertionError(
                f"unclean raw sessions={main.connections} "
                f"listener_tasks={RAW_TCP_LISTENER._tasks}"
            )
        await asyncio.sleep(0.025)


async def run() -> None:
    target, target_port = await echo_server()
    await RAW_TCP_LISTENER.start()
    assert RAW_TCP_LISTENER.running, RAW_TCP_LISTENER.error
    uid, _link = await main.make_link(label="benchmark", protocol="vless-tcp")
    try:
        # Warm bytecode, sockets, TLS and local route caches before sampling.
        await client(uid, target_port, 1)
        for count in (1, 10, 50, 100):
            rss_before, fds_before = rss_kib(), fd_count()
            cpu_before = sum(resource.getrusage(resource.RUSAGE_SELF)[0:2])
            started = time.perf_counter()
            latencies = await asyncio.gather(
                *(client(uid, target_port, index % 251 + 1) for index in range(count))
            )
            elapsed = time.perf_counter() - started
            cpu_elapsed = sum(resource.getrusage(resource.RUSAGE_SELF)[0:2]) - cpu_before
            latencies.sort()
            await wait_for_cleanup()
            assert not main.error_logs, main.error_logs
            assert fd_count() <= fds_before + 1, (fds_before, fd_count())
            throughput = (count * PAYLOAD_SIZE * 2 / 1024 / 1024) / elapsed
            print(
                f"raw tcp {count}x{PAYLOAD_MIB}MiB: success={len(latencies)}/{count} "
                f"p50={statistics.median(latencies):.2f}ms p95={quantile(latencies, .95):.2f}ms "
                f"duplex={throughput:.1f}MiB/s cpu={cpu_elapsed / count * 1000:.2f}ms/conn "
                f"rss-high-water={rss_kib()}KiB (+{rss_kib() - rss_before}) "
                f"fd={fds_before}->{fd_count()} tasks={len(asyncio.all_tasks()) - 1}"
            )
    finally:
        await RAW_TCP_LISTENER.stop()
        target.close()
        await target.wait_closed()


try:
    asyncio.run(run())
finally:
    TMP.cleanup()