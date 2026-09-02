#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1];text=(root/'pages.py').read_text();main=(root/'main.py').read_text();repo=(root/'proxy_repository.py').read_text();worker=(root/'cloudflare-installer'/'worker.js').read_text();req=(root/'requirements.txt').read_text()
checks={
'MD3 panel tokens':text.count('--md-sys-color-')>=80,
'layout preserved':all(x in text for x in ['command-rail-w','route-card','create-panel']),
'SNI only':'"host": transport_host' in main and '"sni": tls_name' in main,
'custom UUID':all(x in text+main for x in ['nl-uuid','requested_uuid=body.get("uuid")','if uid in LINKS:']),
'update button':all(x in text for x in ['update-available-btn','/api/update/status','/api/update/apply','applyLatestUpdate']),
'no panel token UI':all(x not in text for x in ['modal-update','update-railway-token','update-github-token','/api/update/setup','openUpdateSetup']),
'no setup writes':all(x not in main for x in ['@app.post("/api/update/setup")','@app.delete("/api/update/setup")']),
'env-only updater':all(x in (root/'updater.py').read_text() for x in ['LUMEN_GITHUB_TOKEN','LUMEN_RAILWAY_TOKEN','UPSTREAM_REPOSITORY = "highisabella52213/Lumen-Project-Final"']),
'no crypto storage':'cryptography' not in req+(root/'updater.py').read_text() and 'lumen_update.json' not in (root/'updater.py').read_text(),
'worker single-file':sorted(p.name for p in (root/'cloudflare-installer').iterdir())==['worker.js'],
'worker fixed source':'highisabella52213' in worker and 'Lumen-Project-Final' in worker,
'worker only two inputs':worker.count('<input ')==2 and 'github-token' in worker and 'railway-token' in worker,
'worker security':all(x in worker for x in ['Cache-Control','Content-Security-Policy','frame-ancestors','no-store']) and 'console.log' not in worker,
'worker railway provisioning':all(x in worker for x in ['projectCreate','serviceCreate','volumeCreate','serviceDomainCreate','serviceInstanceDeployV2']),
'v19 brand':all(x in text+main for x in ['Command Console · v19','Version 19.0','WS-only v19']),
'durable state':all(x in main for x in ['x4g_state.backup-1.json','LUMEN_STATE_SNAPSHOT_B64','os.fsync','refusing to start and overwrite']),
'installer font':all(x in worker for x in ['Vazirmatn','fonts.googleapis.com','fonts.gstatic.com']),
'volume required':'LUMEN_REQUIRE_PERSISTENT_STORAGE' in worker,
'manual unique secret':'installer_managed' in repo and 'MANUAL_REFRESH_TOKEN_SHA256' not in repo,
}
fail=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('  ok   ' if v else '  FAIL ')+k)
if fail:print(fail);sys.exit(1)
print('panel + installer v19 contract: ALL OK')
