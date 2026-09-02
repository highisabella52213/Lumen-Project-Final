"""Private S3-compatible repository for managed HTTP/HTTPS/SOCKS5 proxies."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
import re
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit, urlunsplit

# ── PRIVATE S3 CONFIGURATION — replace only the two credential placeholders. ──
S3_ENDPOINT = "https://s3.us-west-2.idrivee2.com"
S3_REGION = "us-west-2"
S3_BUCKET = "bt2"
S3_OBJECT_KEY = "www-32k-ort-org-021/proxy.txt"
S3_ACCESS_KEY_ID = "KEY_ID"
S3_SECRET_ACCESS_KEY = "SECRET_ACCESS"
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
_CODES = {
    "finland":"FI", "germany":"DE", "france":"FR", "netherlands":"NL",
    "united states":"US", "usa":"US", "united kingdom":"GB", "uk":"GB",
    "canada":"CA", "sweden":"SE", "norway":"NO", "denmark":"DK",
    "switzerland":"CH", "austria":"AT", "poland":"PL", "italy":"IT",
    "spain":"ES", "turkey":"TR", "iran":"IR", "japan":"JP",
    "singapore":"SG", "india":"IN", "australia":"AU", "brazil":"BR",
    "romania":"RO", "belgium":"BE", "ireland":"IE", "hong kong":"HK",
}

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


def _country(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    if "|" in raw:
        code, name = map(str.strip, raw.split("|", 1))
        if re.fullmatch(r"[A-Za-z]{2}", code):
            return name or code.upper(), code.upper()
    if re.fullmatch(r"[A-Za-z]{2}", raw):
        return raw.upper(), raw.upper()
    return raw or "Unknown", _CODES.get(raw.casefold(), "")


def _flag(code: str) -> str:
    return "".join(chr(127397 + ord(c)) for c in code) if re.fullmatch(r"[A-Z]{2}", code) else "🌐"


def parse_text(text: str) -> list[Record]:
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
        country, code = _country(match.group(1))
        result.append(Record(
            identity, endpoint, urlsplit(endpoint).scheme, country[:60], code,
            _flag(code), max(0, min(100, int(match.group(2)))),
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
    if S3_ACCESS_KEY_ID == "KEY_ID" or S3_SECRET_ACCESS_KEY == "SECRET_ACCESS":
        raise RuntimeError("S3 credentials are not configured in proxy_repository.py")
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
    signature = hmac.new(_signing_key(S3_SECRET_ACCESS_KEY, date, S3_REGION), string_to_sign.encode(), hashlib.sha256).hexdigest()
    authorization = f"AWS4-HMAC-SHA256 Credential={S3_ACCESS_KEY_ID}/{scope}, SignedHeaders={signed_headers}, Signature={signature}"
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


def status() -> dict:
    return {
        "count": len(_records),
        "age_seconds": None if not _last else int(time.monotonic() - _last),
        "error": _error or None,
        "configured": S3_ACCESS_KEY_ID != "KEY_ID" and S3_SECRET_ACCESS_KEY != "SECRET_ACCESS",
        "refresh_seconds": REFRESH_SECONDS,
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
            _error = str(exc)[:200]
        return status()


async def _periodic_loop() -> None:
    while True:
        await asyncio.sleep(REFRESH_SECONDS)
        await refresh(force=True)


def start_periodic_refresh() -> None:
    global _refresh_task
    if _refresh_task is None or _refresh_task.done():
        _refresh_task = asyncio.create_task(_periodic_loop(), name="proxy-repository-refresh")


async def stop_periodic_refresh() -> None:
    global _refresh_task
    if _refresh_task is not None:
        _refresh_task.cancel()
        await asyncio.gather(_refresh_task, return_exceptions=True)
        _refresh_task = None


def public(record: Record) -> dict:
    return {"id":record.id, "type":record.type, "country":record.country, "country_code":record.code, "flag":record.flag, "health":record.health, "managed":True, "safe":True}


async def catalog(force: bool = False) -> dict:
    await refresh(force)
    items = sorted((public(x) for x in _records.values()), key=lambda x:(x["type"], -x["health"], x["country"]))
    return {"proxies":items, "types":["http", "https", "socks5"], "status":status()}


async def resolve(proxy_id: str) -> Record | None:
    # Data-plane lookups are cache-only. Startup/background/catalog refreshes
    # own all S3 I/O so a slow bucket can never make a client ping=-1.
    return _records.get(str(proxy_id or ""))


async def summary(proxy_id: str) -> dict | None:
    record = await resolve(proxy_id)
    return public(record) if record else None


def custom_summary(value: str) -> dict:
    return {"type":urlsplit(validate_url(value)).scheme, "country":"Custom", "flag":"⚠️", "health":None, "managed":False, "safe":False}
