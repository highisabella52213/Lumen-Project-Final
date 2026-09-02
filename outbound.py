"""Reliable per-config HTTP/HTTPS/SOCKS5 outbound connector.

Compatibility goals:
- bounded handshakes and a real first-byte check prevent silent ping=-1 hangs;
- HTTPS-list entries support both TLS-to-proxy and common plain CONNECT semantics;
- domain destinations retry through locally resolved IPs for restrictive proxies;
- any failure closes the proxy socket and fails open to the direct route.
"""
from __future__ import annotations

import asyncio
import base64
import ipaddress
import logging
import socket
import ssl
from urllib.parse import unquote, urlsplit

import proxy_repository as repo

logger = logging.getLogger("Lumen.outbound")
HANDSHAKE_TIMEOUT = 4.0
FIRST_BYTE_TIMEOUT = 4.5
PROXY_TOTAL_TIMEOUT = 7.0
CONNECT_HEADER_MAX = 32 * 1024
MAX_TARGET_ALTERNATIVES = 3

_dialer = asyncio.open_connection
_tuner = None


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


def _complete_tls_record(data) -> bool:
    packet = bytes(data or b"")
    return (
        len(packet) >= 5
        and packet[0] == 0x16
        and packet[1] == 0x03
        and len(packet) >= 5 + int.from_bytes(packet[3:5], "big")
    )


async def _target_alternatives(host: str, port: int) -> list[str]:
    bare = str(host).strip("[]")
    result = [bare]
    if _is_ip(bare):
        return result
    try:
        infos = await asyncio.get_running_loop().getaddrinfo(
            bare, port, type=socket.SOCK_STREAM
        )
    except Exception:
        return result
    for _family, _type, _proto, _canon, sockaddr in infos:
        candidate = sockaddr[0]
        if candidate not in result:
            result.append(candidate)
        if len(result) >= MAX_TARGET_ALTERNATIVES:
            break
    return result


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
            writer.write(first_packet)
            await writer.drain()
        return reader, writer
    except BaseException:
        _close(writer)
        raise


async def _socks_connect(target, port, first_packet, params):
    last_error = None
    for candidate in await _target_alternatives(target, port):
        try:
            return await _socks_once(candidate, port, first_packet, params)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            last_error = exc
    raise last_error or OSError("SOCKS5 connection failed")


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
            writer.write(first_packet)
            await writer.drain()
        return reader, writer
    except BaseException:
        _close(writer)
        raise


async def _http_connect(target, port, first_packet, params):
    targets = await _target_alternatives(target, port)
    if params["scheme"] == "https":
        # Most public `https://IP:port` lists mean an HTTP CONNECT proxy that
        # supports HTTPS destinations, not TLS transport to the proxy itself.
        # Prefer that convention for IPs, but support real TLS proxies too.
        transports = (False, True) if _is_ip(params["hostname"]) else (True, False)
    else:
        transports = (False,)
    last_error = None
    for tls_to_proxy in transports:
        for candidate in targets:
            try:
                return await _http_once(
                    candidate, port, first_packet, params, tls_to_proxy=tls_to_proxy
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_error = exc
    raise last_error or OSError("HTTP proxy connection failed")


async def _verify_downstream(reader):
    chunk = await asyncio.wait_for(reader.read(65536), timeout=FIRST_BYTE_TIMEOUT)
    if not chunk:
        raise OSError("proxy tunnel returned no downstream data")
    # StreamReader.read removed the prefix from its bytearray. No await occurs
    # before feed_data, so putting it back preserves exact byte order.
    reader.feed_data(chunk)
    return reader


async def _endpoint(link):
    if not isinstance(link, dict):
        return None
    mode = str(link.get("exit_proxy_mode") or "direct")
    if mode == "repository":
        record = await repo.resolve(link.get("proxy_id"))
        return record.endpoint if record else None
    if mode == "custom":
        try:
            return repo.validate_url(link.get("custom_proxy"))
        except ValueError:
            return None
    return None


async def open_outbound(address, port, first_packet=None, *, link=None, uuid=""):
    endpoint = await _endpoint(link)
    packet = bytes(first_packet or b"")
    # A validated response is possible only after a complete TLS ClientHello.
    # Empty, delayed-too-far, non-TLS, and incomplete records fail open instead
    # of creating a proxy tunnel that can silently sit at ping=-1.
    if not endpoint or not _complete_tls_record(packet):
        reader, writer = await _dial(address, port)
        _tune(writer)
        return reader, writer, False

    writer = None
    try:
        async with asyncio.timeout(PROXY_TOTAL_TIMEOUT):
            params = parse_proxy_url(endpoint)
            if params["scheme"] == "socks5":
                reader, writer = await _socks_connect(address, port, packet, params)
            else:
                reader, writer = await _http_connect(address, port, packet, params)
            reader = await _verify_downstream(reader)
            return reader, writer, True
    except asyncio.CancelledError:
        _close(writer)
        raise
    except Exception as exc:
        _close(writer)
        logger.warning("managed proxy failed; using direct route: %s", str(exc) or type(exc).__name__)
        reader, direct_writer = await _dial(address, port)
        _tune(direct_writer)
        return reader, direct_writer, False
