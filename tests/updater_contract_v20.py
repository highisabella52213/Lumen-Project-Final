#!/usr/bin/env python3
import asyncio,json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import updater
RAIL='railway-account-token-abcdefghijklmnopqrstuvwxyz';GITHUB='github-classic-token-abcdefghijklmnopqrstuvwxyz';SHA='b'*40;calls=[]
def fake(url,*,method='GET',headers=None,payload=None,timeout=12.0):
 calls.append((url,method,headers or {},payload or {}))
 if url.endswith('/releases/latest'):return {'tag_name':'v20.1.0','html_url':'https://github.com/highisabella52213/Lumen-Project-Final/releases/tag/v20.1.0','published_at':'2026-09-03T00:00:00Z'}
 if url.endswith('/repos/user/Lumen-Project-Final') and method=='GET':return {'full_name':'user/Lumen-Project-Final','fork':True,'parent':{'full_name':'highisabella52213/Lumen-Project-Final'},'default_branch':'main'}
 if url.endswith('/merge-upstream'):return {'message':'Successfully synced'}
 if url.endswith('/commits/main'):return {'sha':SHA}
 if url==updater.RAILWAY_GRAPHQL:
  q=(payload or {}).get('query','')
  if 'LumenCredentialIdentity' in q:return {'data':{'me':{'id':'u1'}}}
  if 'SaveLumenCredentials' in q:return {'data':{'variableCollectionUpsert':True}}
  if 'PersistLumenState' in q:return {'data':{'variableCollectionUpsert':True}}
  if 'DeployLumenUpdate' in q:return {'data':{'serviceInstanceDeployV2':'deployment-20'}}
 raise AssertionError((url,method,payload))
async def main():
 for key in ['LUMEN_RAILWAY_TOKEN','LUMEN_GITHUB_TOKEN','LUMEN_FORK_REPO','LUMEN_CREDENTIAL_SOURCE']:os.environ.pop(key,None)
 os.environ.update({'RAILWAY_PROJECT_ID':'project-1','RAILWAY_SERVICE_ID':'service-1','RAILWAY_ENVIRONMENT_ID':'environment-1','RAILWAY_GIT_BRANCH':'main'})
 updater.configure();updater._cache={'at':0.0,'value':None};updater._request_json=fake
 state=await updater.load();assert not state['configured'] and state['manual_configuration_available'] and not state['credentials_locked']
 saved=await updater.save_setup({'fork_repo':'user/Lumen-Project-Final','branch':'main','railway_token':RAIL,'github_token':GITHUB})
 assert saved['configured'] and saved['credentials_locked'] and saved['credential_source']=='manual'
 assert RAIL not in json.dumps(saved) and GITHUB not in json.dumps(saved)
 persisted=[c for c in calls if c[0]==updater.RAILWAY_GRAPHQL and 'SaveLumenCredentials' in c[3].get('query','')][-1]
 pv=persisted[3]['variables']['input'];assert pv['variables']['LUMEN_GITHUB_TOKEN']==GITHUB and pv['variables']['LUMEN_RAILWAY_TOKEN']==RAIL and pv['skipDeploys'] is True
 try:await updater.save_setup({'fork_repo':'user/Lumen-Project-Final','branch':'main','railway_token':RAIL+'x','github_token':GITHUB+'x'})
 except updater.UpdateError as exc:assert exc.status==409 and 'locked' in str(exc)
 else:raise AssertionError('locked credentials accepted without confirmation')
 latest=await updater.check_latest(force=True);assert latest['available'] and latest['latest_version']=='20.1.0'
 result=await updater.apply_latest('snapshot.v20');assert result['started'] and result['commit']=='b'*12 and result['deployment']=='deployment-20'
 snapshot=[c for c in calls if c[0]==updater.RAILWAY_GRAPHQL and 'PersistLumenState' in c[3].get('query','')][-1];assert snapshot[3]['variables']['input']['variables']['LUMEN_STATE_SNAPSHOT_B64']=='snapshot.v20'
 os.environ['LUMEN_CREDENTIAL_SOURCE']='installer';assert updater.setup_status()['installed_by_installer']
 source=Path(updater.__file__).read_text();assert 'lumen_update.json' not in source and 'save_setup' in source and 'confirm_override' in source
asyncio.run(main())
print('updater v20: manual=OK lock=OK installer-source=OK Railway-persist=OK snapshot=OK sync=OK deploy=OK redaction=OK')
