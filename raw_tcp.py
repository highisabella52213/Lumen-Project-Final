"""Deployment-gated native VLESS Raw TCP ingress.

This module intentionally contains no proxy-routing knowledge.  It owns only
the Railway TCP Proxy/application TLS readiness checks and the separately
managed asyncio listener.  The listener hands an authenticated raw byte stream
to ``relay_vless.raw_tcp_tunnel`` which uses the existing VLESS and exact
outbound pipeline.
"""
from __future__ import annotations

import asyncio
import json
import os
import ssl
from dataclasses import dataclass
from pathlib import Path

from config_address import normalize_sni


RAW_HEADER_TIMEOUT = 5.0
RAW_STREAM_LIMIT = 1024 * 1024


def _positive_port(value: object) -> int | None:
    try:
        port = int(str(value or "").strip())
    except (TypeError, ValueError):
        return None
    return port if 1 <= port <= 65535 else None


def _connection_limit() -> int:
    try:
        return min(1024, max(1, int(os.environ.get("VLESS_TCP_MAX_CONNECTIONS", "128"))))
    except ValueError:
        return 128


def _safe_location_id(value: object) -> str:
    return "".join(
        char for char in str(value or "") if char.isalnum() or char in "-_"
    )[:24]


@dataclass(frozen=True)
class RawTCPDeployment:
    ready: bool
    reason: str
    listen_host: str = "0.0.0.0"
    listen_port: int = 0
    public_host: str = ""
    public_port: int = 0
    cert_file: Path | None = None
    key_file: Path | None = None
    uri_network: str = ""
    sni_locations: dict[str, str] | None = None
    default_sni: str = ""

    def endpoint_for_location(self, location_id: object = None) -> tuple[str, int, str]:
        if not self.ready or not self.sni_locations:
            raise ValueError(self.reason or "Raw TCP ingress is not configured")
        location = _safe_location_id(location_id)
        if not location:
            return self.public_host, self.public_port, self.default_sni
        names = [
            name for name, mapped_location in self.sni_locations.items()
            if mapped_location == location
        ]
        if len(names) != 1:
            raise ValueError(
                "Raw TCP has no verified SNI profile for the selected location"
            )
        return self.public_host, self.public_port, names[0]

    def location_for_sni(self, server_name: object) -> str | None:
        if not self.sni_locations:
            return None
        try:
            normalized = normalize_sni(str(server_name or ""))
        except ValueError:
            return None
        return self.sni_locations.get(normalized)


def deployment() -> RawTCPDeployment:
    """Read the explicit Railway/TLS deployment contract without leaking paths."""
    application_port = _positive_port(os.environ.get("RAILWAY_TCP_APPLICATION_PORT"))
    listen_port = _positive_port(os.environ.get("VLESS_TCP_LISTEN_PORT"))
    public_port = _positive_port(os.environ.get("RAILWAY_TCP_PROXY_PORT"))
    public_host = str(os.environ.get("RAILWAY_TCP_PROXY_DOMAIN", "")).strip()
    uri_network = str(os.environ.get("VLESS_TCP_URI_NETWORK", "")).strip().lower()
    cert_name = str(os.environ.get("VLESS_TCP_TLS_CERT_FILE", "")).strip()
    key_name = str(os.environ.get("VLESS_TCP_TLS_KEY_FILE", "")).strip()
    default_name = str(os.environ.get("VLESS_TCP_DEFAULT_SNI", "")).strip()
    raw_map = str(os.environ.get("VLESS_TCP_SNI_MAP", "")).strip()

    if not application_port or not listen_port or application_port != listen_port:
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: Railway TCP ingress is not configured for the listener port.",
        )
    if not public_host or not public_port:
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: Railway TCP Proxy public hostname and port are missing.",
        )
    if uri_network not in {"tcp", "raw"}:
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: set VLESS_TCP_URI_NETWORK to the staging-validated tcp or raw spelling.",
        )
    if not cert_name or not key_name:
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: application TLS certificate and key paths are required.",
        )
    cert_file, key_file = Path(cert_name), Path(key_name)
    if not cert_file.is_file() or not key_file.is_file():
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: configured application TLS files are not readable.",
        )
    if not raw_map or not default_name:
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: an explicit SNI-to-location map and default SNI are required.",
        )
    try:
        parsed_map = json.loads(raw_map)
        if not isinstance(parsed_map, dict) or not parsed_map:
            raise ValueError
        sni_locations: dict[str, str] = {}
        seen_locations: set[str] = set()
        for raw_name, raw_location in parsed_map.items():
            name = normalize_sni(str(raw_name))
            location = _safe_location_id(raw_location)
            if str(raw_location or "").strip() and not location:
                raise ValueError
            if location and location in seen_locations:
                raise ValueError
            if name in sni_locations:
                raise ValueError
            sni_locations[name] = location
            if location:
                seen_locations.add(location)
        default_sni = normalize_sni(default_name)
        if sni_locations.get(default_sni) != "":
            raise ValueError
    except (TypeError, ValueError, json.JSONDecodeError):
        return RawTCPDeployment(
            False,
            "Raw TCP unavailable: VLESS_TCP_SNI_MAP must be a unique validated hostname-to-location JSON map.",
        )

    return RawTCPDeployment(
        True,
        "",
        listen_host=str(os.environ.get("VLESS_TCP_LISTEN_HOST", "0.0.0.0")).strip() or "0.0.0.0",
        listen_port=listen_port,
        public_host=public_host,
        public_port=public_port,
        cert_file=cert_file,
        key_file=key_file,
        uri_network=uri_network,
        sni_locations=sni_locations,
        default_sni=default_sni,
    )


class RawTCPListener:
    """One TLS Raw TCP listener, deliberately separate from Uvicorn."""

    def __init__(self) -> None:
        self._server: asyncio.AbstractServer | None = None
        self._tasks: set[asyncio.Task] = set()
        self._sni_by_ssl_id: dict[int, str] = {}
        self._admission = asyncio.Semaphore(_connection_limit())
        self._error = ""

    @property
    def running(self) -> bool:
        return self._server is not None and bool(self._server.sockets)

    @property
    def error(self) -> str:
        return self._error

    async def start(self) -> None:
        if self.running:
            return
        settings = deployment()
        if not settings.ready:
            self._error = settings.reason
            return
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.minimum_version = ssl.TLSVersion.TLSv1_2
            context.options |= ssl.OP_NO_COMPRESSION
            context.load_cert_chain(str(settings.cert_file), str(settings.key_file))

            def remember_sni(ssl_object, server_name, _context):
                if server_name:
                    self._sni_by_ssl_id[id(ssl_object)] = str(server_name)

            context.set_servername_callback(remember_sni)
            self._server = await asyncio.start_server(
                self._accepted,
                settings.listen_host,
                settings.listen_port,
                ssl=context,
                ssl_handshake_timeout=RAW_HEADER_TIMEOUT,
                limit=RAW_STREAM_LIMIT,
                backlog=256,
            )
            self._error = ""
        except Exception:
            self._server = None
            self._error = "Raw TCP unavailable: TLS listener could not start."

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        tasks = tuple(self._tasks)
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._sni_by_ssl_id.clear()

    async def _accepted(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        task = asyncio.current_task()
        if task is not None:
            self._tasks.add(task)
        acquired = False
        try:
            try:
                await asyncio.wait_for(self._admission.acquire(), timeout=0.05)
                acquired = True
            except asyncio.TimeoutError:
                return
            settings = deployment()
            ssl_object = writer.get_extra_info("ssl_object")
            server_name = self._sni_by_ssl_id.pop(id(ssl_object), "")
            location_id = settings.location_for_sni(server_name)
            if not server_name or location_id is None:
                return
            peer = writer.get_extra_info("peername") or ("unknown", 0)
            from relay_vless import raw_tcp_tunnel

            await raw_tcp_tunnel(
                reader,
                writer,
                client_ip=str(peer[0]),
                location_id=location_id,
                server_name=str(server_name),
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # The byte-stream handler records safe connection categories.  Do
            # not expose handshake data, TLS errors, IDs, or endpoint details.
            pass
        finally:
            if acquired:
                self._admission.release()
            try:
                writer.close()
                await asyncio.wait_for(writer.wait_closed(), timeout=2.0)
            except Exception:
                pass
            if task is not None:
                self._tasks.discard(task)


RAW_TCP_LISTENER = RawTCPListener()


def availability() -> tuple[bool, str]:
    settings = deployment()
    if not settings.ready:
        return False, settings.reason
    if not RAW_TCP_LISTENER.running:
        return False, RAW_TCP_LISTENER.error or "Raw TCP unavailable: TLS listener is not running."
    return True, ""