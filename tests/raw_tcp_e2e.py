#!/usr/bin/env python3
"""TLS Raw TCP VLESS → exact proxy → destination integration contract."""
from __future__ import annotations

import asyncio
import json
import os
import socket
import ssl
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


TMP = tempfile.TemporaryDirectory(prefix="lumen-raw-tcp-")
ROOT_DATA = Path(TMP.name)
PORT = free_port()
CERT, KEY = ROOT_DATA / "cert.pem", ROOT_DATA / "key.pem"
subprocess.run(
    [
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
        "-subj", "/CN=tcp.test",
        "-addext", "subjectAltName=DNS:tcp.test,DNS:de.tcp.test,DNS:fr.tcp.test",
        "-keyout", str(KEY), "-out", str(CERT),
    ],
    check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
os.environ.update(
    {
        "DATA_DIR": str(ROOT_DATA / "state"),
        "RAILWAY_TCP_APPLICATION_PORT": str(PORT),
        "RAILWAY_TCP_PROXY_DOMAIN": "127.0.0.1",
        "RAILWAY_TCP_PROXY_PORT": str(PORT),
        "VLESS_TCP_LISTEN_HOST": "127.0.0.1",
        "VLESS_TCP_LISTEN_PORT": str(PORT),
        "VLESS_TCP_TLS_CERT_FILE": str(CERT),
        "VLESS_TCP_TLS_KEY_FILE": str(KEY),
        "VLESS_TCP_URI_NETWORK": "tcp",
        "VLESS_TCP_DEFAULT_SNI": "tcp.test",
        "VLESS_TCP_SNI_MAP": json.dumps(
            {"tcp.test": "", "de.tcp.test": "loc-de", "fr.tcp.test": "loc-fr"}
        ),
        "VLESS_TCP_MAX_CONNECTIONS": "32",
    }
)

import main
import proxy_repository as repo
import relay_vless as relay
from raw_tcp import RAW_TCP_LISTENER


def vless_header(uid: str, host: str, port: int, payload: bytes = b"") -> bytes:
    encoded = host.encode("idna")
    return (
        b"\x00" + uuid.UUID(uid).bytes + b"\x00\x01" + port.to_bytes(2, "big")
        + b"\x02" + bytes((len(encoded),)) + encoded + payload
    )


async def pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.IncompleteReadError):
        pass
    finally:
        writer.close()


async def main_run():
    destination_hits: list[bytes] = []
    proxy_log: list[str] = []

    async def destination(reader, writer):
        destination_hits.append(await reader.read(65536))
        writer.write(b"RAW-DESTINATION")
        await writer.drain()
        writer.close()

    destination_server = await asyncio.start_server(destination, "127.0.0.1", 0)
    destination_port = destination_server.sockets[0].getsockname()[1]

    async def proxy_handler(reader, writer, proxy_id: str):
        try:
            header = await reader.readuntil(b"\r\n\r\n")
            proxy_log.append(proxy_id)
            target_reader, target_writer = await asyncio.open_connection(
                "127.0.0.1", destination_port
            )
            writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
            await writer.drain()
            await asyncio.gather(pipe(reader, target_writer), pipe(target_reader, writer))
        except (ConnectionError, asyncio.IncompleteReadError):
            writer.close()

    proxy_servers = []
    records = {}
    for proxy_id, country, code in (("proxy-de", "Germany", "DE"), ("proxy-fr", "France", "FR")):
        server = await asyncio.start_server(
            lambda r, w, p=proxy_id: proxy_handler(r, w, p), "127.0.0.1", 0
        )
        proxy_servers.append(server)
        proxy_port = server.sockets[0].getsockname()[1]
        records[proxy_id] = repo.Record(
            proxy_id, f"http://127.0.0.1:{proxy_port}", "http", country, code, "🏳️", 1
        )
    repo._records = dict(records)
    repo._last = time.monotonic()
    repo._error = ""

    await RAW_TCP_LISTENER.start()
    assert RAW_TCP_LISTENER.running, RAW_TCP_LISTENER.error

    sub_id, _ = await main.create_sub_group(name="raw tcp")
    uid, link = await main.make_link(
        label="raw",
        protocol="vless-tcp",
        sub_id=sub_id,
        exit_proxy_mode="repository",
        proxy_id="proxy-de",
    )
    multi_location = await main.validate_multi_location(
        {
            "enabled": True,
            "remark_text": "Raw",
            "locations": [
                {"id": "loc-de", "code": "DE", "proxy_id": "proxy-de"},
                {"id": "loc-fr", "code": "FR", "proxy_id": "proxy-fr"},
            ],
        }
    )
    async with main.SUBS_LOCK:
        main.SUBS[sub_id]["multi_location"] = multi_location
    await main.save_state(strict=True)

    # Raw TCP persistence retains its distinct endpoint semantics after a
    # restart; it must not acquire the historical WS ALPN default.
    main.LINKS.clear()
    main.SUBS.clear()
    await main.load_state()
    link = main.LINKS[uid]
    assert link["protocol"] == "vless-tcp"
    assert link["transport_settings"] == {}
    assert link["address"] == link["sni"] == link["alpn"] == ""

    entries = main.vless_entries_for_link(link, uid, "ignored.example")
    assert len(entries) == 2 and all(item["shared_quota"] for item in entries)
    q_de = parse_qs(urlsplit(entries[0]["vless_link"]).query)
    q_fr = parse_qs(urlsplit(entries[1]["vless_link"]).query)
    assert q_de["type"] == ["tcp"] and q_de["sni"] == ["de.tcp.test"]
    assert q_fr["sni"] == ["fr.tcp.test"]
    assert "host" not in q_de and "path" not in q_de and "alpn" not in q_de
    assert urlsplit(entries[0]["vless_link"]).port == PORT

    class UpdateRequest:
        headers = {}

        async def json(self):
            return {"address": "attacker.example"}

    try:
        await main.update_link(uid, UpdateRequest())
        raise AssertionError("Raw TCP accepted a client-managed endpoint update")
    except main.HTTPException as exc:
        assert exc.status_code == 400

    # An incomplete deployment SNI map cannot attach a Raw TCP record to a
    # Multi-Location group; the existing association stays untouched.
    blocked_sub, _ = await main.create_sub_group(name="blocked raw tcp")
    async with main.SUBS_LOCK:
        main.SUBS[blocked_sub]["multi_location"] = multi_location
    original_map = os.environ["VLESS_TCP_SNI_MAP"]
    os.environ["VLESS_TCP_SNI_MAP"] = json.dumps({"tcp.test": ""})
    try:
        assert not await main.set_link_sub(uid, blocked_sub)
        assert main.LINKS[uid]["sub_id"] == sub_id
    finally:
        os.environ["VLESS_TCP_SNI_MAP"] = original_map

    # Verify the test certificate for every valid, generated SNI rather than
    # treating a completed encrypted socket as proof of usable TLS.
    tls = ssl.create_default_context(cafile=str(CERT))

    async def connect(sni: str, request: bytes) -> bytes:
        reader, writer = await asyncio.open_connection(
            "127.0.0.1", PORT, ssl=tls, server_hostname=sni
        )
        writer.write(request)
        await writer.drain()
        try:
            first = await asyncio.wait_for(reader.read(2), 3)
            result = first
            if first == b"\x00\x00":
                result += await asyncio.wait_for(reader.readexactly(len(b"RAW-DESTINATION")), 3)
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
        return result

    # Both SNI-selected locations keep one UUID but traverse their exact proxy.
    assert (await connect("de.tcp.test", vless_header(uid, "target.test", destination_port, b"DE"))) == b"\x00\x00RAW-DESTINATION"
    assert proxy_log[-1] == "proxy-de" and destination_hits[-1] == b"DE"
    assert (await connect("fr.tcp.test", vless_header(uid, "target.test", destination_port, b"FR"))) == b"\x00\x00RAW-DESTINATION"
    assert proxy_log[-1] == "proxy-fr" and destination_hits[-1] == b"FR"

    # No Raw query/extension is accepted: default SNI lacks an ML location.
    assert await connect("tcp.test", vless_header(uid, "target.test", destination_port)) == b""
    try:
        await connect("unknown.tcp.test", vless_header(uid, "target.test", destination_port))
        raise AssertionError("unknown SNI unexpectedly passed TLS verification")
    except ssl.SSLCertVerificationError:
        pass
    assert await connect("de.tcp.test", b"\x01" + b"x" * 24) == b""
    assert await connect("de.tcp.test", vless_header(str(uuid.uuid4()), "target.test", destination_port)) == b""

    # An exact dead DE proxy fails closed; the FR selection remains independent.
    repo._records["proxy-de"] = repo.Record(
        "proxy-de", "http://127.0.0.1:1", "http", "Germany", "DE", "🏳️", 1
    )
    before = len(destination_hits)
    assert await connect("de.tcp.test", vless_header(uid, "target.test", destination_port, b"dead")) == b""
    assert len(destination_hits) == before
    assert (await connect("fr.tcp.test", vless_header(uid, "target.test", destination_port, b"still-fr"))) == b"\x00\x00RAW-DESTINATION"
    assert proxy_log[-1] == "proxy-fr"
    repo._records["proxy-de"] = records["proxy-de"]

    # Partial initial headers time out before a full relay/outbound is created.
    previous_timeout = relay.HEADER_TIMEOUT
    relay.HEADER_TIMEOUT = 0.05
    try:
        assert await connect("de.tcp.test", b"\x00" + uuid.UUID(uid).bytes[:4]) == b""
    finally:
        relay.HEADER_TIMEOUT = previous_timeout

    await asyncio.sleep(0.05)
    assert not main.connections, main.connections
    assert not RAW_TCP_LISTENER._tasks, RAW_TCP_LISTENER._tasks

    await RAW_TCP_LISTENER.stop()
    for server in (*proxy_servers, destination_server):
        server.close()
        await server.wait_closed()
    print(
        "raw tcp E2E: TLS=OK SNI-DE->proxy-de SNI-FR->proxy-fr "
        "dead-DE=fail-closed malformed=closed cleanup=OK"
    )


try:
    asyncio.run(main_run())
finally:
    TMP.cleanup()