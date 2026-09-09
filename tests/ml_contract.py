#!/usr/bin/env python3
"""Exact Multi-Location contract: two countries, one stable proxy each, no failover."""
import asyncio, os, sys, tempfile, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ["DATA_DIR"]=tempfile.mkdtemp(prefix="lumen-ml-")
# main.py is tested without downloading framework wheels.
import types
class App:
 def __init__(self,*a,**k):pass
 def deco(self,*a,**k):return lambda f:f
 on_event=get=post=patch=delete=api_route=middleware=deco
 def add_middleware(self,*a,**k):pass
 def add_api_websocket_route(self,*a,**k):pass
class HTTPException(Exception):
 def __init__(self,status_code=500,detail=''):self.status_code=status_code;self.detail=detail
class Dummy:pass
class WebSocketDisconnect(Exception):pass
fa=types.ModuleType('fastapi');fa.FastAPI=App;fa.Request=Dummy;fa.HTTPException=HTTPException;fa.WebSocket=Dummy;fa.WebSocketDisconnect=WebSocketDisconnect;fa.Depends=lambda f:f
responses=types.ModuleType('fastapi.responses')
for n in ['Response','HTMLResponse','JSONResponse','RedirectResponse']:
 setattr(responses,n,type(n,(),{'__init__':lambda self,*a,**k:None}))
cors=types.ModuleType('fastapi.middleware.cors');cors.CORSMiddleware=Dummy
sys.modules.update({'fastapi':fa,'fastapi.responses':responses,'fastapi.middleware':types.ModuleType('fastapi.middleware'),'fastapi.middleware.cors':cors})
sys.modules['aiofiles']=types.ModuleType('aiofiles')
httpx=types.ModuleType('httpx');httpx.AsyncClient=Dummy;httpx.Limits=Dummy;httpx.Timeout=Dummy;sys.modules['httpx']=httpx
uv=types.ModuleType('uvicorn');uv.Config=Dummy;uv.Server=Dummy;sys.modules['uvicorn']=uv
t=types.ModuleType('telegram_bot')
async def noop(*a,**k):pass
t.start_bot=noop;t.stop_bot=noop;sys.modules['telegram_bot']=t
pg=types.ModuleType('pages');pg.LOGIN_HTML=pg.DASHBOARD_HTML=pg.LANDING_HTML='';sys.modules['pages']=pg
import main, outbound, proxy_repository as repo

async def run():
    recs=[
      repo.Record("de1","http://10.0.0.1:8080","http","Germany","DE","🇩🇪",5),
      repo.Record("al1","http://10.0.1.1:8080","http","Albania","AL","🇦🇱",99),
      repo.Record("lv1","http://10.0.2.1:8080","http","Latvia","LV","🇱🇻",100),
    ]
    repo._records={r.id:r for r in recs};repo._last=time.monotonic();repo._error=""
    sub_id,_=await main.create_sub_group(name="exact-two")
    uid,link=await main.make_link(label="shared",limit_bytes=2048,sub_id=sub_id)
    value=await main.validate_multi_location({"enabled":True,"remark_text":"Choice","locations":[
      {"id":"loc-de","code":"de","proxy_id":"de1"},
      {"id":"loc-al","code":"Albania","proxy_id":"al1"},
    ]})
    assert value["selection_mode"]=="explicit" and value["failover"] is False
    assert len(value["locations"])==2 and all("proxy_ids" not in x for x in value["locations"])
    async with main.SUBS_LOCK: main.SUBS[sub_id]["multi_location"]=value
    await main.save_state(strict=True)
    entries=main.vless_entries_for_link(main.LINKS[uid],uid,"h.example")
    assert len(entries)==2 and all(uid in x["vless_link"] for x in entries)
    assert all(x["shared_quota"] for x in entries)
    assert "loc%3Dloc-de" in entries[0]["vless_link"] and "loc%3Dloc-al" in entries[1]["vless_link"]
    assert await main.resolve_exit_endpoints(main.LINKS[uid],"loc-de")==[recs[0].endpoint]
    assert await main.resolve_exit_endpoints(main.LINKS[uid],"loc-al")==[recs[1].endpoint]
    # Repository percentages are opposite the selection and have zero effect.
    assert (await main.resolve_exit_selection(main.LINKS[uid],"loc-de"))["proxy_id"]=="de1"
    for bad_loc in ("", "loc-lv", "missing"):
      try: await main.resolve_exit_endpoints(main.LINKS[uid],bad_loc);raise AssertionError("invalid/missing loc must fail")
      except outbound.ProxyUnavailableError: pass
    # Removing Albania never selects Latvia or Germany.
    repo._records.pop("al1")
    try: await main.resolve_exit_endpoints(main.LINKS[uid],"loc-al");raise AssertionError("dead AL must fail")
    except outbound.ProxyUnavailableError: pass
    repo._records["al1"]=recs[1]
    # Exactly two, distinct countries, one exact existing same-country ID.
    bad=[
      {"enabled":True,"locations":[]},
      {"enabled":True,"locations":[{"code":"DE","proxy_id":"de1"}]},
      {"enabled":True,"locations":[{"code":"DE","proxy_id":"de1"},{"code":"DE","proxy_id":"de1"}]},
      {"enabled":True,"locations":[{"code":"DE","proxy_id":"al1"},{"code":"AL","proxy_id":"al1"}]},
      {"enabled":True,"locations":[{"code":"DE","proxy_id":"ghost"},{"code":"AL","proxy_id":"al1"}]},
    ]
    for payload in bad:
      try: await main.validate_multi_location(payload);raise AssertionError(payload)
      except ValueError: pass
    main.LINKS.clear();main.SUBS.clear();await main.load_state()
    assert uid in main.LINKS and main.LINKS[uid]["limit_bytes"]==2048
    restored=main.SUBS[sub_id]["multi_location"]
    assert len(restored["locations"])==2 and restored["locations"][1]["proxy_id"]=="al1"
    assert await main.resolve_exit_endpoints(main.LINKS[uid],"loc-al")==[recs[1].endpoint]
    print("multi-location exact-two=OK country-to-ID=OK no-failover=OK no-percentage=OK shared-UUID-quota=OK persistence=OK")
asyncio.run(run())
