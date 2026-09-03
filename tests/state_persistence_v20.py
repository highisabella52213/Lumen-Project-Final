#!/usr/bin/env python3
import ast,asyncio,base64,hashlib,hmac,json,logging,os,shutil,tempfile,zlib
from datetime import datetime
from pathlib import Path
source_path=Path(__file__).resolve().parents[1]/'main.py';tree=ast.parse(source_path.read_text())
names={'_state_payload','_validate_state','_snapshot_encode','_snapshot_decode','make_state_snapshot','_atomic_write_state','load_state','save_state'}
nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
ns=dict(asyncio=asyncio,base64=base64,hashlib=hashlib,hmac=hmac,json=json,logging=logging,os=os,shutil=shutil,zlib=zlib,datetime=datetime,Path=Path,logger=logging.getLogger('state-test'),LINKS={},SUBS={},AUTH={'password_hash':'hash'},CONFIG={'secret':'stable-test-secret'},DEFAULT_PROTOCOL='vless-ws',STATE_SNAPSHOT_ENV='LUMEN_STATE_SNAPSHOT_B64',SAVE_LOCK=asyncio.Lock())
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source_path),'exec'),ns)
async def run():
 with tempfile.TemporaryDirectory() as d:
  ns['DATA_DIR']=Path(d);ns['DATA_FILE']=ns['DATA_DIR']/'x4g_state.json';ns['STATE_BACKUPS']=(ns['DATA_DIR']/'x4g_state.backup-1.json',ns['DATA_DIR']/'x4g_state.backup-2.json')
  ns['LINKS'].clear();ns['SUBS'].clear();ns['LINKS']['u1']={'label':'before update','protocol':'vless-ws'};ns['SUBS']['s1']={'name':'group','link_ids':['u1']}
  assert await ns['save_state'](strict=True);ns['LINKS']['u2']={'label':'second','protocol':'vless-ws'};assert await ns['save_state'](strict=True);assert ns['STATE_BACKUPS'][0].exists()
  ns['LINKS'].clear();ns['SUBS'].clear();await ns['load_state']();assert set(ns['LINKS'])=={'u1','u2'} and set(ns['SUBS'])=={'s1'}
  snapshot=ns['make_state_snapshot']();ns['DATA_FILE'].write_text('{broken');ns['STATE_BACKUPS'][0].write_text(json.dumps(ns['_state_payload']()));ns['LINKS'].clear();ns['SUBS'].clear();await ns['load_state']();assert 'u1' in ns['LINKS'] and ns['DATA_FILE'].read_text().startswith('{')
  for x in (ns['DATA_FILE'],*ns['STATE_BACKUPS']):x.unlink(missing_ok=True)
  os.environ[ns['STATE_SNAPSHOT_ENV']]=snapshot;ns['LINKS'].clear();ns['SUBS'].clear();await ns['load_state']();assert set(ns['LINKS'])=={'u1','u2'} and set(ns['SUBS'])=={'s1'} and ns['DATA_FILE'].exists();os.environ.pop(ns['STATE_SNAPSHOT_ENV'],None)
asyncio.run(run());print('state v20 regression: atomic=OK backups=OK recovery=OK signed-snapshot=OK configs=OK subgroups=OK')
