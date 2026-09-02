#!/usr/bin/env python3
"""Static release guard: the product exposes exactly one VLESS transport: WS."""
from pathlib import Path
import ast
import re
import sys

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
check('protocol allowlist is WS-only', protocols == ('vless-ws',), repr(protocols))
check('only WS route registered', 'add_api_websocket_route("/ws/{uuid}"' in main)
check('generated links force type=ws', '"type": "ws"' in main and 'path = f"/ws/{uuid}?ed=4096"' in main)
check('legacy links migrate to WS', '_link["protocol"] = DEFAULT_PROTOCOL' in main)

pages = (ROOT/'pages.py').read_text()
select = re.search(r'<select id="nl-proto".*?</select>', pages, re.S)
options = re.findall(r'<option value="([^"]+)">', select.group(0) if select else '')
check('panel protocol selector is WS-only', options == ['vless-ws'], repr(options))
check('panel has one WS protocol card', pages.count('data-val="vless-ws"') == 1)

if failures:
    print(f"FAILURES: {len(failures)} -> {failures}")
    sys.exit(1)
print('ws-only contract: ALL OK')
