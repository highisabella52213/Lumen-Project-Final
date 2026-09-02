#!/usr/bin/env python3
"""Contract test for zero-copy Turbo WS protocol without installing Uvicorn."""
import asyncio, importlib.util, pathlib, sys, types
class ClientDisconnected(Exception): pass
class Base: pass
utils=types.ModuleType('uvicorn.protocols.utils'); utils.ClientDisconnected=ClientDisconnected
impl=types.ModuleType('uvicorn.protocols.websockets.websockets_sansio_impl'); impl.WebSocketsSansIOProtocol=Base
for name in ['uvicorn','uvicorn.protocols','uvicorn.protocols.websockets']:
    sys.modules[name]=types.ModuleType(name)
sys.modules['uvicorn.protocols.utils']=utils
sys.modules['uvicorn.protocols.websockets.websockets_sansio_impl']=impl
path=pathlib.Path(__file__).resolve().parents[1]/'turbo_ws_protocol.py'
spec=importlib.util.spec_from_file_location('turbo_contract',path)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
class Transport:
    def __init__(self): self.writes=[]; self.pauses=0; self.resumes=0; self.closing=False
    def write(self,data): self.writes.append(data)
    def pause_reading(self): self.pauses+=1
    def resume_reading(self): self.resumes+=1
    def is_closing(self): return self.closing
async def main():
    p=object.__new__(mod.TurboWebSocketsSansIOProtocol)
    p.frames=[]; p.close_sent=False; p.curr_msg_data_type='bytes'; p.queue=asyncio.Queue()
    p.read_paused=False; p.transport=Transport(); p.logger=types.SimpleNamespace(exception=lambda *a,**k:None)
    marker=b'unique'; p.frames=[marker]; p.send_receive_event_to_app()
    event=await p.receive(); assert event['bytes'] is marker
    for i in range(mod.RX_QUEUE_HIGH):
        p.frames=[bytes((i&255,))]; p.send_receive_event_to_app()
    assert p.transport.pauses==1 and p.read_paused
    while p.queue.qsize()>mod.RX_QUEUE_LOW: await p.receive()
    assert p.transport.resumes==1 and not p.read_paused
    while not p.queue.empty(): await p.receive()
    assert p._turbo_queue_bytes==0
    p.frames=[b'burst']; p.send_receive_event_to_app()
    queued=p._turbo_queue_bytes
    burst=p.turbo_receive_nowait()
    assert burst['bytes']==b'burst' and p._turbo_queue_bytes==queued-5
    assert p.turbo_receive_nowait() is None
    p.writable=asyncio.Event(); p.writable.set(); p.disconnected=False; p.close_sent=False
    p.handshake_complete=True; p.config=types.SimpleNamespace(ws_per_message_deflate=False); p.transport=Transport()
    payload=bytearray(b'x'*70000); await p.turbo_send_bytes(payload)
    assert len(p.transport.writes)==2
    assert p.transport.writes[0]==mod._binary_header(len(payload))
    assert p.transport.writes[1] is payload
    print(f'protocol: queue={mod.RX_QUEUE_HIGH}/{mod.RX_QUEUE_LOW} burst-nowait=True direct-payload=True OK')
asyncio.run(main())
