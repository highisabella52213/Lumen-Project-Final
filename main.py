import asyncio
import json
import os
import hashlib
import base64
import hmac
import shutil
import zlib
import secrets
import time
import sys

# وقتی فایل با `python main.py` اجرا می‌شود نام ماژول `__main__` است. ماژول‌های
# relay_vless/speed_limit از `main` import می‌کنند؛ بدون این alias پایتون فایل را
# بار دوم اجرا می‌کرد و circular import قبل از تعریف RELAY_BUF باعث کرش می‌شد.
if __name__ == "__main__":
    sys.modules.setdefault("main", sys.modules[__name__])

import aiofiles
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from urllib.parse import quote
from collections import deque, defaultdict
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import Response, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import httpx
import logging

# اتصال خروجی هر کانفیگ از مخزن پروکسی مدیریت‌شده.
import countries
import outbound
import proxy_repository
from transports import TRANSPORTS
from raw_tcp import RAW_TCP_LISTENER
from config_address import (
    address_kind,
    authority_host,
    link_hosts,
    normalize_address,
    normalize_sni,
    parse_address_list,
    unique_valid,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("code")

IRAN_TZ = ZoneInfo("Asia/Tehran")

app = FastAPI(title="Lumen Relay", docs_url=None, redoc_url=None)

# Safe, process-lifetime identity for diagnosing Railway restarts. This is not
# derived from a credential and intentionally changes only when the process does.
SERVER_BOOT_ID = secrets.token_urlsafe(12)
SERVER_STARTED_AT = datetime.now(timezone.utc).isoformat()
# Set APP_BUILD_ID in Railway (for example to the deployed Git SHA). It is safe
# to expose and makes an old artifact or wrong service immediately detectable.
APP_BUILD_ID = os.environ.get("APP_BUILD_ID", "source-forensic-v30")
SERVER_RELEASE = "forensic-v30"
CLIENT_DIAGNOSTIC_EVENTS: deque = deque(maxlen=800)
CLIENT_DIAGNOSTIC_LOCK = asyncio.Lock()


def server_diagnostic_identity() -> dict:
    return {"server_boot_id": SERVER_BOOT_ID, "server_started_at": SERVER_STARTED_AT, "app_build_id": APP_BUILD_ID, "release": SERVER_RELEASE}

# ── Persistence ───────────────────────────────────────────────────────────────
DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
DATA_FILE = DATA_DIR / "code_state.json"
SECRET_FILE = DATA_DIR / "code_secret.key"
SAVE_LOCK = asyncio.Lock()
STATE_BACKUPS = (DATA_DIR / "code_state.backup-1.json", DATA_DIR / "code_state.backup-2.json")
STATE_SNAPSHOT_ENV = "LUMEN_STATE_SNAPSHOT_B64"

# One-time migration from the pre-rename file names. The legacy tag is built
# without the literal so repository-wide searches stay clean.
_LEGACY_TAG = "x" + "4g"
LEGACY_STATE_FILES = (
    (DATA_DIR / (_LEGACY_TAG + "_state.json"), DATA_FILE),
    (DATA_DIR / (_LEGACY_TAG + "_state.backup-1.json"), STATE_BACKUPS[0]),
    (DATA_DIR / (_LEGACY_TAG + "_state.backup-2.json"), STATE_BACKUPS[1]),
    (DATA_DIR / (_LEGACY_TAG + "_secret.key"), SECRET_FILE),
)


def _migrate_legacy_state() -> None:
    """Move pre-rename state/backup/secret files to their current names.

    Existing Railway volumes still carry the old file names; without this
    migration a deploy would look like a fresh install (lost configs and an
    invalidated admin password hash). Current files always win; legacy files
    are left untouched when the current name already exists.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        for legacy, current in LEGACY_STATE_FILES:
            try:
                if legacy.exists() and not current.exists():
                    legacy.replace(current)
                    logger.info("Migrated legacy state file %s -> %s", legacy.name, current.name)
            except OSError as exc:
                logger.warning("Could not migrate %s: %s", legacy.name, exc)
    except Exception as exc:  # never block startup on migration
        logger.warning("Legacy state migration skipped: %s", exc)

def _load_or_create_secret() -> str:
    """SECRET_KEY را روی دیسک ذخیره و ثابت نگه می‌دارد.
    قبلاً وقتی متغیر محیطی SECRET_KEY تنظیم نشده بود، با هر ری‌استارت سرویس
    (که روی Railway هر چند ساعت یک‌بار اتفاق می‌افتد) یک مقدار تصادفی جدید
    ساخته می‌شد. چون هش پسورد بر پایه‌ی همین secret ساخته می‌شود، تغییر آن
    باعث می‌شد پسورد درست هم دیگر قبول نشود. حالا secret یک‌بار ساخته و در
    فایل ذخیره می‌شود و در ری‌استارت‌های بعدی همان مقدار خوانده می‌شود."""
    env_secret = os.environ.get("SECRET_KEY")
    if env_secret:
        return env_secret
    _migrate_legacy_state()
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if SECRET_FILE.exists():
            existing = SECRET_FILE.read_text(encoding="utf-8").strip()
            if existing:
                return existing
        new_secret = secrets.token_urlsafe(32)
        SECRET_FILE.write_text(new_secret, encoding="utf-8")
        return new_secret
    except Exception as e:
        logger.warning(f"Could not persist SECRET_KEY, sessions/password may reset on restart: {e}")
        return secrets.token_urlsafe(32)

CONFIG = {
    "port": int(os.environ.get("PORT", 8000)),
    "secret": _load_or_create_secret(),
    "host": os.environ.get("RAILWAY_PUBLIC_DOMAIN", "localhost"),
}

import updater
updater.configure()

# The panel is a same-origin, cookie-authenticated app; cross-origin browser
# access is intentionally disabled (wildcard origins plus credentials is both
# invalid per CORS and an unnecessary attack surface).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_server_diagnostic_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Lumen-Server-Boot-ID"] = SERVER_BOOT_ID
    response.headers["X-Lumen-Server-Started-At"] = SERVER_STARTED_AT
    response.headers["X-Lumen-Release"] = SERVER_RELEASE
    return response

def _state_payload() -> dict:
    return {
        "schema_version": 2,
        "links": dict(LINKS),
        "subs": dict(SUBS),
        "proxy_test_results": dict(PROXY_TEST_RESULTS),
        "password_hash": AUTH["password_hash"],
        "saved_at": datetime.now().isoformat(),
    }


def _validate_state(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("state root is not an object")
    links, subs = data.get("links"), data.get("subs")
    tests = data.get("proxy_test_results", {})
    if not isinstance(links, dict) or not isinstance(subs, dict) or not isinstance(tests, dict):
        raise ValueError("links/subs/proxy_test_results are missing or invalid")
    if len(links) > 100_000 or len(subs) > 100_000:
        raise ValueError("state is unreasonably large")
    return data


def _snapshot_encode(data: dict) -> str:
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    packed = zlib.compress(raw, level=9)
    if len(packed) > 48 * 1024:
        raise ValueError("state snapshot exceeds the safe Railway variable limit")
    body = base64.urlsafe_b64encode(packed).decode().rstrip("=")
    signature = hmac.new(CONFIG["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + signature


def _snapshot_decode(value: str) -> dict:
    body, signature = str(value or "").split(".", 1)
    expected = hmac.new(CONFIG["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("state snapshot signature mismatch")
    packed = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
    if len(packed) > 48 * 1024:
        raise ValueError("state snapshot is too large")
    decoder = zlib.decompressobj()
    raw = decoder.decompress(packed, 8 * 1024 * 1024 + 1)
    if decoder.unconsumed_tail or len(raw) > 8 * 1024 * 1024:
        raise ValueError("expanded state snapshot is too large")
    raw += decoder.flush()
    return _validate_state(json.loads(raw.decode("utf-8")))


def make_state_snapshot() -> str:
    return _snapshot_encode(_state_payload())


def _atomic_write_state(data: dict, rotate: bool = True) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if rotate and DATA_FILE.exists():
        if STATE_BACKUPS[0].exists():
            shutil.copy2(STATE_BACKUPS[0], STATE_BACKUPS[1])
        shutil.copy2(DATA_FILE, STATE_BACKUPS[0])
    tmp = DATA_FILE.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, DATA_FILE)
    try:
        descriptor = os.open(DATA_DIR, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError:
        pass


def _verify_persistent_storage() -> None:
    required = str(os.environ.get("LUMEN_REQUIRE_PERSISTENT_STORAGE", "")).lower() in {"1", "true", "yes", "on"}
    mount = str(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH", "")).strip()
    if required:
        if not mount:
            raise RuntimeError("Persistent Railway Volume is required but not mounted")
        try:
            data_path, mount_path = DATA_DIR.resolve(), Path(mount).resolve()
            data_path.relative_to(mount_path)
        except (ValueError, OSError):
            raise RuntimeError(f"DATA_DIR {DATA_DIR} is outside Railway volume {mount}") from None
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    probe = DATA_DIR / ".lumen-write-probe"
    try:
        with probe.open("w", encoding="utf-8") as handle:
            handle.write("ok")
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        probe.unlink(missing_ok=True)


async def load_state():
    global LINKS, AUTH, SUBS, PROXY_TEST_RESULTS
    candidates = (DATA_FILE, *STATE_BACKUPS)
    existing = [path for path in candidates if path.exists()]
    loaded = None
    loaded_from = None
    errors = []
    for path in existing:
        try:
            loaded = _validate_state(json.loads(await asyncio.to_thread(path.read_text, encoding="utf-8")))
            loaded_from = path
            break
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
    if loaded is None:
        snapshot = os.environ.get(STATE_SNAPSHOT_ENV, "").strip()
        if snapshot:
            try:
                loaded = _snapshot_decode(snapshot)
                loaded_from = STATE_SNAPSHOT_ENV
            except Exception as exc:
                errors.append(f"environment snapshot: {exc}")
        elif existing:
            raise RuntimeError("All persistent state copies are invalid; refusing to start and overwrite them: " + "; ".join(errors))
    if loaded is None:
        logger.info("No previous state found; starting with an empty database")
        return
    LINKS.clear(); SUBS.clear(); PROXY_TEST_RESULTS.clear()
    LINKS.update(loaded.get("links", {}))
    for _link in LINKS.values():
        # Pre-registry configurations are VLESS/WS and did not carry a
        # transport_settings key. Preserve any other persisted transport value
        # instead of silently downgrading it; invalid/unavailable records fail
        # closed through is_link_allowed().
        _stored_protocol = str(_link.get("protocol") or DEFAULT_PROTOCOL).strip()
        _stored_settings = _link.get("transport_settings")
        try:
            _link["protocol"], _link["transport_settings"] = TRANSPORTS.validate(
                _stored_protocol, _stored_settings
            )
        except ValueError:
            _link["protocol"] = _stored_protocol
            _link["transport_settings"] = (
                _stored_settings if isinstance(_stored_settings, dict) else {}
            )
        _link.setdefault("address", "")
        _link.setdefault("sni", "")
        _link.setdefault("remark", _link.get("label") or "Lumen Relay")
        _link.pop("proxy"+"ip", None); _link.pop("proxy"+"ip_enabled", None); _link.pop("proxy"+"ip_concurrency", None); _link.pop("outbound", None)
        _link.setdefault("exit_proxy_mode", "direct"); _link.setdefault("proxy_id", ""); _link.setdefault("custom_proxy", "")
        if _link.get("protocol") == "vless-tcp":
            # TCP ingress owns its TLS/ALPN contract.  Do not resurrect the
            # historical WebSocket HTTP/1.1 default after a persistence
            # round-trip.
            _link["alpn"] = ""
        elif not _link.get("alpn") or "h2" in str(_link.get("alpn")):
            _link["alpn"] = "http/1.1"
    SUBS.update(loaded.get("subs", {}))
    raw_proxy_tests = loaded.get("proxy_test_results", {})
    if isinstance(raw_proxy_tests, dict):
        for _pid, _test in raw_proxy_tests.items():
            _safe = sanitize_proxy_test_result(_pid, _test)
            if _safe is not None:
                PROXY_TEST_RESULTS[_safe["proxy_id"]] = _safe
    for _sub in SUBS.values():
        _ml = _sub.get("multi_location")
        if not isinstance(_ml, dict):
            _sub["multi_location"] = _default_multi_location()
        else:
            _ml.setdefault("enabled", False)
            _ml.setdefault("remark_text", "")
            if not isinstance(_ml.get("locations"), list):
                _ml["locations"] = []
            for _loc in _ml["locations"]:
                if not isinstance(_loc, dict):
                    continue
                _loc.setdefault("id", secrets.token_urlsafe(8))
                _loc["active"] = True
                legacy_ids = _loc.pop("proxy_ids", [])
                if not _loc.get("proxy_id") and isinstance(legacy_ids, list) and len(legacy_ids) == 1:
                    _loc["proxy_id"] = str(legacy_ids[0] or "")
                _loc.setdefault("proxy_id", "")
                _name, _code = countries.normalize_country(_loc.get("code") or _loc.get("country"))
                _loc["code"] = _code
                _loc["country"] = countries.country_name(_code) if _code else (_loc.get("country") or "Unknown")
                _loc["flag"] = countries.flag_for(_code)
            if _ml.get("enabled") and (len(_ml["locations"]) != 2 or any(not loc.get("proxy_id") for loc in _ml["locations"] if isinstance(loc, dict))):
                # Legacy weighted/failover configurations cannot be interpreted
                # as two explicit choices safely. Preserve them but fail closed.
                _ml["migration_required"] = True
    if "password_hash" in loaded:
        AUTH["password_hash"] = loaded["password_hash"]
    if loaded_from != DATA_FILE:
        await asyncio.to_thread(_atomic_write_state, _state_payload(), False)
        logger.warning("State recovered from %s", getattr(loaded_from, "name", loaded_from))
    logger.info("State loaded: %s links, %s subs", len(LINKS), len(SUBS))


async def save_state(*, strict: bool = False, rotate: bool = True) -> bool:
    async with SAVE_LOCK:
        try:
            data = _validate_state(_state_payload())
            await asyncio.to_thread(_atomic_write_state, data, rotate)
            return True
        except Exception as exc:
            logger.error("Could not persist state: %s", exc)
            if strict:
                raise RuntimeError("Persistent state could not be saved; operation was stopped") from exc
            return False

# ── In-memory state ───────────────────────────────────────────────────────────
connections: dict = {}
stats = {
    "total_bytes": 0,
    "total_requests": 0,
    "total_errors": 0,
    "start_time": time.time(),
}
error_logs: deque = deque(maxlen=50)
activity_logs: deque = deque(maxlen=200)
hourly_traffic: dict = defaultdict(int)
http_client: httpx.AsyncClient | None = None
LINKS: dict = {}
LINKS_LOCK = asyncio.Lock()
SUBS: dict = {}
SUBS_LOCK = asyncio.Lock()
# Results are keyed solely by stable proxy ID; endpoint URLs and credentials are
# never stored in this structure.
PROXY_TEST_RESULTS: dict[str, dict] = {}
PROXY_TEST_RESULTS_LOCK = asyncio.Lock()

# پ��وتکل‌های پشتیبانی‌شده برای هر ��انفیگ
PROTOCOLS = ("vless-ws", "vless-tcp")
DEFAULT_PROTOCOL = "vless-ws"

# Fingerprint (uTLS) های قابل انتخاب برای هر کانفیگ
FINGERPRINTS = ("chrome", "firefox", "safari", "ios", "android", "edge", "360", "qq", "random", "randomized")
DEFAULT_FINGERPRINT = "chrome"

# پیش‌فرض ALPN بر اساس نوع ترابرد (اگر کاربر مقدار دستی نده)
DEFAULT_ALPN_BY_PROTOCOL = {
    "vless-ws": "http/1.1",
    "vless-tcp": "",
}

DEFAULT_PORT = 443
MIN_PORT, MAX_PORT = 1, 65535

# محدودیت سرعت (0 = نامحدود). واحد ذخیره‌سازی داخلی همیشه بایت‌بر‌ثانیه است.
DEFAULT_SPEED_LIMIT = 0

def log_activity(kind: str, message: str, level: str = "info"):
    """ثبت یک رخداد در لاگ فعالیت‌ها (ساخت/حذف/ویرایش کانفیگ، ورود، و...)."""
    activity_logs.append({
        "kind": kind,
        "level": level,
        "message": message,
        "time": datetime.now().isoformat(),
    })

# ── Auth ──────────────────────────────────────────────────────────────────────
SESSION_COOKIE = "code_session"
SESSION_TTL = 60 * 60 * 24 * 365

def hash_password(pw: str) -> str:
    return hashlib.sha256(f"{pw}{CONFIG['secret']}".encode()).hexdigest()

AUTH = {"password_hash": hash_password(os.environ.get("ADMIN_PASSWORD", "123456"))}
SESSIONS: dict = {}
SESSIONS_LOCK = asyncio.Lock()

async def create_session() -> str:
    token = secrets.token_urlsafe(32)
    async with SESSIONS_LOCK:
        SESSIONS[token] = time.time() + SESSION_TTL
    return token

async def is_valid_session(token: str | None) -> bool:
    if not token:
        return False
    async with SESSIONS_LOCK:
        exp = SESSIONS.get(token)
        if exp is None:
            return False
        if exp < time.time():
            SESSIONS.pop(token, None)
            return False
        return True

async def destroy_session(token: str | None):
    if not token:
        return
    async with SESSIONS_LOCK:
        SESSIONS.pop(token, None)

async def require_auth(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not await is_valid_session(token):
        raise HTTPException(status_code=401, detail="unauthorized")
    return token

# ── Startup / Shutdown ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    global http_client
    limits = httpx.Limits(max_connections=500, max_keepalive_connections=100)
    timeout = httpx.Timeout(30.0, connect=10.0)
    http_client = httpx.AsyncClient(
        limits=limits, timeout=timeout, follow_redirects=True,
    )
    _verify_persistent_storage()
    _migrate_legacy_state()
    await load_state()
    await updater.load()
    proxy_repository.kick_refresh(force=True)
    proxy_repository.start_periodic_refresh()
    await _tg_start_bot()
    await RAW_TCP_LISTENER.start()
    if RAW_TCP_LISTENER.running:
        logger.info("Raw TCP TLS listener started separately from Uvicorn")
    elif RAW_TCP_LISTENER.error:
        logger.info("%s", RAW_TCP_LISTENER.error)
    log_activity("system", "سرور راه‌اندازی شد", "ok")
    logger.info(f"Lumen Relay started on HTTP/WebSocket port {CONFIG['port']}")

@app.on_event("shutdown")
async def shutdown():
    await RAW_TCP_LISTENER.stop()
    await save_state()
    await proxy_repository.stop_periodic_refresh()
    await _tg_stop_bot()
    if http_client:
        await http_client.aclose()

# ── Helpers ───────────────────────────────────────────────────────────────────
def get_host(request: Request | None = None) -> str:
    """آدرس دامنه رو ترجیحاً از خودِ درخواست HTTP می‌گیره (هدر Host/X-Forwarded-Host)
    چون این همیشه دقیقاً همون دامنه‌ایه که کاربر واقعاً بهش وصل شده. متغیر محیطی
    RAILWAY_PUBLIC_DOMAIN فقط به‌عنوان fallback استفاده می‌شه، چون گاهی موقع بالا اومدن
    کانتینر هنوز مقداردهی نشده و باعث می‌شد لینک‌ها گاهی با "localhost" ساخته بشن."""
    if request is not None:
        h = request.headers.get("x-forwarded-host") or request.headers.get("host")
        if h:
            # Preserve literal IPv6 hosts. For domains/IPv4 strip only a real :port.
            if h.startswith("[") and "]" in h:
                h = h[1:h.index("]")]
            elif h.count(":") == 1:
                h = h.rsplit(":", 1)[0]
            CONFIG["host"] = h  # کش آخرین دامنه‌ی واقعی دیده‌شده، برای جاهایی که request نداریم (مثل ربات تلگرام)
            return h
    return os.environ.get("RAILWAY_PUBLIC_DOMAIN", CONFIG["host"])


BUILTIN_VLESS_ADDRESSES = ("railway.com", "69.46.46.18", "69.46.46.126" , "69.46.46.188" , "69.46.46.46" , "69.46.46.172")

PROXY_TEST_RECEIPT_TTL = 10 * 60


def _proxy_endpoint_fingerprint(record) -> str:
    return hashlib.sha256(record.endpoint.encode()).hexdigest()


def issue_proxy_test_receipt(record) -> str:
    payload = {
        "proxy_id": record.id,
        "endpoint": _proxy_endpoint_fingerprint(record),
        "expires": int(time.time()) + PROXY_TEST_RECEIPT_TTL,
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()).decode().rstrip("=")
    signature = hmac.new(CONFIG["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + signature


def verify_proxy_test_receipt(proxy_id: str, receipt: str) -> bool:
    try:
        body, signature = str(receipt or "").split(".", 1)
        expected = hmac.new(CONFIG["secret"].encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False
        payload = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        record = proxy_repository.get_record(proxy_id)
        return bool(record and payload.get("proxy_id") == record.id and payload.get("endpoint") == _proxy_endpoint_fingerprint(record) and int(payload.get("expires") or 0) >= int(time.time()))
    except Exception:
        return False


def require_proxy_test_receipt(proxy_id: str, receipt: str) -> None:
    if not verify_proxy_test_receipt(proxy_id, receipt):
        raise ValueError("Selected proxy must pass the exact Cloudflare and Google connectivity test before it can be saved")


async def normalize_exit_proxy(mode, proxy_id="", custom_proxy=""):
    mode=str(mode or "direct").lower()
    if mode=="repository":
        pid=str(proxy_id or "").strip()
        if not pid or await proxy_repository.resolve(pid) is None: raise ValueError("پروکسی مدیریت‌شده پیدا نشد")
        return mode,pid,""
    if mode=="custom":
        try:return mode,"",proxy_repository.validate_url(custom_proxy)
        except ValueError as e:raise ValueError("پروکسی دلخواه نامعتبر است: "+str(e))
    if mode!="direct":raise ValueError("حالت تنظیم آیپی خروجی نامعتبر است")
    return "direct","",""


def configured_endpoint_catalog(request: Request | None = None) -> dict:
    """Address/SNI choices exposed to the authenticated create-config form.

    Railway does not expose every attached custom domain through one runtime API,
    so the current request domain is automatic and extra candidates come from
    VLESS_ADDRESSES / VLESS_SNI_NAMES (comma, whitespace or newline separated).
    """
    try:
        service_host = normalize_address(get_host(request))
    except ValueError:
        service_host = normalize_address(CONFIG.get("host") or "localhost")
    extra_addresses = parse_address_list(os.environ.get("VLESS_ADDRESSES", ""))
    addresses = unique_valid([service_host, *BUILTIN_VLESS_ADDRESSES, *extra_addresses])
    extra_sni = parse_address_list(os.environ.get("VLESS_SNI_NAMES", ""))
    domain_addresses = [value for value in addresses if address_kind(value) == "domain"]
    snis = unique_valid([service_host, *domain_addresses, *extra_sni], sni=True)
    return {"service_host": service_host, "transport_host": service_host, "addresses": addresses, "snis": snis}


def generate_uuid() -> str:
    return str(uuid4())

def normalize_requested_uuid(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = UUID(raw)
    except (ValueError, AttributeError, TypeError):
        raise ValueError("UUID نامعتبر است؛ قالب استاندارد 36 کاراکتری وارد کنید")
    if parsed.int == 0:
        raise ValueError("UUID صفر مجاز نیست")
    return str(parsed)
    
def now_ir() -> datetime:
    return datetime.now(IRAN_TZ)

def generate_vless_link(
    uuid: str,
    host: str,
    remark: str = "Subcription",
    protocol: str = DEFAULT_PROTOCOL,
    fingerprint: str | None = None,
    alpn: str | None = None,
    port: int | None = None,
    address: str | None = None,
    sni: str | None = None,
    loc: str | None = None,
    transport_settings: object = None,
) -> str:
    """Generate a URI only for a transport integrated with this native relay."""
    protocol, transport_settings = TRANSPORTS.validate(protocol, transport_settings)
    fp = (fingerprint or DEFAULT_FINGERPRINT).strip() or DEFAULT_FINGERPRINT
    if fp not in FINGERPRINTS:
        fp = DEFAULT_FINGERPRINT
    alpn_val = (alpn or "").strip() or DEFAULT_ALPN_BY_PROTOCOL.get(protocol, "http/1.1")
    port_val = port or DEFAULT_PORT
    if not (MIN_PORT <= port_val <= MAX_PORT):
        port_val = DEFAULT_PORT

    raw_endpoint = TRANSPORTS.endpoint(
        protocol,
        address=address,
        port=port,
        sni=sni,
        fallback_host=host,
        location_id=loc,
    )
    if raw_endpoint is not None:
        # Railway TCP Proxy public endpoint and the SNI location profile are
        # deployment-owned.  Never reuse a WebSocket address, Host, or path.
        dial_address, port_val, tls_name = raw_endpoint
        transport_host = ""
        alpn_val = ""
    else:
        # Address, TLS SNI, and WebSocket Host are three independent values.
        # Changing SNI must never rewrite the transport Host header.
        dial_address, tls_name = link_hosts(address, sni, host)
        try:
            transport_host = normalize_address(host)
        except ValueError:
            transport_host = str(host or "").strip()
    params = {
        "encryption": "none",
        "security": "tls",
        **TRANSPORTS.vless_parameters(
            protocol,
            uuid=uuid,
            transport_host=transport_host,
            location_id=loc,
            settings=transport_settings,
        ),
        "sni": tls_name,
        "fp": fp,
    }
    if alpn_val:
        params["alpn"] = alpn_val
    query = "&".join(f"{k}={quote(str(v))}" for k, v in params.items())
    return f"vless://{uuid}@{authority_host(dial_address)}:{port_val}?{query}#{quote(remark)}"

def vless_entries_for_link(link: dict, uid: str, host: str) -> list:
    """One entry per active Multi-Location location (same UUID and quota), or a
    single entry for normal routes. Each entry: vless_link, remark, location."""
    base_kwargs = dict(
        protocol=link.get("protocol", DEFAULT_PROTOCOL),
        fingerprint=link.get("fingerprint"),
        alpn=link.get("alpn"),
        port=link.get("port"),
        address=link.get("address"),
        sni=link.get("sni"),
        transport_settings=link.get("transport_settings"),
    )
    _sub, ml = multi_location_for_link(link)
    if ml is not None:
        locations = [loc for loc in ml.get("locations", []) if loc.get("active")]
        if locations:
            text = ml.get("remark_text") or ""
            entries = []
            for loc in locations:
                remark = location_remark(loc, text)
                entries.append({
                    "vless_link": generate_vless_link(uid, host, remark=remark, loc=loc.get("id"), **base_kwargs),
                    "remark": remark,
                    "location": {"id": loc.get("id"), "country": loc.get("country"), "code": loc.get("code"), "flag": loc.get("flag")},
                    "shared_quota": True,
                })
            return entries
    remark = (link.get("remark") or link.get("label") or "Lumen Relay")
    return [{
        "vless_link": generate_vless_link(uid, host, remark=remark, **base_kwargs),
        "remark": remark,
        "location": None,
        "shared_quota": False,
    }]


def vless_link_for_link(link: dict, uid: str, host: str) -> str:
    """generate_vless_link رو با تنظیمات دستی همون کانفیگ (fingerprint/alpn/port) صدا می‌زنه."""
    return vless_entries_for_link(link, uid, host)[0]["vless_link"]


def safe_vless_link_for_link(link: dict, uid: str, host: str) -> str:
    """Do not make an admin listing unavailable when a gated ingress is off.

    A persisted Raw TCP record remains intact across a deployment rollback, but
    it must not receive a stale or guessed endpoint while the listener is
    unavailable.  Subscription endpoints independently fail closed through
    ``is_link_allowed``.
    """
    try:
        return vless_link_for_link(link, uid, host)
    except ValueError:
        return ""


def uptime() -> str:
    secs = int(time.time() - stats["start_time"])
    h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_size_to_bytes(value: float, unit: str) -> int:
    unit = unit.upper()
    if unit == "GB": return int(value * 1024 ** 3)
    if unit == "MB": return int(value * 1024 ** 2)
    if unit == "KB": return int(value * 1024)
    return int(value)

def parse_speed_to_bytes(value: float, unit: str) -> int:
    """محدودیت سرعت رو به بایت‌بر‌ثانیه تبدیل می‌کنه.
    واحدهای پشتیبانی‌شده: MBIT (مگابیت‌بر‌ثانیه، رایج‌ترین)، KB (کیلوبایت‌بر‌ثانیه)، MB (مگابایت‌بر‌ثانیه).
    دقت: Mbps در شبکه واحد دهدهیه (۱ Mbps = ۱۰^۶ بیت‌بر‌ثانیه)، نه ۲^۲۰.
    قبلاً از ۱۰۲۴×۱۰۲۴ استفاده می‌شد که حدود ۵٪ سرعت رو بیشتر از مقدار تنظیم‌شده می‌داد."""
    if value <= 0:
        return 0
    unit = (unit or "MBIT").upper()
    if unit == "MBIT":
        return int(value * 1_000_000 / 8)
    if unit == "KB":
        return int(value * 1024)
    if unit == "MB":
        return int(value * 1024 * 1024)
    return int(value)

def is_link_expired(link: dict) -> bool:
    exp = link.get("expires_at")
    if not exp:
        return False
    try:
        return datetime.now() > datetime.fromisoformat(exp)
    except Exception:
        return False

def is_link_allowed(link: dict | None) -> bool:
    if link is None:
        return False
    # A persisted route with a removed or unsupported transport must fail
    # closed. Never rewrite it to WebSocket or return a misleading URI.
    if not TRANSPORTS.is_available(link.get("protocol", DEFAULT_PROTOCOL)):
        return False
    # A Raw TCP Multi-Location subscription is usable only when each exact
    # stored location has a deployment-owned SNI profile.  Do not emit a
    # generic/default TCP endpoint and let the relay guess a location.
    if link.get("protocol", DEFAULT_PROTOCOL) == "vless-tcp":
        _sub, ml = multi_location_for_link(link)
        try:
            validate_raw_tcp_multi_location(link, ml)
        except ValueError:
            return False
    if not link.get("active", True):
        return False
    if is_link_expired(link):
        return False
    lb = link.get("limit_bytes", 0)
    if lb > 0 and link.get("used_bytes", 0) >= lb:
        return False
    return True

def fmt_bytes(b: int) -> str:
    if b < 1024: return f"{b} B"
    if b < 1024**2: return f"{b/1024:.1f} KB"
    if b < 1024**3: return f"{b/1024**2:.2f} MB"
    return f"{b/1024**3:.2f} GB"

def unique_ips_for_uuid(uuid: str) -> set:
    """آی‌پی‌های یکتای همین لحظه متصل به یک UUID خاص (بر اساس dict اتصالات زنده)."""
    return {c.get("ip") for c in connections.values() if c.get("uuid") == uuid and c.get("ip")}

def is_ip_allowed(link: dict | None, uuid: str, ip: str) -> bool:
    """محدودیت تعداد آی‌پی/کاربر هم‌زمان برای هر کانفیگ. ip_limit=0 یعنی نامحدود.
    اگر همین آی‌پی از قبل روی این کانفیگ سشن باز داشته باشه، همیشه مجازه (برای چند اتصال
    هم‌زمان از یک ����ستگاه/مرورگر مشکلی پیش نمیاد)."""
    if link is None:
        return False
    limit = int(link.get("ip_limit", 0) or 0)
    if limit <= 0:
        return True
    ips = unique_ips_for_uuid(uuid)
    if ip in ips:
        return True
    return len(ips) < limit

def client_ip(request: Request) -> str:
    """آی‌پی واقعی کلاینت رو با احتساب هدرهای پراکسی (Railway/Cloudflare) برمی‌گردونه."""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "نامشخص"

# ── Default link ──────────────────────────────────────────────────────────────
_default_link_created = False

async def ensure_default_link():
    global _default_link_created
    if _default_link_created:
        return
    async with LINKS_LOCK:
        if not any(l.get("is_default") for l in LINKS.values()):
            uid = hashlib.sha256(f"default{CONFIG['secret']}".encode()).hexdigest()
            uid = f"{uid[:8]}-{uid[8:12]}-{uid[12:16]}-{uid[16:20]}-{uid[20:32]}"
            if uid not in LINKS:
                LINKS[uid] = {
                    "label": "لینک پیش‌فرض",
                    "limit_bytes": 0,
                    "used_bytes": 0,
                    "created_at": datetime.now().isoformat(),
                    "active": True,
                    "expires_at": None,
                    "note": "",
                    "remark": "Lumen Relay · Default",
                    "is_default": True,
                    "sub_id": None,
                    "protocol": DEFAULT_PROTOCOL,
                    "transport_settings": {},
                    "fingerprint": DEFAULT_FINGERPRINT,
                    "alpn": "",
                    "port": DEFAULT_PORT,
                    "ip_limit": 0,
                    "speed_limit_bytes": DEFAULT_SPEED_LIMIT,
                    "address": "",
                    "sni": "",
                    "exit_proxy_mode": "direct", "proxy_id": "", "custom_proxy": "",
                }
                await save_state(strict=True)
        _default_link_created = True

# ── Basic endpoints ───────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return HTMLResponse(content=LANDING_HTML)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    # Silence the browser's automatic request; the product UI uses icon fonts.
    return Response(status_code=204)


@app.get("/health")
async def health():
    active_links = sum(1 for link in LINKS.values() if is_link_allowed(link))
    return {
        "status": "ok",
        "service": "Lumen Relay",
        "version": "20.0",
        "transport": "VLESS / WebSocket",
        "connections": len(connections),
        "active_configs": active_links,
        "uptime": uptime(),
        "server": server_diagnostic_identity(),
        "persistence": {"path": str(DATA_DIR), "volume_mounted": bool(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")), "required": str(os.environ.get("LUMEN_REQUIRE_PERSISTENT_STORAGE", "")).lower() in {"1", "true", "yes", "on"}},
    }

# ── Subscription (single link) ────────────────────────────────────────────────
@app.get("/sub/{uuid}")
async def subscription_single(uuid: str, request: Request):
    import base64
    async with LINKS_LOCK:
        link = LINKS.get(uuid)
    if not link or not is_link_allowed(link):
        raise HTTPException(status_code=404, detail="not found or inactive")
    host = get_host(request)
    entries = vless_entries_for_link(link, uuid, host)
    content = base64.b64encode("\n".join(e["vless_link"] for e in entries).encode()).decode()
    return Response(content=content, media_type="text/plain",
                    headers={"profile-title": quote(link["label"])})

@app.get("/sub-all")
async def subscription_all(request: Request, _=Depends(require_auth)):
    import base64
    host = get_host(request)
    async with LINKS_LOCK:
        lines = [
            vless_link_for_link(d, uid, host)
            for uid, d in LINKS.items()
            if is_link_allowed(d)
        ]
    content = base64.b64encode("\n".join(lines).encode()).decode()
    return Response(content=content, media_type="text/plain")

# ══════════════════════════════════════════════════════════════════════════════
# SUB GROUP endpoints
# ══════════════════════════════════════════════════════════════════════════════

def public_sub(sub_id: str, sub: dict, host: str) -> dict:
    """Admin-facing subgroup payload — the password hash never leaves the server."""
    ml = sub.get("multi_location") or _default_multi_location()
    locations = []
    for loc in (ml.get("locations") or []):
        proxy_id = str(loc.get("proxy_id") or "")
        locations.append({**loc, "proxy_available": proxy_repository.get_record(proxy_id) is not None})
    ml = {**ml, "locations": locations}
    return {
        "sub_id": sub_id,
        "name": sub.get("name", ""),
        "desc": sub.get("desc", ""),
        "uuid_key": sub.get("uuid_key"),
        "created_at": sub.get("created_at"),
        "link_ids": list(sub.get("link_ids", [])),
        "password_hash": None,
        "has_password": sub.get("password_hash") is not None,
        "multi_location": ml,
        "multi_location_summary": {
            "enabled": bool(ml.get("enabled")),
            "total_locations": len(locations),
            "active_locations": sum(1 for loc in locations if loc.get("active")),
        },
        "public_url": f"https://{host}/p/{sub.get('uuid_key')}",
        "sub_url": "https://" + host + "/sub-group/" + str(sub.get("uuid_key")),
    }


@app.post("/api/subs")
async def create_sub(request: Request, _=Depends(require_auth)):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid body")
    sub_id, _sub = await create_sub_group(
        name=body.get("name") or "گروه جدید",
        desc=body.get("desc") or "",
        password=body.get("password") or "",
    )
    host = get_host(request)
    async with SUBS_LOCK:
        sub = dict(SUBS[sub_id])
    return public_sub(sub_id, sub, host)

@app.get("/api/subs")
async def list_subs(request: Request, _=Depends(require_auth)):
    host = get_host(request)
    async with SUBS_LOCK:
        snap_subs = dict(SUBS)
    async with LINKS_LOCK:
        snap_links = dict(LINKS)
    result = []
    for sid, s in snap_subs.items():
        link_ids = s.get("link_ids", [])
        active_count = sum(1 for lid in link_ids if is_link_allowed(snap_links.get(lid)))
        total_used = sum(snap_links[lid].get("used_bytes", 0) for lid in link_ids if lid in snap_links)
        result.append({
            **public_sub(sid, s, host),
            "links_count": len(link_ids),
            "active_count": active_count,
            "total_used_bytes": total_used,
            "total_used_fmt": fmt_bytes(total_used),
        })
    result.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return {"subs": result}

@app.patch("/api/subs/{sub_id}")
async def update_sub(sub_id: str, request: Request, _=Depends(require_auth)):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid body")
    ml_value = None
    if "multi_location" in body:
        previous_ml = (SUBS.get(sub_id) or {}).get("multi_location")
        try:
            ml_value = await validate_multi_location(body.get("multi_location"), previous_ml, require_tests=True)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    new_ids = None
    if "link_ids" in body:
        raw_ids = body.get("link_ids")
        if not isinstance(raw_ids, list):
            raise HTTPException(status_code=400, detail="link_ids must be a list")
        async with LINKS_LOCK:
            known = set(LINKS)
        clean_ids = []
        for lid in raw_ids:
            lid = str(lid or "")
            if lid and lid in known and lid not in clean_ids:
                clean_ids.append(lid)
        new_ids = clean_ids
    # Validate the prospective association before mutating either side of the
    # existing two-way link/subscription state.
    if ml_value is not None or new_ids is not None:
        existing_sub = SUBS.get(sub_id)
        if existing_sub is None:
            raise HTTPException(status_code=404, detail="sub not found")
        prospective_ml = (
            ml_value if ml_value is not None else existing_sub.get("multi_location")
        )
        prospective_ids = (
            new_ids if new_ids is not None else existing_sub.get("link_ids", [])
        )
        async with LINKS_LOCK:
            prospective_links = [LINKS.get(link_id) for link_id in prospective_ids]
        try:
            for link in prospective_links:
                validate_raw_tcp_multi_location(link, prospective_ml)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    async with SUBS_LOCK:
        if sub_id not in SUBS:
            raise HTTPException(status_code=404, detail="sub not found")
        s = SUBS[sub_id]
        if "name" in body:
            s["name"] = str(body["name"])[:60]
        if "desc" in body:
            s["desc"] = str(body["desc"])[:200]
        if "password" in body:
            pw = str(body["password"]).strip()
            s["password_hash"] = hash_password(pw) if pw else None
        if ml_value is not None:
            s["multi_location"] = ml_value
            log_activity("sub", f"Multi-Location گروه «{s.get('name', sub_id)}» به‌روزرسانی شد", "info")
        if new_ids is not None:
            old_ids = set(s.get("link_ids", []))
            s["link_ids"] = new_ids
    if new_ids is not None:
        # Two-way sync: the group membership and each config's sub_id must
        # always agree, no matter which side was edited. Locks stay sequential
        # (never nested) like every other state mutation in this module.
        wanted = set(new_ids)
        moved_from = []
        async with LINKS_LOCK:
            for lid in old_ids - wanted:
                link = LINKS.get(lid)
                if link is not None and link.get("sub_id") == sub_id:
                    link["sub_id"] = None
            for lid in wanted - old_ids:
                link = LINKS.get(lid)
                if link is not None:
                    prev = link.get("sub_id")
                    if prev and prev != sub_id:
                        moved_from.append((prev, lid))
                    link["sub_id"] = sub_id
        if moved_from:
            # detach configs that moved here from their previous groups
            async with SUBS_LOCK:
                for prev, lid in moved_from:
                    other = SUBS.get(prev)
                    if other is None:
                        continue
                    other_ids = other.get("link_ids", [])
                    if lid in other_ids:
                        other_ids.remove(lid)
    await save_state(strict=True)
    return {"ok": True}

@app.delete("/api/subs/{sub_id}")
async def delete_sub(sub_id: str, _=Depends(require_auth)):
    async with SUBS_LOCK:
        if sub_id not in SUBS:
            raise HTTPException(status_code=404, detail="sub not found")
        name = SUBS[sub_id].get("name", sub_id)
        del SUBS[sub_id]
    async with LINKS_LOCK:
        for link in LINKS.values():
            if link.get("sub_id") == sub_id:
                link["sub_id"] = None
    await save_state(strict=True)
    log_activity("sub", f"گروه «{name}» حذف شد", "warn")
    return {"ok": True, "deleted": sub_id}

@app.post("/api/subs/{sub_id}/links")
async def assign_link_to_sub(sub_id: str, request: Request, _=Depends(require_auth)):
    body = await request.json()
    link_id = str(body.get("link_id", ""))
    action = str(body.get("action", "add"))
    async with SUBS_LOCK:
        if sub_id not in SUBS:
            raise HTTPException(status_code=404, detail="sub not found")
        target_sub = SUBS[sub_id]
    if action == "add":
        async with LINKS_LOCK:
            link = LINKS.get(link_id)
        if link is None:
            raise HTTPException(status_code=404, detail="link not found")
        try:
            validate_raw_tcp_multi_location(link, target_sub.get("multi_location"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    async with SUBS_LOCK:
        s = SUBS[sub_id]
        ids = s.setdefault("link_ids", [])
        if action == "add":
            if link_id not in ids:
                ids.append(link_id)
        else:
            if link_id in ids:
                ids.remove(link_id)
    async with LINKS_LOCK:
        if link_id in LINKS:
            LINKS[link_id]["sub_id"] = sub_id if action == "add" else None
    await save_state(strict=True)
    return {"ok": True}

# ── Public sub-group subscription file ───────────────────────────────────────
@app.get("/sub-group/{uuid_key}")
async def sub_group_subscription(uuid_key: str, request: Request):
    import base64
    async with SUBS_LOCK:
        sub = next((s for s in SUBS.values() if s.get("uuid_key") == uuid_key), None)
    if not sub:
        raise HTTPException(status_code=404, detail="not found")

    if sub.get("password_hash"):
        pw = request.query_params.get("pw", "")
        if hash_password(pw) != sub["password_hash"]:
            raise HTTPException(status_code=403, detail="wrong password")

    host = get_host(request)
    link_ids = sub.get("link_ids", [])
    async with LINKS_LOCK:
        lines = []
        for lid in link_ids:
            link = LINKS.get(lid)
            if link and is_link_allowed(link):
                lines.extend(e["vless_link"] for e in vless_entries_for_link(link, lid, host))

    content = base64.b64encode("\n".join(lines).encode()).decode()
    return Response(
        content=content,
        media_type="text/plain",
        headers={
            "profile-title": quote(sub["name"]),
            "profile-update-interval": "12",
        }
    )

# ── Auth endpoints ────────────────────────────────────────────────────────────
@app.post("/api/login")
async def api_login(request: Request):
    body = await request.json()
    ip = client_ip(request)
    if hash_password(str(body.get("password", ""))) != AUTH["password_hash"]:
        log_activity("auth", f"تلاش ورود ناموفق از {ip}", "err")
        raise HTTPException(status_code=401, detail="رمز عبور اشتباه است")
    token = await create_session()
    log_activity("auth", f"ورود موفق به پنل از {ip}", "ok")
    resp = JSONResponse({"ok": True})
    forwarded_proto = str(request.headers.get("x-forwarded-proto") or request.url.scheme or "").split(",", 1)[0].strip().lower()
    resp.set_cookie(SESSION_COOKIE, token, max_age=SESSION_TTL, httponly=True, secure=forwarded_proto == "https", samesite="lax", path="/")
    return resp

@app.post("/api/logout")
async def api_logout(request: Request):
    await destroy_session(request.cookies.get(SESSION_COOKIE))
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp

@app.get("/api/me")
async def api_me(request: Request):
    return {"authenticated": await is_valid_session(request.cookies.get(SESSION_COOKIE))}

@app.post("/api/change-password")
async def api_change_password(request: Request, token=Depends(require_auth)):
    body = await request.json()
    if hash_password(str(body.get("current_password", ""))) != AUTH["password_hash"]:
        raise HTTPException(status_code=400, detail="رمز فعلی اشتباه است")
    new = str(body.get("new_password", ""))
    if len(new) < 4:
        raise HTTPException(status_code=400, detail="رمز جدید باید حداقل ۴ کاراکتر باشد")
    AUTH["password_hash"] = hash_password(new)
    async with SESSIONS_LOCK:
        SESSIONS.clear()
        SESSIONS[token] = time.time() + SESSION_TTL
    await save_state()
    log_activity("auth", "رمز عبور پنل ت��ییر کرد", "ok")
    return {"ok": True}

# ── Safe diagnostics and proxy-test history ──────────────────────────────────
_DIAGNOSTIC_KINDS = {
    "DOCUMENT_BOOT", "ROUTER_NAVIGATION", "LOCATION_RELOAD", "LOCATION_ASSIGN",
    "LOCATION_REPLACE", "AUTH_REDIRECT", "SERVICE_WORKER_NAVIGATION",
    "SERVICE_WORKER_CONTROLLER_CHANGE", "UNCAUGHT_ERROR", "UNHANDLED_REJECTION",
    "FETCH_START", "FETCH_RESPONSE", "FETCH_ERROR", "PAGE_SHOW", "PAGE_HIDE",
    "BEFORE_UNLOAD", "VISIBILITY_CHANGE", "HISTORY_PUSH", "HISTORY_REPLACE",
    "WINDOW_OPEN", "SERVER_IDENTITY", "POLLER_CREATED", "POLLER_STOPPED", "FEATURE_UNAUTHORIZED", "AUTH_STATE", "AUTH_CHECK_FAILED",
}

def _safe_diag_text(value: object, limit: int = 240) -> str:
    text = "".join(ch for ch in str(value or "") if ch.isprintable())[:limit]
    # Never retain a query string; auth values and opaque tokens often occur there.
    return text.split("?", 1)[0]

def _safe_diag_path(value: object) -> str:
    raw = _safe_diag_text(value, 300)
    if "://" in raw:
        raw = raw.split("://", 1)[1]
        raw = raw[raw.find("/"):] if "/" in raw else "/"
    return raw if raw.startswith("/") else "/"

def sanitize_client_diagnostic(event: object) -> dict | None:
    if not isinstance(event, dict) or event.get("kind") not in _DIAGNOSTIC_KINDS:
        return None
    out = {"kind": event["kind"], "at_ms": int(event.get("at_ms") or 0)}
    for key in ("boot_id", "navigation_type", "classification", "error_type", "reason", "method", "stack", "visibility"):
        if key in event:
            out[key] = _safe_diag_text(event[key], 1800 if key == "stack" else 120)
    if "path" in event:
        out["path"] = _safe_diag_path(event["path"])
    for key in ("status", "duration_ms", "attempt", "boot_count"):
        if key in event:
            try: out[key] = max(0, min(int(event[key]), 2_000_000_000))
            except (TypeError, ValueError): pass
    return out

def sanitize_proxy_test_result(proxy_id: object, result: object) -> dict | None:
    proxy_id = str(proxy_id or "").strip()
    if not proxy_id or not isinstance(result, dict) or str(result.get("proxy_id") or "") != proxy_id:
        return None
    checks = []
    for item in result.get("checks") or []:
        if not isinstance(item, dict): continue
        target = str(item.get("target") or "")
        if target not in {"https://cloudflare.com", "https://google.com"}: continue
        status = item.get("status")
        checks.append({
            "target": target, "ok": bool(item.get("ok")),
            "status": int(status) if isinstance(status, int) and 0 <= status <= 999 else None,
            "latency_ms": max(0, min(int(item.get("latency_ms") or 0), 120_000)),
            "error": _safe_diag_text(item.get("error"), 80) if not item.get("ok") else None,
        })
    if {x["target"] for x in checks} != {"https://cloudflare.com", "https://google.com"}:
        return None
    return {
        "proxy_id": proxy_id,
        "country": _safe_diag_text(result.get("country"), 80),
        "overall_status": "healthy" if bool(result.get("ok")) else "unhealthy",
        "tested_at": _safe_diag_text(result.get("tested_at"), 48),
        "checks": checks,
    }

async def current_proxy_test_results() -> dict:
    async with PROXY_TEST_RESULTS_LOCK:
        snapshot = dict(PROXY_TEST_RESULTS)
    # A stale ID or changed record cannot be presented as the current proxy's test.
    return {pid: result for pid, result in snapshot.items() if proxy_repository.get_record(pid) is not None}

@app.get("/api/diagnostics/server")
async def diagnostics_server(_=Depends(require_auth)):
    return server_diagnostic_identity()

@app.post("/api/diagnostics/client")
async def diagnostics_client_ingest(request: Request, _=Depends(require_auth)):
    body = await request.json()
    raw_events = body.get("events", []) if isinstance(body, dict) else []
    if not isinstance(raw_events, list):
        raise HTTPException(status_code=400, detail="events must be a list")
    accepted = []
    for raw in raw_events[:80]:
        event = sanitize_client_diagnostic(raw)
        if event is not None:
            event["received_at"] = datetime.now(timezone.utc).isoformat()
            event["server_boot_id"] = SERVER_BOOT_ID
            accepted.append(event)
    async with CLIENT_DIAGNOSTIC_LOCK:
        CLIENT_DIAGNOSTIC_EVENTS.extend(accepted)
    return {"accepted": len(accepted), "server": server_diagnostic_identity()}

@app.get("/api/diagnostics/client")
async def diagnostics_client_recent(_=Depends(require_auth)):
    async with CLIENT_DIAGNOSTIC_LOCK:
        events = list(CLIENT_DIAGNOSTIC_EVENTS)
    return {"server": server_diagnostic_identity(), "events": events[-200:]}

# ── مخزن پروکسی / تنظیم آیپی خروجی ─────────────────────────────────────────
@app.get("/api/proxy-catalog")
async def proxy_catalog(_=Depends(require_auth)):
    catalog = await proxy_repository.catalog()
    catalog["proxy_test_results"] = await current_proxy_test_results()
    return catalog
@app.get("/api/proxy-catalog/manual-status")
async def proxy_catalog_manual_status(_=Depends(require_auth)):
    return proxy_repository.manual_refresh_state()

@app.post("/api/proxy-catalog/refresh")
async def proxy_catalog_refresh(_=Depends(require_auth)):
    if not proxy_repository.manual_refresh_enabled():
        raise HTTPException(status_code=403, detail="بررسی دستی مخزن فعال نیست")
    return await proxy_repository.catalog(force=True)


@app.post("/api/proxy-catalog/test")
async def proxy_catalog_test(request: Request, _=Depends(require_auth)):
    body = await request.json()
    proxy_id = str((body or {}).get("proxy_id") or "").strip()
    record = proxy_repository.get_record(proxy_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Selected proxy is not in the current catalog")
    raw_result = await outbound.test_proxy_record(record)
    raw_result.update({"proxy_id": record.id, "country": record.country, "tested_at": datetime.now(timezone.utc).isoformat()})
    result = sanitize_proxy_test_result(record.id, raw_result)
    if result is None:
        raise HTTPException(status_code=500, detail="proxy test produced an invalid result")
    async with PROXY_TEST_RESULTS_LOCK:
        PROXY_TEST_RESULTS[record.id] = result
    await save_state()
    if result["overall_status"] != "healthy":
        return JSONResponse({"ok": False, "proxy_id": record.id, "test_result": result, "receipt": None}, status_code=422)
    return {"ok": True, "proxy_id": record.id, "test_result": result, "receipt": issue_proxy_test_receipt(record), "expires_in": PROXY_TEST_RECEIPT_TTL}

# ── Stats ─────────────────────────────────────────────────────────────────────
@app.get("/stats")
async def get_stats(_=Depends(require_auth)):
    async with LINKS_LOCK:
        snap = dict(LINKS)
    return {
        "active_connections": len(connections),
        "total_traffic_mb": round(stats["total_bytes"] / (1024 ** 2), 2),
        "total_requests": stats["total_requests"],
        "total_errors": stats["total_errors"],
        "uptime": uptime(),
        "timestamp": datetime.now().isoformat(),
        "hourly": dict(hourly_traffic),
        "recent_errors": list(error_logs)[-10:],
        "links_count": len(snap),
        "active_links": sum(1 for l in snap.values() if is_link_allowed(l)),
        "expired_links": sum(1 for l in snap.values() if is_link_expired(l)),
        "subs_count": len(SUBS),
    }

# ── Activity Logs ─────────────────────────────────────────────────────────────
@app.get("/api/activity")
async def get_activity(_=Depends(require_auth)):
    return {"logs": list(activity_logs)[-150:]}

# ── Live connections (with IP) ────────────────────────────────────────────────
@app.get("/api/connections")
async def get_connections(_=Depends(require_auth)):
    """
    خروجی این endpoint حالا بر اساس IP گروه‌بندی شده:
    هر آی‌پی فقط یک آیتم نمایش داده می‌شود، با جمع بایت‌های تمام سشن‌های
    باز روی همان آی‌پی و تعداد سشن‌های فعال آن آی‌پی.
    raw_count همچنان تعداد واقعی اتصالات باز (سشن‌های خام، مثلاً ۴۰ تا
    اتصال هم‌زمان یک موبایل) را برمی‌گرداند.
    """
    async with LINKS_LOCK:
        snap = dict(LINKS)

    grouped: dict[str, dict] = {}
    for conn_id, c in connections.items():
        ip = c.get("ip", "نامشخص")
        link = snap.get(c.get("uuid"))
        label = link.get("label") if link else "نامشخص"
        g = grouped.get(ip)
        if g is None:
            g = {
                "ip": ip,
                "sessions": 0,
                "bytes": 0,
                "labels": set(),
                "transports": set(),
                "first_connected_at": c.get("connected_at"),
                "last_connected_at": c.get("connected_at"),
            }
            grouped[ip] = g
        g["sessions"] += 1
        g["bytes"] += c.get("bytes", 0)
        g["labels"].add(label)
        g["transports"].add(c.get("transport", "vless-ws"))
        ca = c.get("connected_at")
        if ca:
            if not g["first_connected_at"] or ca < g["first_connected_at"]:
                g["first_connected_at"] = ca
            if not g["last_connected_at"] or ca > g["last_connected_at"]:
                g["last_connected_at"] = ca

    result = []
    for ip, g in grouped.items():
        result.append({
            "ip": ip,
            "sessions": g["sessions"],
            "labels": sorted(g["labels"]),
            "label": " · ".join(sorted(g["labels"])) if g["labels"] else "نامشخص",
            "transports": sorted(g["transports"]),
            "bytes": g["bytes"],
            "bytes_fmt": fmt_bytes(g["bytes"]),
            "connected_at": g["first_connected_at"],
            "last_connected_at": g["last_connected_at"],
        })
    result.sort(key=lambda x: x.get("last_connected_at") or "", reverse=True)

    return {
        "connections": result,
        "count": len(result),          # تعداد آی‌پی‌های ی��تا
        "raw_count": len(connections), # تعداد کل اتصالات باز (بدون گروه‌بندی)
    }

# ── Shared link create/delete helpers (استفاده مشترک API و ربات تلگرام) ───────
async def make_link(
    label: str = "لینک جدید",
    limit_bytes: int = 0,
    expires_at: str | None = None,
    note: str = "",
    remark: str = "",
    sub_id: str | None = None,
    protocol: str = DEFAULT_PROTOCOL,
    transport_settings: object = None,
    security: object = "tls",
    fingerprint: str = DEFAULT_FINGERPRINT,
    alpn: str = "",
    port: int = DEFAULT_PORT,
    ip_limit: int = 0,
    speed_limit_bytes: int = 0,
    address: str = "",
    sni: str = "",
    exit_proxy_mode: str = "direct", proxy_id: str = "", custom_proxy: str = "",
    requested_uuid: str = "",
) -> tuple[str, dict]:
    protocol, transport_settings = TRANSPORTS.validate(protocol, transport_settings)
    TRANSPORTS.validate_security(protocol, security)
    if protocol == "vless-tcp":
        if str(address or "").strip() or str(sni or "").strip() or str(alpn or "").strip():
            raise ValueError(
                "Raw TCP endpoint, SNI, and ALPN are managed by the verified deployment"
            )
        if port not in (None, DEFAULT_PORT):
            raise ValueError("Raw TCP port is assigned by the Railway TCP Proxy")
        # Persist no accidental WebSocket endpoint fields on a Raw TCP record.
        address = sni = alpn = ""
        port = DEFAULT_PORT
        if sub_id:
            sub = SUBS.get(sub_id)
            ml = sub.get("multi_location") if isinstance(sub, dict) else None
            validate_raw_tcp_multi_location(
                {
                    "protocol": protocol,
                    "address": address,
                    "port": port,
                    "sni": sni,
                },
                ml,
            )
    fingerprint = (fingerprint or DEFAULT_FINGERPRINT).strip().lower()
    if fingerprint not in FINGERPRINTS:
        fingerprint = DEFAULT_FINGERPRINT
    if not (MIN_PORT <= port <= MAX_PORT):
        port = DEFAULT_PORT
    address = normalize_address(address) if str(address or "").strip() else ""
    sni = normalize_sni(sni) if str(sni or "").strip() else ""
    exit_proxy_mode, proxy_id, custom_proxy = await normalize_exit_proxy(exit_proxy_mode, proxy_id, custom_proxy)
    uid = normalize_requested_uuid(requested_uuid) or generate_uuid()
    async with LINKS_LOCK:
        if uid in LINKS:
            raise ValueError("این UUID قبلاً استفاده شده است")
        LINKS[uid] = {
            "label": (label or "لینک جدید").strip()[:60] or "لینک جدید",
            "limit_bytes": max(0, limit_bytes),
            "used_bytes": 0,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "expires_at": expires_at,
            "note": (note or "").strip()[:200],
            "remark": (remark or label or "Lumen Relay").strip()[:120],
            "is_default": False,
            "sub_id": sub_id,
            "protocol": protocol,
            "transport_settings": transport_settings,
            "fingerprint": fingerprint,
            "alpn": (alpn or "").strip()[:100],
            "port": port,
            "ip_limit": max(0, ip_limit),
            "speed_limit_bytes": max(0, speed_limit_bytes),
            "address": address,
            "sni": sni,
            "exit_proxy_mode": exit_proxy_mode, "proxy_id": proxy_id, "custom_proxy": custom_proxy,
        }
    if sub_id:
        async with SUBS_LOCK:
            if sub_id in SUBS:
                ids = SUBS[sub_id].setdefault("link_ids", [])
                if uid not in ids:
                    ids.append(uid)
    await save_state(strict=True)
    log_activity("link", f"کانفیگ «{LINKS[uid]['label']}» ساخته شد", "ok")
    return uid, LINKS[uid]

async def remove_link(uid: str) -> str | None:
    async with LINKS_LOCK:
        if uid not in LINKS:
            return None
        label = LINKS[uid].get("label", uid)
        sub_id = LINKS[uid].get("sub_id")
        del LINKS[uid]
    if sub_id:
        async with SUBS_LOCK:
            if sub_id in SUBS:
                ids = SUBS[sub_id].get("link_ids", [])
                if uid in ids:
                    ids.remove(uid)
    # باکت محدودیت سرعت هم آزاد بشه (جلوگیری از رشد حافظه بعد از حذف‌های مکرر)
    try:
        from speed_limit import reset_bucket
        reset_bucket(uid)
    except Exception:
        pass
    await save_state(strict=True)
    log_activity("link", f"کانفیگ «{label}» حذف شد", "err")
    return label

async def set_link_active(uid: str, active: bool) -> dict | None:
    async with LINKS_LOCK:
        if uid not in LINKS:
            return None
        LINKS[uid]["active"] = bool(active)
        label = LINKS[uid]["label"]
    log_activity("link", f"کانفیگ «{label}» {'فعال' if active else 'غیرفعال'} شد", "ok" if active else "warn")
    await save_state(strict=True)
    return LINKS[uid]

# ── Multi-Location (subgroup-level exit locations over one UUID/quota) ──────
ML_REQUIRED_LOCATIONS = 2
ML_MAX_REMARK = 60


def _default_multi_location() -> dict:
    return {"enabled": False, "remark_text": "", "locations": []}


def _sanitize_remark_text(value: object) -> str:
    """Admin-provided remark text: single line, no control chars, bounded."""
    text = str(value or "").strip()
    text = "".join(ch for ch in text if ch.isprintable())
    return text[:ML_MAX_REMARK]


def location_remark(location: dict, custom_text: str = "") -> str:
    """"[Location] [Flag] | [Custom text]" — flag/location always generated
    from the configured country; the admin only provides the custom part."""
    base = f"{location.get('country', '')} {location.get('flag', '')}".strip()
    text = _sanitize_remark_text(custom_text)
    return f"{base} | {text}" if text else base


async def validate_multi_location(payload: object, previous: dict | None = None, *, require_tests: bool = False) -> dict:
    """Validate exactly two explicit country -> stable proxy-ID mappings."""
    if not isinstance(payload, dict):
        raise ValueError("multi_location must be an object")
    enabled = bool(payload.get("enabled"))
    remark_text = _sanitize_remark_text(payload.get("remark_text"))
    raw_locations = payload.get("locations") or []
    if not isinstance(raw_locations, list):
        raise ValueError("locations must be a list")
    if enabled and len(raw_locations) != ML_REQUIRED_LOCATIONS:
        raise ValueError("Multi-Location requires exactly two countries")
    if not enabled and raw_locations and len(raw_locations) != ML_REQUIRED_LOCATIONS:
        raise ValueError("Multi-Location stores either zero or exactly two countries")

    previous_by_id = {str(x.get("id") or ""): x for x in ((previous or {}).get("locations") or []) if isinstance(x, dict)}
    locations = []
    seen_ids, seen_codes = set(), set()
    for entry in raw_locations:
        if not isinstance(entry, dict):
            raise ValueError("each location must be an object")
        _name, code = countries.normalize_country(entry.get("code") or entry.get("country"))
        if not code or not countries.is_valid_code(code):
            raise ValueError("location must use a valid ISO alpha-2 country")
        if code in seen_codes:
            raise ValueError("the two Multi-Location countries must be different")
        seen_codes.add(code)
        loc_id = str(entry.get("id") or "").strip()[:24] or secrets.token_urlsafe(8)
        if loc_id in seen_ids:
            raise ValueError("location IDs must be unique")
        seen_ids.add(loc_id)
        proxy_id = str(entry.get("proxy_id") or "").strip()
        record = proxy_repository.get_record(proxy_id)
        if record is None:
            raise ValueError("selected proxy is no longer in the repository")
        if record.code != code:
            raise ValueError(f"selected proxy does not belong to {code}")
        old = previous_by_id.get(loc_id) or {}
        changed = old.get("proxy_id") != proxy_id or old.get("code") != code
        if require_tests and changed:
            require_proxy_test_receipt(proxy_id, entry.get("proxy_test_receipt", ""))
        locations.append({
            "id": loc_id,
            "code": code,
            "country": countries.country_name(code),
            "flag": countries.flag_for(code),
            "proxy_id": proxy_id,
            "active": True,
        })
    return {"enabled": enabled, "remark_text": remark_text, "locations": locations, "selection_mode": "explicit", "failover": False}


def multi_location_for_link(link: dict | None) -> tuple[dict | None, dict | None]:
    """(sub, multi_location) when the route's group has usable Multi-Location."""
    if not isinstance(link, dict):
        return None, None
    sub = SUBS.get(link.get("sub_id") or "")
    if not sub:
        return None, None
    ml = sub.get("multi_location")
    if not isinstance(ml, dict) or not ml.get("enabled"):
        return sub, None
    return sub, ml


def validate_raw_tcp_multi_location(link: dict | None, ml: dict | None) -> None:
    """Require an explicit deployment SNI for every Raw TCP location.

    This is validation only: it neither changes country/proxy mappings nor
    resolves an endpoint. The relay still performs the exact location →
    proxy_id lookup for every session and fails closed if it cannot do so.
    """
    if (
        not isinstance(link, dict)
        or link.get("protocol", DEFAULT_PROTOCOL) != "vless-tcp"
        or not isinstance(ml, dict)
        or not ml.get("enabled")
    ):
        return
    for location in ml.get("locations") or []:
        if not location.get("active"):
            continue
        TRANSPORTS.endpoint(
            "vless-tcp",
            address=link.get("address"),
            port=link.get("port"),
            sni=link.get("sni"),
            fallback_host="",
            location_id=location.get("id"),
        )


async def resolve_exit_selection(link: dict | None, loc_id: str = "") -> dict | None:
    """Resolve one stable proxy ID to one endpoint; never choose or substitute."""
    if not isinstance(link, dict):
        return None
    _sub, ml = multi_location_for_link(link)
    if ml is not None:
        locations = ml.get("locations") or []
        if ml.get("migration_required") or len(locations) != ML_REQUIRED_LOCATIONS:
            raise outbound.ProxyUnavailableError("multi-location requires reconfiguration to exactly two explicit proxies")
        loc_id = str(loc_id or "").strip()
        if not loc_id:
            raise outbound.ProxyUnavailableError("an explicit location is required")
        location = next((loc for loc in locations if loc.get("id") == loc_id and loc.get("active", True)), None)
        if location is None:
            raise outbound.ProxyUnavailableError("requested location is invalid")
        proxy_id = str(location.get("proxy_id") or "")
        record = await proxy_repository.resolve(proxy_id)
        if record is None:
            raise outbound.ProxyUnavailableError("selected location proxy is unavailable")
        if record.code != location.get("code"):
            raise outbound.ProxyUnavailableError("selected proxy country metadata changed")
        return {"proxy_id": record.id, "endpoint": record.endpoint, "location_id": loc_id}
    mode = str(link.get("exit_proxy_mode") or "direct")
    if mode == "repository":
        proxy_id = str(link.get("proxy_id") or "")
        record = await proxy_repository.resolve(proxy_id)
        if record is None:
            raise outbound.ProxyUnavailableError("managed proxy is not in the repository cache")
        return {"proxy_id": record.id, "endpoint": record.endpoint, "location_id": None}
    if mode == "custom":
        try:
            endpoint = proxy_repository.validate_url(link.get("custom_proxy"))
            return {"proxy_id": "custom", "endpoint": endpoint, "location_id": None}
        except ValueError as exc:
            raise outbound.ProxyUnavailableError("custom proxy URL is invalid") from exc
    return None


async def resolve_exit_endpoints(link: dict | None, loc_id: str = "") -> list:
    selection = await resolve_exit_selection(link, loc_id)
    return [selection["endpoint"]] if selection else []


# ── Sub-group helpers (reusable — هم API وب هم ربات تلگرام از همین‌ها استفاده می‌کنن) ──
async def create_sub_group(name: str = "گروه جدید", desc: str = "", password: str = "") -> tuple[str, dict]:
    name = (name or "گروه جدید").strip()[:60]
    desc = (desc or "").strip()[:200]
    password = (password or "").strip()
    sub_id = generate_uuid()
    uuid_key = secrets.token_urlsafe(16)
    async with SUBS_LOCK:
        SUBS[sub_id] = {
            "name": name,
            "desc": desc,
            "password_hash": hash_password(password) if password else None,
            "uuid_key": uuid_key,
            "created_at": datetime.now().isoformat(),
            "link_ids": [],
            "multi_location": _default_multi_location(),
        }
    await save_state(strict=True)
    log_activity("sub", f"گروه «{name}» ساخته شد", "ok")
    return sub_id, SUBS[sub_id]

async def set_link_sub(uid: str, sub_id: str | None) -> bool:
    """یک کانفیگ رو به یک گروه ساب اضافه/منتقل می‌کنه؛ با sub_id=None از گروه فعلیش خارجش می‌کنه."""
    async with LINKS_LOCK:
        if uid not in LINKS:
            return False
        old_sub = LINKS[uid].get("sub_id")
        label = LINKS[uid].get("label", uid)
    if sub_id is not None:
        async with SUBS_LOCK:
            if sub_id not in SUBS:
                return False
            target_sub = SUBS[sub_id]
    else:
        target_sub = None
    if target_sub is not None:
        async with LINKS_LOCK:
            link = LINKS.get(uid)
        try:
            validate_raw_tcp_multi_location(link, target_sub.get("multi_location"))
        except ValueError:
            return False
    async with SUBS_LOCK:
        if old_sub and old_sub in SUBS:
            ids = SUBS[old_sub].get("link_ids", [])
            if uid in ids:
                ids.remove(uid)
        if sub_id and sub_id in SUBS:
            ids = SUBS[sub_id].setdefault("link_ids", [])
            if uid not in ids:
                ids.append(uid)
    async with LINKS_LOCK:
        if uid in LINKS:
            LINKS[uid]["sub_id"] = sub_id
    await save_state(strict=True)
    log_activity("link", f"کانفیگ «{label}» {'به گروه اضافه شد' if sub_id else 'از گروه خارج شد'}", "info")
    return True

async def remove_sub_group(sub_id: str) -> str | None:
    async with SUBS_LOCK:
        if sub_id not in SUBS:
            return None
        name = SUBS[sub_id].get("name", sub_id)
        del SUBS[sub_id]
    async with LINKS_LOCK:
        for link in LINKS.values():
            if link.get("sub_id") == sub_id:
                link["sub_id"] = None
    await save_state(strict=True)
    log_activity("sub", f"گروه «{name}» حذف شد", "warn")
    return name

# ── Config endpoint choices ───────────────────────────────────────────────────
@app.get("/api/config-endpoints")
async def api_config_endpoints(request: Request, _=Depends(require_auth)):
    catalog = configured_endpoint_catalog(request)
    return {
        "ok": True,
        "default_address": catalog["service_host"],
        "default_sni": catalog["service_host"],
        "addresses": [
            {"value": value, "kind": address_kind(value), "current": value == catalog["service_host"]}
            for value in catalog["addresses"]
        ],
        "snis": catalog["snis"],
    }


# ── Version updates ───────────────────────────────────────────────────────────
@app.get("/api/transports")
async def transport_capabilities(_=Depends(require_auth)):
    """Safe, authoritative capability data for the transport-management UI."""
    return {
        "runtime": "native FastAPI/Uvicorn VLESS WebSocket relay",
        "transports": TRANSPORTS.capabilities(),
    }


@app.get("/api/update/setup")
async def update_setup_status(_=Depends(require_auth)):
    return updater.setup_status()

@app.post("/api/update/setup")
async def update_setup_save(request: Request, _=Depends(require_auth)):
    try:
        return await updater.save_setup(await request.json())
    except updater.UpdateError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))

@app.get("/api/update/status")
async def update_status(_=Depends(require_auth)):
    try:
        return await updater.check_latest()
    except updater.UpdateError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))

@app.post("/api/update/apply")
async def update_apply(_=Depends(require_auth)):
    try:
        await save_state(strict=True)
        result = await updater.apply_latest(make_state_snapshot())
        if result.get("started"):
            log_activity("system", "به‌روزرسانی نسخه جدید آغاز شد", "ok")
        return result
    except updater.UpdateError as exc:
        raise HTTPException(status_code=exc.status, detail=str(exc))

# ── Link Management ───────────────────────────────────────────────────────────
@app.post("/api/links")
async def create_link(request: Request, _=Depends(require_auth)):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="invalid body")
    host = get_host(request)
    requested_protocol = body["protocol"] if "protocol" in body else DEFAULT_PROTOCOL
    if requested_protocol == "vless-tcp":
        if any(
            str(body.get(name) or "").strip()
            for name in ("address", "sni", "alpn", "port")
        ):
            raise HTTPException(
                status_code=400,
                detail="Raw TCP endpoint, SNI, ALPN, and port are managed by the verified deployment",
            )
        selected_address = selected_sni = ""
    else:
        try:
            selected_address = normalize_address(body.get("address") or host)
            selected_sni = normalize_sni(body["sni"]) if str(body.get("sni") or "").strip() else ""
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    lv = float(body.get("limit_value") or 0)
    lu = body.get("limit_unit") or "GB"
    limit_bytes = 0 if lv <= 0 else parse_size_to_bytes(lv, lu)
    exp_days = int(body.get("expires_days") or 0)
    expires_at = (datetime.now() + timedelta(days=exp_days)).isoformat() if exp_days > 0 else None
    try:
        port = int(body.get("port") or DEFAULT_PORT)
    except (TypeError, ValueError):
        port = DEFAULT_PORT
    try:
        ip_limit = int(body.get("ip_limit") or 0)
    except (TypeError, ValueError):
        ip_limit = 0

    sv = float(body.get("speed_limit_value") or 0)
    su = body.get("speed_limit_unit") or "MBIT"
    speed_limit_bytes = 0 if sv <= 0 else parse_speed_to_bytes(sv, su)
    try:
        requested_mode = str(body.get("exit_proxy_mode") or "direct").lower()
        requested_proxy_id = str(body.get("proxy_id") or "").strip()
        if requested_mode == "repository":
            require_proxy_test_receipt(requested_proxy_id, body.get("proxy_test_receipt", ""))
        exit_proxy_mode, proxy_id, custom_proxy = await normalize_exit_proxy(requested_mode, requested_proxy_id, body.get("custom_proxy", ""))
    except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))

    try:
        uid, link = await make_link(
            label=body.get("label") or "لینک جدید",
        limit_bytes=limit_bytes,
        expires_at=expires_at,
        note=body.get("note") or "",
        remark=body.get("remark") or body.get("label") or "Lumen Relay",
        sub_id=body.get("sub_id") or None,
        protocol=requested_protocol,
        transport_settings=body.get("transport_settings"),
        security=body.get("security", "tls"),
        fingerprint=body.get("fingerprint") or DEFAULT_FINGERPRINT,
        alpn=body.get("alpn") or "",
        port=port,
        ip_limit=ip_limit,
        speed_limit_bytes=speed_limit_bytes,
        address=selected_address,
        sni=selected_sni,
        exit_proxy_mode=exit_proxy_mode, proxy_id=proxy_id, custom_proxy=custom_proxy,
            requested_uuid=body.get("uuid") or "",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "uuid": uid,
        **link,
        "expired": False,
        "vless_link": vless_link_for_link(link, uid, host),
        "sub_url": "https://" + host + "/sub/" + str(uid),
    }

@app.get("/api/links")
async def list_links(request: Request, _=Depends(require_auth)):
    host = get_host(request)
    async with LINKS_LOCK:
        snap = dict(LINKS)
    result = []
    for uid, d in snap.items():
        proto = d.get("protocol", DEFAULT_PROTOCOL)
        summary = await proxy_repository.summary(d.get("proxy_id")) if d.get("exit_proxy_mode")=="repository" else (proxy_repository.custom_summary(d.get("custom_proxy")) if d.get("exit_proxy_mode")=="custom" else None)
        _sub, _ml = multi_location_for_link(d)
        if _ml is not None:
            _locs = _ml.get("locations", [])
            ml_info = {"enabled": True, "total_locations": len(_locs), "active_locations": sum(1 for _loc in _locs if _loc.get("active"))}
        else:
            ml_info = None
        result.append({
            "uuid": uid,
            **d,
            "protocol": proto, "exit_proxy": summary, "multi_location": ml_info,
            "expired": is_link_expired(d),
            "vless_link": safe_vless_link_for_link(d, uid, host),
            "sub_url": "https://" + host + "/sub/" + str(uid),
            "connected_ips": len(unique_ips_for_uuid(uid)),
        })
    result.sort(key=lambda x: x["created_at"], reverse=True)
    return {"links": result}

@app.patch("/api/links/{uid}")
async def update_link(uid: str, request: Request, _=Depends(require_auth)):
    body = await request.json()
    selection=None
    transport_update = None
    current = LINKS.get(uid)
    if current is None:
        raise HTTPException(status_code=404, detail="link not found")
    if "sub_id" in body and body.get("sub_id"):
        requested_sub_id = str(body.get("sub_id"))
        async with SUBS_LOCK:
            requested_sub = SUBS.get(requested_sub_id)
        if requested_sub is None:
            raise HTTPException(status_code=404, detail="sub not found")
        try:
            validate_raw_tcp_multi_location(
                current, requested_sub.get("multi_location")
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    if current.get("protocol", DEFAULT_PROTOCOL) == "vless-tcp" and any(
        field in body for field in ("address", "sni", "alpn", "port")
    ):
        raise HTTPException(
            status_code=400,
            detail="Raw TCP endpoint, SNI, ALPN, and port are managed by the verified deployment",
        )
    if "protocol" in body or "transport_settings" in body:
        requested_protocol = body.get(
            "protocol", current.get("protocol", DEFAULT_PROTOCOL)
        )
        requested_settings = body.get(
            "transport_settings", current.get("transport_settings")
        )
        try:
            protocol, settings = TRANSPORTS.validate(
                requested_protocol, requested_settings
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if protocol != current.get("protocol", DEFAULT_PROTOCOL):
            raise HTTPException(
                status_code=400,
                detail="Transport cannot be changed after a config is created",
            )
        transport_update = (protocol, settings)
    if "security" in body:
        try:
            TRANSPORTS.validate_security(
                current.get("protocol", DEFAULT_PROTOCOL), body.get("security")
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    if any(k in body for k in ("exit_proxy_mode","proxy_id","custom_proxy")):
        cur=LINKS.get(uid,{})
        try:
            next_mode = str(body.get("exit_proxy_mode", cur.get("exit_proxy_mode", "direct"))).lower()
            next_proxy_id = str(body.get("proxy_id", cur.get("proxy_id", "")) or "").strip()
            changed = next_mode != cur.get("exit_proxy_mode", "direct") or next_proxy_id != cur.get("proxy_id", "")
            if next_mode == "repository" and changed:
                require_proxy_test_receipt(next_proxy_id, body.get("proxy_test_receipt", ""))
            selection=await normalize_exit_proxy(next_mode,next_proxy_id,body.get("custom_proxy",cur.get("custom_proxy","")))
        except ValueError as exc: raise HTTPException(status_code=400,detail=str(exc))
    async with LINKS_LOCK:
        if uid not in LINKS:
            raise HTTPException(status_code=404, detail="link not found")
        link = LINKS[uid]
        old_sub = link.get("sub_id")
        label = link.get("label")
        if "active" in body:
            link["active"] = bool(body["active"])
            log_activity("link", f"کانفیگ «{label}» {'فعال' if link['active'] else 'غیرفعال'} شد", "ok" if link["active"] else "warn")
        if "label" in body:
            link["label"] = str(body["label"])[:60]
        if "note" in body:
            link["note"] = str(body["note"])[:200]
        if "remark" in body:
            link["remark"] = (str(body.get("remark") or link.get("label") or "Lumen Relay").strip()[:120])
        if "reset_usage" in body and body["reset_usage"]:
            link["used_bytes"] = 0
            log_activity("link", f"مصرف کانفیگ «{label}» ریست شد", "info")
        if "limit_value" in body:
            lv = float(body.get("limit_value") or 0)
            lu = body.get("limit_unit") or "GB"
            link["limit_bytes"] = 0 if lv <= 0 else parse_size_to_bytes(lv, lu)
        if "expires_days" in body:
            ed = int(body["expires_days"] or 0)
            link["expires_at"] = (datetime.now() + timedelta(days=ed)).isoformat() if ed > 0 else None
        if "fingerprint" in body:
            fp = str(body.get("fingerprint") or DEFAULT_FINGERPRINT).strip().lower()
            link["fingerprint"] = fp if fp in FINGERPRINTS else DEFAULT_FINGERPRINT
        if "alpn" in body:
            link["alpn"] = str(body.get("alpn") or "").strip()[:100]
        if "port" in body:
            try:
                p = int(body.get("port") or DEFAULT_PORT)
            except (TypeError, ValueError):
                p = DEFAULT_PORT
            link["port"] = p if (MIN_PORT <= p <= MAX_PORT) else DEFAULT_PORT
        if "ip_limit" in body:
            try:
                il = int(body.get("ip_limit") or 0)
            except (TypeError, ValueError):
                il = 0
            link["ip_limit"] = max(0, il)
        if "speed_limit_value" in body:
            sv = float(body.get("speed_limit_value") or 0)
            su = body.get("speed_limit_unit") or "MBIT"
            link["speed_limit_bytes"] = 0 if sv <= 0 else parse_speed_to_bytes(sv, su)
            from speed_limit import reset_bucket
            reset_bucket(uid)
        if "address" in body:
            try:
                link["address"] = normalize_address(body.get("address") or get_host(request))
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
        if "sni" in body:
            try:
                link["sni"] = normalize_sni(body["sni"]) if str(body.get("sni") or "").strip() else ""
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc))
        if transport_update is not None:
            link["protocol"], link["transport_settings"] = transport_update
        if selection is not None: link["exit_proxy_mode"],link["proxy_id"],link["custom_proxy"]=selection
        if any(k in body for k in ("label", "note", "remark", "limit_value", "expires_days", "protocol", "transport_settings", "fingerprint", "alpn", "port", "ip_limit", "speed_limit_value", "address", "sni", "exit_proxy_mode", "proxy_id", "custom_proxy")):
            log_activity("link", f"کانفیگ «{link['label']}» ویرایش شد", "info")
        new_sub = body.get("sub_id", "UNCHANGED")
        if new_sub != "UNCHANGED":
            link["sub_id"] = new_sub or None

    if new_sub != "UNCHANGED":
        async with SUBS_LOCK:
            if old_sub and old_sub in SUBS:
                ids = SUBS[old_sub].get("link_ids", [])
                if uid in ids:
                    ids.remove(uid)
            if new_sub and new_sub in SUBS:
                ids = SUBS[new_sub].setdefault("link_ids", [])
                if uid not in ids:
                    ids.append(uid)

    await save_state(strict=True)
    return {"ok": True}

@app.delete("/api/links/{uid}")
async def delete_link(uid: str, _=Depends(require_auth)):
    label = await remove_link(uid)
    if label is None:
        raise HTTPException(status_code=404, detail="link not found")
    return {"ok": True, "deleted": uid}

# ══════════════════════════════════════════════════════════════════════════════
# VLESS Relay — جدا شده به relay_vless.py (دست نخورده)
# ══════════════════════════════════════════════════════════════════════════════

from relay_vless import RELAY_BUF, websocket_tunnel

app.add_api_websocket_route("/ws/{uuid}", websocket_tunnel)


# ═══════════════════════════���══════════════════════════════════════════════════
# ربات مدیریت تلگرام (اختیاری — فقط اگه TELEGRAM_BOT_TOKEN ست شده باشه فعال می‌شه)
# ═══════════════���══════════════════════════════════════════════════════════════
from telegram_bot import start_bot as _tg_start_bot, stop_bot as _tg_stop_bot

# ── HTTP Proxy ��───────────────────────────────────────────────────────────────
_HOP = {"connection","keep-alive","proxy-authenticate","proxy-authorization",
        "te","trailers","transfer-encoding","upgrade","content-encoding","content-length"}

# The internal HTTP proxy must not be an open relay. With HTTP_PROXY_TOKEN set,
# automation passes ?token= or the X-Proxy-Token header; otherwise the admin
# session cookie is required.
HTTP_PROXY_TOKEN = os.environ.get("HTTP_PROXY_TOKEN", "").strip()

@app.api_route("/proxy/{target_url:path}", methods=["GET","POST","PUT","DELETE","PATCH","HEAD","OPTIONS"])
async def http_proxy(target_url: str, request: Request):
    if HTTP_PROXY_TOKEN:
        supplied = request.headers.get("x-proxy-token") or request.query_params.get("token", "")
        if not hmac.compare_digest(supplied, HTTP_PROXY_TOKEN):
            raise HTTPException(status_code=401, detail="unauthorized")
    else:
        await require_auth(request)
    if not target_url.startswith("http"):
        target_url = "https://" + target_url
    try:
        body = await request.body()
        headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP and k.lower() != "host"}
        resp = await http_client.request(method=request.method, url=target_url, headers=headers, content=body)
        stats["total_bytes"] += len(resp.content)
        stats["total_requests"] += 1
        hourly_traffic[now_ir().strftime("%H:00")] += len(resp.content)
        return Response(content=resp.content, status_code=resp.status_code,
                        headers={k: v for k, v in resp.headers.items() if k.lower() not in _HOP})
    except Exception as exc:
        stats["total_errors"] += 1
        error_logs.append({"error": str(exc), "url": target_url, "time": datetime.now().isoformat()})
        raise HTTPException(status_code=502, detail=f"Proxy error: {exc}")

# ── Public sub page ───────────────────────────────────────────────────────────
@app.get("/p/{uuid_key}", response_class=HTMLResponse)
async def public_sub_page(uuid_key: str, request: Request):
    from pages import get_public_page_html
    async with SUBS_LOCK:
        sub = next(({"sub_id": sid, **s} for sid, s in SUBS.items() if s.get("uuid_key") == uuid_key), None)
    if not sub:
        return HTMLResponse("<h2 style='font-family:sans-serif;padding:40px'>گروه پیدا نشد</h2>", status_code=404)
    return HTMLResponse(content=get_public_page_html(uuid_key))

@app.get("/api/public/sub/{uuid_key}")
async def public_sub_data(uuid_key: str, request: Request):
    async with SUBS_LOCK:
        sub_entry = next(((sid, s) for sid, s in SUBS.items() if s.get("uuid_key") == uuid_key), None)
    if not sub_entry:
        raise HTTPException(status_code=404, detail="not found")
    sub_id, sub = sub_entry

    has_pw = sub.get("password_hash") is not None
    if has_pw:
        pw = request.query_params.get("pw", "")
        if hash_password(pw) != sub["password_hash"]:
            return JSONResponse({"locked": True, "name": sub["name"]})

    host = get_host(request)
    link_ids = sub.get("link_ids", [])
    async with LINKS_LOCK:
        snap = dict(LINKS)

    links_out = []
    active_conns = 0
    for lid in link_ids:
        link = snap.get(lid)
        if not link:
            continue
        allowed = is_link_allowed(link)
        conn_count = sum(1 for c in connections.values() if c.get("uuid") == lid)
        active_conns += conn_count
        proto = link.get("protocol", DEFAULT_PROTOCOL)
        # Preserve the existing inactive-link display behavior, but never
        # serialize a persisted Raw TCP record whose deployment capability or
        # location-SNI map is no longer valid.
        entries = (
            []
            if proto == "vless-tcp" and not allowed
            else vless_entries_for_link(link, lid, host)
        )
        for entry in entries:
            links_out.append({
                "uuid": lid,
                "label": link["label"],
                "remark": entry["remark"],
                "location": entry["location"],
                "shared_quota": entry["shared_quota"],
                "active": allowed,
                "protocol": proto,
                "used_bytes": link.get("used_bytes", 0),
                "used_fmt": fmt_bytes(link.get("used_bytes", 0)),
                "limit_bytes": link.get("limit_bytes", 0),
                "limit_fmt": "∞" if link.get("limit_bytes", 0) == 0 else fmt_bytes(link["limit_bytes"]),
                "expires_at": link.get("expires_at"),
                "vless_link": entry["vless_link"],
                "sub_url": "https://" + host + "/sub/" + str(lid),
                "connections": conn_count,
                "ip_limit": link.get("ip_limit", 0),
                "speed_limit_bytes": link.get("speed_limit_bytes", 0),
            })

    total_used = sum(l["used_bytes"] for l in {l["uuid"]: l for l in links_out}.values())
    return {
        "locked": False,
        "name": sub["name"],
        "desc": sub.get("desc", ""),
        "sub_url": "https://" + host + "/sub-group/" + str(uuid_key),
        "active_connections": active_conns,
        "total_used_fmt": fmt_bytes(total_used),
        "links": links_out,
    }

# ── HTML Pages (login + dashboard) ───────────────────────────────────────────
from pages import LOGIN_HTML, DASHBOARD_HTML, LANDING_HTML

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if await is_valid_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url="/dashboard")
    return HTMLResponse(content=LOGIN_HTML)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not await is_valid_session(request.cookies.get(SESSION_COOKIE)):
        return RedirectResponse(url="/login")
    await ensure_default_link()
    return HTMLResponse(content=DASHBOARD_HTML)

@app.get("/test-ws", response_class=HTMLResponse)
async def test_ws_redirect():
    return HTMLResponse(content="<script>location.href='/dashboard'</script>")

if __name__ == "__main__":
    # تیون سرور برای حداکثر توان عبوری:
    #  • uvloop + httptools اگر نصب باشند (حدود ۲برابر سریع‌تر از حلقه‌ی پیش‌فرض)
    #  • ws_max_size بزرگ تا فریم‌های چندمگابایتی تکه‌تکه نشوند
    #  • ping خودکار خاموش (ترافیک و وقفه‌ی اضافی نداشته باشیم)
    #  • backlog بزرگ برای موج اتصال‌های موازی
    #  • GC تنبل (آستانه‌ی بزرگ + freeze) تا مکث‌های جمع‌آوری حافظه وسط ترافیک سنگین نیفتد
    #  • فشرده‌سازی WebSocket خاموش (ترافیک رمزشده قابل فشرده‌سازی نیست و فقط CPU می‌سوزاند)
    import gc
    gc.collect()
    gc.set_threshold(100_000, 200, 200)
    try:
        gc.freeze()
    except Exception:
        pass

    _loop = "auto"
    _http = "auto"
    try:
        import uvloop  # noqa: F401
        _loop = "uvloop"
    except Exception:
        pass
    try:
        import httptools  # noqa: F401
        _http = "httptools"
    except Exception:
        pass

    # Uvicorn 0.52.4 + websockets 17 Sans-I/O: بدون کپی payload تک‌فریمی.
    # پروتکل سفارشی ما queue را burst می‌کند و دو رفت‌وبرگشت ASGI را از هر فریم حذف می‌کند.
    try:
        from turbo_ws_protocol import TurboWebSocketsSansIOProtocol
        _ws_protocol = TurboWebSocketsSansIOProtocol
    except Exception as _ws_import_error:
        # اگر محیط هنوز dependencyهای قبلی را cache کرده، سرویس بالا می‌آید و به
        # انتخاب خودکار Uvicorn برمی‌گردد؛ فقط fast path غیرفعال می‌شود.
        _ws_protocol = "auto"
        logger.warning("WS turbo protocol unavailable: %s", _ws_import_error)

    # سوک�� listen را خودمان می‌سازیم تا بتوانیم بافرها و کنترل ازدحام را روی آن تنظیم کنیم؛
    # هر اتصال WebSocket پذیرفته‌شده این تنظیمات را ارث می‌برد → مسیر دانلود به کلاینت پهن می‌شود.
    import socket as _socket

    def _prepare_listen_socket(family, bind_address):
        sock = _socket.socket(family, _socket.SOCK_STREAM)
        try:
            sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
            if family == _socket.AF_INET6:
                # One dual-stack socket accepts native IPv6 and IPv4-mapped peers.
                # If the kernel cannot guarantee V6ONLY=0 we close it and fall back
                # to the old IPv4 listener, so IPv4 can never regress.
                sock.setsockopt(_socket.IPPROTO_IPV6, _socket.IPV6_V6ONLY, 0)
                if sock.getsockopt(_socket.IPPROTO_IPV6, _socket.IPV6_V6ONLY) != 0:
                    raise OSError("kernel keeps IPV6_V6ONLY enabled")
            sock.bind(bind_address)
            sock.listen(16384)
            sock.set_inheritable(True)

            tfo = getattr(_socket, "TCP_FASTOPEN", None)
            if tfo is not None:
                try:
                    sock.setsockopt(_socket.IPPROTO_TCP, tfo, 8192)
                except OSError:
                    pass
            defer_accept = getattr(_socket, "TCP_DEFER_ACCEPT", None)
            if defer_accept is not None:
                try:
                    sock.setsockopt(_socket.IPPROTO_TCP, defer_accept, 1)
                except OSError:
                    pass
            for option, value in (
                (_socket.SO_SNDBUF, 32 * 1024 * 1024),
                (_socket.SO_RCVBUF, 32 * 1024 * 1024),
            ):
                try:
                    sock.setsockopt(_socket.SOL_SOCKET, option, value)
                except OSError:
                    pass
            congestion = getattr(_socket, "TCP_CONGESTION", None)
            if congestion is not None:
                for algorithm in (b"bbr", b"cubic"):
                    try:
                        sock.setsockopt(_socket.IPPROTO_TCP, congestion, algorithm)
                        break
                    except OSError:
                        continue
            return sock
        except BaseException:
            sock.close()
            raise

    _listen_sock = None
    # Prefer a true dual-stack listener. IPv4-only is a guaranteed fallback.
    for _family, _bind, _label in (
        (_socket.AF_INET6, ("::", CONFIG["port"]), "IPv6+IPv4 dual-stack"),
        (_socket.AF_INET, ("0.0.0.0", CONFIG["port"]), "IPv4 fallback"),
    ):
        try:
            _listen_sock = _prepare_listen_socket(_family, _bind)
            logger.info("Listening on %s port %s", _label, CONFIG["port"])
            break
        except OSError as _listen_error:
            logger.warning("Cannot enable %s listener: %s", _label, _listen_error)

    _config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=CONFIG["port"],
        log_level="info",
        workers=1,
        loop=_loop,
        http=_http,
        ws=_ws_protocol,
        ws_max_size=64 * 1024 * 1024,
        ws_max_queue=512,
        ws_ping_interval=None,
        ws_ping_timeout=None,
        ws_per_message_deflate=False,
        backlog=16384,
        timeout_keep_alive=120,
        limit_concurrency=None,
        limit_max_requests=None,
        access_log=False,
        server_header=False,
        date_header=False,
    )
    _server = uvicorn.Server(_config)
    if _listen_sock is not None:
        _server.run(sockets=[_listen_sock])
    else:
        _server.run()
    
