#!/usr/bin/env python3
import asyncio,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import outbound,proxy_repository as repo

async def main():
 seen=[];connect_lines=[]
 async def destination(r,w):
  seen.append(await r.read(64));w.write(b'OK');await w.drain();w.close()
 dest=await asyncio.start_server(destination,'127.0.0.1',0);dp=dest.sockets[0].getsockname()[1]
 async def proxy(cr,cw):
  header=await cr.readuntil(b'\r\n\r\n');connect_lines.append(header.split(b'\r\n')[0]);rr,rw=await asyncio.open_connection('127.0.0.1',dp);cw.write(b'HTTP/1.1 200 OK\r\n\r\n');await cw.drain()
  async def pipe(r,w):
   try:
    while x:=await r.read(65536):w.write(x);await w.drain()
   except Exception:pass
   w.close()
  await asyncio.gather(pipe(cr,rw),pipe(rr,cw))
 ps=await asyncio.start_server(proxy,'127.0.0.1',0);pp=ps.sockets[0].getsockname()[1]
 rec=repo.Record('managed-test',f'http://127.0.0.1:{pp}','http','Finland','FI','🇫🇮',88);repo._records={rec.id:rec};repo._last=time.monotonic();repo._error=''
 r,w,written=await outbound.open_outbound('127.0.0.1',dp,b'HELLO',link={'exit_proxy_mode':'repository','proxy_id':rec.id});assert written and await r.read(2)==b'OK';w.close();await asyncio.sleep(.05)
 assert seen==[b'HELLO'] and connect_lines and b'CONNECT' in connect_lines[0]
 seen.clear();r,w,written=await outbound.open_outbound('127.0.0.1',dp,b'DIRECT',link={'exit_proxy_mode':'custom','custom_proxy':'http://127.0.0.1:1'});assert not written;w.write(b'DIRECT');await w.drain();assert await r.read(2)==b'OK';w.close()
 dest.close();ps.close();await dest.wait_closed();await ps.wait_closed();print('managed outbound: HTTP=OK payload-once=OK broken-custom-fallback=OK')
asyncio.run(main())
