#!/usr/bin/env python3
"""HTTP/HTTPS-list/SOCKS5 compatibility plus blackhole fail-open coverage."""
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
 outbound.FIRST_BYTE_TIMEOUT=.3;outbound.HANDSHAKE_TIMEOUT=.5;outbound.PROXY_TOTAL_TIMEOUT=1.2
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
 async def use(record,target=APP):
  repo._records={record.id:record};repo._last=time.monotonic();r,w,written=await outbound.open_outbound(target,dp,TLS,link={'exit_proxy_mode':'repository','proxy_id':record.id});data=await asyncio.wait_for(r.read(len(BANNER)),1);w.close();return written,data
 rec=repo.Record('http','http://'+APP+':'+str(hp),'http','FI','FI','🇫🇮',90);written,data=await use(rec);assert written and data==BANNER and seen[-1]==TLS
 rec=repo.Record('https-label','https://'+APP+':'+str(hp),'https','DE','DE','🇩🇪',80);written,data=await use(rec);assert written and data==BANNER and len(http_connects)>=2
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
 rec=repo.Record('socks',f'socks5://{APP}:{sp}','socks5','NL','NL','🇳🇱',85);written,data=await use(rec,'localhost');assert written and data==BANNER and atyp[0]==3 and any(x in (1,4) for x in atyp[1:])
 # CONNECT success followed by silence must fall back direct instead of ping=-1.
 black_seen=[]
 async def blackhole(r,w):
  try:await r.readuntil(b'\r\n\r\n');w.write(b'HTTP/1.1 200 OK\r\n\r\n');await w.drain();black_seen.append(await r.read(len(TLS)));await asyncio.sleep(3)
  except Exception:pass
  w.close()
 bs=await asyncio.start_server(blackhole,APP,0);bp=bs.sockets[0].getsockname()[1];rec=repo.Record('black','http://'+APP+':'+str(bp),'http','US','US','🇺🇸',20);repo._records={rec.id:rec};repo._last=time.monotonic();start=time.monotonic();r,w,written=await outbound.open_outbound(APP,dp,TLS,link={'exit_proxy_mode':'repository','proxy_id':rec.id});assert not written and time.monotonic()-start<1.1;w.write(TLS);await w.drain();assert await asyncio.wait_for(r.read(len(BANNER)),1)==BANNER;w.close();assert black_seen and black_seen[0]==TLS
 # Non-TLS never enters an unverifiable proxy tunnel.
 r,w,written=await outbound.open_outbound(APP,dp,b'plain',link={'exit_proxy_mode':'repository','proxy_id':rec.id});assert not written;w.write(TLS);await w.drain();assert await r.read(len(BANNER))==BANNER;w.close()
 for srv in (dest,hs,ss,bs):srv.close();await srv.wait_closed()
 await asyncio.sleep(.05)
 print('proxy reliability: HTTP=OK HTTPS-list=OK SOCKS-DNS-retry=OK blackhole-direct=OK nonTLS-direct=OK')
asyncio.run(main())
