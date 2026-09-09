#!/usr/bin/env python3
"""HTTP/HTTPS-list/SOCKS5 compatibility and deterministic fail-closed routing."""
import asyncio,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import outbound,proxy_repository as repo
TLS_BODY=b'client-hello-for-proxy-test';TLS=b'\x16\x03\x01'+len(TLS_BODY).to_bytes(2,'big')+TLS_BODY
BANNER=b'SERVER-HELLO';APP='127.0.0.1'

async def pipe(r,w):
 try:
  while data:=await r.read(65536):w.write(data);await w.drain()
 except Exception:pass
 try:w.close()
 except Exception:pass

async def main():
 outbound.HANDSHAKE_TIMEOUT=.5
 seen=[]
 async def destination(r,w):
  seen.append(await r.read(len(TLS)));w.write(BANNER);await w.drain();w.close()
 dest=await asyncio.start_server(destination,APP,0);dp=dest.sockets[0].getsockname()[1]
 http_connects=[]
 async def http_proxy(r,w):
  try:
   header=await r.readuntil(b'\r\n\r\n');http_connects.append(header.split(b'\r\n',1)[0]);ur,uw=await asyncio.open_connection(APP,dp);w.write(b'HTTP/1.1 200 Connection established\r\n\r\n');await w.drain();await asyncio.gather(pipe(r,uw),pipe(ur,w))
  except Exception:w.close()
 hs=await asyncio.start_server(http_proxy,APP,0);hp=hs.sockets[0].getsockname()[1]
 async def use(record,target=APP,packet=TLS):
  repo._records={record.id:record};repo._last=time.monotonic();r,w,written=await outbound.open_outbound(target,dp,packet,link={'exit_proxy_mode':'repository','proxy_id':record.id});data=await asyncio.wait_for(r.read(len(BANNER)),1);w.close();return written,data
 rec=repo.Record('http','http://'+APP+':'+str(hp),'http','Finland','FI','🇫🇮',90);written,data=await use(rec);assert written and data==BANNER and seen[-1]==TLS
 rec=repo.Record('https-label','https://'+APP+':'+str(hp),'https','Germany','DE','🇩🇪',80);written,data=await use(rec);assert written and data==BANNER and len(http_connects)>=2
 # Non-TLS payloads also use the tunnel: traffic type never decides the route.
 plain=b'GET / HTTP/1.1\r\n\r\n'
 async def plain_dest(r,w):
  seen.append(await r.read(len(plain)));w.write(BANNER);await w.drain();w.close()
 d2=await asyncio.start_server(plain_dest,APP,0);dp2=d2.sockets[0].getsockname()[1]
 repo._records={rec.id:rec};repo._last=time.monotonic()
 r,w,written=await outbound.open_outbound(APP,dp2,plain,link={'exit_proxy_mode':'repository','proxy_id':rec.id});assert written
 assert await asyncio.wait_for(r.read(len(BANNER)),1)==BANNER and seen[-1]==plain;w.close()
 # SOCKS proxy rejects domain ATYP once, then accepts the locally resolved IP retry.
 atyp=[]
 async def socks(r,w):
  try:
   head=await r.readexactly(2);await r.readexactly(head[1]);w.write(b'\x05\x00');await w.drain();req=await r.readexactly(4);kind=req[3];atyp.append(kind)
   if kind==1:await r.readexactly(6)
   elif kind==4:await r.readexactly(18)
   else:n=(await r.readexactly(1))[0];await r.readexactly(n+2)
   if kind==3:w.write(b'\x05\x08\x00\x01'+bytes(6));await w.drain();w.close();return
   ur,uw=await asyncio.open_connection(APP,dp);w.write(b'\x05\x00\x00\x01'+bytes(6));await w.drain();await asyncio.gather(pipe(r,uw),pipe(ur,w))
  except Exception:w.close()
 ss=await asyncio.start_server(socks,APP,0);sp=ss.sockets[0].getsockname()[1]
 rec=repo.Record('socks',f'socks5://{APP}:{sp}','socks5','Netherlands','NL','🇳🇱',85)
 try: await use(rec,'localhost');raise AssertionError('domain rejection must fail closed without local DNS')
 except OSError: pass
 assert atyp==[3],atyp
 # Fail-closed: a blackhole proxy (CONNECT ok, then silence) must NOT fall back
 # to a direct connection; the destination must see nothing.
 black_seen=[]
 async def blackhole(r,w):
  try:await r.readuntil(b'\r\n\r\n');w.write(b'HTTP/1.1 200 OK\r\n\r\n');await w.drain();black_seen.append(await r.read(len(TLS)));await asyncio.sleep(3)
  except Exception:pass
  w.close()
 bs=await asyncio.start_server(blackhole,APP,0);bp=bs.sockets[0].getsockname()[1];rec=repo.Record('black','http://'+APP+':'+str(bp),'http','United States','US','🇺🇸',20);repo._records={rec.id:rec};repo._last=time.monotonic()
 dest_seen_before=len(seen)
 r,w,written=await outbound.open_outbound(APP,dp,TLS,link={'exit_proxy_mode':'repository','proxy_id':rec.id})
 for _ in range(20):
  if black_seen:break
  await asyncio.sleep(.05)
 assert written and black_seen and black_seen[0]==TLS
 try:await asyncio.wait_for(r.read(1),.4);raise AssertionError('blackhole delivered data')
 except asyncio.TimeoutError:pass
 w.close();await asyncio.sleep(.05);assert len(seen)==dest_seen_before,'destination must not be contacted directly'
 # Fail-closed: a dead proxy raises; no direct fallback connection happens.
 repo._records={'dead':repo.Record('dead','http://127.0.0.1:1','http','France','FR','🇫🇷',10)};repo._last=time.monotonic()
 try:
  await outbound.open_outbound(APP,dp,TLS,link={'exit_proxy_mode':'repository','proxy_id':'dead'});raise AssertionError('dead proxy must raise')
 except OSError:pass
 assert len(seen)==dest_seen_before,'dead proxy must never fall back to direct'
 # A repository id missing from the cache must also fail closed.
 try:
  await outbound.open_outbound(APP,dp,TLS,link={'exit_proxy_mode':'repository','proxy_id':'ghost'});raise AssertionError('ghost proxy must raise')
 except outbound.ProxyUnavailableError:pass
 # Multiple endpoints are forbidden; explicit routing never fails over.
 try: await outbound.open_outbound(APP,dp,TLS,endpoints=['http://127.0.0.1:1','http://'+APP+':'+str(hp)]);raise AssertionError('multiple endpoints must be rejected')
 except outbound.ProxyUnavailableError: pass
 for srv in (dest,d2,hs,ss,bs):srv.close();await srv.wait_closed()
 await asyncio.sleep(.05)
 print('proxy reliability: HTTP=OK HTTPS-list=OK nonTLS-proxied=OK SOCKS-remote-DNS=OK blackhole-failclosed=OK dead-proxy-raises=OK no-silent-direct=OK multi-endpoint-rejected=OK remote-DNS-only=OK')
asyncio.run(main())
