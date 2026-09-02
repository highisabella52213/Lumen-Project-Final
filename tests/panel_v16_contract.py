#!/usr/bin/env python3
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1];text=(root/'pages.py').read_text();main=(root/'main.py').read_text();repo=(root/'proxy_repository.py').read_text();out=(root/'outbound.py').read_text();relay=(root/'relay_vless.py').read_text()
foreign=('Farajian','X4GHUB','x4g_group','vpnfreev2rayconfig','x4gKing','support-url','pg-support','data-pg="support"')
checks={
'MD3 tokens':text.count('--md-sys-color-')>=80,
'layout preserved':all(x in text for x in ['command-rail-w','route-card','create-panel']),
'exit IP controls':all(x in text for x in ['Exit IP settings','تنظیم آیپی خروجی','nl-exit-mode','nl-proxy-id','nl-custom-proxy','el-exit-mode']),
'managed schemes':all(x in text+repo+out for x in ['http','https','socks5']),
'catalog APIs':all(x in text+main for x in ['/api/proxy-catalog','/api/proxy-catalog/manual-status']),
'custom warning':all(x in text for x in ['outside the managed safety boundary','may fail or traffic may be exposed']),
'manual recheck':all(x in text for x in ['proxy-recheck-btn','refreshProxyCatalogNow','Recheck now','بررسی جدید']),
'manual server gate':all(x in main for x in ['manual_refresh_enabled()','status_code=403','manual_refresh_state()']),
'private S3':all(x in repo for x in ['s3.us-west-2.idrivee2.com','us-west-2','bt2','www-32k-ort-org-021/proxy.txt']),
'2 hour interval':'REFRESH_SECONDS = 2 * 60 * 60' in repo,
'anti -1 watchdog':all(x in out for x in ['FIRST_BYTE_TIMEOUT','_verify_downstream','PROXY_TOTAL_TIMEOUT']),
'split TLS prefetch':'prefetch_payload=link_uses_proxy(link)' in relay,
'cache-only data plane':'await refresh()' not in repo[repo.index('async def resolve'):repo.index('async def summary')],
'support removed':all(x not in text+main for x in ('pg-support','data-pg="support"','support-url','t.me/','youtube.com/')),
'v16 brand':'Command Console · v16' in text and 'Version 16.0' in text,
}
fail=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('  ok   ' if v else '  FAIL ')+k)
if fail:print(fail);sys.exit(1)
print('panel v16 contract: ALL OK')
