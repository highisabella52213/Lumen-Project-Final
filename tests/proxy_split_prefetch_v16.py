#!/usr/bin/env python3
"""Execute the actual relay parser/collector in isolation and verify split TLS handling."""
import ast,asyncio,base64,socket,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];tree=ast.parse((ROOT/'relay_vless.py').read_text())
selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in ('_parse_vless_header','_collect_header')]
class WebSocketDisconnect(Exception):pass
ns={'asyncio':asyncio,'base64':base64,'socket':socket,'time':time,'HEADER_MAX':16384,'HEADER_TIMEOUT':2.0,'WebSocketDisconnect':WebSocketDisconnect,'_WSIO':object}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(ROOT/'relay_vless.py'),'exec'),ns)
TLS_BODY=b'split-client-hello';TLS=b'\x16\x03\x01'+len(TLS_BODY).to_bytes(2,'big')+TLS_BODY
HEADER=b'\x01'+bytes(16)+b'\x00\x01'+(443).to_bytes(2,'big')+b'\x01\x7f\x00\x00\x01'
class IO:
 def __init__(self,chunks):self.chunks=list(chunks);self.calls=0
 async def receive(self):self.calls+=1;return {'type':'websocket.receive','bytes':self.chunks.pop(0)}
async def main():
 io=IO([TLS[2:]]);parsed=await ns['_collect_header'](io,HEADER+TLS[:2],prefetch_payload=True);assert parsed[3]==TLS and parsed[4]==len(HEADER)+len(TLS) and io.calls==1
 io=IO([TLS]);parsed=await ns['_collect_header'](io,HEADER,prefetch_payload=False);assert parsed[3]==b'' and parsed[4]==len(HEADER) and io.calls==0
 print('proxy split prefetch: complete-TLS=OK direct-no-wait=OK accounting-once=OK')
asyncio.run(main())
