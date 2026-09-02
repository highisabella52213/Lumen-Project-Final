#!/usr/bin/env python3
"""Static UI contract for the v12 bilingual route studio and command rail."""
from pathlib import Path
import re, sys
text=(Path(__file__).resolve().parents[1]/'pages.py').read_text()
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
 'v12 visible brand':all(x in text for x in ['Lumen Relay','Version 12.0','Command Console · v12']),
 'old dashboard brand gone':'Admin Panel' not in text,
}
failed=[name for name,ok in checks.items() if not ok]
for name,ok in checks.items(): print(('  ok   ' if ok else '  FAIL ')+name)
if failed:
 print('FAILURES:',failed);sys.exit(1)
print('panel v12 contract: ALL OK')
