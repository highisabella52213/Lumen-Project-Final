#!/usr/bin/env python3
"""Native-runtime transport guard.

The UI may name future transports, but only a transport with a real inbound
runtime may be selected, persisted, or serialized. The current deployment has
one native VLESS ingress: WebSocket.
"""
from pathlib import Path
import ast
import re
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transports import TRANSPORTS, TransportUnavailableError, TransportValidationError

ROOT = Path(__file__).resolve().parent.parent
failures = []

def check(name, cond, detail=""):
    print(("  ok   " if cond else "  FAIL ") + name + (("  " + detail) if detail and not cond else ""))
    if not cond:
        failures.append(name)

forbidden = ("x" + "http", "packet" + "-up", "stream" + "-up", "stream" + "-one", "x" + "mux")
texts = {}
for path in ROOT.rglob('*'):
    if not path.is_file() or '__pycache__' in path.parts or path.suffix not in {'.py','.md','.txt'}:
        continue
    if path == Path(__file__):
        continue
    texts[path] = path.read_text(encoding='utf-8', errors='replace').lower()

hits=[]
for path,text in texts.items():
    for token in forbidden:
        if token in text:
            hits.append(f"{path.relative_to(ROOT)}:{token}")
check('no removed-transport references', not hits, ', '.join(hits[:10]))
check('removed implementation file absent', not (ROOT / ('x'+'http_siz10.py')).exists())
check('removed stress test absent', not (ROOT / 'tests' / ('x'+'http_transport_stress.py')).exists())

main = (ROOT/'main.py').read_text()
tree = ast.parse(main)
protocols = None
for node in tree.body:
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name) and target.id=='PROTOCOLS':
                protocols=ast.literal_eval(node.value)
check('protocol allowlist includes deployment-gated Raw TCP', protocols == ('vless-ws', 'vless-tcp'), repr(protocols))
check('only WS route registered', 'add_api_websocket_route("/ws/{uuid}"' in main)
check('WS VLESS serialization delegated to registry', 'TRANSPORTS.vless_parameters(' in main)
check('legacy links receive empty transport settings', '_stored_settings = _link.get("transport_settings")' in main)
check('persisted unsupported transports fail closed', 'TRANSPORTS.is_available(link.get("protocol", DEFAULT_PROTOCOL))' in main)
check('authenticated capability route is present', '@app.get("/api/transports")' in main)

capabilities = {item['id']: item for item in TRANSPORTS.capabilities()}
check('registry names all requested transports', set(capabilities) == {
    'vless-ws', 'vless-tcp', 'vless-grpc', 'vless-kcp', 'vless-httpupgrade'
}, repr(sorted(capabilities)))
check('only WS has a default runtime', [item['id'] for item in capabilities.values() if item['available']] == ['vless-ws'])
for transport_id in ('vless-tcp', 'vless-grpc', 'vless-kcp', 'vless-httpupgrade'):
    try:
        TRANSPORTS.validate(transport_id, {})
        unavailable = False
    except TransportUnavailableError:
        unavailable = True
    check(f'{transport_id} rejects unavailable runtime', unavailable)

try:
    TRANSPORTS.validate('unknown-transport', {})
    unknown_rejected = False
except TransportValidationError:
    unknown_rejected = True
check('unknown transport is rejected', unknown_rejected)

params = TRANSPORTS.vless_parameters(
    'vless-ws', uuid='u1', transport_host='relay.example', location_id='loc-A'
)
check('WS serializer is semantically correct', params == {
    'type': 'ws', 'host': 'relay.example', 'path': '/ws/u1?ed=4096&loc=loc-A'
}, repr(params))

pages = (ROOT/'pages.py').read_text()
select = re.search(r'<select id="nl-proto".*?</select>', pages, re.S)
options = re.findall(r'<option value="([^"]+)">', select.group(0) if select else '')
check('hidden selection includes deployment-gated Raw TCP', options == ['vless-ws', 'vless-tcp'], repr(options))
check('panel has one WS protocol card', pages.count('data-val="vless-ws"') == 1)
pattern = r'data-val="vless-tcp"[^>]*aria-disabled="true"[^>]*disabled'
check('panel shows deployment-gated vless-tcp', re.search(pattern, pages) is not None)
for transport_id in ('vless-grpc', 'vless-kcp', 'vless-httpupgrade'):
    pattern = rf'data-val="{transport_id}"[^>]*aria-disabled="true"[^>]*disabled'
    check(f'panel shows disabled {transport_id}', re.search(pattern, pages) is not None)
check('panel loads server capability status', "authF('/api/transports')" in pages and 'loadTransportCapabilities();' in pages)

if failures:
    print(f"FAILURES: {len(failures)} -> {failures}")
    sys.exit(1)
print('ws-only contract: ALL OK')
