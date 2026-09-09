"""Reliable per-config HTTP/HTTPS/SOCKS5 outbound connector.

Routing contract (fail-closed):
- a config that selects a proxy ALWAYS exits through a proxy; there is no
  silent fallback to the direct route — a failing proxy fails the connection
  instead of leaking the server's own IP;
- any payload (TLS, plain HTTP, DNS-over-TCP, …) uses the tunnel, so traffic
  type can never decide whether the proxy is used;
- destination domains are always handed to the selected proxy for remote DNS;
- exactly one configured endpoint is accepted, so failure can never switch the
  route to another proxy or to the Railway server.

Compatibility goals retained:
- bounded handshakes prevent hangs on dead proxies;
- HTTPS-list entries support both TLS-to-proxy and plain CONNECT semantics.
"""
from __future__ import annotations

import asyncio
import base64
import ipaddress
import logging
import socket
import ssl
import time
from urllib.parse import unquote, urlsplit

import proxy_repository as repo

logger = logging.getLogger("Lumen.outbound")
HANDSHAKE_TIMEOUT = 4.0
CONNECT_HEADER_MAX = 32 * 1024
FAILURE_BASE_SECONDS = 10.0
FAILURE_MAX_SECONDS = 300.0

class ProxyUnavailableError(OSError):
    """A proxy was configured for this route but none can currently be used.
    Raised so the caller can fail the connection instead of leaking a direct
    server-side exit."""



_dialer = asyncio.open_connection
_tuner = None

# endpoint -> (consecutive_failures, cooldown_until_monotonic)
_proxy_health: dict[str, tuple[int, float]] = {}


def set_dialer(fn):
    global _dialer
    _dialer = fn


def set_tuner(fn):
    global _tuner
    _tuner = fn


def _tune(writer):
    if _tuner:
        try:
            _tuner(writer)
        except Exception:
            pass


async def _dial(host, port):
    return await _dialer(host, port)


def _close(writer) -> None:
    if writer is not None:
        try:
            writer.close()
        except Exception:
            pass


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(str(value).strip("[]").split("%", 1)[0])
        return True
    except ValueError:
        return False


def parse_proxy_url(value):
    parsed = urlsplit(repo.validate_url(value))
    return {
        "scheme": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "username": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
    }


def link_uses_proxy(link) -> bool:
    if not isinstance(link, dict):
        return False
    mode = str(link.get("exit_proxy_mode") or "direct")
    return (mode == "repository" and bool(link.get("proxy_id"))) or (
        mode == "custom" and bool(link.get("custom_proxy"))
    )


def proxy_health_snapshot() -> dict:
    """endpoint -> failure count for endpoints currently cooling down."""
    now = time.monotonic()
    return {ep: fails for ep, (fails, until) in _proxy_health.items() if until > now}


def _record_proxy_success(endpoint: str) -> None:
    _proxy_health.pop(endpoint, None)


def _record_proxy_failure(endpoint: str) -> None:
    fails, _until = _proxy_health.get(endpoint, (0, 0.0))
    fails = min(fails + 1, 8)
    cooldown = min(FAILURE_BASE_SECONDS * (2 ** (fails - 1)), FAILURE_MAX_SECONDS)
    _proxy_health[endpoint] = (fails, time.monotonic() + cooldown)
    if len(_proxy_health) > 4096:
        # Bound memory: drop the entries closest to recovery.
        for key in sorted(_proxy_health, key=lambda k: _proxy_health[k][1])[:512]:
            _proxy_health.pop(key, None)


def _socks_target(host: str, port: int) -> bytes:
    bare = str(host).strip("[]")
    try:
        ip = ipaddress.ip_address(bare.split("%", 1)[0])
        address = (b"\x01" if ip.version == 4 else b"\x04") + ip.packed
    except ValueError:
        encoded = bare.encode("idna")
        if len(encoded) > 255:
            raise ValueError("SOCKS5 target hostname too long")
        address = b"\x03" + bytes([len(encoded)]) + encoded
    return address + int(port).to_bytes(2, "big")


async def _read_socks_reply(reader):
    head = await reader.readexactly(4)
    if head[0] != 5 or head[1] != 0:
        raise OSError("SOCKS5 CONNECT failed: " + str(head[1] if len(head) > 1 else -1))
    if head[3] == 1:
        await reader.readexactly(6)
    elif head[3] == 4:
        await reader.readexactly(18)
    elif head[3] == 3:
        await reader.readexactly((await reader.readexactly(1))[0] + 2)
    else:
        raise OSError("SOCKS5 invalid reply address type")


async def _socks_once(target, port, first_packet, params):
    reader, writer = await _dial(params["hostname"], params["port"])
    _tune(writer)
    try:
        async with asyncio.timeout(HANDSHAKE_TIMEOUT):
            username = params["username"]
            password = params["password"]
            has_auth = bool(username or password)
            writer.write(b"\x05\x02\x00\x02" if has_auth else b"\x05\x01\x00")
            await writer.drain()
            response = await reader.readexactly(2)
            if response[0] != 5:
                raise OSError("SOCKS5 invalid greeting")
            if response[1] == 2:
                if not has_auth:
                    raise OSError("SOCKS5 authentication required")
                user = username.encode()
                secret = password.encode()
                if len(user) > 255 or len(secret) > 255:
                    raise ValueError("SOCKS5 credentials too long")
                writer.write(b"\x01" + bytes([len(user)]) + user + bytes([len(secret)]) + secret)
                await writer.drain()
                auth = await reader.readexactly(2)
                if auth[0] != 1 or auth[1] != 0:
                    raise OSError("SOCKS5 authentication failed")
            elif response[1] != 0:
                raise OSError("SOCKS5 authentication method rejected")
            writer.write(b"\x05\x01\x00" + _socks_target(target, port))
            await writer.drain()
            await _read_socks_reply(reader)
            if first_packet:
                writer.write(first_packet)
                await writer.drain()
        return reader, writer
    except BaseException:
        _close(writer)
        raise


async def _socks_connect(target, port, first_packet, params):
    # Keep the hostname inside SOCKS5. Local DNS fallback would leak DNS and can
    # make a tested identity behave differently at runtime.
    return await _socks_once(target, port, first_packet, params)


def _connect_authority(host: str, port: int) -> str:
    bare = str(host).strip("[]")
    return ("[" + bare + "]" if ":" in bare else bare) + ":" + str(port)


def _connect_request(host: str, port: int, params: dict) -> bytes:
    authority = _connect_authority(host, port)
    lines = [
        "CONNECT " + authority + " HTTP/1.1",
        "Host: " + authority,
        "User-Agent: Mozilla/5.0",
        "Proxy-Connection: keep-alive",
        "Connection: keep-alive",
    ]
    if params["username"] or params["password"]:
        token = base64.b64encode(
            (params["username"] + ":" + params["password"]).encode()
        ).decode()
        lines.append("Proxy-Authorization: Basic " + token)
    return ("\r\n".join(lines) + "\r\n\r\n").encode()


async def _http_once(target, port, first_packet, params, tls_to_proxy: bool):
    reader, writer = await _dial(params["hostname"], params["port"])
    _tune(writer)
    try:
        async with asyncio.timeout(HANDSHAKE_TIMEOUT):
            if tls_to_proxy:
                # Public/managed proxy lists commonly contain IP endpoints with
                # self-signed or hostname-mismatched certs. Encryption is kept,
                # while endpoint trust comes from the private managed list.
                context = ssl.create_default_context()
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
                server_hostname = None if _is_ip(params["hostname"]) else params["hostname"]
                await writer.start_tls(context, server_hostname=server_hostname)
            writer.write(_connect_request(target, port, params))
            await writer.drain()
            header = await reader.readuntil(b"\r\n\r\n")
            if len(header) > CONNECT_HEADER_MAX:
                raise OSError("proxy CONNECT header too long")
            fields = header.split(b"\r\n", 1)[0].split()
            code = int(fields[1]) if len(fields) > 1 and fields[1].isdigit() else -1
            if not 200 <= code < 300:
                raise OSError("proxy CONNECT failed: HTTP " + str(code))
            if first_packet:
                writer.write(first_packet)
                await writer.drain()
        return reader, writer
    except BaseException:
        _close(writer)
        raise


async def _http_connect(target, port, first_packet, params):
    if params["scheme"] == "https":
        # Most public `https://IP:port` lists mean an HTTP CONNECT proxy that
        # supports HTTPS destinations, not TLS transport to the proxy itself.
        # Prefer that convention for IPs, but support real TLS proxies too.
        transports = (False, True) if _is_ip(params["hostname"]) else (True, False)
    else:
        transports = (False,)
    last_error = None
    for tls_to_proxy in transports:
        try:
            return await _http_once(target, port, first_packet, params, tls_to_proxy=tls_to_proxy)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            last_error = exc
    # Never resolve the destination locally. The selected proxy either accepts
    # the hostname or the connection fails closed.
    raise last_error or OSError("HTTP proxy connection failed")


async def _endpoint_from_link(link) -> str | None:
    """Single endpoint for a per-config exit proxy. Fail-closed: a configured
    proxy that cannot be resolved raises instead of silently going direct."""
    if not isinstance(link, dict):
        return None
    mode = str(link.get("exit_proxy_mode") or "direct")
    if mode == "repository":
        record = await repo.resolve(link.get("proxy_id"))
        if record is None:
            raise ProxyUnavailableError("managed proxy is not in the repository cache")
        return record.endpoint
    if mode == "custom":
        try:
            return repo.validate_url(link.get("custom_proxy"))
        except ValueError as exc:
            raise ProxyUnavailableError("custom proxy URL is invalid") from exc
    return None


async def _open_via(endpoint: str, address: str, port: int, packet: bytes):
    params = parse_proxy_url(endpoint)
    if params["scheme"] == "socks5":
        return await _socks_connect(address, port, packet, params)
    return await _http_connect(address, port, packet, params)


async def open_outbound(address, port, first_packet=None, *, link=None, uuid="", endpoints=None, proxy_id=""):
    """Open one deterministic upstream path.

    No endpoints means an intentional direct route. Exactly one endpoint means
    the exact selected managed/custom proxy. More than one endpoint is rejected
    because retrying another proxy would violate explicit-selection semantics.
    """
    packet = bytes(first_packet or b"")
    if endpoints is None:
        single = await _endpoint_from_link(link)
        endpoints = [single] if single else []
    exact = list(dict.fromkeys(str(e) for e in endpoints or [] if e))
    if not exact:
        if link_uses_proxy(link):
            raise ProxyUnavailableError("configured proxy did not resolve")
        reader, writer = await _dial(address, port)
        _tune(writer)
        return reader, writer, False
    if len(exact) != 1:
        raise ProxyUnavailableError("explicit routing accepts exactly one proxy endpoint")

    endpoint = exact[0]
    try:
        reader, writer = await _open_via(endpoint, address, port, packet)
        _record_proxy_success(endpoint)
        return reader, writer, True
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        _record_proxy_failure(endpoint)
        # Log the stable ID only. Never log endpoint URLs or credentials.
        logger.info("selected proxy failed id=%s target=%s:%d error=%s", str(proxy_id or "unknown")[:32], address, port, type(exc).__name__)
        raise OSError(f"selected proxy {str(proxy_id or 'unknown')[:32]} failed closed") from exc


async def _probe_https_target(endpoint: str, hostname: str, timeout: float = 10.0) -> dict:
    """Issue one measured HTTPS GET through one exact proxy endpoint."""
    writer = None
    started = time.perf_counter()
    try:
        async with asyncio.timeout(timeout):
            reader, writer = await _open_via(endpoint, hostname, 443, b"")
            context = ssl.create_default_context()
            await writer.start_tls(context, server_hostname=hostname)
            request = (
                f"GET / HTTP/1.1\r\nHost: {hostname}\r\n"
                "User-Agent: Lumen-Exact-Proxy-Test/29\r\n"
                "Accept: */*\r\nConnection: close\r\n\r\n"
            ).encode("ascii")
            writer.write(request)
            await writer.drain()
            status_line = await reader.readline()
            fields = status_line.split()
            status = int(fields[1]) if len(fields) > 1 and fields[1].isdigit() else 0
            # Cloudflare and Google may redirect their root URL. A valid HTTPS
            # response in the 2xx/3xx range proves outbound HTTPS connectivity.
            return {"target": "https://" + hostname, "ok": 200 <= status < 400, "status": status or None, "latency_ms": round((time.perf_counter() - started) * 1000)}
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        return {"target": "https://" + hostname, "ok": False, "status": None, "latency_ms": round((time.perf_counter() - started) * 1000), "error": type(exc).__name__}
    finally:
        _close(writer)
        if writer is not None:
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def test_proxy_record(record, timeout: float = 10.0) -> dict:
    """Test both required targets through the exact selected record only."""
    targets = ("cloudflare.com", "google.com")
    results = await asyncio.gather(*(_probe_https_target(record.endpoint, host, timeout) for host in targets))
    return {"proxy_id": record.id, "ok": all(item.get("ok") for item in results), "checks": list(results)}
