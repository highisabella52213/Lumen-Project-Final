#!/usr/bin/env python3
"""Transport capabilities, persistence, and fail-closed integration contract.

Runs without FastAPI/Uvicorn wheels so it remains a deterministic source-level
regression test. A separate real WebSocket data-plane test is run when the
project runtime dependencies are installed.
"""
import asyncio
import json
import os
import sys
import tempfile
import time
import types
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="lumen-transport-")

from transports import (
    TRANSPORTS,
    TransportUnavailableError,
    TransportValidationError,
)


class App:
    def __init__(self, *_args, **_kwargs):
        pass

    def deco(self, *_args, **_kwargs):
        return lambda function: function

    on_event = get = post = patch = delete = api_route = middleware = deco

    def add_middleware(self, *_args, **_kwargs):
        pass

    def add_api_websocket_route(self, *_args, **_kwargs):
        pass


class HTTPException(Exception):
    def __init__(self, status_code=500, detail=""):
        self.status_code = status_code
        self.detail = detail


class Dummy:
    pass


class Response:
    def __init__(self, *_args, **_kwargs):
        pass


fastapi = types.ModuleType("fastapi")
fastapi.FastAPI = App
fastapi.Request = Dummy
fastapi.HTTPException = HTTPException
fastapi.WebSocket = Dummy
fastapi.WebSocketDisconnect = type("WebSocketDisconnect", (Exception,), {})
fastapi.Depends = lambda value: value
responses = types.ModuleType("fastapi.responses")
for name in ("Response", "HTMLResponse", "JSONResponse", "RedirectResponse"):
    setattr(responses, name, Response)
cors = types.ModuleType("fastapi.middleware.cors")
cors.CORSMiddleware = Dummy
httpx = types.ModuleType("httpx")
httpx.AsyncClient = Dummy
httpx.Limits = Dummy
httpx.Timeout = Dummy
uvicorn = types.ModuleType("uvicorn")
uvicorn.Config = Dummy
uvicorn.Server = Dummy
telegram = types.ModuleType("telegram_bot")


async def noop(*_args, **_kwargs):
    pass


telegram.start_bot = noop
telegram.stop_bot = noop
pages = types.ModuleType("pages")
pages.LOGIN_HTML = pages.DASHBOARD_HTML = pages.LANDING_HTML = ""
sys.modules.update(
    {
        "fastapi": fastapi,
        "fastapi.responses": responses,
        "fastapi.middleware": types.ModuleType("fastapi.middleware"),
        "fastapi.middleware.cors": cors,
        "aiofiles": types.ModuleType("aiofiles"),
        "httpx": httpx,
        "uvicorn": uvicorn,
        "telegram_bot": telegram,
        "pages": pages,
    }
)

import main
import proxy_repository as repo


class Request:
    def __init__(self, body):
        self._body = body
        self.headers = {}

    async def json(self):
        return self._body


def expect(error_type, callback, label):
    try:
        callback()
    except error_type:
        return
    raise AssertionError(f"{label} was accepted")


async def expect_http_400(body, label):
    try:
        await main.create_link(Request(body))
    except HTTPException as exc:
        assert exc.status_code == 400, (label, exc.status_code, exc.detail)
        return
    raise AssertionError(f"{label} was accepted by the API")


async def run():
    # Transport adapter schema + serialization: only the native WS adapter can
    # emit a URI; none of the unavailable adapters can be serialized as a fake
    # config.
    ws_id, ws_settings = TRANSPORTS.validate("vless-ws", None)
    assert (ws_id, ws_settings) == ("vless-ws", {})
    expect(
        TransportValidationError,
        lambda: TRANSPORTS.validate("unknown-transport", {}),
        "unknown transport",
    )
    expect(
        TransportValidationError,
        lambda: TRANSPORTS.validate("vless-ws", {"path": "/ignored"}),
        "unsupported WS setting",
    )
    expect(
        TransportValidationError,
        lambda: TRANSPORTS.validate_security("vless-ws", "none"),
        "non-TLS security",
    )
    for transport_id in ("vless-grpc", "vless-kcp", "vless-httpupgrade"):
        expect(
            TransportUnavailableError,
            lambda transport_id=transport_id: TRANSPORTS.validate(
                transport_id, {}
            ),
            transport_id,
        )
        expect(
            TransportUnavailableError,
            lambda transport_id=transport_id: TRANSPORTS.vless_parameters(
                transport_id,
                uuid="unit-id",
                transport_host="relay.example",
            ),
            transport_id + " serializer",
        )

    serialized = TRANSPORTS.vless_parameters(
        "vless-ws",
        uuid="unit-id",
        transport_host="relay.example",
        location_id="loc-A",
    )
    assert serialized == {
        "type": "ws",
        "host": "relay.example",
        "path": "/ws/unit-id?ed=4096&loc=loc-A",
    }

    # Establish a selected repository proxy solely to prove the transport
    # registry neither rewrites the stored ID nor changes resolver output.
    record = repo.Record(
        "exact-proxy",
        "http://127.0.0.1:8080",
        "http",
        "Germany",
        "DE",
        "🇩🇪",
        1,
    )
    repo._records = {record.id: record}
    repo._last = time.monotonic()
    repo._error = ""

    uid, link = await main.make_link(
        label="transport contract",
        protocol="vless-ws",
        transport_settings={},
        exit_proxy_mode="repository",
        proxy_id=record.id,
    )
    assert link["protocol"] == "vless-ws"
    assert link["transport_settings"] == {}
    assert link["proxy_id"] == record.id
    assert (await main.resolve_exit_selection(link))["proxy_id"] == record.id

    uri = main.vless_link_for_link(link, uid, "relay.example")
    query = parse_qs(urlsplit(uri).query)
    assert query["type"] == ["ws"]
    assert query["host"] == ["relay.example"]
    assert query["path"] == [f"/ws/{uid}?ed=4096"]

    # Actual JSON state save/reload round trip, including the omitted legacy
    # setting default. Existing WS records remain usable and generated.
    await main.save_state(strict=True)
    saved = json.loads(main.DATA_FILE.read_text(encoding="utf-8"))
    assert saved["links"][uid]["transport_settings"] == {}
    saved["links"][uid].pop("transport_settings")
    main.DATA_FILE.write_text(json.dumps(saved), encoding="utf-8")
    main.LINKS.clear()
    await main.load_state()
    restored = main.LINKS[uid]
    assert restored["protocol"] == "vless-ws"
    assert restored["transport_settings"] == {}
    assert main.is_link_allowed(restored)
    assert (await main.resolve_exit_selection(restored))["proxy_id"] == record.id
    assert parse_qs(urlsplit(main.vless_link_for_link(restored, uid, "relay.example")).query)["type"] == ["ws"]

    # Backend API is authoritative: unknown and unsupported choices are never
    # converted to WS or written. A failed update leaves the exact proxy and
    # transport intact.
    before = dict(restored)
    await expect_http_400({"protocol": "unknown-transport"}, "unknown transport")
    await expect_http_400(
        {"protocol": "vless-ws", "security": "none"},
        "non-TLS security",
    )
    for transport_id in ("vless-grpc", "vless-kcp", "vless-httpupgrade"):
        await expect_http_400({"protocol": transport_id}, transport_id)
        try:
            await main.update_link(uid, Request({"protocol": transport_id}))
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "NOT SUPPORTED BY CURRENT RUNTIME" in exc.detail
        else:
            raise AssertionError(f"{transport_id} update was accepted")
        assert main.LINKS[uid]["proxy_id"] == before["proxy_id"]
        assert main.LINKS[uid]["protocol"] == before["protocol"]
        assert (await main.resolve_exit_selection(main.LINKS[uid]))["proxy_id"] == record.id

    # Capability data is explicit and safe for the admin UI.
    payload = await main.transport_capabilities()
    capability = {item["id"]: item for item in payload["transports"]}
    assert payload["runtime"] == "native FastAPI/Uvicorn VLESS WebSocket relay"
    assert capability["vless-ws"]["available"] is True
    for transport_id in ("vless-grpc", "vless-kcp", "vless-httpupgrade"):
        assert capability[transport_id]["available"] is False
        assert capability[transport_id]["status"] == "NOT SUPPORTED BY CURRENT RUNTIME"
        assert capability[transport_id]["settings_schema"]["properties"] == {}

    await main.shutdown()
    print(
        "transport registry: WS-schema/persistence/serialization=OK "
        "gRPC=blocked KCP=blocked HTTPUpgrade=blocked "
        "unknown=blocked exact-proxy-unchanged=OK"
    )


asyncio.run(run())