#!/usr/bin/env python3
import ast,sys
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
from uuid import UUID,uuid4
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
from config_address import authority_host,link_hosts,normalize_address
text=(root/'main.py').read_text();tree=ast.parse(text)
names={'generate_uuid','normalize_requested_uuid','generate_vless_link'}
selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
from urllib.parse import quote
ns={'UUID':UUID,'uuid4':uuid4,'quote':quote,'authority_host':authority_host,'link_hosts':link_hosts,'normalize_address':normalize_address,'DEFAULT_FINGERPRINT':'chrome','FINGERPRINTS':('chrome',),'DEFAULT_ALPN_BY_PROTOCOL':{'vless-ws':'http/1.1'},'DEFAULT_PROTOCOL':'vless-ws','DEFAULT_PORT':443,'MIN_PORT':1,'MAX_PORT':65535}
exec(compile(ast.Module(body=selected,type_ignores=[]),str(root/'main.py'),'exec'),ns)
custom='6BA7B810-9DAD-11D1-80B4-00C04FD430C8'
link=ns['generate_vless_link'](custom,'service.example.com',address='104.16.1.1',sni='front.example.org');q=parse_qs(urlsplit(link).query)
assert q['host']==['service.example.com'] and q['sni']==['front.example.org'],q
link2=ns['generate_vless_link'](custom,'service.example.com',address='104.16.1.1',sni='other.example.org');q2=parse_qs(urlsplit(link2).query);assert q2['host']==q['host'] and q2['sni']==['other.example.org']
assert ns['normalize_requested_uuid'](custom)=='6ba7b810-9dad-11d1-80b4-00c04fd430c8';assert UUID(ns['generate_uuid']()).version==4
for bad in ('not-a-uuid','00000000-0000-0000-0000-000000000000'):
 try:ns['normalize_requested_uuid'](bad);raise AssertionError('accepted '+bad)
 except ValueError:pass
assert 'requested_uuid=body.get("uuid")' in text and 'if uid in LINKS:' in text and 'این UUID قبلاً استفاده شده است' in text
print('SNI/UUID v17: transport-host-fixed=OK tls-sni-only=OK custom=OK auto-v4=OK duplicate-guard=OK')
