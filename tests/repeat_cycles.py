#!/usr/bin/env python3
"""Repeated connection cycles with FD/task/error leak checks."""
import asyncio, os, sys
from pathlib import Path
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
saved=sys.argv[:]; sys.argv=[sys.argv[0],str(ROOT)]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ws_hyper_stress as H
sys.argv=saved
CYCLES=8; CLIENTS=24; SIZE=1024*1024
async def main():
    target,tp=await H.echo_server(); gateway,gp=await H.gateway_server()
    fd0=len(os.listdir('/proc/self/fd')) if os.path.isdir('/proc/self/fd') else 0
    try:
        for cycle in range(CYCLES):
            got=await asyncio.wait_for(asyncio.gather(*(H.client_case(gp,tp,SIZE,(i%250)+1) for i in range(CLIENTS))),60)
            assert sum(got)>=CYCLES*0+CLIENTS*SIZE
            await asyncio.sleep(.02)
            assert not H.main_stub.connections,H.main_stub.connections
            assert not H.main_stub.error_logs,H.main_stub.error_logs
        await asyncio.sleep(.1)
        fd1=len(os.listdir('/proc/self/fd')) if fd0 else 0
        # Listening sockets remain open; completed client/upstream FDs must not grow.
        assert not fd0 or fd1<=fd0+3,(fd0,fd1)
        live=[t for t in asyncio.all_tasks() if t is not asyncio.current_task() and not t.done()]
        assert len(live)<=2,[t.get_name() for t in live]
        print(f'repeat: {CYCLES}x{CLIENTS} connections, active=0 errors=0 fd={fd0}->{fd1} tasks={len(live)} OK')
    finally:
        gateway.close(); target.close(); await gateway.wait_closed(); await target.wait_closed()
asyncio.run(main())
