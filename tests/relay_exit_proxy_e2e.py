#!/usr/bin/env python3
"""End-to-end: VLESS client -> WS relay -> managed proxy -> destination.

Proves the exit-IP contract on the real server stack:
- proxied configs reach the destination THROUGH the proxy (never directly);
- non-TLS payloads (e.g. DNS-over-TCP) use the tunnel too;
- a dead proxy fails the WebSocket instead of silently using the server IP;
- Multi-Location locations share one UUID/quota and never fail over.
"""
import asyncio
import os
import socket
import sys
import tempfile
import time
import uuid as uuidlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

_tmp = tempfile.mkdtemp(prefix="lumen-e2e-")
os.environ["DATA_DIR"] = _tmp
os.environ["PORT"] = "8899"
os.environ["ADMIN_PASSWORD"] = "e2e-test"

import uvicorn

import main
import outbound
import proxy_repository as repo

APP = "127.0.0.1"
BANNER = b"E2E-SERVER-HELLO"


async def pipe(r, w):
    try:
        while data := await r.read(65536):
            w.write(data)
            await w.drain()
    except Exception:
        pass
    try:
        w.close()
    except Exception:
        pass


def vless_header(uid: str, host: str, port: int) -> bytes:
    u = uuidlib.UUID(uid).bytes
    bare = host.strip("[]")
    try:
        packed = socket.inet_pton(socket.AF_INET, bare)
        addr = b"\x01" + packed
    except OSError:
        encoded = bare.encode("idna")
        addr = b"\x02" + bytes([len(encoded)]) + encoded
    return b"\x00" + u + b"\x00\x01" + port.to_bytes(2, "big") + addr


async def read_vless_response(ws, expect: bytes) -> bytes:
    """Skip the 2-byte VLESS response prefix, return the first data frame."""
    got_prefix = False
    for _ in range(8):
        data = await asyncio.wait_for(ws.recv(), 5)
        if isinstance(data, str):
            continue
        if not got_prefix and data[:2] == b"\x00\x00":
            got_prefix = True
            data = data[2:]
        if data:
            return data
    return b""


async def run():
    dest_hits = []

    async def destination(r, w):
        peer = r.transport.get_extra_info("peername") if hasattr(r, "transport") else None
        data = await r.read(1024)
        dest_hits.append((peer, data))
        w.write(BANNER)
        await w.drain()
        w.close()

    dest = await asyncio.start_server(destination, APP, 0)
    dest_port = dest.sockets[0].getsockname()[1]

    connect_log = []

    async def http_proxy(r, w):
        try:
            header = await r.readuntil(b"\r\n\r\n")
            connect_log.append(header.split(b"\r\n", 1)[0])
            ur, uw = await asyncio.open_connection(APP, dest_port)
            w.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await w.drain()
            await asyncio.gather(pipe(r, uw), pipe(ur, w))
        except Exception:
            w.close()

    proxy = await asyncio.start_server(http_proxy, APP, 0)
    proxy_port = proxy.sockets[0].getsockname()[1]

    rec = repo.Record("p1", f"http://{APP}:{proxy_port}", "http", "Germany", "DE", "🇩🇪", 95)
    repo._records = {rec.id: rec}
    repo._last = time.monotonic()
    repo._error = ""

    # Route 1: repository proxy. Route 2: dead proxy (reachable record, closed port).
    dead_rec = repo.Record("pd", "http://127.0.0.1:1", "http", "France", "FR", "🇫🇷", 10)
    repo._records = {rec.id: rec, dead_rec.id: dead_rec}
    uid_ok, _ = await main.make_link(label="proxied", exit_proxy_mode="repository", proxy_id=rec.id)
    uid_dead, _ = await main.make_link(label="dead", exit_proxy_mode="repository", proxy_id=dead_rec.id)

    # Multi-Location subgroup: dead location first, healthy second.
    sub_id, _sub = await main.create_sub_group(name="ml")
    await main.set_link_sub(uid_ok, sub_id)
    ml_value = await main.validate_multi_location({
        "enabled": True,
        "remark_text": "E2E",
        "locations": [
            {"id": "loc-dead", "code": "FR", "proxy_id": "pd", "active": True},
            {"id": "loc-de", "code": "DE", "proxy_id": "p1", "active": True},
        ],
    })
    assert ml_value["locations"][0]["country"] == "France" and ml_value["locations"][0]["flag"] == "🇫🇷"
    async with main.SUBS_LOCK:
        main.SUBS[sub_id]["multi_location"] = ml_value
    await main.save_state(strict=True)

    config = uvicorn.Config("main:app", host="127.0.0.1", port=8899, log_level="error", ws="auto")
    server = uvicorn.Server(config)
    task = asyncio.create_task(server.serve())
    for _ in range(100):
        if server.started:
            break
        await asyncio.sleep(0.05)
    assert server.started, "server did not start"

    import websockets

    # 1) proxied route reaches the destination through the proxy
    payload = b"PING-THROUGH-PROXY"
    async with websockets.connect(f"ws://127.0.0.1:8899/ws/{uid_ok}", max_size=2**22) as ws:
        await ws.send(vless_header(uid_ok, APP, dest_port) + payload)
        data = await read_vless_response(ws, BANNER)
        assert data == BANNER, f"expected banner, got {data!r}"
    assert connect_log and b"CONNECT 127.0.0.1:" in connect_log[-1], "proxy was not used"
    assert dest_hits and dest_hits[-1][1] == payload, "destination did not get payload"
    # fail-closed needs the dead-route check below; here the tunnel must exist
    assert b"CONNECT" in connect_log[-1]

    # 2) non-TLS payload through the proxy (the old code sent this DIRECT)
    dest_hits.clear(); connect_log.clear()
    plain = b"DNS-OVER-TCP-STYLE-PAYLOAD"
    async with websockets.connect(f"ws://127.0.0.1:8899/ws/{uid_ok}", max_size=2**22) as ws:
        await ws.send(vless_header(uid_ok, APP, dest_port) + plain)
        data = await read_vless_response(ws, BANNER)
        assert data == BANNER
    assert connect_log, "non-TLS payload bypassed the proxy"
    assert dest_hits[-1][1] == plain

    # 3) dead proxy: the WS must fail and the destination must stay untouched
    dest_hits.clear()
    try:
        async with websockets.connect(f"ws://127.0.0.1:8899/ws/{uid_dead}", max_size=2**22) as ws:
            await ws.send(vless_header(uid_dead, APP, dest_port) + b"x")
            await asyncio.wait_for(ws.recv(), 3)
            raise AssertionError("dead-proxy connection must not deliver data")
    except AssertionError:
        raise
    except Exception:
        pass
    await asyncio.sleep(0.1)
    assert not dest_hits, "dead proxy silently fell back to a direct connection"

    # 4) Multi-Location: requested dead location fails closed and never uses DE.
    dest_hits.clear(); connect_log.clear()
    try:
        async with websockets.connect(f"ws://127.0.0.1:8899/ws/{uid_ok}?ed=0&loc=loc-dead", max_size=2**22) as ws:
            await ws.send(vless_header(uid_ok, APP, dest_port) + payload)
            await asyncio.wait_for(ws.recv(), 3)
            raise AssertionError("dead location must not deliver data")
    except AssertionError:
        raise
    except Exception:
        pass
    assert not connect_log and not dest_hits, "dead FR switched to DE or direct"

    # Explicit healthy location uses its exact proxy.
    async with websockets.connect(f"ws://127.0.0.1:8899/ws/{uid_ok}?ed=0&loc=loc-de", max_size=2**22) as ws:
        await ws.send(vless_header(uid_ok, APP, dest_port) + payload)
        assert await read_vless_response(ws, BANNER) == BANNER
    assert connect_log, "healthy exact location did not use its proxy"

    # 5) subscription for the ML group lists one entry per location, same UUID
    host = "127.0.0.1"
    async with main.SUBS_LOCK:
        sub = dict(main.SUBS[sub_id])
    link = main.LINKS[uid_ok]
    entries = main.vless_entries_for_link(link, uid_ok, host)
    if not (len(entries) == 2 and entries[0]["remark"].startswith("France 🇫🇷") and entries[1]["remark"].startswith("Germany 🇩🇪")):
        raise AssertionError(f"ML entries wrong: {[(e['remark'], e['location']) for e in entries]}")
    assert all(uid_ok in e["vless_link"] for e in entries)
    assert all(e["shared_quota"] for e in entries)
    # the loc hint travels URL-encoded inside the path query parameter
    assert "loc%3Dloc-de" in entries[1]["vless_link"] and "loc%3Dloc-dead" in entries[0]["vless_link"]

    server.should_exit = True
    await asyncio.wait_for(task, 10)
    for srv in (dest, proxy):
        srv.close()
        await srv.wait_closed()
    await main.shutdown()
    print("relay e2e: proxied=OK nonTLS-tunneled=OK dead-proxy-failclosed=OK ml-no-failover=OK ml-subscription=OK")


asyncio.run(run())
