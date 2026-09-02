#!/usr/bin/env python3
"""Direct XHTTP protocol correctness/stress harness without FastAPI dependency."""
from __future__ import annotations
import asyncio, collections, datetime, logging, os, sys, time, types
from pathlib import Path
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
MODE=sys.argv[2] if len(sys.argv)>2 else 'all'
CLIENTS=int(sys.argv[3]) if len(sys.argv)>3 else 8
MIB=float(sys.argv[4]) if len(sys.argv)>4 else 8.0
UID='11111111-2222-3333-4444-555555555555'
class HTTPException(Exception):
    def __init__(self,status_code=500,detail=''): super().__init__(detail); self.status_code=status_code; self.detail=detail
class WebSocketDisconnect(Exception): pass
class APIRouter:
    def get(self,*a,**k): return lambda f:f
    def post(self,*a,**k): return lambda f:f
class Request: pass
class WebSocket: pass
class Response:
    def __init__(self,content=b'',headers=None,media_type=None,status_code=200,**kwargs):
        self.body=content; self.headers=headers or {}; self.media_type=media_type; self.status_code=status_code
class StreamingResponse(Response):
    def __init__(self,content,headers=None,media_type=None,status_code=200,**kwargs):
        super().__init__(b'',headers,media_type,status_code,**kwargs); self.body_iterator=content; self.background=None
    async def stream_response(self,send):
        await send({'type':'http.response.start','status':self.status_code,'headers':[]})
        async for chunk in self.body_iterator:
            await send({'type':'http.response.body','body':chunk,'more_body':True})
        await send({'type':'http.response.body','body':b'','more_body':False})
fastapi=types.ModuleType('fastapi'); fastapi.APIRouter=APIRouter; fastapi.Request=Request; fastapi.HTTPException=HTTPException
fastapi.WebSocket=WebSocket; fastapi.WebSocketDisconnect=WebSocketDisconnect
responses=types.ModuleType('fastapi.responses'); responses.Response=Response; responses.StreamingResponse=StreamingResponse
sys.modules['fastapi']=fastapi; sys.modules['fastapi.responses']=responses
main=types.ModuleType('main'); main.LINKS={UID:{'label':'xhttp-test','used_bytes':0,'limit_bytes':0,'speed_limit_bytes':0,'active':True}}
main.LINKS_LOCK=asyncio.Lock(); main.stats=collections.defaultdict(int); main.hourly_traffic=collections.defaultdict(int)
main.connections={}; main.error_logs=[]; main.logger=logging.getLogger('xhttp-test')
main.is_link_allowed=lambda link:bool(link and link.get('active',True)); main.is_ip_allowed=lambda *a:True
async def save_state(): pass
main.save_state=save_state; main.log_activity=lambda *a,**k:None; main.now_ir=datetime.datetime.now
sys.modules['main']=main; sys.path.insert(0,str(ROOT))
import xhttp_siz10 as X
class FakeRequest:
    def __init__(self,body=b'',chunks=None):
        self._body=body; self._chunks=list(chunks if chunks is not None else ([body] if body else []))
        self.headers={}; self.query_params={}; self.client=types.SimpleNamespace(host='127.0.0.1')
    async def body(self): return self._body
    async def stream(self):
        for chunk in self._chunks:
            await asyncio.sleep(0)
            yield chunk

def vless_header(port,payload=b''):
    return b'\0'+bytes(16)+b'\0\1'+port.to_bytes(2,'big')+b'\1\x7f\0\0\1'+payload
async def echo_server():
    async def echo(r,w):
        try:
            while data:=await r.read(2*1024*1024):
                w.write(data)
                if w.transport.get_write_buffer_size()>=8*1024*1024: await w.drain()
            await w.drain()
        except (ConnectionError,asyncio.CancelledError): pass
        finally:
            w.close()
            try: await w.wait_closed()
            except Exception: pass
    s=await asyncio.start_server(echo,'127.0.0.1',0,limit=32*1024*1024)
    return s,s.sockets[0].getsockname()[1]
async def collect(iterator,expected):
    out=bytearray()
    try:
        async for chunk in iterator:
            if chunk: out.extend(chunk)
            if len(out)>=expected: break
    finally:
        close=getattr(iterator,'aclose',None)
        if close:
            try: await close()
            except Exception: pass
    return bytes(out)
async def drain_response(resp):
    if not hasattr(resp,'body_iterator'): return
    try:
        async for _ in resp.body_iterator: pass
    except Exception: pass
async def packet_case(port,size,token):
    sid=f'p-{token}-{time.time_ns()}'
    down=await X.xhttp_downlink('packet-up',UID,sid,FakeRequest())
    prefix=b'seed-'+bytes((token,)); expected=2+len(prefix)+size
    read_task=asyncio.create_task(collect(down.body_iterator,expected))
    await X.xhttp_packet_up('packet-up',UID,sid,0,FakeRequest(vless_header(port,prefix)))
    chunk=bytes((token,))*min(4_000_000,max(1,size)); packets=[]; left=size; seq=1
    while left:
        data=chunk if left>=len(chunk) else chunk[:left]; packets.append((seq,data)); seq+=1; left-=len(data)
    for i in range(0,len(packets),8):
        batch=packets[i:i+8]
        # Exercise the required out-of-order packet buffer.
        await asyncio.gather(*(X.xhttp_packet_up('packet-up',UID,sid,s,FakeRequest(b)) for s,b in reversed(batch)))
    got=await asyncio.wait_for(read_task,30); assert got[:2]==b'\0\0' and got[2:2+len(prefix)]==prefix
    assert got[2+len(prefix):]==bytes((token,))*size
    await X._teardown(sid); return size
async def stream_case(mode,port,size,token,fragment=False):
    sid=f's-{token}-{time.time_ns()}'; prefix=b'seed-'+bytes((token,)); header=vless_header(port,prefix)
    bulk=bytes((token,))*size; chunks=[]
    if fragment: chunks.extend((header[:7],header[7:19],header[19:]))
    else: chunks.append(header)
    step=1024*1024; chunks.extend(bulk[i:i+step] for i in range(0,len(bulk),step))
    req=FakeRequest(chunks=chunks); expected=2+len(prefix)+size
    if mode=='stream-one':
        resp=await X.xhttp_stream_upload(mode,UID,sid,req)
        got=await asyncio.wait_for(collect(resp.body_iterator,expected),30)
    else:
        down=await X.xhttp_downlink(mode,UID,sid,FakeRequest())
        read_task=asyncio.create_task(collect(down.body_iterator,expected))
        upload_resp=await X.xhttp_stream_upload(mode,UID,sid,req)
        upload_drain=asyncio.create_task(drain_response(upload_resp))
        got=await asyncio.wait_for(read_task,30)
        await X._teardown(sid); await asyncio.gather(upload_drain,return_exceptions=True)
    assert got[:2]==b'\0\0' and got[2:2+len(prefix)]==prefix
    assert got[2+len(prefix):]==bulk
    await X._teardown(sid); return size
async def packet_fragmented_header_case(port,size=1024*1024,token=248):
    sid=f'pf-{time.time_ns()}'; prefix=b'packet-frag'; header=vless_header(port,prefix); bulk=bytes((token,))*size
    down=await X.xhttp_downlink('packet-up',UID,sid,FakeRequest())
    read=asyncio.create_task(collect(down.body_iterator,2+len(prefix)+size))
    await X.xhttp_packet_up('packet-up',UID,sid,0,FakeRequest(header[:10]))
    await X.xhttp_packet_up('packet-up',UID,sid,1,FakeRequest(header[10:]+bulk))
    # A retried POST is idempotent and must not duplicate bytes.
    await X.xhttp_packet_up('packet-up',UID,sid,1,FakeRequest(header[10:]+bulk))
    got=await asyncio.wait_for(read,30); assert got==b'\0\0'+prefix+bulk
    await X._teardown(sid)

async def duplex_response_contract():
    async def body(): yield b'ok'
    response=X._DuplexStreamingResponse(body())
    receive_calls=0; sent=[]
    async def receive():
        nonlocal receive_calls; receive_calls+=1
        raise AssertionError('duplex response must not consume ASGI receive')
    async def send(message): sent.append(message)
    await response({},receive,send)
    assert receive_calls==0 and sent[-1]['more_body'] is False

async def base_stream_one_case(port,size=1024*1024,token=251):
    prefix=b'base-one'; header=vless_header(port,prefix); bulk=bytes((token,))*size
    req=FakeRequest(chunks=[header[:5],header[5:18],header[18:],bulk])
    resp=await X.xhttp_stream_one_base('stream-one',UID,req)
    assert resp.headers['content-type']=='text/event-stream'
    got=await asyncio.wait_for(collect(resp.body_iterator,2+len(prefix)+size),30)
    assert got==b'\0\0'+prefix+bulk
    assert not X.xhttp_sessions and not main.connections
    print('xhttp contract: official stream-one base path + fragmented VLESS header OK')

async def run_mode(mode,port,fragment=False):
    size=int(MIB*1024*1024); start=time.perf_counter()
    fn=packet_case if mode=='packet-up' else lambda p,s,t:stream_case(mode,p,s,t,fragment)
    totals=await asyncio.gather(*(fn(port,size,(i%250)+1) for i in range(CLIENTS)))
    elapsed=time.perf_counter()-start; mib=sum(totals)/2**20
    assert not X.xhttp_sessions,X.xhttp_sessions; assert not main.connections,main.connections; assert not main.error_logs,main.error_logs
    print(f'xhttp {mode} {CLIENTS}x{MIB:g}MiB: {mib/elapsed:.1f} MiB/s each way elapsed={elapsed:.3f}s active=0 errors=0')
async def amain():
    server,port=await echo_server()
    try:
        if MODE=='contract':
            await stream_case('stream-up',port,1024*1024,249,fragment=True)
            await packet_fragmented_header_case(port)
            await base_stream_one_case(port)
            await duplex_response_contract()
            print('xhttp contract: packet reorder/idempotency + single ASGI receive consumer OK')
        elif MODE=='repeat':
            fd0=len(os.listdir('/proc/self/fd')) if os.path.isdir('/proc/self/fd') else 0
            for _ in range(6):
                for mode in ('packet-up','stream-up','stream-one'):
                    await run_mode(mode,port,fragment=True)
            await asyncio.sleep(.1)
            fd1=len(os.listdir('/proc/self/fd')) if fd0 else 0
            assert not fd0 or fd1<=fd0+2,(fd0,fd1)
            live=[t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done() and t.get_name()!='xhttp-reaper']
            assert len(live)<=1,[t.get_name() for t in live]
            print(f'xhttp repeat: cycles=6 active=0 errors=0 fd={fd0}->{fd1} tasks={len(live)} OK')
        else:
            modes=('packet-up','stream-up','stream-one') if MODE=='all' else (MODE,)
            for mode in modes: await run_mode(mode,port,fragment=False)
    finally:
        for sid in list(X.xhttp_sessions): await X._teardown(sid)
        server.close(); await server.wait_closed()
asyncio.run(amain())
