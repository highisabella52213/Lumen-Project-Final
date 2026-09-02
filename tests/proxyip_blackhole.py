"""بازتولید باگ «پینگ -1».

ریلی‌ای که TCP را قبول می‌کند ولی ترافیک را فوروارد نمی‌کند (blackhole)
قبلاً باعث می‌شد اتصال موفق تلقی شود، fallback فعال نشود، و تونل بماند.
"""
import asyncio
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import outbound

APP_IP = "127.0.0.1"
RELAY_EXIT_IP = "127.0.0.9"
TLS_HELLO = bytes([0x16, 0x03, 0x01, 0x00, 0x05]) + b"hello"
PLAIN_FIRST = b"GET / HTTP/1.1\r\nHost: x\r\n\r\n"

failures = []
servers = []


def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  " + detail) if detail and not cond else ""))
    if not cond:
        failures.append(name)


async def start_destination(seen):
    async def handle(reader, writer):
        peer = writer.get_extra_info("peername")
        seen.append(peer[0] if peer else "?")
        writer.write(b"SRV-HELLO")
        await writer.drain()
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=3)
        except Exception:
            data = b""
        if data:
            writer.write(b"ECHO:" + data)
            try:
                await writer.drain()
            except Exception:
                pass

    srv = await asyncio.start_server(handle, APP_IP, 0)
    servers.append(srv)
    return srv.sockets[0].getsockname()[1]


async def start_blackhole():
    """پورت را باز می‌کند، می‌خواند، ولی هیچ وقت جواب نمی‌دهد."""
    holder = []

    async def handle(reader, writer):
        holder.append(writer)
        try:
            while True:
                data = await reader.read(4096)
                if not data:
                    break
        except Exception:
            pass

    srv = await asyncio.start_server(handle, APP_IP, 0)
    servers.append(srv)
    return srv.sockets[0].getsockname()[1]


async def start_relay(dest_port, exit_ip):
    async def handle(reader, writer):
        try:
            up_r, up_w = await asyncio.open_connection(
                APP_IP, dest_port, local_addr=(exit_ip, 0)
            )
        except Exception:
            writer.close()
            return

        async def pipe(r, w):
            try:
                while True:
                    data = await r.read(65536)
                    if not data:
                        break
                    w.write(data)
                    await w.drain()
            except Exception:
                pass

        await asyncio.gather(pipe(reader, up_w), pipe(up_r, writer))

    srv = await asyncio.start_server(handle, APP_IP, 0)
    servers.append(srv)
    return srv.sockets[0].getsockname()[1]


def reset(**kw):
    outbound.SETTINGS.update(outbound._initial_settings())
    outbound.reset_caches()
    outbound.configure(**kw)


async def main():
    outbound.FIRST_BYTE_TIMEOUT = 1.0
    outbound.PROBE_TLS_TIMEOUT = 1.0

    seen = []
    dest_port = await start_destination(seen)
    black_port = await start_blackhole()
    relay_port = await start_relay(dest_port, RELAY_EXIT_IP)

    print("[blackhole relay + fallback ON -> must still work, via direct]")
    seen.clear()
    reset(mode="proxyip", proxyip=APP_IP + ":" + str(black_port), fallback=True, concurrency=1)
    try:
        reader, writer, written = await asyncio.wait_for(
            outbound.open_outbound(APP_IP, dest_port, TLS_HELLO), timeout=10
        )
        check("connection established", True)
        check("did not mark payload as written", written is False, "written=%r" % written)
        if not written:
            writer.write(TLS_HELLO)
            await writer.drain()
        data = await asyncio.wait_for(reader.read(4096), timeout=3)
        check("real data received", data.startswith(b"SRV-HELLO"), repr(data[:40]))
        check("exit ip is direct (app ip)", seen and seen[0] == APP_IP, str(seen))
        writer.close()
    except Exception as exc:
        check("connection established", False, repr(exc))

    print()
    print("[blackhole relay + fallback OFF -> still fails open to direct]")
    seen.clear()
    reset(mode="proxyip", proxyip=APP_IP + ":" + str(black_port), fallback=False, concurrency=1)
    try:
        reader, writer, written = await asyncio.wait_for(outbound.open_outbound(APP_IP, dest_port, TLS_HELLO), timeout=10)
        if not written:
            writer.write(TLS_HELLO); await writer.drain()
        data = await asyncio.wait_for(reader.read(4096), timeout=3)
        check("legacy fallback off cannot cut config", data.startswith(b"SRV-HELLO"), repr(data[:40]))
        check("falls back to direct exit", seen and seen[0] == APP_IP, str(seen)); writer.close()
    except Exception as exc:
        check("legacy fallback off cannot cut config", False, repr(exc))

    print()
    print("[healthy relay -> works and loses no bytes]")
    seen.clear()
    reset(mode="proxyip", proxyip=APP_IP + ":" + str(relay_port), fallback=False, concurrency=1)
    try:
        reader, writer, written = await asyncio.wait_for(
            outbound.open_outbound(APP_IP, dest_port, TLS_HELLO), timeout=10
        )
        check("payload marked written", written is True, "written=%r" % written)
        check("EXIT IP IS RELAY IP", seen and seen[0] == RELAY_EXIT_IP, str(seen))
        got = b""
        while len(got) < 9:
            chunk = await asyncio.wait_for(reader.read(4096), timeout=3)
            if not chunk:
                break
            got += chunk
        check("PEEKED BYTES NOT LOST", got.startswith(b"SRV-HELLO"), repr(got[:40]))
        writer.close()
    except Exception as exc:
        check("healthy relay works", False, repr(exc))

    print()
    print("[non-TLS first packet -> watchdog must NOT fire]")
    seen.clear()
    reset(mode="proxyip", proxyip=APP_IP + ":" + str(black_port), fallback=False, concurrency=1)
    try:
        reader, writer, written = await asyncio.wait_for(
            outbound.open_outbound(APP_IP, dest_port, PLAIN_FIRST), timeout=6
        )
        check("server-speaks-second protocol still allowed", True)
        writer.close()
    except Exception as exc:
        check("server-speaks-second protocol still allowed", False, repr(exc))

    print()
    print("[failover: blackhole first, healthy second]")
    seen.clear()
    pool = APP_IP + ":" + str(black_port) + "," + APP_IP + ":" + str(relay_port)
    reset(mode="proxyip", proxyip=pool, fallback=False, concurrency=1)
    try:
        reader, writer, written = await asyncio.wait_for(
            outbound.open_outbound(APP_IP, dest_port, TLS_HELLO), timeout=12
        )
        got = await asyncio.wait_for(reader.read(4096), timeout=3)
        check("failed over to healthy relay", got.startswith(b"SRV-HELLO"), repr(got[:40]))
        check("exit ip is relay ip", seen and seen[0] == RELAY_EXIT_IP, str(seen))
        writer.close()
    except Exception as exc:
        check("failed over to healthy relay", False, repr(exc))

    print()
    print("[probe reports a non-forwarding relay]")
    reset(mode="proxyip", proxyip=APP_IP + ":" + str(black_port), fallback=True, concurrency=1)
    result = await outbound.probe(target_host="example.com")
    cands = result.get("candidates") or []
    check("probe found candidate", len(cands) == 1, str(result))
    if cands:
        check("probe: tcp ok", cands[0].get("ok") is True, str(cands[0]))
        check("PROBE FLAGS RELAY AS BROKEN", cands[0].get("relay_ok") is False, str(cands[0]))

    for srv in servers:
        srv.close()

    print()
    if failures:
        print("FAILURES: %d -> %s" % (len(failures), failures))
        return 1
    print("proxyip blackhole: ALL OK")
    return 0


sys.exit(asyncio.run(main()))
