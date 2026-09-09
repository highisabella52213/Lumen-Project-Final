#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
text=(root/'pages.py').read_text();main=(root/'main.py').read_text();updater=(root/'updater.py').read_text()
installer=(root/'railway-installer'/'server.js').read_text();railway=(root/'railway-installer'/'railway.json').read_text()
proxies=['176.111.37.216:39811','107.167.18.122:443','130.110.103.245:3128','176.111.37.5:39811','94.249.197.220:40001','13.203.138.32:3001']
checks={
'MD3 panel tokens':text.count('--md-sys-color-')>=80,
'manual token settings':all(x in text for x in ['update-railway-token','update-github-token','Change protected values','/api/update/setup']),
'locked installer warning':all(x in text for x in ['Installer-managed credentials are filled and locked','confirm_override']),
'backend setup routes':all(x in main for x in ['@app.get("/api/update/setup")','@app.post("/api/update/setup")','updater.save_setup']),
'all six proxies':all(host in installer and ('port: '+port) in installer for host,port in (item.split(':') for item in proxies)) and installer.count('Object.freeze({ hostname:')==6,
'Railway deployment probe':all(x in installer for x in ['refreshDeploymentNetwork','selectTransport','probeRoute','LumenNetworkProbe','GITHUB_API + "/meta"']),
'health gates deployment':all(x in installer+railway for x in ['status === "ready" ? 200 : 503','"healthcheckPath": "/health"','"healthcheckTimeout": 300']),
'both targets checked':all(x in installer for x in ['githubOk','railwayOk','githubOk && railwayOk']),
'fast healthy selection':'left.latencyMs - right.latencyMs' in installer,
'direct-first control route':all(x in installer for x in ['Direct is preferred for token-bearing control-plane operations','directFetch','DIRECT_PROBE_TIMEOUT_MS']),
'safe GitHub route qualification':all(x in installer for x in ['selectAuthenticatedTransport','/user','NO_GITHUB_AUTH_ROUTE']) and 'query InstallerIdentity' not in installer,
'IPv6 and Virginia':all(x in installer for x in ['ipv6EgressEnabled: true','us-east4-eqdc4a','multiRegionConfig']),
'seven deployment polls':all(x in installer for x in ['attempt <= 7','20_000','DEPLOYMENT_TIMEOUT','deploymentStatus !== "SUCCESS"']),
'async install status':all(x in installer for x in ['/api/install/start','/api/install/status','startInstallJob','installJobs']),
'live deployment title':all(x in installer for x in ['progress-title','renderLiveProgress','Deployment status:']),
'safe project names':all(x in installer for x in ['railwayProjectName','invalid project name','ownerLimit','slice(0, 32)']),
'workspace before project':all(x in installer for x in ['ensureWorkspace','InstallerWorkspaces','InstallerWorkspaceCapability','InstallerWorkspaceCreate','workspaceId: workspace.id']),
'workspace fallback':all(x in installer for x in ['reused-lumen','reused-existing','WORKSPACE_REQUIRED']),
'official service sequence':all(x in installer for x in ['InstallerVariables','variableCollectionUpsert','InstallerSource','serviceConnect','commitSha: $commitSha']) and 'skipInitialDeploys' not in installer,
'structured UI errors':all(x in installer for x in ['messageFa','messageEn','requestId','error: detail']),
'Railway token guidance':all(x in installer for x in ['RAILWAY_TOKEN_INVALID','No workspace','not authorized']),
'request-scoped route':all(x in installer for x in ['async function github(route','async function railway(route','async function provisionRailway(route']),
'proxy TLS':all(x in installer for x in ['servername: targetHostname','rejectUnauthorized: true','ALPNProtocols: ["http/1.1"]']),
'early HTTP completion':all(x in installer for x in ['responseIsComplete','content-length','transfer-encoding']),
'selected route shown':all(x in installer for x in ['networkRoute','networkChecks','network-route','Selected network route']),
'complete Railway folder':sorted(p.name for p in (root/'railway-installer').iterdir())==['Dockerfile','README.md','package.json','railway.json','server.js'],
'Cloudflare installer removed':not (root/'cloudflare-installer').exists() and 'Cloudflare' not in installer,
'Vazirmatn':all(x in installer for x in ['Vazirmatn','fonts.googleapis.com','fonts.gstatic.com']),
'v28 brand':all(x in text+main+installer+updater for x in ['Command Console · v28','Version 28.0','WS-only v28','28.0.0']),
'durable state':all(x in main for x in ['code_state.backup-1.json','LUMEN_STATE_SNAPSHOT_B64','os.fsync','refusing to start and overwrite']),
}
fail=[k for k,v in checks.items() if not v]
for k,v in checks.items():print(('  ok   ' if v else '  FAIL ')+k)
if fail:print(fail);sys.exit(1)
print('panel + Railway installer v28 contract: ALL OK')
