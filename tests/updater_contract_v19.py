#!/usr/bin/env python3
import asyncio,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import updater
RAIL='railway-account-token-abcdefghijklmnopqrstuvwxyz';GITHUB='github-classic-token-abcdefghijklmnopqrstuvwxyz';SHA='a'*40;calls=[]
def fake(url,*,method='GET',headers=None,payload=None,timeout=12.0):
 calls.append((url,method,headers or {},payload or {}))
 if url.endswith('/repos/highisabella52213/Lumen-Project-Final/releases/latest'):return {'tag_name':'v19.1.0','html_url':'https://github.com/highisabella52213/Lumen-Project-Final/releases/tag/v18.1.0','published_at':'2026-09-02T00:00:00Z'}
 if url.endswith('/repos/user/Lumen-Project-Final') and method=='GET':return {'full_name':'user/Lumen-Project-Final','fork':True,'parent':{'full_name':'highisabella52213/Lumen-Project-Final'},'default_branch':'main'}
 if url.endswith('/merge-upstream'):return {'message':'Successfully synced','merge_type':'fast-forward'}
 if url.endswith('/commits/main'):return {'sha':SHA}
 if url==updater.RAILWAY_GRAPHQL:
  q=(payload or {}).get('query','')
  if 'variableCollectionUpsert' in q:return {'data':{'variableCollectionUpsert':True}}
  return {'data':{'serviceInstanceDeployV2':'deployment-1'}}
 raise AssertionError((url,method,payload))
async def main():
 os.environ.update({'RAILWAY_PROJECT_ID':'project-1','RAILWAY_SERVICE_ID':'service-1','RAILWAY_ENVIRONMENT_ID':'environment-1','LUMEN_RAILWAY_TOKEN':RAIL,'LUMEN_GITHUB_TOKEN':GITHUB,'LUMEN_FORK_REPO':'user/Lumen-Project-Final','RAILWAY_GIT_BRANCH':'main'})
 updater.configure();updater._cache={'at':0.0,'value':None};updater._request_json=fake
 state=await updater.load();assert state['configured'] and state['upstream_repo']=='highisabella52213/Lumen-Project-Final'
 assert RAIL not in json.dumps(state) and GITHUB not in json.dumps(state)
 latest=await updater.check_latest(force=True);assert latest['available'] and latest['latest_version']=='19.1.0'
 result=await updater.apply_latest('snapshot.payload');assert result['started'] and result['commit']=='a'*12 and result['deployment']=='deployment-1'
 snapshot=[c for c in calls if c[0]==updater.RAILWAY_GRAPHQL and 'variableCollectionUpsert' in c[3].get('query','')][-1];assert snapshot[3]['variables']['input']['variables']['LUMEN_STATE_SNAPSHOT_B64']=='snapshot.payload'
 deploy=[c for c in calls if c[0]==updater.RAILWAY_GRAPHQL and 'serviceInstanceDeployV2' in c[3].get('query','')][-1];assert deploy[3]['variables']['commitSha']==SHA and deploy[2]['Authorization']=='Bearer '+RAIL
 merge=[c for c in calls if c[0].endswith('/merge-upstream')][-1];assert merge[3]=={'branch':'main'} and merge[2]['Authorization']=='Bearer '+GITHUB
 source=Path(updater.__file__).read_text();assert 'cryptography' not in source and 'lumen_update.json' not in source and 'save_setup' not in source and 'clear_setup' not in source
asyncio.run(main())
print('updater v19: env-only=OK snapshot=OK fixed-source=OK release-check=OK sync=OK deploy=OK secrets-redacted=OK')
