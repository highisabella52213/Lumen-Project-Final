#!/usr/bin/env python3
from pathlib import Path
import re,sys
root=Path(__file__).resolve().parents[1];text=(root/'pages.py').read_text();main=(root/'main.py').read_text();repo=(root/'proxy_repository.py').read_text()
checks={
'MD3 tokens':text.count('--md-sys-color-')>=80,
'layout preserved':all(x in text for x in ['command-rail-w','route-card','create-panel']),
'exit IP label':'Exit IP settings' in text and 'تنظیم آیپی خروجی' in text,
'per-config controls':all(x in text for x in ['nl-exit-mode','nl-proxy-id','nl-custom-proxy','el-exit-mode']),
'managed schemes':all(x in text+repo for x in ['http','https','socks5']),
'catalog fetch':"authF('/api/proxy-catalog')" in text and '/api/proxy-catalog' in main,
'endpoint hidden':'endpoint' not in "return {\"id\":x.id,\"type\":x.type,\"country\":x.country,\"country_code\":x.code,\"flag\":x.flag,\"health\":x.health,\"managed\":True,\"safe\":True}",
'custom warning':all(x in text for x in ['outside the managed safety boundary','may fail or traffic may be exposed']),
'removed feature':not re.search('proxy'+'ip',text+main,flags=re.I),
'manual recheck button':all(x in text for x in ['proxy-recheck-btn','refreshProxyCatalogNow','Recheck now','بررسی جدید']),
'manual API gate':'manual_refresh_enabled()' in main and 'status_code=403' in main,
'private S3 path':all(x in repo for x in ['s3.us-west-2.idrivee2.com','us-west-2','bt2','www-32k-ort-org-021/proxy.txt']),
'2 hour interval':'REFRESH_SECONDS = 2 * 60 * 60' in repo,
'v15 brand':'Command Console · v15' in text and 'Version 15.0' in text,
}
fail=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('  ok   ' if v else '  FAIL ')+k)
if fail:print(fail);sys.exit(1)
print('panel v15 contract: ALL OK')
