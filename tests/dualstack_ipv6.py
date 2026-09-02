#!/usr/bin/env python3
"""IPv6/IPv4 Happy-Eyeballs correctness and no-regression tests."""
import asyncio, collections, logging, socket, sys, types
fa=types.ModuleType('fastapi')
class WebSocket: pass
class WebSocketDisconnect(Exception): pass
fa.WebSocket=WebSocket; fa.WebSocketDisconnect=WebSocketDisconnect; sys.modules['fastapi']=fa
m=types.ModuleType('main'); m.LINKS={}; m.LINKS_LOCK=asyncio.Lock(); m.stats=collections.defaultdict(int)
m.hourly_traffic=collections.defaultdict(int); m.connections={}; m.error_logs=[]; m.logger=logging.getLogger('dual')
m.is_link_allowed=lambda x:True; m.is_ip_allowed=lambda *a:True
async def save(): pass
m.save_state=save; m.log_activity=lambda *a,**k:None
import datetime; m.now_ir=datetime.datetime.now; sys.modules['main']=m
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import relay_vless as R
async def echo_server(host,family):
    async def echo(r,w):
        try:
            d=await r.readexactly(4); w.write(d); await w.drain()
        except Exception: pass
        w.close()
    s=await asyncio.start_server(echo,host,0,family=family)
    return s,s.sockets[0].getsockname()[1]
async def check_echo(host,port):
    r,w=await R._open_upstream(host,port); w.write(b'test'); await w.drain(); assert await r.readexactly(4)==b'test'; w.close(); await w.wait_closed()
async def main():
    # Family ordering alternates rather than exhausting IPv6 or IPv4 first.
    v6a=(socket.AF_INET6,('2001:db8::1',443,0,0)); v6b=(socket.AF_INET6,('2001:db8::2',443,0,0))
    v4a=(socket.AF_INET,('192.0.2.1',443)); v4b=(socket.AF_INET,('192.0.2.2',443))
    ordered=R._interleave_families([v6a,v6b,v4a,v4b],None)
    assert [x[0] for x in ordered]==[socket.AF_INET6,socket.AF_INET,socket.AF_INET6,socket.AF_INET]

    # Real native IPv6 and IPv4 loopback paths.
    if socket.has_ipv6:
        s6,p6=await echo_server('::1',socket.AF_INET6)
        try: await check_echo('::1',p6)
        finally: s6.close(); await s6.wait_closed()
        print('native IPv6 ::1: OK')
    s4,p4=await echo_server('127.0.0.1',socket.AF_INET)
    try:
        await check_echo('127.0.0.1',p4)
        # Broken/slow IPv6 must not delay the first IPv4 attempt.
        old_resolve,old_connect=R._resolve,R._connect_candidate
        async def resolve(_h,_p): return [(socket.AF_INET6,('2001:db8::dead',p4,0,0)),(socket.AF_INET,('127.0.0.1',p4))]
        async def connect(delay,family,sockaddr):
            if family==socket.AF_INET6:
                await asyncio.sleep(.20); raise OSError('synthetic v6 blackhole')
            return await old_connect(delay,family,sockaddr)
        R._resolve,R._connect_candidate=resolve,connect
        start=asyncio.get_running_loop().time(); await check_echo('dual-fallback.test',p4); elapsed=asyncio.get_running_loop().time()-start
        assert elapsed<.10,elapsed
        print(f'broken IPv6 -> IPv4 fallback: {elapsed*1000:.1f}ms OK')
        R._resolve,R._connect_candidate=old_resolve,old_connect

        # If IPv6 is faster, it wins and is remembered.
        class Writer:
            def close(self): pass
        async def resolve2(_h,_p): return [v6a,v4a]
        async def connect2(delay,family,sockaddr):
            lag=.004 if family==socket.AF_INET6 else .040
            await asyncio.sleep(delay+lag); return object(),Writer(),lag*1000
        R._resolve,R._connect_candidate=resolve2,connect2
        await R._open_upstream('v6-wins.test',443)
        assert R._route_cache[('v6-wins.test',443)][1]==socket.AF_INET6
        print('faster IPv6 wins + route memory: OK')
        R._resolve,R._connect_candidate=old_resolve,old_connect
    finally:
        s4.close(); await s4.wait_closed()
asyncio.run(main())
