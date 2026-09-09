#!/usr/bin/env python3
from pathlib import Path
import ast, re, sys
ROOT=Path(__file__).resolve().parents[1]
pages=(ROOT/'pages.py').read_text();main=(ROOT/'main.py').read_text();out=(ROOT/'outbound.py').read_text();repo=(ROOT/'proxy_repository.py').read_text();relay=(ROOT/'relay_vless.py').read_text()
checks={
 '15m request identified':"startSerializedPoller(loadUpdateStatus,15*60*1000,'updater')" in pages and "authF('/api/update/status')" in pages and "POLLER_CREATED" in pages and "POLLER_STOPPED" in pages,
 'network bounded retry':all(x in pages for x in ['class ApiRequestError','NETWORK_ERROR','NETWORK_TIMEOUT','attempt<=retries','timeoutMs']),
 'no interval pileup':'setInterval(fetchStats' not in pages and 'setInterval(()=>loadUpdateStatus' not in pages and 'startSerializedPoller' in pages,
 'network cannot reload':"location.reload()" not in pages,
 'auth-only redirect':all(x in pages for x in ["policy.authoritativeAuth===true", "authRedirect('authoritative /api/me returned 401')", "FEATURE_UNAUTHORIZED", "dashboardNavigate('LOCATION_REPLACE','/login',reason)"]),
 '5xx classified':"r.status>=500" in pages and "SERVER_ERROR" in pages,
 'exact health endpoint':'@app.post("/api/proxy-catalog/test")' in main and 'outbound.test_proxy_record(record)' in main,
 'both targets':all(x in out for x in ['"cloudflare.com"','"google.com"','_probe_https_target(record.endpoint']),
 'test receipt binding':all(x in main for x in ['_proxy_endpoint_fingerprint','verify_proxy_test_receipt','require_proxy_test_receipt']),
 'exact runtime ID':'resolve_exit_selection' in main and 'selected_proxy_id = exit_selection["proxy_id"]' in relay and 'proxy_id=selected_proxy_id' in relay,
 'one endpoint only':'len(exact) != 1' in out and 'explicit routing accepts exactly one proxy endpoint' in out,
 'exact two locations':'ML_REQUIRED_LOCATIONS = 2' in main and 'len(raw_locations) != ML_REQUIRED_LOCATIONS' in main,
 'one proxy per location':'"proxy_id": proxy_id' in main and 'proxy_ids' not in main[main.index('async def validate_multi_location'):main.index('def multi_location_for_link')],
 'no health sorting':'.sort(key=lambda record: -record.health)' not in main and '-x["health"]' not in repo,
 'no local DNS fallback':'for candidate in await _resolve_target_ips' not in out,
 'five pending addresses':all(ip in repo for ip in ['69.46.46.60','69.46.46.120','69.46.46.121','69.46.46.188','69.46.46.146']),
 'legacy tag only synthesized':('x'+'4g') not in '\n'.join(p.read_text(errors='ignore') for p in ROOT.rglob('*') if p.is_file() and p.suffix not in {'.pyc'}),
 'public protocol hidden':"function protoChip(_p){return ''}" in pages,
 'forensic diagnostics':all(x in pages for x in ['DOCUMENT_BOOT','FETCH_START','FETCH_RESPONSE','FETCH_ERROR','AUTH_REDIRECT','LOCATION_REPLACE','UNCAUGHT_ERROR','UNHANDLED_REJECTION','disableUnexpectedServiceWorkers']) and all(x in main for x in ['SERVER_BOOT_ID','SERVER_STARTED_AT','/api/diagnostics/client','X-Lumen-Server-Boot-ID']),
 'proxy results keyed by id':all(x in main for x in ['PROXY_TEST_RESULTS','proxy_test_results','latency_ms']) and 'latency_ms' in out,
}
for name,ok in checks.items():print(('  ok   ' if ok else '  FAIL ')+name)
failed=[k for k,v in checks.items() if not v]
if failed:print(failed);sys.exit(1)
print('exact routing + dashboard resilience contract: ALL OK')
