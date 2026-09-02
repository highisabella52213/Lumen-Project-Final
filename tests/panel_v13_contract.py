#!/usr/bin/env python3
"""Static UI contract for the v13 bilingual route studio and command rail."""
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import pages
text=(ROOT/'pages.py').read_text()
landing=pages.LANDING_HTML.lower()
checks={
 'address select':'id="nl-address"' in text,
 'address custom':'id="nl-address-custom"' in text,
 'sni select':'id="nl-sni"' in text,
 'sni custom':'id="nl-sni-custom"' in text,
 'live endpoint preview':all(x in text for x in ['endpoint-preview-address','endpoint-preview-sni','updateEndpointPreview']),
 'endpoint catalog API':"authF('/api/config-endpoints')" in text,
 'create submits endpoints':'speed_limit_unit,address,sni' in text,
 'remark create and edit':all(x in text for x in ['id="nl-remark"','id="el-remark"','label,remark,limit_value']),
 'bilingual switch':all(x in text for x in ['toggleLanguage()','dashboard-i18n','lumen-ui-lang']),
 'command rail and route cards':all(x in text for x in ['command-rail-w','route-card','route-action primary']),
 'health landing':all(x in text for x in ['LANDING_HTML','Service health','/health']),
 'edit submits endpoints':all(x in text for x in ['id="el-address"','id="el-sni"',"document.getElementById('el-address').value"]),
 'subgroup survives polling':all(x in text for x in ['const selectedSub=nlSub.value','subs.some(s=>s.sub_id===selectedSub)','nlSub.value=selectedSub']),
 'MD3 semantic tokens':text.count('--md-sys-color-')>=80,
 'MD3 shapes':all(x in text for x in ['--md-sys-shape-corner-extra-large','--md-sys-shape-corner-full']),
 'MD3 motion':all(x in text for x in ['--md-sys-motion-easing-emphasized','prefers-reduced-motion']),
 'adaptive breakpoints':all(x in text for x in ['max-width:1050px','max-width:839px','max-width:599px']),
 'v13 visible brand':all(x in text for x in ['Lumen Relay','Version 13.0','Command Console · v13']),
 'per-config ProxyIP create':all(x in text for x in ['id="nl-proxy-mode"','id="nl-proxyip"','id="nl-proxy-concurrency"','proxyip_enabled,proxyip,proxyip_concurrency']),
 'per-config ProxyIP edit':all(x in text for x in ['id="el-proxy-mode"','id="el-proxyip"','id="el-proxy-concurrency"']),
 'global ProxyIP panel removed':all(x not in text for x in ['id="ob-mode"','id="ob-proxyip"','Exit IP &middot; ProxyIP']),
 'direct fallback notice':'Direct fallback is always enabled' in text,
 'neutral landing copy':all(x not in landing for x in ['relay','websocket','vless','رله']),
 'old dashboard brand gone':'Admin Panel' not in text,
}
failed=[name for name,ok in checks.items() if not ok]
for name,ok in checks.items(): print(('  ok   ' if ok else '  FAIL ')+name)
if failed:
 print('FAILURES:',failed);sys.exit(1)
print('panel v13 contract: ALL OK')
