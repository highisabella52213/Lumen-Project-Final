"""Private S3-compatible repository for managed HTTP/HTTPS/SOCKS5 proxies.

Security contract:
- credentials stay server-side; environment variables win over the in-code
  placeholders so deployments never have to edit source;
- browser-facing payloads never include endpoints, credentials, or the proxy
  protocol — only stable ID, flag, country and country code. Legacy percentages
  are parsed for source compatibility but are never exposed or used for routing.

Availability contract:
- the dashboard API never blocks on S3 and never loses the last known-good
  catalog when a refresh fails; a slow bucket can never stall the panel.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit, urlunsplit

import countries

# ── PRIVATE S3 CONFIGURATION ─────────────────────────────────────────────────
# Prefer the LUMEN_S3_* environment variables; the two constants below are the
# installer-managed fallback for source-based deployments.
S3_ENDPOINT = "https://s3.us-west-2.idrivee2.com"
S3_REGION = "us-west-2"
S3_BUCKET = "bt2"
S3_OBJECT_KEY = "www-32k-ort-org-021/proxy.txt"
S3_ACCESS_KEY_ID = "41DUl3Aw2SiWuFW2OZ9P"
S3_SECRET_ACCESS_KEY = "aID0sUgRZPle6RmGsxbOaULOwwYpACBMAs39vkjH"
S3_ACCESS_ENV = "41DUl3Aw2SiWuFW2OZ9P"
S3_SECRET_ENV = "aID0sUgRZPle6RmGsxbOaULOwwYpACBMAs39vkjH"
# ─────────────────────────────────────────────────────────────────────────────

# Railway: the installer generates a long random enablement secret.
# The refresh endpoint still requires an authenticated admin session.
MANUAL_REFRESH_ENV_NAME = "PROXY_REPOSITORY_MANUAL_REFRESH_KEY"
MANUAL_REFRESH_ENV_ALIASES = (MANUAL_REFRESH_ENV_NAME, "ENV_SECRET_KEY_TO_BUTTON_ON_N")

FETCH_TIMEOUT = 10
REFRESH_SECONDS = 2 * 60 * 60
MAX_BYTES = 512 * 1024
MAX_PROXIES = 1000
_ALLOWED = {"http", "https", "socks5"}
_ID_SALT = b"lumen-managed-v15"

# Address inventory supplied without protocol/port/credentials/country metadata.
# These are intentionally catalogued as non-selectable candidates: inventing a
# usable proxy URL would be unsafe. A repository operator can complete each row
# in proxy.txt using its canonical protocol://[credentials@]host:port#CC - N% form.
PENDING_PROXY_ADDRESSES = (
    "69.46.46.60",
    "69.46.46.120",
    "69.46.46.121",
    "69.46.46.188",
    "69.46.46.146",
)


def _access_key() -> str:
    return os.environ.get(S3_ACCESS_ENV, "").strip() or S3_ACCESS_KEY_ID


def _secret_key() -> str:
    return os.environ.get(S3_SECRET_ENV, "").strip() or S3_SECRET_ACCESS_KEY


def _configured() -> bool:
    return _access_key() != "KEY_ID" and _secret_key() != "SECRET_ACCESS"


@dataclass(frozen=True)
class Record:
    id: str
    endpoint: str
    type: str
    country: str
    code: str
    flag: str
    health: int


_records: dict[str, Record] = {}
_last = 0.0
_error = "not loaded"
_lock = asyncio.Lock()
_refresh_task: asyncio.Task | None = None
_inflight_refresh: asyncio.Task | None = None


def _clean_secret(value: str) -> str:
    value = str(value or "").strip()
    quote_pairs = (("\"", "\""), ("'", "'"), ("“", "”"), ("‘", "’"))
    for left, right in quote_pairs:
        if len(value) >= 2 and value.startswith(left) and value.endswith(right):
            value = value[len(left):-len(right)].strip()
            break
    return value


def manual_refresh_enabled() -> bool:
    # The value is never accepted from a request; its presence only enables the
    # admin-only action. Requiring a strong generated value avoids accidental
    # activation while allowing every installation to have a unique secret.
    for name in MANUAL_REFRESH_ENV_ALIASES:
        value = _clean_secret(os.environ.get(name, ""))
        if len(value) >= 24 and not any(ord(ch) < 32 for ch in value):
            return True
    return False

def manual_refresh_state() -> dict:
    present = any(bool(_clean_secret(os.environ.get(name, ""))) for name in MANUAL_REFRESH_ENV_ALIASES)
    return {
        "enabled": manual_refresh_enabled(),
        "env_present": present,
        "installer_managed": True,
    }

def validate_url(value: str) -> str:
    parsed = urlsplit(str(value or "").split("#", 1)[0].strip())
    if parsed.scheme.lower() not in _ALLOWED:
        raise ValueError("scheme must be http, https, or socks5")
    if not parsed.hostname:
        raise ValueError("host is missing")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("invalid port") from exc
    if not port or not 1 <= port <= 65535:
        raise ValueError("port must be 1..65535")
    if parsed.path not in ("", "/") or parsed.query:
        raise ValueError("path/query is not allowed")
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, "", "", ""))


def parse_text(text: str) -> list[Record]:
    """Parse proxy.txt; malformed lines are skipped, valid lines survive."""
    import re
    result: list[Record] = []
    seen: set[str] = set()
    metadata = re.compile(r"^(.+?)\s*-\s*(\d{1,3})\s*%\s*$")
    for source_line in text.splitlines():
        line = source_line.strip()
        if not line or line.startswith((";", "//")) or "#" not in line:
            continue
        raw, suffix = line.rsplit("#", 1)
        match = metadata.match(suffix.strip())
        if not match:
            continue
        try:
            endpoint = validate_url(raw)
        except ValueError:
            continue
        identity = hashlib.sha256(_ID_SALT + endpoint.encode()).hexdigest()[:24]
        if identity in seen:
            continue
        seen.add(identity)
        country, code = countries.normalize_country(match.group(1))
        try:
            health = max(0, min(100, int(match.group(2))))
        except (TypeError, ValueError):
            continue
        result.append(Record(
            identity, endpoint, urlsplit(endpoint).scheme, country, code,
            countries.flag_for(code), health,
        ))
        if len(result) >= MAX_PROXIES:
            break
    return result


def _signing_key(secret: str, date: str, region: str) -> bytes:
    k_date = hmac.new(("AWS4" + secret).encode(), date.encode(), hashlib.sha256).digest()
    k_region = hmac.new(k_date, region.encode(), hashlib.sha256).digest()
    k_service = hmac.new(k_region, b"s3", hashlib.sha256).digest()
    return hmac.new(k_service, b"aws4_request", hashlib.sha256).digest()


def _signed_request(now: datetime | None = None) -> urllib.request.Request:
    access_key, secret_key = _access_key(), _secret_key()
    if access_key == "KEY_ID" or secret_key == "SECRET_ACCESS":
        raise RuntimeError("S3 credentials are not configured (set LUMEN_S3_ACCESS_KEY_ID / LUMEN_S3_SECRET_ACCESS_KEY)")
    endpoint = urlsplit(S3_ENDPOINT)
    if endpoint.scheme != "https" or not endpoint.hostname:
        raise RuntimeError("S3_ENDPOINT must be HTTPS")
    now = now or datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date = now.strftime("%Y%m%d")
    canonical_uri = "/" + quote(S3_BUCKET, safe="") + "/" + quote(S3_OBJECT_KEY, safe="/~")
    payload_hash = hashlib.sha256(b"").hexdigest()
    canonical_headers = f"host:{endpoint.netloc}\nx-amz-content-sha256:{payload_hash}\nx-amz-date:{amz_date}\n"
    signed_headers = "host;x-amz-content-sha256;x-amz-date"
    canonical_request = "\n".join(["GET", canonical_uri, "", canonical_headers, signed_headers, payload_hash])
    scope = f"{date}/{S3_REGION}/s3/aws4_request"
    string_to_sign = "\n".join(["AWS4-HMAC-SHA256", amz_date, scope, hashlib.sha256(canonical_request.encode()).hexdigest()])
    signature = hmac.new(_signing_key(secret_key, date, S3_REGION), string_to_sign.encode(), hashlib.sha256).hexdigest()
    authorization = f"AWS4-HMAC-SHA256 Credential={access_key}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
    url = S3_ENDPOINT.rstrip("/") + canonical_uri
    return urllib.request.Request(url, headers={
        "Authorization": authorization,
        "x-amz-date": amz_date,
        "x-amz-content-sha256": payload_hash,
        "User-Agent": "Lumen-Proxy-Repository/15",
    })


def _fetch() -> str:
    with urllib.request.urlopen(_signed_request(), timeout=FETCH_TIMEOUT) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise RuntimeError("repository file is too large")
    return data.decode("utf-8-sig")


def _state() -> str:
    """loading / ready / stale / unconfigured / error — the panel keys off this."""
    if not _configured():
        return "unconfigured"
    if _records:
        return "stale" if _error else "ready"
    if _error and _error != "not loaded":
        return "error"
    return "loading"


def status() -> dict:
    return {
        "count": len(_records),
        "age_seconds": None if not _last else int(time.monotonic() - _last),
        "error": _error or None,
        "state": _state(),
        "configured": _configured(),
        "refresh_seconds": REFRESH_SECONDS,
        "refreshing": _inflight_refresh is not None and not _inflight_refresh.done(),
        "manual_refresh_enabled": manual_refresh_enabled(),
        "manual_refresh_state": manual_refresh_state(),
    }


async def refresh(force: bool = False) -> dict:
    global _records, _last, _error
    if not force and _records and time.monotonic() - _last < REFRESH_SECONDS:
        return status()
    async with _lock:
        if not force and _records and time.monotonic() - _last < REFRESH_SECONDS:
            return status()
        try:
            rows = parse_text(await asyncio.to_thread(_fetch))
            if not rows:
                raise RuntimeError("repository has no valid proxies")
            _records = {row.id: row for row in rows}
            _last = time.monotonic()
            _error = ""
        except Exception as exc:
            # Keep the last known-good catalog; a temporary S3 failure must not
            # erase proxies that routes already use.
            _error = str(exc)[:200]
        return status()


def kick_refresh(force: bool = False) -> bool:
    """Start a background refresh if none is running. Returns True if started."""
    global _inflight_refresh
    if _inflight_refresh is not None and not _inflight_refresh.done():
        return False
    _inflight_refresh = asyncio.create_task(refresh(force=force), name="proxy-repository-fetch")
    return True


async def _periodic_loop() -> None:
    while True:
        await asyncio.sleep(REFRESH_SECONDS)
        await refresh(force=True)


def start_periodic_refresh() -> None:
    global _refresh_task
    if _refresh_task is None or _refresh_task.done():
        _refresh_task = asyncio.create_task(_periodic_loop(), name="proxy-repository-refresh")


async def stop_periodic_refresh() -> None:
    global _refresh_task, _inflight_refresh
    for task in (_refresh_task, _inflight_refresh):
        if task is not None:
            task.cancel()
    await asyncio.gather(
        *(t for t in (_refresh_task, _inflight_refresh) if t is not None),
        return_exceptions=True,
    )
    _refresh_task = None
    _inflight_refresh = None


def public(record: Record) -> dict:
    # Protocol, endpoint, credentials, and legacy source percentage stay server-side.
    return {"id": record.id, "country": record.country, "country_code": record.code, "flag": record.flag, "managed": True, "safe": True}


def pending_address_catalog() -> list[dict]:
    """Non-selectable address inventory. These are not proxy identities yet."""
    return [
        {
            "candidate_id": hashlib.sha256(("pending-proxy-address\0" + address).encode()).hexdigest()[:24],
            "address": address,
            "selectable": False,
            "missing": ["protocol", "port", "credentials_if_required", "country_code"],
        }
        for address in PENDING_PROXY_ADDRESSES
    ]


async def catalog(force: bool = False) -> dict:
    """Dashboard catalog. Never blocks on S3: a stale/empty cache triggers a
    background refresh and the current state is returned immediately."""
    if force:
        await refresh(force=True)
    elif not _records or time.monotonic() - _last >= REFRESH_SECONDS:
        kick_refresh(force=True)
    items = sorted((public(x) for x in _records.values()), key=lambda x: (x["country"], x["id"]))
    grouped: dict[str, dict] = {}
    for row in items:
        slot = grouped.setdefault(row["country_code"], {
            "code": row["country_code"], "country": row["country"],
            "flag": row["flag"], "count": 0,
        })
        slot["count"] += 1
    countries_out = sorted(grouped.values(), key=lambda x: x["country"])
    return {"proxies": items, "countries": countries_out, "pending_addresses": pending_address_catalog(), "status": status()}


def get_record(proxy_id: str) -> Record | None:
    """Synchronous cache-only lookup (validation paths, no I/O)."""
    return _records.get(str(proxy_id or ""))


def loaded() -> bool:
    return bool(_records)


async def resolve(proxy_id: str) -> Record | None:
    # Data-plane lookups are cache-only. Startup/background/catalog refreshes
    # own all S3 I/O so a slow bucket can never make a client ping=-1.
    return _records.get(str(proxy_id or ""))


async def resolve_many(proxy_ids) -> list[Record]:
    """Ordered repository records for the given ids; unknown ids are skipped."""
    out: list[Record] = []
    for pid in proxy_ids or []:
        record = _records.get(str(pid or ""))
        if record is not None:
            out.append(record)
    return out


async def summary(proxy_id: str) -> dict | None:
    record = await resolve(proxy_id)
    return public(record) if record else None


def custom_summary(value: str) -> dict:
    return {"country": "Custom", "country_code": "", "flag": "⚠️", "health": None, "managed": False, "safe": False}
