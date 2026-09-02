"""Validation and selection helpers for per-config VLESS address and TLS SNI."""
from __future__ import annotations

import ipaddress
import re
from typing import Iterable

_SPLIT = re.compile(r"[\s,;]+")
_LABEL = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$", re.I)
_IPV4_SHAPE = re.compile(r"^\d+(?:\.\d+){3}$")


def normalize_address(value: object) -> str:
    """Return a canonical IPv4/IPv6/domain without scheme, path or port."""
    raw = str(value or "").strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1].strip()
    if not raw:
        raise ValueError("آدرس خالی است")
    if len(raw) > 253 or any(ch.isspace() for ch in raw):
        raise ValueError("طول یا فاصله در آدرس نامعتبر است")
    if "://" in raw or any(ch in raw for ch in "/?#@"):
        raise ValueError("Address باید فقط IP یا دامنه و بدون پروتکل، مسیر و پورت باشد")
    if "%" in raw:
        raise ValueError("IPv6 دارای zone-id برای لینک عمومی قابل استفاده نیست")
    try:
        return ipaddress.ip_address(raw).compressed
    except ValueError:
        pass
    if _IPV4_SHAPE.fullmatch(raw):
        raise ValueError("IPv4 نامعتبر است")
    try:
        domain = raw.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("دامنه نامعتبر است") from exc
    labels = domain.split(".")
    if not domain or len(domain) > 253 or any(not _LABEL.fullmatch(x) for x in labels):
        raise ValueError("دامنه نامعتبر است")
    return domain


def address_kind(value: object) -> str:
    normalized = normalize_address(value)
    try:
        ip = ipaddress.ip_address(normalized)
        return "ipv6" if ip.version == 6 else "ipv4"
    except ValueError:
        return "domain"


def normalize_sni(value: object) -> str:
    """SNI is a DNS hostname, never a URL or IP literal."""
    normalized = normalize_address(value)
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        return normalized
    raise ValueError("TLS SNI باید دامنه باشد؛ IP را در بخش Address وارد کنید")


def parse_address_list(raw: object) -> list[str]:
    """Parse comma/space/newline separated address candidates; skip invalid entries."""
    out: list[str] = []
    for item in _SPLIT.split(str(raw or "").strip()):
        if not item:
            continue
        try:
            value = normalize_address(item)
        except ValueError:
            continue
        if value not in out:
            out.append(value)
    return out


def unique_valid(values: Iterable[object], *, sni: bool = False) -> list[str]:
    out: list[str] = []
    normalizer = normalize_sni if sni else normalize_address
    for item in values:
        try:
            value = normalizer(item)
        except ValueError:
            continue
        if value not in out:
            out.append(value)
    return out


def link_hosts(address: object, sni: object, service_host: object) -> tuple[str, str]:
    """Return (dial_address, tls_name).

    Custom SNI wins. In auto mode a selected domain is its own SNI; a raw IP
    keeps the service domain as SNI/Host so TLS certificates and routing work.
    """
    service = normalize_address(service_host)
    chosen = normalize_address(address) if str(address or "").strip() else service
    if str(sni or "").strip():
        tls_name = normalize_sni(sni)
    elif address_kind(chosen) == "domain":
        tls_name = normalize_sni(chosen)
    else:
        try:
            tls_name = normalize_sni(service)
        except ValueError:
            tls_name = service
    return chosen, tls_name


def authority_host(value: object) -> str:
    host = normalize_address(value)
    return "[" + host + "]" if address_kind(host) == "ipv6" else host
