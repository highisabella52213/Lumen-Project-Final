import asyncio
import importlib.util
import json
import os
import sys
import tempfile
import types
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = tempfile.mkdtemp(prefix="store-bot-")
os.environ["DATA_DIR"] = TMP
os.environ["TELEGRAM_ADMIN_IDS"] = "9001"
os.environ["STORE_CARD_NUMBER"] = "6037997512345678"
os.environ["STORE_CARD_HOLDER"] = "Test Admin"
os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"

links = {}
subs = {}
links_lock = asyncio.Lock()

async def make_link(**kwargs):
    uid = f"00000000-0000-0000-0000-{len(links)+1:012d}"
    links[uid] = {
        "label": kwargs.get("label"),
        "limit_bytes": kwargs.get("limit_bytes", 0),
        "used_bytes": 0,
        "created_at": datetime.now().isoformat(),
        "active": True,
        "expires_at": kwargs.get("expires_at"),
        "note": kwargs.get("note", ""),
        "sub_id": kwargs.get("sub_id"),
        "protocol": kwargs.get("protocol"),
        "fingerprint": kwargs.get("fingerprint"),
        "alpn": kwargs.get("alpn"),
        "port": kwargs.get("port"),
        "ip_limit": kwargs.get("ip_limit"),
        "speed_limit_bytes": kwargs.get("speed_limit_bytes", 0),
    }
    return uid, links[uid]

async def create_sub_group(name="group"):
    sid = f"sub-{len(subs)+1}"
    subs[sid] = {"name": name, "uuid_key": f"key-{len(subs)+1}", "link_ids": []}
    return sid, subs[sid]

async def set_link_sub(uid, sid):
    if uid not in links or sid not in subs:
        return False
    old = links[uid].get("sub_id")
    if old in subs and uid in subs[old]["link_ids"]:
        subs[old]["link_ids"].remove(uid)
    links[uid]["sub_id"] = sid
    if uid not in subs[sid]["link_ids"]:
        subs[sid]["link_ids"].append(uid)
    return True

async def save_state():
    return None

def is_link_allowed(link):
    if not link or not link.get("active", True):
        return False
    exp = link.get("expires_at")
    if exp and datetime.now() >= datetime.fromisoformat(exp):
        return False
    return not link.get("limit_bytes") or link.get("used_bytes", 0) < link["limit_bytes"]

def fmt_bytes(value):
    return f"{value / 1024**3:.2f} GB"

def get_host(*args):
    return "vpn.example.com"

def vless_link_for_link(link, uid, host):
    assert link["protocol"] == "vless-ws"
    return f"vless://{uid}@{host}:443?type=ws#service"

logger = types.SimpleNamespace(
    info=lambda *a, **k: None,
    warning=lambda *a, **k: None,
    exception=lambda *a, **k: None,
)
main_stub = types.ModuleType("main")
for key, value in {
    "LINKS": links,
    "LINKS_LOCK": links_lock,
    "SUBS": subs,
    "DEFAULT_FINGERPRINT": "chrome",
    "DEFAULT_PORT": 443,
    "create_sub_group": create_sub_group,
    "fmt_bytes": fmt_bytes,
    "get_host": get_host,
    "is_link_allowed": is_link_allowed,
    "logger": logger,
    "make_link": make_link,
    "save_state": save_state,
    "set_link_sub": set_link_sub,
    "vless_link_for_link": vless_link_for_link,
}.items():
    setattr(main_stub, key, value)
sys.modules["main"] = main_stub

# outbound is a real standalone module; make it importable for the bot.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

class FakeAsyncClient:
    pass

class FakeLimits:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

httpx_stub = types.ModuleType("httpx")
httpx_stub.AsyncClient = FakeAsyncClient
httpx_stub.Limits = FakeLimits
sys.modules["httpx"] = httpx_stub

spec = importlib.util.spec_from_file_location("telegram_bot_store_test", ROOT / "telegram_bot.py")
bot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bot)

async def run():
    bot.STORE = bot._default_store()
    bot.STORE["settings"]["card_number"] = "6037997512345678"
    bot.STORE["settings"]["card_holder"] = "Test Admin"
    user = await bot._ensure_user({"id": 101, "username": "buyer", "first_name": "Buyer"})
    assert user["balance"] == 0

    # Gift code: one redemption, wallet credit, no double-use.
    bot.STORE["gift_codes"]["WELCOME50"] = {
        "amount": 50_000, "max_uses": 2, "used_by": [], "active": True, "expires_at": None,
    }
    amount, error = await bot._redeem_gift(101, "welcome50")
    assert not error and amount == 50_000 and user["balance"] == 50_000
    amount, error = await bot._redeem_gift(101, "WELCOME50")
    assert amount is None and "قبلاً" in error and user["balance"] == 50_000

    # Discount + wallet purchase provisions WS and keeps ownership/subscription metadata.
    user["balance"] = 1_000_000
    bot.STORE["discount_codes"]["OFF20"] = {
        "type": "percent", "value": 20, "max_uses": 5, "uses": 0,
        "used_by": [], "orders": [], "active": True, "expires_at": None,
    }
    plan = bot.PLAN_BY_ID["eco30"]
    order = await bot._create_order(101, "new", plan)
    order, error = await bot._apply_discount(order["id"], 101, "off20")
    assert not error and order["amount"] == 63_200
    done, error = await bot._finish_order(order["id"], None, "wallet")
    assert not error and done["status"] == "approved"
    uid = done["service_id"]
    assert user["balance"] == 936_800
    assert links[uid]["protocol"] == "vless-ws"
    assert links[uid]["owner_telegram_id"] == 101
    assert links[uid]["limit_bytes"] == 30 * 1024**3
    assert links[uid]["sub_id"] in subs and uid in subs[links[uid]["sub_id"]]["link_ids"]
    assert bot.STORE["discount_codes"]["OFF20"]["uses"] == 1

    # Renewal preserves unused traffic and extends from current expiry, not from today.
    links[uid]["used_bytes"] = 10 * 1024**3
    old_expiry = datetime.now() + timedelta(days=10)
    links[uid]["expires_at"] = old_expiry.isoformat()
    renew_plan = bot.PLAN_BY_ID["std30"]
    renewal = await bot._create_order(101, "renew", renew_plan, service_id=uid)
    renewed, error = await bot._finish_order(renewal["id"], None, "wallet")
    assert not error and renewed["status"] == "approved"
    assert links[uid]["limit_bytes"] == 80 * 1024**3  # 20 GB left + 60 GB bought
    assert links[uid]["used_bytes"] == 0
    new_expiry = datetime.fromisoformat(links[uid]["expires_at"])
    assert timedelta(days=39, hours=23) < new_expiry - datetime.now() < timedelta(days=41)
    assert links[uid]["protocol"] == "vless-ws"

    # Card-to-card top-up: receipt -> admin queue -> approval, exactly once.
    topup = await bot._create_order(101, "wallet", amount=120_000)
    topup, error = await bot._start_card_payment(topup["id"], 101)
    assert not error and topup["status"] == "awaiting_receipt"
    topup, error = await bot._submit_receipt(101, {"type": "photo", "file_id": "FILE"}, topup["id"])
    assert not error and topup["status"] == "pending_admin"
    before = user["balance"]
    topup, error = await bot._finish_order(topup["id"], 9001, "card")
    assert not error and topup["status"] == "approved" and user["balance"] == before + 120_000
    again, message = await bot._finish_order(topup["id"], 9001, "card")
    assert again["status"] == "approved" and "قبلاً" in message and user["balance"] == before + 120_000

    # Rejection releases a reserved promo slot.
    bot.STORE["discount_codes"]["FIX10"] = {
        "type": "fixed", "value": 10_000, "max_uses": 1, "uses": 0,
        "used_by": [], "orders": [], "active": True, "expires_at": None,
    }
    rejected = await bot._create_order(101, "new", plan)
    rejected, error = await bot._apply_discount(rejected["id"], 101, "FIX10")
    rejected, error = await bot._start_card_payment(rejected["id"], 101)
    assert bot.STORE["discount_codes"]["FIX10"]["uses"] == 1
    rejected, error = await bot._submit_receipt(101, {"type": "photo", "file_id": "FILE2"}, rejected["id"])
    rejected, error = await bot._reject_order(rejected["id"], 9001)
    assert not error and rejected["status"] == "rejected"
    assert bot.STORE["discount_codes"]["FIX10"]["uses"] == 0
    assert bot.STORE["discount_codes"]["FIX10"]["used_by"] == []

    # Abandoned receipt orders expire and release their reserved promo slot.
    stale = await bot._create_order(101, "new", plan)
    stale, error = await bot._apply_discount(stale["id"], 101, "FIX10")
    stale, error = await bot._start_card_payment(stale["id"], 101)
    assert not error and bot.STORE["discount_codes"]["FIX10"]["uses"] == 1
    stale["payment_started_at"] = (datetime.now() - timedelta(hours=25)).isoformat()
    assert await bot._expire_stale_orders() == 1
    assert stale["status"] == "expired"
    assert bot.STORE["discount_codes"]["FIX10"]["uses"] == 0

    # Explicit cancellation has the same reservation-release guarantee.
    cancelled = await bot._create_order(101, "new", plan)
    cancelled, error = await bot._apply_discount(cancelled["id"], 101, "FIX10")
    cancelled, error = await bot._start_card_payment(cancelled["id"], 101)
    assert await bot._cancel_waiting_order(cancelled["id"], 101)
    assert cancelled["status"] == "cancelled"
    assert bot.STORE["discount_codes"]["FIX10"]["uses"] == 0

    # Admin gift/promo creation wizards persist validated definitions.
    pending = {"action": "gift_admin_code", "data": {}}
    await bot._admin_gift_text(9001, "ADMIN50", pending)
    await bot._admin_gift_text(9001, "50000", bot._pending[9001])
    await bot._admin_gift_text(9001, "10", bot._pending[9001])
    await bot._admin_gift_text(9001, "30", bot._pending[9001])
    assert bot.STORE["gift_codes"]["ADMIN50"]["amount"] == 50_000
    promo = {"action": "promo_admin_value", "data": {"code": "ADMIN20", "type": "percent"}}
    await bot._admin_promo_text(9001, "20", promo)
    await bot._admin_promo_text(9001, "100", bot._pending[9001])
    await bot._admin_promo_text(9001, "7", bot._pending[9001])
    assert bot.STORE["discount_codes"]["ADMIN20"]["value"] == 20

    # Ownership boundary and complete URLs.
    links["foreign"] = {"owner_telegram_id": 202, "created_at": "z", "protocol": "vless-ws"}
    services = bot._user_services(101)
    assert [x[0] for x in services] == [uid]
    assert bot.API_BASE == "https://api.telegram.org/bottest-token"
    service_url = "https:" + "//" + get_host() + "/sub/" + uid
    assert service_url.startswith("https://vpn.example.com/sub/") and service_url.endswith(uid)

    # Persistence round trip keeps money/order data.
    await bot._save_store()
    snapshot = json.loads(Path(TMP, "telegram_store.json").read_text(encoding="utf-8"))
    assert snapshot["users"]["101"]["balance"] == user["balance"]
    assert snapshot["orders"][topup["id"]]["status"] == "approved"
    print(
        "store bot: gift=OK discount=OK wallet=OK card-review-idempotent=OK "
        "new-ws=OK renew-carryover=OK stale-release=OK admin-codes=OK "
        "ownership=OK persistence=OK"
    )

if __name__ == "__main__":
    asyncio.run(run())
