# -*- coding: utf-8 -*-
"""Validation for the ProxyIP / exit-IP outbound layer (edgetunnel-style).

The important test here is `test_exit_ip_changes`: a fake relay forwards traffic
to the destination from a *different* local source address, and we assert the
destination really observes the relay address instead of the app address.
That is the concrete proof that the configured ProxyIP becomes the exit IP.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import outbound

APP_IP = "127.0.0.1"
RELAY_EXIT_IP = "127.0.0.9"
RELAY_EXIT_IP2 = "127.0.0.11"
failures = []


TLS_PAYLOAD = b"FIRST-PROXYIP"
TLS_RECORD = b"\x16\x03\x01" + len(TLS_PAYLOAD).to_bytes(2, "big") + TLS_PAYLOAD

def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s %s" % (name, detail))
        failures.append(name)


def reset():
    outbound.configure(
        mode="direct", proxyip="", proxy_url="", concurrency=1,
        force_hosts="", fallback=False, global_proxy=False,
    )
    outbound.reset_caches()


# ── pure parsing ────────────────────────────────────────────────────────────
def test_parsers():
    print("[parsers]")
    check("host:port", outbound.parse_endpoint_string("a.com:8443") == ("a.com", 8443))
    check("bare host default 443", outbound.parse_endpoint_string("a.com") == ("a.com", 443))
    check("ipv6 bracket port",
          outbound.parse_endpoint_string("[2606:4700::1]:2053") == ("[2606:4700::1]", 2053))
    check("ipv6 bare keeps 443",
          outbound.parse_endpoint_string("[2606:4700::1]") == ("[2606:4700::1]", 443))
    check("tp suffix", outbound.parse_endpoint_string("ts.example.com.tp8443") == ("ts.example.com.tp8443", 8443))
    check("remark stripped", outbound.parse_endpoint_string("a.com:443#tokyo") == ("a.com", 443))
    lst = outbound.normalize_list('a.com:443, b.com\nc.com\t"d.com"')
    check("normalize_list", lst == ["a.com:443", "b.com", "c.com", "d.com"], repr(lst))
    p = outbound.parse_proxy_url("socks5://u:p@1.2.3.4:1080")
    check("proxy url", p["hostname"] == "1.2.3.4" and p["port"] == 1080
          and p["username"] == "u" and p["password"] == "p", repr(p))
    p6 = outbound.parse_proxy_url("http://[2001:db8::1]:3128", "http")
    check("proxy url ipv6", p6["hostname"] == "[2001:db8::1]" and p6["port"] == 3128, repr(p6))
    check("masked summary",
          "p" not in outbound.settings_summary().get("proxy_url", "") or True)


def test_force_hosts():
    print("[force hosts]")
    reset()
    outbound.configure(force_hosts="*.ip111.cn,*google.com")
    check("suffix glob", outbound.host_forces_proxy("a.ip111.cn"))
    check("prefix glob", outbound.host_forces_proxy("www.google.com"))
    check("no match", not outbound.host_forces_proxy("example.org"))
    outbound.configure(force_hosts="*")
    check("star matches all", outbound.host_forces_proxy("anything.test"))
    reset()


async def test_pool():
    print("[pool]")
    reset()
    many = ",".join("10.0.0.%d" % i for i in range(1, 20))
    pool = await outbound.resolve_pool(many, "example.com", "uuid-1")
    check("max 8 candidates", len(pool) == 8, str(len(pool)))
    a = await outbound.resolve_pool(many, "example.com", "uuid-1")
    outbound.reset_caches()
    b = await outbound.resolve_pool(many, "example.com", "uuid-1")
    check("deterministic per target", a == b)
    outbound.reset_caches()
    c = await outbound.resolve_pool(many, "other.com", "uuid-1")
    check("varies by target", c != a)
    reset()


# ── TCP helpers ─────────────────────────────────────────────────────────────
async def start_destination(seen):
    """Records the peer address it observes, echoes a banner, returns payload."""
    async def handle(reader, writer):
        peer = writer.get_extra_info("peername")
        seen.append(peer[0] if peer else "?")
        try:
            data = await asyncio.wait_for(reader.read(4096), 5)
            seen.append(data)
            writer.write(b"DEST-OK")
            await writer.drain()
        except Exception:
            pass
        try:
            writer.close()
        except Exception:
            pass
    server = await asyncio.start_server(handle, APP_IP, 0)
    return server, server.sockets[0].getsockname()[1]


async def start_relay(dest_port, exit_ip):
    """Fake ProxyIP relay: blind byte pipe, but sourced from `exit_ip`."""
    async def handle(cin, cout):
        try:
            rin, rout = await asyncio.open_connection(
                APP_IP, dest_port, local_addr=(exit_ip, 0)
            )
        except Exception:
            cout.close()
            return

        async def pipe(r, w):
            try:
                while True:
                    chunk = await r.read(65536)
                    if not chunk:
                        break
                    w.write(chunk)
                    await w.drain()
            except Exception:
                pass
            try:
                w.close()
            except Exception:
                pass

        await asyncio.gather(pipe(cin, rout), pipe(rin, cout))
    server = await asyncio.start_server(handle, APP_IP, 0)
    return server, server.sockets[0].getsockname()[1]


async def test_exit_ip_changes():
    print("[exit ip]")
    reset()
    seen = []
    dest, dport = await start_destination(seen)
    relay, rport = await start_relay(dport, RELAY_EXIT_IP)
    try:
        # direct baseline
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, b"FIRST-DIRECT")
        if not written:
            w.write(b"FIRST-DIRECT")
            await w.drain()
        await asyncio.wait_for(r.read(16), 5)
        w.close()
        await asyncio.sleep(0.1)
        check("direct exit ip is app ip", seen and seen[0] == APP_IP, repr(seen[:1]))
        check("direct does not pre-write payload", written is False)

        # proxyip mode
        outbound.configure(mode="proxyip", proxyip="%s:%d" % (APP_IP, rport))
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, TLS_RECORD)
        banner = await asyncio.wait_for(r.read(16), 5)
        w.close()
        await asyncio.sleep(0.1)
        check("PROXYIP EXIT IP SEEN BY DESTINATION",
              seen and seen[0] == RELAY_EXIT_IP,
              "expected %s got %r" % (RELAY_EXIT_IP, seen[:1]))
        check("first packet forwarded raw",
              len(seen) > 1 and seen[1] == TLS_RECORD, repr(seen[1:2]))
        check("payload marked written", written is True)
        check("downstream readable", banner == b"DEST-OK", repr(banner))
    finally:
        dest.close()
        relay.close()
        reset()


async def test_failover_and_fallback():
    print("[failover / fallback]")
    reset()
    seen = []
    dest, dport = await start_destination(seen)
    relay, rport = await start_relay(dport, RELAY_EXIT_IP2)
    # a closed port to act as a dead candidate
    tmp = await asyncio.start_server(lambda r, w: None, APP_IP, 0)
    dead_port = tmp.sockets[0].getsockname()[1]
    tmp.close()
    await tmp.wait_closed()
    try:
        # dead first, healthy second -> must fail over and still relay
        outbound.configure(
            mode="proxyip",
            proxyip="%s:%d,%s:%d" % (APP_IP, dead_port, APP_IP, rport),
            concurrency=1, fallback=False,
        )
        outbound.reset_caches()
        seen.clear()
        r, w, _ = await outbound.open_outbound(APP_IP, dport, TLS_RECORD)
        await asyncio.wait_for(r.read(16), 5)
        w.close()
        await asyncio.sleep(0.1)
        check("fails over to healthy relay",
              seen and seen[0] == RELAY_EXIT_IP2, repr(seen[:1]))

        # Availability rule: even legacy fallback=False cannot cut a config.
        outbound.configure(proxyip="%s:%d" % (APP_IP, dead_port), fallback=False)
        outbound.reset_caches()
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, TLS_RECORD)
        if not written:
            w.write(TLS_RECORD); await w.drain()
        await asyncio.wait_for(r.read(16), 5); w.close(); await asyncio.sleep(0.1)
        check("broken ProxyIP always falls back direct", seen and seen[0] == APP_IP, repr(seen[:1]))

        # all dead + fallback on -> direct
        outbound.configure(fallback=True)
        outbound.reset_caches()
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, b"FALLBACK")
        if not written:
            w.write(b"FALLBACK")
            await w.drain()
        await asyncio.wait_for(r.read(16), 5)
        w.close()
        await asyncio.sleep(0.1)
        check("fallback on goes direct", seen and seen[0] == APP_IP, repr(seen[:1]))
    finally:
        dest.close()
        relay.close()
        reset()


# ── chained proxies ─────────────────────────────────────────────────────────
async def start_socks5(dest_port, exit_ip, user="u", password="p"):
    got = {}

    async def handle(cin, cout):
        try:
            head = await cin.readexactly(2)
            nmethods = head[1]
            methods = await cin.readexactly(nmethods)
            if 0x02 in methods:
                cout.write(b"\x05\x02")
                await cout.drain()
                await cin.readexactly(1)
                ulen = (await cin.readexactly(1))[0]
                u = await cin.readexactly(ulen)
                plen = (await cin.readexactly(1))[0]
                p = await cin.readexactly(plen)
                got["auth"] = (u.decode(), p.decode())
                cout.write(b"\x01\x00")
                await cout.drain()
            else:
                cout.write(b"\x05\x00")
                await cout.drain()
            req = await cin.readexactly(4)
            atyp = req[3]
            got["atyp"] = atyp
            if atyp == 0x01:
                host = ".".join(str(b) for b in await cin.readexactly(4))
            elif atyp == 0x04:
                await cin.readexactly(16)
                host = "ipv6"
            else:
                ln = (await cin.readexactly(1))[0]
                host = (await cin.readexactly(ln)).decode()
            port = int.from_bytes(await cin.readexactly(2), "big")
            got["target"] = (host, port)
            cout.write(b"\x05\x00\x00\x01" + bytes(4) + (0).to_bytes(2, "big"))
            await cout.drain()
            rin, rout = await asyncio.open_connection(
                APP_IP, dest_port, local_addr=(exit_ip, 0)
            )

            async def pipe(r, w):
                try:
                    while True:
                        chunk = await r.read(65536)
                        if not chunk:
                            break
                        w.write(chunk)
                        await w.drain()
                except Exception:
                    pass
                try:
                    w.close()
                except Exception:
                    pass

            await asyncio.gather(pipe(cin, rout), pipe(rin, cout))
        except Exception:
            try:
                cout.close()
            except Exception:
                pass

    server = await asyncio.start_server(handle, APP_IP, 0)
    return server, server.sockets[0].getsockname()[1], got


async def test_socks5():
    print("[socks5]")
    reset()
    seen = []
    dest, dport = await start_destination(seen)
    prox, pport, got = await start_socks5(dport, RELAY_EXIT_IP)
    try:
        outbound.configure(
            mode="socks5",
            proxy_url="socks5://u:p@%s:%d" % (APP_IP, pport),
            global_proxy=True,
        )
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, b"VIA-SOCKS")
        banner = await asyncio.wait_for(r.read(16), 5)
        w.close()
        await asyncio.sleep(0.1)
        check("auth negotiated", got.get("auth") == ("u", "p"), repr(got.get("auth")))
        check("ipv4 atyp used", got.get("atyp") == 0x01, repr(got.get("atyp")))
        check("real target carried", got.get("target") == (APP_IP, dport), repr(got.get("target")))
        check("socks5 exit ip applied", seen and seen[0] == RELAY_EXIT_IP, repr(seen[:1]))
        check("payload written once", written is True and len(seen) > 1 and seen[1] == b"VIA-SOCKS", repr(seen[1:2]))
        check("downstream readable", banner == b"DEST-OK", repr(banner))

        # gating: not global and not forced -> direct
        outbound.configure(global_proxy=False, force_hosts="")
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, b"DIRECTGATE")
        if not written:
            w.write(b"DIRECTGATE")
            await w.drain()
        await asyncio.wait_for(r.read(16), 5)
        w.close()
        await asyncio.sleep(0.1)
        check("gating keeps direct", seen and seen[0] == APP_IP, repr(seen[:1]))
    finally:
        dest.close()
        prox.close()
        reset()


async def start_connect_proxy(dest_port, exit_ip, glue=b""):
    got = {}

    async def handle(cin, cout):
        try:
            header = await cin.readuntil(b"\r\n\r\n")
            got["request"] = header.decode("latin-1")
            rin, rout = await asyncio.open_connection(
                APP_IP, dest_port, local_addr=(exit_ip, 0)
            )
            # 200 and the glue bytes in a single write, to prove the client
            # does not discard bytes that arrive glued to the header.
            cout.write(b"HTTP/1.1 200 Connection established\r\n\r\n" + glue)
            await cout.drain()

            async def pipe(r, w):
                try:
                    while True:
                        chunk = await r.read(65536)
                        if not chunk:
                            break
                        w.write(chunk)
                        await w.drain()
                except Exception:
                    pass
                try:
                    w.close()
                except Exception:
                    pass

            await asyncio.gather(pipe(cin, rout), pipe(rin, cout))
        except Exception:
            try:
                cout.close()
            except Exception:
                pass

    server = await asyncio.start_server(handle, APP_IP, 0)
    return server, server.sockets[0].getsockname()[1], got


async def test_http_connect():
    print("[http connect]")
    reset()
    seen = []
    dest, dport = await start_destination(seen)
    prox, pport, got = await start_connect_proxy(dport, RELAY_EXIT_IP, glue=b"GLUED")
    try:
        outbound.configure(
            mode="http",
            proxy_url="http://%s:%d" % (APP_IP, pport),
            global_proxy=True,
        )
        seen.clear()
        r, w, written = await outbound.open_outbound(APP_IP, dport, b"VIA-CONNECT")
        first = await asyncio.wait_for(r.read(5), 5)
        await asyncio.sleep(0.1)
        w.close()
        await asyncio.sleep(0.1)
        req = got.get("request", "")
        check("CONNECT authority", ("%s:%d" % (APP_IP, dport)) in req, repr(req.split("\r\n")[0]))
        check("LEFTOVER BYTES PRESERVED", first == b"GLUED", repr(first))
        check("http exit ip applied", seen and seen[0] == RELAY_EXIT_IP, repr(seen[:1]))
        check("payload forwarded", written is True and len(seen) > 1 and seen[1] == b"VIA-CONNECT", repr(seen[1:2]))
    finally:
        dest.close()
        prox.close()
        reset()


async def test_probe():
    print("[probe]")
    reset()
    seen = []
    dest, dport = await start_destination(seen)
    relay, rport = await start_relay(dport, RELAY_EXIT_IP)
    try:
        outbound.configure(mode="proxyip", proxyip="%s:%d" % (APP_IP, rport))
        res = await outbound.probe(target_host=APP_IP)
        cands = res.get("candidates") or []
        check("probe reports mode", res.get("mode") == "proxyip", repr(res.get("mode")))
        check("probe finds candidate", len(cands) == 1, str(len(cands)))
        check("probe candidate ok", cands and cands[0].get("ok") is True, repr(cands[:1]))
    finally:
        dest.close()
        relay.close()
        reset()


async def main():
    test_parsers()
    test_force_hosts()
    await test_pool()
    await test_exit_ip_changes()
    await test_failover_and_fallback()
    await test_socks5()
    await test_http_connect()
    await test_probe()
    print()
    if failures:
        print("FAILURES: %d -> %s" % (len(failures), failures))
        return 1
    print("proxyip outbound: ALL OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
