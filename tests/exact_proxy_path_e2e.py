#!/usr/bin/env python3
"""Real local data-plane: exact ID -> exact proxy -> distinct observed exit."""
import asyncio, ssl, subprocess, tempfile, time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import outbound, proxy_repository as repo

async def pipe(reader,writer):
    try:
        while data:=await reader.read(65536):
            writer.write(data);await writer.drain()
    except Exception: pass
    try: writer.close()
    except Exception: pass

async def run():
    with tempfile.TemporaryDirectory() as td:
        cert=Path(td)/'cert.pem';key=Path(td)/'key.pem'
        subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1','-subj','/CN=localhost','-keyout',str(key),'-out',str(cert)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        tls_ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls_ctx.load_cert_chain(cert,key)
        probe_hits=[];runtime_hits=[]
        async def tls_target(r,w):
            peer=w.get_extra_info('peername');line=await r.readline();probe_hits.append((peer[0],line));
            while await r.readline()!=b'\r\n': pass
            w.write(b'HTTP/1.1 204 No Content\r\nContent-Length: 0\r\nConnection: close\r\n\r\n');await w.drain();w.close()
        async def runtime_target(r,w):
            peer=w.get_extra_info('peername');data=await r.read(64);runtime_hits.append((peer[0],data));w.write(b'EXIT:'+peer[0].encode());await w.drain();w.close()
        tls_srv=await asyncio.start_server(tls_target,'127.0.0.1',0,ssl=tls_ctx);tls_port=tls_srv.sockets[0].getsockname()[1]
        run_srv=await asyncio.start_server(runtime_target,'127.0.0.1',0);run_port=run_srv.sockets[0].getsockname()[1]
        proxy_logs={};servers=[];records=[]
        for idx,source_ip in enumerate(('127.0.0.2','127.0.0.3','127.0.0.4'),1):
            pid=f'proxy-{idx}';proxy_logs[pid]=[]
            async def handler(r,w,pid=pid,source_ip=source_ip):
                try:
                    header=await r.readuntil(b'\r\n\r\n');first=header.split(b'\r\n',1)[0];proxy_logs[pid].append(first)
                    authority=first.split()[1].decode();host,port_text=authority.rsplit(':',1);requested_port=int(port_text)
                    target_port=tls_port if host in {'cloudflare.com','google.com'} else run_port
                    ur,uw=await asyncio.open_connection('127.0.0.1',target_port,local_addr=(source_ip,0))
                    w.write(b'HTTP/1.1 200 Connection established\r\n\r\n');await w.drain();await asyncio.gather(pipe(r,uw),pipe(ur,w))
                except Exception:
                    try:w.close()
                    except Exception:pass
            srv=await asyncio.start_server(handler,'127.0.0.1',0);servers.append(srv);port=srv.sockets[0].getsockname()[1]
            records.append(repo.Record(pid,f'http://127.0.0.1:{port}','http',['Germany','Albania','Latvia'][idx-1],['DE','AL','LV'][idx-1],['🇩🇪','🇦🇱','🇱🇻'][idx-1],[1,99,50][idx-1]))
        repo._records={r.id:r for r in records};repo._last=time.monotonic();repo._error=''
        original=ssl.create_default_context
        ssl.create_default_context=lambda *a,**k: ssl._create_unverified_context()
        try:
            for rec in records:
                result=await outbound.test_proxy_record(rec,timeout=3)
                assert result['proxy_id']==rec.id and result['ok'] and len(result['checks'])==2
                assert proxy_logs[rec.id]==[b'CONNECT cloudflare.com:443 HTTP/1.1',b'CONNECT google.com:443 HTTP/1.1']
        finally: ssl.create_default_context=original
        for rec,expected_ip in zip(records,('127.0.0.2','127.0.0.3','127.0.0.4')):
            before={k:len(v) for k,v in proxy_logs.items()}
            reader,writer,sent=await outbound.open_outbound('runtime.test',run_port,b'PING',endpoints=[rec.endpoint],proxy_id=rec.id)
            assert sent;reply=await reader.read(64);writer.close();await writer.wait_closed()
            assert reply==b'EXIT:'+expected_ip.encode();assert runtime_hits[-1]==(expected_ip,b'PING')
            assert len(proxy_logs[rec.id])==before[rec.id]+1
            assert all(len(proxy_logs[other.id])==before[other.id] for other in records if other.id!=rec.id)
        dead=repo.Record('dead','http://127.0.0.1:1','http','France','FR','🇫🇷',100)
        try: await outbound.open_outbound('runtime.test',run_port,b'PING',endpoints=[dead.endpoint],proxy_id=dead.id);raise AssertionError('dead proxy must fail')
        except OSError: pass
        for srv in [tls_srv,run_srv,*servers]:srv.close();await srv.wait_closed()
        print('exact proxy E2E: A->A/127.0.0.2 B->B/127.0.0.3 C->C/127.0.0.4 probes=Cloudflare+Google-through-exact-ID dead=fail-closed OK')
asyncio.run(run())
