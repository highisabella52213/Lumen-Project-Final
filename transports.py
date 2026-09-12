"""Transport capability registry for the native VLESS relay.

Transport concerns deliberately live here: each adapter owns its identifier,
validation, VLESS serialization, and whether the *installed* data-plane can
run it. It must never select an exit proxy, location, or fallback route.

The current application is a native FastAPI/Uvicorn WebSocket relay with an
optional, separately managed TLS Raw TCP listener. It does not bundle or
invoke Xray/sing-box, a gRPC/HTTP2 server, or a UDP/KCP listener. Consequently,
gRPC, KCP, and HTTPUpgrade are recognized so the admin UI and API can report
an accurate compatibility result, but they are rejected before they can be
persisted or serialized as a working configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import raw_tcp


class TransportValidationError(ValueError):
    """A transport identifier or its settings are malformed."""


class TransportUnavailableError(TransportValidationError):
    """A known transport cannot run on the installed data plane."""


def _safe_location_id(value: object) -> str:
    """Bound a subscription location hint without changing routing semantics."""
    return "".join(
        char for char in str(value or "") if char.isalnum() or char in "-_"
    )[:24]


@dataclass(frozen=True)
class TransportAdapter:
    """One VLESS transport's schema and runtime integration contract."""

    id: str
    label: str
    short_label: str
    description: str
    available: bool
    unavailable_reason: str = ""
    default_alpn: str = "http/1.1"

    def availability(self) -> tuple[bool, str]:
        """Return the runtime status without exposing deployment secrets."""
        return self.available, self.unavailable_reason

    def validate_settings(self, value: object) -> dict[str, Any]:
        """Validate this transport's own settings only.

        The native WebSocket transport has no separately configurable
        transport settings today; Address, SNI, ALPN, fingerprint, and port
        remain the existing link-level fields. Rejecting unknown settings
        prevents clients from assuming an option was silently accepted.
        """
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TransportValidationError(
                f"{self.label} transport settings must be an object"
            )
        if value:
            names = ", ".join(sorted(str(key) for key in value))
            raise TransportValidationError(
                f"{self.label} does not support transport settings: {names}"
            )
        return {}

    def require_available(self) -> None:
        available, detail = self.availability()
        if not available:
            raise TransportUnavailableError(
                f"{self.label}: NOT SUPPORTED BY CURRENT RUNTIME. "
                f"{detail}"
            )

    def validate_security(self, value: object) -> str:
        """The native VLESS ingress accepts TLS only.

        Keep this in the transport adapter so an API client cannot submit a
        security setting that is silently ignored or downgraded.
        """
        security = str(value if value is not None else "tls").strip().lower()
        if security != "tls":
            raise TransportValidationError(
                f"{self.label} requires security=tls in this deployment"
            )
        return security

    def vless_parameters(
        self, *, uuid: str, transport_host: str, location_id: object = None
    ) -> dict[str, str]:
        """Generate this adapter's VLESS URI parameters.

        The base adapter is the WebSocket serializer. Unsupported adapters
        intentionally raise rather than emit a URI that clients cannot use;
        deployment-gated adapters override this method with their native
        serializer.
        """
        self.require_available()
        if self.id != "vless-ws":
            # Defensive guard for a future adapter: availability alone is not
            # evidence that it has been integrated with the native runtime.
            raise TransportUnavailableError(
                f"{self.label}: NOT SUPPORTED BY CURRENT RUNTIME. "
                "No native serializer is registered."
            )
        path = f"/ws/{uuid}?ed=4096"
        safe_location = _safe_location_id(location_id)
        if safe_location:
            path += f"&loc={safe_location}"
        return {"type": "ws", "host": transport_host, "path": path}

    def capability(self) -> dict[str, object]:
        """Safe capability data for the authenticated transport-management UI."""
        available, detail = self.availability()
        return {
            "id": self.id,
            "label": self.label,
            "short_label": self.short_label,
            "description": self.description,
            "available": available,
            "status": (
                "VERIFIED — REAL RUNTIME SUPPORT"
                if available
                else "NOT SUPPORTED BY CURRENT RUNTIME"
            ),
            "detail": "" if available else detail,
            "settings_schema": {
                "type": "object",
                "additional_properties": False,
                "properties": {},
            },
        }


@dataclass(frozen=True)
class RawTCPAdapter(TransportAdapter):
    """The optional native Raw TCP ingress, backed by ``raw_tcp`` only."""

    def availability(self) -> tuple[bool, str]:
        return raw_tcp.availability()

    def capability(self) -> dict[str, object]:
        payload = super().capability()
        if not payload["available"]:
            payload["status"] = "BLOCKED — RAILWAY/TLS DEPLOYMENT REQUIREMENT"
        return payload

    def validate_settings(self, value: object) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict) or value:
            raise TransportValidationError(
                "Raw TCP transport settings are deployment-managed; "
                "custom transport settings are not accepted"
            )
        return {}

    def vless_parameters(
        self, *, uuid: str, transport_host: str, location_id: object = None
    ) -> dict[str, str]:
        self.require_available()
        # ``type`` is selected explicitly by the staging-validated deployment
        # setting; no client-specific spelling is guessed by the application.
        return {"type": raw_tcp.deployment().uri_network}

    def endpoint(
        self,
        *,
        address: object,
        port: object,
        sni: object,
        fallback_host: str,
        location_id: object = None,
    ) -> tuple[str, int, str]:
        if any(str(value or "").strip() for value in (address, sni)):
            raise TransportValidationError(
                "Raw TCP address and SNI are managed by the verified TCP deployment"
            )
        if port not in (None, "", 443):
            raise TransportValidationError(
                "Raw TCP port is assigned by the Railway TCP Proxy"
            )
        return raw_tcp.deployment().endpoint_for_location(location_id)


class TransportRegistry:
    """Fixed capability registry for this deployment's native data plane."""

    def __init__(self, adapters: tuple[TransportAdapter, ...]) -> None:
        self._adapters = {adapter.id: adapter for adapter in adapters}
        self._ordered = adapters

    def get(self, transport_id: object) -> TransportAdapter:
        value = str(transport_id or "").strip()
        adapter = self._adapters.get(value)
        if adapter is None:
            raise TransportValidationError(
                f"Unknown transport: {value or '(empty)'}"
            )
        return adapter

    def validate(
        self, transport_id: object, settings: object = None
    ) -> tuple[str, dict[str, Any]]:
        """Return normalized settings for one genuinely runnable transport."""
        adapter = self.get(transport_id)
        adapter.require_available()
        return adapter.id, adapter.validate_settings(settings)

    def is_available(self, transport_id: object) -> bool:
        try:
            return self.get(transport_id).availability()[0]
        except TransportValidationError:
            return False

    def validate_security(self, transport_id: object, value: object = None) -> str:
        adapter = self.get(transport_id)
        adapter.require_available()
        return adapter.validate_security(value)

    def vless_parameters(
        self,
        transport_id: object,
        *,
        uuid: str,
        transport_host: str,
        location_id: object = None,
        settings: object = None,
    ) -> dict[str, str]:
        adapter = self.get(transport_id)
        adapter.require_available()
        adapter.validate_settings(settings)
        return adapter.vless_parameters(
            uuid=uuid, transport_host=transport_host, location_id=location_id
        )

    def capabilities(self) -> list[dict[str, object]]:
        return [adapter.capability() for adapter in self._ordered]

    def endpoint(
        self,
        transport_id: object,
        *,
        address: object,
        port: object,
        sni: object,
        fallback_host: str,
        location_id: object = None,
    ) -> tuple[str, int, str] | None:
        """Return a deployment-owned endpoint for transports that need one."""
        adapter = self.get(transport_id)
        endpoint = getattr(adapter, "endpoint", None)
        if endpoint is None:
            return None
        adapter.require_available()
        return endpoint(
            address=address,
            port=port,
            sni=sni,
            fallback_host=fallback_host,
            location_id=location_id,
        )


TRANSPORTS = TransportRegistry(
    (
        TransportAdapter(
            id="vless-ws",
            label="VLESS / WebSocket Turbo",
            short_label="VLESS / WS",
            description="Native WebSocket ingress with the existing Turbo relay.",
            available=True,
        ),
        RawTCPAdapter(
            id="vless-tcp",
            label="VLESS / Raw TCP",
            short_label="VLESS / TCP",
            description="Native TLS Raw TCP ingress through a Railway TCP Proxy.",
            available=False,
            unavailable_reason=(
                "Raw TCP ingress is not configured. Configure the Railway TCP "
                "Proxy, application TLS files, explicit SNI map, and URI network."
            ),
            default_alpn="",
        ),
        TransportAdapter(
            id="vless-grpc",
            label="gRPC",
            short_label="gRPC",
            description="VLESS over gRPC.",
            available=False,
            unavailable_reason=(
                "This deployment has no gRPC/HTTP2 VLESS inbound runtime; "
                "the installed data plane is FastAPI/Uvicorn WebSocket only."
            ),
        ),
        TransportAdapter(
            id="vless-kcp",
            label="KCP",
            short_label="KCP",
            description="VLESS over the KCP UDP transport.",
            available=False,
            unavailable_reason=(
                "This deployment has no UDP/KCP listener or KCP VLESS runtime; "
                "the installed data plane is FastAPI/Uvicorn WebSocket only."
            ),
        ),
        TransportAdapter(
            id="vless-httpupgrade",
            label="HTTPUpgrade",
            short_label="HTTPUpgrade",
            description="VLESS over HTTP Upgrade.",
            available=False,
            unavailable_reason=(
                "This deployment has no HTTPUpgrade VLESS inbound runtime; "
                "the installed data plane is FastAPI/Uvicorn WebSocket only."
            ),
        ),
    )
)