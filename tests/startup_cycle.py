#!/usr/bin/env python3
"""Reproduce `python main.py` startup with dependency stubs and catch import cycles."""
import asyncio, json, pathlib, sys, types
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class App:
    def __init__(self,*a,**k): self.routes=[]
    def _decorator(self,*a,**k): return lambda fn: fn
    on_event=get=post=patch=delete=api_route=_decorator
    def add_middleware(self,*a,**k): pass
    def add_api_websocket_route(self,*a,**k): pass
    def include_router(self,*a,**k): pass
class HTTPException(Exception):
    def __init__(self,status_code=500,detail=''): self.status_code=status_code; self.detail=detail
class Dummy: pass
class WebSocketDisconnect(Exception): pass
fa=types.ModuleType('fastapi'); fa.FastAPI=App; fa.Request=Dummy; fa.HTTPException=HTTPException
fa.WebSocket=Dummy; fa.WebSocketDisconnect=WebSocketDisconnect; fa.Depends=lambda x:x
responses=types.ModuleType('fastapi.responses')
for n in ['Response','HTMLResponse','JSONResponse','RedirectResponse','StreamingResponse']:
    setattr(responses,n,type(n,(),{'__init__':lambda self,*a,**k:None}))
cors=types.ModuleType('fastapi.middleware.cors'); cors.CORSMiddleware=Dummy
sys.modules.update({'fastapi':fa,'fastapi.responses':responses,'fastapi.middleware':types.ModuleType('fastapi.middleware'),'fastapi.middleware.cors':cors})
sys.modules['aiofiles']=types.ModuleType('aiofiles')
httpx=types.ModuleType('httpx'); httpx.AsyncClient=Dummy; httpx.Limits=Dummy; httpx.Timeout=Dummy; sys.modules['httpx']=httpx

uvicorn=types.ModuleType('uvicorn')
class Config:
    def __init__(self,*a,**k): self.args=a; self.kwargs=k
class Server:
    ran=False
    def __init__(self,c): self.config=c
    def run(self,*a,**k): Server.ran=True
uvicorn.Config=Config; uvicorn.Server=Server; sys.modules['uvicorn']=uvicorn
t=types.ModuleType('telegram_bot')
async def noop(*a,**k): pass
t.start_bot=noop; t.stop_bot=noop; sys.modules['telegram_bot']=t
p=types.ModuleType('pages'); p.LOGIN_HTML=''; p.DASHBOARD_HTML=''; p.LANDING_HTML=''; sys.modules['pages']=p

# Execute exactly as `python main.py`: module name is __main__, while relay imports `main`.
old_main=sys.modules.get('__main__'); module=types.ModuleType('__main__')
module.__file__=str(ROOT/'main.py'); module.__package__=None
for name in ['main','relay_vless','speed_limit']:
    sys.modules.pop(name,None)
sys.modules['__main__']=module
try:
    code=compile((ROOT/'main.py').read_text(encoding='utf-8'),str(ROOT/'main.py'),'exec')
    exec(code,module.__dict__)
    assert sys.modules.get('main') is module
    assert module.RELAY_BUF > 0
    assert Server.ran
    assert module.PROTOCOLS == ('vless-ws',)

    # Address is the network dial target; Host/SNI remain the TLS routing name.
    from urllib.parse import urlsplit, parse_qs, unquote
    uid = "11111111-2222-3333-4444-555555555555"
    ip_link = module.generate_vless_link(uid, "app.example.com", address="104.16.1.1")
    ip_url = urlsplit(ip_link)
    ip_qs = parse_qs(ip_url.query)
    assert ip_url.hostname == "104.16.1.1"
    assert ip_qs["host"] == ["app.example.com"] and ip_qs["sni"] == ["app.example.com"]

    custom_link = module.generate_vless_link(uid, "app.example.com", address="104.16.1.1", sni="front.example.org")
    custom_qs = parse_qs(urlsplit(custom_link).query)
    assert custom_qs["host"] == ["front.example.org"] and custom_qs["sni"] == ["front.example.org"]

    ipv6_link = module.generate_vless_link(uid, "app.example.com", address="2606:4700::1")
    assert "@[2606:4700::1]:443?" in ipv6_link
    ipv6_qs = parse_qs(urlsplit(ipv6_link).query)
    assert ipv6_qs["sni"] == ["app.example.com"]

    domain_link = module.generate_vless_link(uid, "app.example.com", address="edge.example.net")
    domain_qs = parse_qs(urlsplit(domain_link).query)
    assert domain_qs["host"] == ["edge.example.net"] and domain_qs["sni"] == ["edge.example.net"]

    remark_link = module.vless_link_for_link({"label":"Internal label","remark":"Visible client remark","protocol":"vless-ws"}, uid, "app.example.com")
    assert unquote(urlsplit(remark_link).fragment) == "Visible client remark"
    print(f"python-main startup: alias=True RELAY_BUF={module.RELAY_BUF} protocols=ws-only endpoints=domain+ipv4+ipv6 remark=exact server.run=True OK")
finally:
    if old_main is not None: sys.modules['__main__']=old_main
