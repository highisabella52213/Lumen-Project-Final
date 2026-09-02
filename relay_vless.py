# relay_vless.py
# VLESS-over-WebSocket relay — Hyper data plane
#
# Standard VLESS and Xray WebSocket framing are unchanged. The optimizations are
# entirely server-side: current Sans-I/O WS fast hooks, burst queueing, low-copy
# StreamReader extraction, large but bounded backpressure windows, DNS/route
# caching, raced connects, and batched accounting.

from __future__ import annotations

import asyncio
import base64
import secrets
import socket
import time
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from main import (
    LINKS,
    LINKS_LOCK,
    stats,
    hourly_traffic,
    connections,
    error_logs,
    logger,
    is_link_allowed,
    is_ip_allowed,
    save_state,
    log_activity,
    now_ir,
)
from speed_limit import QuotaGate, throttle
import outbound
from outbound import open_outbound, link_uses_proxy

# ── Bulk data-plane tuning ───────────────────────────────────────────────────
READ_MIN = 128 * 1024
READ_MAX = 8 * 1024 * 1024
READ_START = 1024 * 1024
STREAM_LIMIT = 32 * 1024 * 1024
BULK_TRIGGER = 128 * 1024
BULK_STREAK_TRIGGER = 2
WS_UPLOAD_BURST_MESSAGES = 32
WS_UPLOAD_BURST_BYTES = 4 * 1024 * 1024

WRITE_HW_MIN = 512 * 1024
WRITE_HW_MAX = 64 * 1024 * 1024
WRITE_HW_START = 8 * 1024 * 1024
FLOW_FAST_DRAIN_MS = 2.0
FLOW_SLOW_DRAIN_MS = 30.0

SOCK_BUF_SIZE = 32 * 1024 * 1024
PREFERRED_CC = (b"bbr", b"cubic")
CONNECT_TIMEOUT = 10.0
HEADER_TIMEOUT = 15.0
HEADER_MAX = 16 * 1024

PARALLEL_CONNECT = 6
DUAL_STACK_DELAY = 0.0          # first IPv6 and first IPv4 start together
ADDITIONAL_CONNECT_STAGGER = 0.05
DNS_TTL = 300.0
ROUTE_TTL = 1800.0
ROUTE_FAILURE_BASE = 10.0
ROUTE_FAILURE_MAX = 300.0
DNS_CACHE_MAX = 4096

# Backwards-compatible export used by main.py and older integrations.
RELAY_BUF = READ_START

_dns_cache: dict[tuple[str, int], tuple[float, list[tuple[int, tuple]]]] = {}
_dns_inflight: dict[tuple[str, int], asyncio.Task] = {}
_route_cache: dict[tuple[str, int], tuple[float, int, tuple]] = {}
_route_health: dict[tuple, tuple[float, int, float]] = {}


class _AdaptiveFlow:
    """AIMD write-buffer threshold for WS -> target TCP."""

    __slots__ = ("high_water",)

    def __init__(self) -> None:
        self.high_water = WRITE_HW_START

    def observe(self, drain_ms: float, transport: asyncio.BaseTransport) -> None:
        if drain_ms <= FLOW_FAST_DRAIN_MS:
            self.high_water = min(
                int(self.high_water * 1.5) + 64 * 1024, WRITE_HW_MAX
            )
        elif drain_ms >= FLOW_SLOW_DRAIN_MS:
            self.high_water = max(self.high_water // 2, WRITE_HW_MIN)
        try:
            transport.set_write_buffer_limits(
                high=self.high_water, low=max(self.high_water // 4, 64 * 1024)
            )
        except Exception:
            pass


class _WSIO:
    """Select custom Uvicorn fast hooks when available, otherwise use Starlette."""

    __slots__ = (
        "ws", "protocol", "_receive", "_receive_nowait", "_send", "_flush"
    )

    def __init__(self, ws: WebSocket) -> None:
        self.ws = ws
        self.protocol = _ws_protocol_owner(ws)
        self._receive = getattr(self.protocol, "turbo_receive", None)
        self._receive_nowait = getattr(self.protocol, "turbo_receive_nowait", None)
        self._send = getattr(self.protocol, "turbo_send_bytes", None)
        self._flush = getattr(self.protocol, "turbo_flush", None)

    async def receive(self) -> dict:
        if self._receive is not None:
            return await self._receive()
        return await self.ws.receive()

    def receive_nowait(self) -> dict | None:
        if self._receive_nowait is None:
            return None
        return self._receive_nowait()

    async def send_bytes(self, data: bytes | bytearray | memoryview) -> None:
        if self._send is not None:
            await self._send(data)
            return
        # ASGI formally requires bytes. The custom fast path accepts bytes-like
        # objects and can preserve a detached bytearray without another copy.
        if not isinstance(data, bytes):
            data = bytes(data)
        await self.ws.send_bytes(data)

    async def flush(self) -> None:
        if self._flush is not None:
            await self._flush()


def _ws_protocol_owner(ws: WebSocket) -> Any | None:
    for attr in ("_send", "_receive"):
        fn = getattr(ws, attr, None)
        owner = getattr(fn, "__self__", None)
        if owner is not None and hasattr(owner, "transport"):
            return owner
    return None


def _ws_client_ip(ws: WebSocket) -> str:
    fwd = ws.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    real_ip = ws.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    client = getattr(ws, "client", None)
    return client.host if client else "نامشخص"


def _early_data(ws: WebSocket) -> bytes:
    """Decode Xray ``?ed=`` data carried in Sec-WebSocket-Protocol."""
    raw = ws.headers.get("sec-websocket-protocol")
    if not raw:
        return b""
    token = raw.split(",", 1)[0].strip()
    # 16 KiB decoded is already much larger than a legal VLESS request header.
    if not token or len(token) > ((HEADER_MAX * 4 + 2) // 3):
        return b""
    try:
        pad = "=" * (-len(token) % 4)
        return base64.urlsafe_b64decode(token + pad)
    except Exception:
        return b""


def _set_common_tcp_options(sock: socket.socket) -> None:
    for level, option, value in (
        (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
        (socket.SOL_SOCKET, socket.SO_SNDBUF, SOCK_BUF_SIZE),
        (socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUF_SIZE),
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

    # Do not set TCP_NOTSENT_LOWAT here. A low fixed value can cap throughput on
    # high-BDP paths (for example 1 Gbps at 100 ms needs ~12.5 MiB in flight).
    try:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x10)
    except OSError:
        pass
    # Equivalent low-delay traffic class for native IPv6 sockets.
    ipv6_tclass = getattr(socket, "IPV6_TCLASS", None)
    if ipv6_tclass is not None:
        try:
            sock.setsockopt(socket.IPPROTO_IPV6, ipv6_tclass, 0x10)
        except OSError:
            pass


def _tune_socket(writer: asyncio.StreamWriter, high_water: int) -> None:
    transport = writer.transport
    try:
        sock = transport.get_extra_info("socket")
    except Exception:
        sock = None
    if sock is not None:
        _set_common_tcp_options(sock)
    try:
        transport.set_write_buffer_limits(
            high=high_water, low=max(high_water // 4, 64 * 1024)
        )
    except Exception:
        pass


def _tune_client_socket(ws: WebSocket) -> None:
    """Best-effort fallback; custom Turbo protocol tunes accepted sockets itself."""
    protocol = _ws_protocol_owner(ws)
    transport = getattr(protocol, "transport", None)
    sock = None
    if transport is not None:
        try:
            sock = transport.get_extra_info("socket")
            transport.set_write_buffer_limits(
                high=16 * 1024 * 1024, low=2 * 1024 * 1024
            )
        except Exception:
            sock = None

    if sock is None:
        try:
            scope = getattr(ws, "scope", {}) or {}
            transport = scope.get("transport")
            if transport is not None and hasattr(transport, "get_extra_info"):
                sock = transport.get_extra_info("socket")
        except Exception:
            sock = None
    if sock is not None:
        _set_common_tcp_options(sock)


# ── Adaptive dual-stack DNS + raced upstream connection ─────────────────────
def _numeric_address(host: str, port: int) -> list[tuple[int, tuple]] | None:
    bare = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    # Strip an RFC 4007 zone id only for inet_pton; preserve scope via getaddrinfo.
    plain = bare.split("%", 1)[0]
    try:
        socket.inet_pton(socket.AF_INET, plain)
        return [(socket.AF_INET, (plain, port))]
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, plain)
        if "%" in bare:
            try:
                infos = socket.getaddrinfo(
                    bare, port, socket.AF_INET6, socket.SOCK_STREAM
                )
                return [(socket.AF_INET6, infos[0][4])]
            except OSError:
                pass
        return [(socket.AF_INET6, (plain, port, 0, 0))]
    except OSError:
        return None


def _sockaddr_identity(family: int, sockaddr: tuple) -> tuple:
    # flowinfo is route metadata; address, port and scope identify an endpoint.
    scope = sockaddr[3] if family == socket.AF_INET6 and len(sockaddr) > 3 else 0
    return family, sockaddr[0], sockaddr[1], scope


async def _do_resolve(host: str, port: int) -> list[tuple[int, tuple]]:
    numeric = _numeric_address(host, port)
    if numeric is not None:
        return numeric

    infos = await asyncio.get_running_loop().getaddrinfo(
        host, port, type=socket.SOCK_STREAM
    )
    result: list[tuple[int, tuple]] = []
    seen: set[tuple] = set()
    # Keep RFC 6724 order from the operating system; don't force IPv4 first.
    for family, _socktype, _proto, _canonname, sockaddr in infos:
        if family not in (socket.AF_INET, socket.AF_INET6):
            continue
        identity = _sockaddr_identity(family, sockaddr)
        if identity in seen:
            continue
        seen.add(identity)
        result.append((family, sockaddr))
    return result


def _interleave_families(
    addresses: list[tuple[int, tuple]], preferred: tuple[int, tuple] | None
) -> list[tuple[int, tuple]]:
    """HEv2-style alternation while keeping an observed winner first."""
    unique = list(addresses)
    if preferred is not None:
        try:
            unique.remove(preferred)
        except ValueError:
            pass
        else:
            unique.insert(0, preferred)

    if not unique:
        return []
    first_family = unique[0][0]
    second_family = socket.AF_INET if first_family == socket.AF_INET6 else socket.AF_INET6
    queues = {
        first_family: [item for item in unique if item[0] == first_family],
        second_family: [item for item in unique if item[0] == second_family],
    }
    ordered: list[tuple[int, tuple]] = []
    while queues[first_family] or queues[second_family]:
        if queues[first_family]:
            ordered.append(queues[first_family].pop(0))
        if queues[second_family]:
            ordered.append(queues[second_family].pop(0))
    return ordered


async def _resolve(host: str, port: int) -> list[tuple[int, tuple]]:
    key = (host, port)
    now = time.monotonic()
    hit = _dns_cache.get(key)
    if hit and hit[0] > now:
        result = list(hit[1])
    else:
        task = _dns_inflight.get(key)
        if task is None:
            task = asyncio.create_task(_do_resolve(host, port))
            _dns_inflight[key] = task
        try:
            result = list(await asyncio.shield(task))
        finally:
            if _dns_inflight.get(key) is task and task.done():
                _dns_inflight.pop(key, None)
        if len(_dns_cache) >= DNS_CACHE_MAX:
            _dns_cache.clear()
            _route_cache.clear()
            _route_health.clear()
        _dns_cache[key] = (now + DNS_TTL, list(result))

    route = _route_cache.get(key)
    preferred = None
    if route and route[0] > now:
        preferred = (route[1], route[2])
    return _interleave_families(result, preferred)


def _candidate_key(host: str, port: int, family: int, sockaddr: tuple) -> tuple:
    return (host, port, *_sockaddr_identity(family, sockaddr))


def _record_route_success(
    host: str, port: int, family: int, sockaddr: tuple, connect_ms: float
) -> None:
    key = _candidate_key(host, port, family, sockaddr)
    old = _route_health.get(key)
    ewma = connect_ms if old is None else 0.70 * old[0] + 0.30 * connect_ms
    _route_health[key] = (ewma, 0, 0.0)
    _route_cache[(host, port)] = (
        time.monotonic() + ROUTE_TTL, family, sockaddr
    )


def _record_route_failure(host: str, port: int, family: int, sockaddr: tuple) -> None:
    key = _candidate_key(host, port, family, sockaddr)
    old = _route_health.get(key, (9999.0, 0, 0.0))
    failures = min(old[1] + 1, 8)
    cooldown = min(ROUTE_FAILURE_BASE * (2 ** (failures - 1)), ROUTE_FAILURE_MAX)
    _route_health[key] = (old[0], failures, time.monotonic() + cooldown)


def _connection_schedule(
    host: str, port: int, addresses: list[tuple[int, tuple]]
) -> list[tuple[float, int, tuple]]:
    """Start first IPv6 and first IPv4 together; stagger only extra addresses."""
    # Never duplicate the same numeric endpoint: it adds target load and delays
    # short web requests without providing another route. Dual-stack DNS still
    # starts at least one candidate from each available family.
    selected = list(addresses[:PARALLEL_CONNECT])

    seen_family: set[int] = set()
    extra_index = 0
    schedule: list[tuple[float, int, tuple]] = []
    now = time.monotonic()
    for family, sockaddr in selected:
        if family not in seen_family:
            delay = DUAL_STACK_DELAY
            seen_family.add(family)
        else:
            extra_index += 1
            delay = ADDITIONAL_CONNECT_STAGGER * extra_index
        health = _route_health.get(_candidate_key(host, port, family, sockaddr))
        if health and health[2] > now:
            # Failed routes still get retried, but never ahead of a healthy family.
            delay = max(delay, ADDITIONAL_CONNECT_STAGGER * 2)
        schedule.append((delay, family, sockaddr))
    return schedule


async def _connect_candidate(
    delay: float, family: int, sockaddr: tuple
) -> tuple[asyncio.StreamReader, asyncio.StreamWriter, float]:
    if delay > 0:
        await asyncio.sleep(delay)
    started = time.monotonic()
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setblocking(False)
    try:
        # Start the SYN immediately. Full high-throughput socket tuning happens
        # after the race has a winner, so dozens of short page connections don't
        # serialize behind setsockopt calls before they can even connect.
        await asyncio.get_running_loop().sock_connect(sock, sockaddr)
        reader, writer = await asyncio.open_connection(sock=sock, limit=STREAM_LIMIT)
        return reader, writer, (time.monotonic() - started) * 1000.0
    except BaseException:
        sock.close()
        raise


async def _open_upstream(address: str, port: int):
    """Adaptive Happy-Eyeballs: IPv6 improves without delaying IPv4 fallback."""
    try:
        addresses = await _resolve(address, port)
    except Exception:
        addresses = []
    if not addresses:
        return await asyncio.wait_for(
            asyncio.open_connection(address, port, limit=STREAM_LIMIT),
            timeout=CONNECT_TIMEOUT,
        )

    # The common numeric/single-address case needs no task set or race. This
    # keeps first-byte latency low for pages while the multi-address path below
    # retains full Happy-Eyeballs behavior.
    if len(addresses) == 1:
        family, sockaddr = addresses[0]
        try:
            async with asyncio.timeout(CONNECT_TIMEOUT):
                reader, writer, connect_ms = await _connect_candidate(
                    0.0, family, sockaddr
                )
        except Exception:
            _record_route_failure(address, port, family, sockaddr)
            raise
        _record_route_success(address, port, family, sockaddr, connect_ms)
        return reader, writer

    schedule = _connection_schedule(address, port, addresses)

    async def attempt(delay: float, family: int, sockaddr: tuple):
        try:
            reader, writer, connect_ms = await _connect_candidate(
                delay, family, sockaddr
            )
            return reader, writer, family, sockaddr, connect_ms
        except asyncio.CancelledError:
            raise
        except Exception:
            _record_route_failure(address, port, family, sockaddr)
            raise

    pending = {
        asyncio.create_task(attempt(delay, family, sockaddr))
        for delay, family, sockaddr in schedule
    }
    winner = None
    last_error: Exception | None = None
    deadline = time.monotonic() + CONNECT_TIMEOUT
    try:
        while pending and winner is None:
            done, pending = await asyncio.wait(
                pending,
                timeout=max(deadline - time.monotonic(), 0.01),
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done:
                raise asyncio.TimeoutError
            successes = []
            for task in done:
                try:
                    successes.append(task.result())
                except Exception as exc:
                    last_error = exc
            if successes:
                # If both families completed in the same loop turn, keep lower RTT.
                successes.sort(key=lambda item: item[4])
                winner = successes[0]
                for result in successes[1:]:
                    result[1].close()
    finally:
        for task in pending:
            task.cancel()
        if pending:
            results = await asyncio.gather(*pending, return_exceptions=True)
            for result in results:
                if isinstance(result, tuple):
                    result[1].close()

    if winner is None:
        raise last_error or OSError(f"connect failed: {address}:{port}")
    reader, writer, family, sockaddr, connect_ms = winner
    _record_route_success(address, port, family, sockaddr, connect_ms)
    return reader, writer


# لایه‌ی «آی‌پی خروجی» (پروکسی HTTP/HTTPS/SOCKS5) از همین کانکتور استفاده می‌کند،
# پس اتصال به پروکسی هم Happy-Eyeballs، حافظه‌ی مسیر و تیونینگ سوکت را می‌گیرد.
outbound.set_dialer(_open_upstream)
outbound.set_tuner(lambda writer: _tune_socket(writer, WRITE_HW_START))


# ── VLESS header + accounting ────────────────────────────────────────────────
def _parse_vless_header(chunk: bytes | bytearray | memoryview):
    view = memoryview(chunk)
    length = len(view)
    if length < 19:
        raise ValueError("incomplete vless prefix")

    pos = 1 + 16
    addon_len = view[pos]
    pos += 1
    if length < pos + addon_len + 4:
        raise ValueError("incomplete vless options")
    pos += addon_len

    command = view[pos]
    pos += 1
    if command != 1:
        raise ValueError(f"unsupported vless command: {command}")

    port = int.from_bytes(view[pos : pos + 2], "big")
    pos += 2
    if port == 0:
        raise ValueError("invalid destination port")

    addr_type = view[pos]
    pos += 1
    if addr_type == 1:
        if length < pos + 4:
            raise ValueError("incomplete ipv4")
        address = socket.inet_ntop(socket.AF_INET, view[pos : pos + 4])
        pos += 4
    elif addr_type == 2:
        if length < pos + 1:
            raise ValueError("incomplete domain length")
        domain_len = view[pos]
        pos += 1
        if domain_len == 0 or length < pos + domain_len:
            raise ValueError("incomplete domain")
        address = bytes(view[pos : pos + domain_len]).decode("idna")
        pos += domain_len
    elif addr_type == 3:
        if length < pos + 16:
            raise ValueError("incomplete ipv6")
        address = socket.inet_ntop(socket.AF_INET6, view[pos : pos + 16])
        pos += 16
    else:
        raise ValueError(f"unknown address type: {addr_type}")

    return command, address, port, bytes(view[pos:])


async def check_and_use(uid: str, nbytes: int) -> bool:
    if nbytes <= 0:
        return True
    async with LINKS_LOCK:
        link = LINKS.get(uid)
        if link is None or not is_link_allowed(link):
            return False
        link["used_bytes"] = int(link.get("used_bytes", 0) or 0) + nbytes
        stats["total_bytes"] = int(stats.get("total_bytes", 0) or 0) + nbytes
        hourly_traffic[now_ir().strftime("%H:00")] += nbytes
    return True


def _speed_limited(uid: str) -> bool:
    link = LINKS.get(uid)
    return bool(link and int(link.get("speed_limit_bytes", 0) or 0) > 0)


# ── Relay: WebSocket -> target TCP ──────────────────────────────────────────
async def relay_ws_to_tcp(
    ws: WebSocket,
    writer: asyncio.StreamWriter,
    conn_id: str,
    uid: str,
    io: _WSIO | None = None,
):
    io = io or _WSIO(ws)
    gate = QuotaGate(uid, check_and_use)
    conn = connections.get(conn_id)
    flow = _AdaptiveFlow()
    limited = _speed_limited(uid)
    transport = writer.transport
    ticks = 0
    # Cache bound methods used for every WS frame; this removes repeated
    # attribute lookups from the upload hot loop without changing semantics.
    write = writer.write
    buffer_size = transport.get_write_buffer_size
    receive_nowait = io.receive_nowait
    stage = gate.stage
    commit = gate.commit
    throttle_local = throttle

    stop = False
    try:
        while not stop:
            message = await io.receive()
            burst_messages = 0
            burst_bytes = 0
            while message is not None:
                burst_messages += 1
                if message["type"] == "websocket.disconnect":
                    stop = True
                    break
                data = message.get("bytes")
                if data is None:
                    text = message.get("text")
                    data = text.encode() if text else None
                if data:
                    nbytes = len(data)
                    account_batch = stage(nbytes)
                    if account_batch < 0 or (
                        account_batch and not await commit(account_batch)
                    ):
                        await ws.close(code=1008, reason="quota/disabled/unknown")
                        stop = True
                        break

                    ticks += 1
                    if not (ticks & 127):
                        limited = _speed_limited(uid)
                    if limited:
                        await throttle_local(uid, nbytes)
                    if conn is not None:
                        conn["bytes"] += nbytes
                    write(data)
                    burst_bytes += nbytes

                if buffer_size() >= flow.high_water:
                    started = time.monotonic()
                    await writer.drain()
                    flow.observe((time.monotonic() - started) * 1000.0, transport)
                    break
                if (
                    limited
                    or burst_messages >= WS_UPLOAD_BURST_MESSAGES
                    or burst_bytes >= WS_UPLOAD_BURST_BYTES
                ):
                    break
                message = receive_nowait()
    except (WebSocketDisconnect, ConnectionError, OSError):
        pass
    finally:
        try:
            await gate.flush()
        except Exception:
            pass
        try:
            writer.write_eof()
        except Exception:
            pass


async def _read_stream_chunk(
    reader: asyncio.StreamReader, max_bytes: int, coalesce_one_turn: bool
) -> bytes | bytearray:
    """Read with one-copy avoidance on CPython's feature-detected StreamReader.

    ``StreamReader.read`` always copies its bytearray. When the entire buffered
    burst fits in one WS frame, detach that bytearray and replace it with an
    empty one. The custom Sans-I/O sender accepts bytes-like objects, eliminating
    that full payload copy. Any incompatible Python implementation falls back to
    the public ``read`` API.
    """
    buffer = getattr(reader, "_buffer", None)
    wait_for_data = getattr(reader, "_wait_for_data", None)
    maybe_resume = getattr(reader, "_maybe_resume_transport", None)
    if not isinstance(buffer, bytearray) or not callable(wait_for_data):
        return await reader.read(max_bytes)

    exception = getattr(reader, "_exception", None)
    if exception is not None:
        raise exception
    if not buffer and not getattr(reader, "_eof", False):
        await wait_for_data("turbo-read")

    # During established bulk flow, give the event loop exactly one zero-delay
    # turn to append already-arrived packets. There is no timer and interactive
    # traffic never enters this branch.
    if (
        coalesce_one_turn
        and len(reader._buffer) < READ_MIN
        and not getattr(reader, "_eof", False)
    ):
        await asyncio.sleep(0)

    buffer = reader._buffer
    if not buffer:
        return b""
    count = min(len(buffer), max_bytes)
    if count == len(buffer):
        data = buffer
        reader._buffer = bytearray()
    else:
        data = bytes(memoryview(buffer)[:count])
        del buffer[:count]
    if callable(maybe_resume):
        maybe_resume()
    return data


# ── Relay: target TCP -> WebSocket ──────────────────────────────────────────
async def relay_tcp_to_ws(
    ws: WebSocket,
    reader: asyncio.StreamReader,
    conn_id: str,
    uid: str,
    io: _WSIO | None = None,
):
    io = io or _WSIO(ws)
    gate = QuotaGate(uid, check_and_use)
    conn = connections.get(conn_id)
    limited = _speed_limited(uid)
    ticks = 0
    bulk_streak = 0
    # Same hot-path caching for target -> WS frames.
    send_bytes = io.send_bytes
    stage = gate.stage
    commit = gate.commit
    throttle_local = throttle

    try:
        await send_bytes(b"\x00\x00")
        while True:
            data = await _read_stream_chunk(
                reader, READ_MAX, bulk_streak >= BULK_STREAK_TRIGGER
            )
            if not data:
                break

            nbytes = len(data)
            if nbytes >= BULK_TRIGGER:
                bulk_streak = min(bulk_streak + 1, BULK_STREAK_TRIGGER + 2)
            elif nbytes < READ_MIN // 4:
                bulk_streak = max(bulk_streak - 1, 0)

            account_batch = stage(nbytes)
            if account_batch < 0 or (
                account_batch and not await commit(account_batch)
            ):
                await ws.close(code=1008, reason="quota/disabled/unknown")
                break

            ticks += 1
            if not (ticks & 127):
                limited = _speed_limited(uid)
            if limited:
                await throttle_local(uid, nbytes)

            if conn is not None:
                conn["bytes"] += nbytes
            await send_bytes(data)
    except (WebSocketDisconnect, ConnectionError, OSError):
        pass
    finally:
        try:
            await gate.flush()
        except Exception:
            pass
        try:
            await io.flush()
        except Exception:
            pass


# ── Tunnel lifecycle ─────────────────────────────────────────────────────────
async def _collect_header(
    io: _WSIO, early: bytes, *, prefetch_payload: bool = False
):
    """Collect VLESS header and a bounded complete TLS record for proxies.

    Many clients put the ClientHello in the next WS frame. Without this small
    prefetch window a proxy can accept CONNECT but never be verified, leaving
    the client at ping=-1. Direct configs do not wait here.
    """
    buffer = bytearray(early)
    prefetch_deadline = None
    while True:
        parsed = None
        if len(buffer) >= 19:
            try:
                parsed = _parse_vless_header(buffer)
            except ValueError:
                parsed = None
        if parsed is not None:
            payload = parsed[3]
            if not prefetch_payload:
                return (*parsed, len(buffer))
            if payload:
                if payload[0] != 0x16 or (len(payload) >= 2 and payload[1] != 0x03):
                    return (*parsed, len(buffer))
            if len(payload) >= 5:
                record_size = 5 + int.from_bytes(payload[3:5], "big")
                if len(payload) >= record_size:
                    return (*parsed, len(buffer))
            if prefetch_deadline is None:
                prefetch_deadline = time.monotonic() + 0.8
            remaining = prefetch_deadline - time.monotonic()
            if remaining <= 0:
                return (*parsed, len(buffer))
            timeout = min(remaining, HEADER_TIMEOUT)
        else:
            if len(buffer) >= HEADER_MAX:
                raise ValueError("vless header too large or invalid")
            timeout = HEADER_TIMEOUT
        try:
            message = await asyncio.wait_for(io.receive(), timeout=timeout)
        except asyncio.TimeoutError:
            if parsed is not None:
                return (*parsed, len(buffer))
            raise
        if message["type"] == "websocket.disconnect":
            raise WebSocketDisconnect(1006)
        chunk = message.get("bytes")
        if chunk is None and message.get("text") is not None:
            try:
                chunk = base64.b64decode(message["text"], validate=True)
            except Exception:
                chunk = message["text"].encode()
        if chunk:
            buffer.extend(chunk)


async def websocket_tunnel(ws: WebSocket, uuid: str):
    early = _early_data(ws)
    await ws.accept()
    _tune_client_socket(ws)
    io = _WSIO(ws)

    async with LINKS_LOCK:
        link = LINKS.get(uuid)

    if not is_link_allowed(link):
        logger.warning("WS rejected uuid=%s… (not allowed)", uuid[:8])
        await ws.close(code=1008, reason="not authorized")
        return

    ip = _ws_client_ip(ws)
    if not is_ip_allowed(link, uuid, ip):
        logger.warning("WS rejected uuid=%s… ip=%s (ip limit)", uuid[:8], ip)
        log_activity(
            "connection",
            f"اتصال {ip} به کانفیگ «{link.get('label', '?')}» رد شد (محدودیت تعداد آی‌پی)",
            "warn",
        )
        await ws.close(code=1008, reason="ip limit reached")
        return

    conn_id = secrets.token_urlsafe(6)
    connections[conn_id] = {
        "uuid": uuid,
        "ip": ip,
        "transport": "vless-ws-hyper",
        "connected_at": datetime.now().isoformat(),
        "bytes": 0,
    }
    logger.info(
        "WS [%s] uuid=%s… ip=%s ed=%dB total=%d",
        conn_id,
        uuid[:8],
        ip,
        len(early),
        len(connections),
    )
    log_activity(
        "connection",
        f"اتصال جدید از {ip} (کانفیگ {link.get('label', '?')})",
        "info",
    )

    writer: asyncio.StreamWriter | None = None
    try:
        _command, address, port, payload, header_bytes = await _collect_header(
            io, early, prefetch_payload=link_uses_proxy(link)
        )
        if not await check_and_use(uuid, header_bytes):
            await ws.close(code=1008, reason="quota/disabled")
            return

        stats["total_requests"] = int(stats.get("total_requests", 0) or 0) + 1
        conn = connections.get(conn_id)
        if conn is not None:
            conn["bytes"] += header_bytes
        logger.info("WS [%s] -> %s:%d", conn_id, address, port)

        reader, writer, payload_sent = await open_outbound(
            address, port, payload, link=link, uuid=uuid
        )
        _tune_socket(writer, WRITE_HW_START)
        if payload and not payload_sent:
            writer.write(payload)
            await writer.drain()

        upload = asyncio.create_task(
            relay_ws_to_tcp(ws, writer, conn_id, uuid, io), name=f"ws-up-{conn_id}"
        )
        download = asyncio.create_task(
            relay_tcp_to_ws(ws, reader, conn_id, uuid, io),
            name=f"ws-down-{conn_id}",
        )
        done, pending = await asyncio.wait(
            {upload, download}, return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)
        # Retrieve completed task exceptions so programming faults are visible.
        for task in done:
            error = task.exception()
            if error is not None:
                raise error

        await io.flush()
        try:
            await save_state(rotate=False)
        except TypeError as exc:
            # Compatibility with embedded/test callbacks that predate v19.
            if "rotate" not in str(exc):
                raise
            await save_state()

    except WebSocketDisconnect:
        pass
    except asyncio.TimeoutError:
        stats["total_errors"] = int(stats.get("total_errors", 0) or 0) + 1
        error_logs.append(
            {"error": "connection timeout", "time": datetime.now().isoformat()}
        )
    except Exception as exc:
        stats["total_errors"] = int(stats.get("total_errors", 0) or 0) + 1
        error_logs.append({"error": str(exc), "time": datetime.now().isoformat()})
        logger.error("WS error [%s]: %s", conn_id, exc)
    finally:
        if writer is not None:
            try:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=2.0)
            except Exception:
                pass
        connections.pop(conn_id, None)
        logger.info("WS closed [%s] total=%d", conn_id, len(connections))
