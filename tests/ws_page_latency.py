#!/usr/bin/env python3
"""Many short WS/VLESS transfers: page-load/first-response latency benchmark."""
import asyncio, statistics, sys, time
from pathlib import Path
ROOT=Path(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parents[1])
REQUESTS=int(sys.argv[2]) if len(sys.argv)>2 else 240
PAYLOAD_KIB=int(sys.argv[3]) if len(sys.argv)>3 else 16
# ws_hyper_stress reads argv on import; hide benchmark-specific numeric args.
saved=sys.argv[:]; sys.argv=[sys.argv[0],str(ROOT)]
sys.path.insert(0,str(Path(__file__).resolve().parent))
import ws_hyper_stress as H
sys.argv=saved
async def main():
    target,target_port=await H.echo_server(); gateway,gateway_port=await H.gateway_server()
    try:
        # Warm bytecode, DNS and route caches before the measured browser-like burst.
        await H.client_case(gateway_port,target_port,1024,1)
        async def one(i):
            t=time.perf_counter()
            await H.client_case(gateway_port,target_port,PAYLOAD_KIB*1024,(i%250)+1)
            return (time.perf_counter()-t)*1000
        start=time.perf_counter(); lat=await asyncio.gather(*(one(i) for i in range(REQUESTS))); elapsed=time.perf_counter()-start
        lat.sort(); q=lambda p:lat[min(len(lat)-1,int(len(lat)*p))]
        assert not H.main_stub.error_logs,H.main_stub.error_logs
        print(f'page {REQUESTS}x{PAYLOAD_KIB}KiB: {REQUESTS/elapsed:.1f} req/s elapsed={elapsed:.3f}s p50={statistics.median(lat):.2f}ms p95={q(.95):.2f}ms p99={q(.99):.2f}ms errors=0')
    finally:
        gateway.close(); target.close(); await gateway.wait_closed(); await target.wait_closed()
asyncio.run(main())
