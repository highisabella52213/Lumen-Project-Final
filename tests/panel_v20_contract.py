#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1];text=(root/'pages.py').read_text();main=(root/'main.py').read_text();updater=(root/'updater.py').read_text();worker=(root/'cloudflare-installer'/'worker.js').read_text()
checks={
'MD3 panel tokens':text.count('--md-sys-color-')>=80,
'layout preserved':all(x in text for x in ['command-rail-w','route-card','create-panel']),
'manual token settings':all(x in text for x in ['update-railway-token','update-github-token','Change protected values','/api/update/setup','unlockUpdateCredentials']),
'locked installer warning':all(x in text for x in ['Installer-managed credentials are filled and locked','Incorrect tokens can break updates','confirm_override']),
'backend setup routes':all(x in main for x in ['@app.get("/api/update/setup")','@app.post("/api/update/setup")','updater.save_setup']),
'Railway protected persistence':all(x in updater for x in ['SaveLumenCredentials','variableCollectionUpsert','skipDeploys','LUMEN_CREDENTIAL_SOURCE']),
'secrets redacted':all(x in updater for x in ['github_token_set','railway_token_set']) and '"github_token": github_token' not in updater,
'proxy enforced':all(x in worker for x in ['HTTP_PROXY = Object.freeze({ hostname: "176.111.37.216", port: 39811 })','proxyFetch','openProxyTunnel','node:net','node:tls']),
'proxy TLS':all(x in worker for x in ['servername: targetHostname','rejectUnauthorized: true','ALPNProtocols: ["http/1.1"]']),
'no proxy fallback':'return await proxyFetch(url, options, timeoutMs)' in worker and 'fetch(url,' not in worker.split('const INSTALLER_HTML =',1)[0],
'worker universal':all(x in worker for x in ['public one-file','Every user deploys this same file','This file is public']),
'worker credential source':'LUMEN_CREDENTIAL_SOURCE: "installer"' in worker,
'worker single-file':sorted(p.name for p in (root/'cloudflare-installer').iterdir())==['worker.js'],
'Vazirmatn':all(x in worker for x in ['Vazirmatn','fonts.googleapis.com','fonts.gstatic.com']),
'v20 brand':all(x in text+main+worker for x in ['Command Console · v20','Version 20.0','WS-only v20','20.0.0']),
'durable state':all(x in main for x in ['x4g_state.backup-1.json','LUMEN_STATE_SNAPSHOT_B64','os.fsync','refusing to start and overwrite']),
}
fail=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('  ok   ' if v else '  FAIL ')+k)
if fail:print(fail);sys.exit(1)
print('panel + installer v20 contract: ALL OK')
