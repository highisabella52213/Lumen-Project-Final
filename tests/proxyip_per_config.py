#!/usr/bin/env python3
"""v13: ProxyIP isolation, fail-open safety, stable routing, split TLS prefetch."""
import asyncio, sys, types, logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Minimal import surface for relay_vless's pure header collector.
fa=types.ModuleType("fastapi")
class WebSocket: pass
class WebSocketDisconnect(Exception): pass
fa.WebSocket=WebSocket; fa.WebSocketDisconnect=WebSocketDisconnect; sys.modules["fastapi"]=fa
ms=types.ModuleType("main")
ms.LINKS={}; ms.LINKS_LOCK=asyncio.Lock(); ms.stats={}; ms.hourly_traffic={}; ms.connections={}; ms.error_logs=[]; ms.logger=logging.getLogger("test")
async def noop(*a,**k): return True
for n in ("is_link_allowed","is_ip_allowed","save_state","log_activity"): setattr(ms,n,noop)
ms.now_ir=lambda: None; sys.modules["main"]=ms
import outbound
import relay_vless

APP="127.0.0.1"; RELAY="127.0.0.2"; failures=[]
TLS_BODY=b"client-hello-test"
TLS=b"\x16\x03\x01"+len(TLS_BODY).to_bytes(2,"big")+TLS_BODY

def ok(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ")+name+("  "+detail if detail and not cond else ""))
    if not cond: failures.append(name)

async def destination(seen):
    async def handle(r,w):
        seen.append(w.get_extra_info("peername")[0]); seen.append(await r.read(len(TLS)))
        w.write(b"SERVER-OK"); await w.drain(); w.close()
    srv=await asyncio.start_server(handle,APP,0); return srv,srv.sockets[0].getsockname()[1]

async def relay(dest_port):
    async def handle(cr,cw):
        try: rr,rw=await asyncio.open_connection(APP,dest_port,local_addr=(RELAY,0))
        except Exception: cw.close(); return
        async def pipe(r,w):
            try:
                while data:=await r.read(65536): w.write(data); await w.drain()
            except Exception: pass
            try: w.close()
            except Exception: pass
        await asyncio.gather(pipe(cr,rw),pipe(rr,cw))
    srv=await asyncio.start_server(handle,APP,0); return srv,srv.sockets[0].getsockname()[1]

async def use(dest_port,link,seen,uuid="u"):
    r,w,written=await outbound.open_outbound(APP,dest_port,TLS,link=link,uuid=uuid)
    if not written: w.write(TLS); await w.drain()
    got=await asyncio.wait_for(r.read(32),2); w.close(); await w.wait_closed()
    await asyncio.sleep(.05); return got,written

class FakeIO:
    def __init__(self,chunks): self.chunks=list(chunks); self.calls=0
    async def receive(self):
        self.calls+=1
        if not self.chunks: await asyncio.sleep(10)
        return {"type":"websocket.receive","bytes":self.chunks.pop(0)}

async def main():
    outbound.FIRST_BYTE_TIMEOUT=.6; outbound.PROXY_TOTAL_TIMEOUT=1.2
    outbound.configure(mode="proxyip",proxyip="127.0.0.1:1",fallback=False)
    e=outbound._effective({"uuid":"B"})
    ok("global ProxyIP cannot affect config B",e["mode"]=="direct")
    e=outbound._effective({"uuid":"A","proxyip":"127.0.0.1:9","proxyip_enabled":True,"proxyip_concurrency":99})
    ok("config A is isolated ProxyIP",e["mode"]=="proxyip" and e["fallback"] is True and e["concurrency"]==6)
    ok("legacy per-link ProxyIP migrates",outbound.link_uses_proxyip({"proxyip":"127.0.0.1:9"}))
    ok("explicit disabled stays direct",outbound._effective({"proxyip":"127.0.0.1:9","proxyip_enabled":False})["mode"]=="direct")

    seen=[]; ds,dp=await destination(seen); rs,rp=await relay(dp)
    try:
        for cycle in range(3):
            seen.clear(); got,written=await use(dp,{"proxyip":f"{APP}:{rp}","proxyip_enabled":True,"proxyip_concurrency":2},seen,"A")
            ok(f"cycle {cycle+1}: A uses relay exit",got==b"SERVER-OK" and written and seen[0]==RELAY,str(seen))
            seen.clear(); got,written=await use(dp,{"proxyip":"","proxyip_enabled":False},seen,"B")
            ok(f"cycle {cycle+1}: B remains direct",got==b"SERVER-OK" and not written and seen[0]==APP,str(seen))
        seen.clear(); got,written=await use(dp,{"proxyip":f"{APP}:1","proxyip_enabled":True},seen,"A")
        ok("bad A ProxyIP automatically falls back direct",got==b"SERVER-OK" and not written and seen[0]==APP,str(seen))
        seen.clear(); r,w,written=await outbound.open_outbound(APP,dp,b"plain",link={"proxyip":f"{APP}:{rp}","proxyip_enabled":True},uuid="A")
        if not written: w.write(b"plain"); await w.drain()
        await r.read(32); w.close(); await w.wait_closed(); await asyncio.sleep(.05)
        ok("non-TLS bypasses ProxyIP",not written and seen[0]==APP,str(seen))
    finally: ds.close();rs.close();await ds.wait_closed();await rs.wait_closed()

    pool=[("127.0.0.1",443),("127.0.0.2",443),("127.0.0.3",443)]
    a=outbound._seeded_shuffle(pool,"example.com|uuid-a")
    ok("candidate order stable per UUID/target",a==outbound._seeded_shuffle(pool,"example.com|uuid-a"))

    # VLESS header followed by a split TLS record: prefetch exactly once.
    header=b"\x01"+bytes(16)+b"\x00\x01"+(443).to_bytes(2,"big")+b"\x01\x7f\x00\x00\x01"
    io=FakeIO([TLS[2:]])
    parsed=await relay_vless._collect_header(io,header+TLS[:2],prefetch_payload=True)
    ok("split TLS ClientHello prefetched",parsed[3]==TLS and io.calls==1,repr(parsed[3]))
    io=FakeIO([TLS])
    parsed=await relay_vless._collect_header(io,header,prefetch_payload=False)
    ok("direct config never prefetches",parsed[3]==b"" and io.calls==0)

    dangling=[t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
    ok("no outbound candidate tasks leaked",not dangling,repr(dangling))
    print("\n"+("proxyip per config: ALL OK" if not failures else f"FAILURES: {failures}"))
    return bool(failures)

sys.exit(asyncio.run(main()))
