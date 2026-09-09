#!/usr/bin/env node
import assert from 'node:assert/strict';
import {once} from 'node:events';
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const mod=await import(pathToFileURL(new URL('../railway-installer/server.js',import.meta.url).pathname).href);
const GH='ghp_abcdefghijklmnopqrstuvwxyz1234567890';
const RW='railway_abcdefghijklmnopqrstuvwxyz1234567890';
globalThis.__LUMEN_TEST_DEPLOYMENT_POLL_MS__=1;
const chosen='http://107.167.18.122:443';
const primary='http://176.111.37.216:39811';
let mode='install';let calls=[];
const response=(data,status=200)=>new Response(data===null?null:JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
const routeMock=async(route,url,options={})=>{
 const label=mod.__test.routeLabel(route);const body=options.body?JSON.parse(options.body):{};const q=body.query||'';
 const probe=String(url).endsWith('/meta')||q.includes('LumenNetworkProbe');calls.push({label,url:String(url),options,body,probe});
 if(probe){let healthy=mode==='direct'?route.kind==='direct':mode==='direct-preferred'?(route.kind==='direct'||label===chosen):mode==='auth-failover'?[primary,chosen].includes(label):label===chosen;if(!healthy)throw new Error('route down');return String(url).endsWith('/meta')?response({ok:true}):response({data:{__typename:'Query'}})}
 if(mode==='auth-failover'&&label===primary&&String(url).endsWith('/user'))throw new Error('proxy stripped authorization');
 if(label!==chosen&&!(mode==='direct'&&route.kind==='direct'))throw new Error('installation escaped selected route');const u=String(url);
 if(u.endsWith('/user'))return response({login:'tester'});
 if(u.includes('/user/starred/'))return response(null,204);
 if(u.endsWith('/repos/tester/Lumen-Project-Final'))return response({fork:true,full_name:'tester/Lumen-Project-Final',html_url:'https://github.com/tester/Lumen-Project-Final',default_branch:'main',owner:{login:'tester'},parent:{full_name:'highisabella52213/Lumen-Project-Final'}});
 if(u.endsWith('/commits/main'))return response({sha:'a'.repeat(40)});
 if(u.includes('backboard.railway.com')){
  if(q.includes('InstallerIdentity'))return response({data:{me:{id:'u1'}}});
  if(q.includes('InstallerWorkspaces')){const items=mode==='workspace-existing'?[{id:'w-existing',name:'Lumen tester'}]:[{id:'w-default',name:'Personal'}];return response({data:{me:{workspaces:items}}})}
  if(q.includes('InstallerWorkspaceCapability'))return response({data:{__type:{fields:mode==='workspace-fallback'?[]:[{name:'workspaceCreate'}]}}});
  if(q.includes('InstallerWorkspaceCreate'))return response({data:{workspaceCreate:{id:'w-lumen',name:'Lumen tester'}}});
  if(q.includes('InstallerProject(')){if(mode==='railway-auth-error')return response({errors:[{message:'Not Authorized'}]});const projectCalls=calls.filter(c=>(c.body.query||'').includes('InstallerProject('));if(mode==='project-name-retry'&&projectCalls.length===1)return response({errors:[{message:'Invalid project name'}]});return response({data:{projectCreate:{id:'p1',name:body.variables.input.name,environments:{edges:[{node:{id:'e1',name:'production'}}]}}}})}
  if(q.includes('InstallerService(')){if(mode==='service-error')return response({errors:[{message:'Unknown input field in ServiceCreateInput'}]});return response({data:{serviceCreate:{id:'s1',name:'Lumen'}}})}
  if(q.includes('InstallerServiceSettings'))return response({data:{serviceInstanceUpdate:true}});
  if(q.includes('InstallerVariables'))return response({data:{variableCollectionUpsert:true}});
  if(q.includes('InstallerVolume'))return response({data:{volumeCreate:{id:'v1',name:'data'}}});
  if(q.includes('InstallerDomain'))return response({data:{serviceDomainCreate:{id:'dm1',domain:'lumen-production.up.railway.app'}}});
  if(q.includes('InstallerSource'))return response({data:{serviceConnect:{id:'s1'}}});
  if(q.includes('InstallerDeploy('))return response({data:{serviceInstanceDeployV2:'d1'}});
  if(q.includes('InstallerDeployment')){const checks=calls.filter(c=>(c.body.query||'').includes('InstallerDeployment')).length;if(mode==='deployment-timeout'||(mode==='deployment-seven'&&checks<7))return response({data:{deployment:{id:'d1',status:'BUILDING'}}});return response({data:{deployment:{id:'d1',status:'SUCCESS'}}})}
 }
 throw new Error('unexpected '+u+' '+JSON.stringify(body));
};
globalThis.__LUMEN_TEST_ROUTE_FETCH__=routeMock;
// Full install uses the documented empty-service sequence and one qualified route.
const result=await mod.__test.installPayload({githubToken:GH,railwayToken:RW});
assert.equal(result.ok,true);assert.equal(result.deploymentStatus,'SUCCESS');assert.equal(result.networkRoute.label,chosen);assert.equal(result.workspaceId,'w-lumen');assert.equal(result.workspaceMode,'created');assert.equal(result.networkChecks.length,7);assert.equal(result.authenticatedRouteChecks.at(-1).ok,true);
const probes=calls.filter(x=>x.probe);assert.equal(new Set(probes.map(x=>x.label)).size,7);for(const label of new Set(probes.map(x=>x.label)))assert.equal(probes.filter(x=>x.label===label).length,2);assert.ok(probes.every(x=>!new Headers(x.options.headers||{}).has('Authorization')));
const operational=calls.filter(x=>!x.probe);assert.ok(operational.length>8&&operational.every(x=>x.label===chosen));
const findQuery=name=>operational.find(c=>(c.body.query||'').includes(name));
const workspaceCreate=findQuery('InstallerWorkspaceCreate');const projectCall=findQuery('InstallerProject(');assert.equal(projectCall.body.variables.input.workspaceId,'w-lumen');assert.match(projectCall.body.variables.input.name,/^[a-z][a-z0-9-]{0,31}$/);assert.ok(projectCall.body.variables.input.name.length<=32);assert.ok(!/[ _A-Z]/.test(projectCall.body.variables.input.name));assert.ok(operational.indexOf(workspaceCreate)<operational.indexOf(projectCall));
const serviceInput=findQuery('InstallerService(').body.variables.input;assert.deepEqual(serviceInput,{projectId:'p1',environmentId:'e1',name:'Lumen'});assert.ok(!('skipInitialDeploys' in serviceInput)&&!('source' in serviceInput)&&!('variables' in serviceInput));
const settingsInput=findQuery('InstallerServiceSettings').body.variables.input;assert.equal(settingsInput.ipv6EgressEnabled,true);assert.equal(settingsInput.region,'us-east4-eqdc4a');assert.deepEqual(settingsInput.multiRegionConfig,{'us-east4-eqdc4a':{numReplicas:1}});
const varsCall=findQuery('InstallerVariables');const varsInput=varsCall.body.variables.input;assert.equal(varsInput.skipDeploys,true);assert.equal(varsInput.variables.PORT,'8000');assert.equal(varsInput.variables.LUMEN_GITHUB_TOKEN,GH);assert.equal(varsInput.variables.LUMEN_RAILWAY_TOKEN,RW);
const sourceCall=findQuery('InstallerSource');assert.deepEqual(sourceCall.body.variables.input,{repo:'tester/Lumen-Project-Final',branch:'main'});assert.equal(findQuery('InstallerDeploy').body.variables.commitSha,'a'.repeat(40));assert.ok(operational.indexOf(varsCall)<operational.indexOf(sourceCall));assert.ok(operational.indexOf(sourceCall)<operational.indexOf(findQuery('InstallerDeploy')));
assert.ok(!JSON.stringify(result).includes(GH)&&!JSON.stringify(result).includes(RW));
// Project names are normalized to Railway-safe lowercase slugs, including long or unusual account names.
for(const raw of ['Tester User','A'.repeat(39),'__name__','کاربر']){const name=mod.__test.railwayProjectName(raw,'ABC_DEF_123456789');assert.match(name,/^[a-z][a-z0-9-]{0,31}$/);assert.ok(name.length<=32)}
// If Railway still rejects a generated name, retry once with a minimal randomized slug.
mode='project-name-retry';calls=[];const retried=await mod.__test.installPayload({githubToken:GH,railwayToken:RW});assert.equal(retried.ok,true);const retriedProjects=calls.filter(c=>(c.body.query||'').includes('InstallerProject('));assert.equal(retriedProjects.length,2);assert.notEqual(retriedProjects[0].body.variables.input.name,retriedProjects[1].body.variables.input.name);assert.ok(retriedProjects.every(c=>/^[a-z][a-z0-9-]{0,31}$/.test(c.body.variables.input.name)));
// Poll deployment every configured interval and only succeed on the seventh successful check.
mode='deployment-seven';calls=[];const seventh=await mod.__test.installPayload({githubToken:GH,railwayToken:RW});assert.equal(seventh.deploymentStatus,'SUCCESS');assert.equal(calls.filter(c=>(c.body.query||'').includes('InstallerDeployment')).length,7);
// Seven non-terminal checks return a precise timeout instead of a false success.
mode='deployment-timeout';calls=[];await assert.rejects(()=>mod.__test.installPayload({githubToken:GH,railwayToken:RW}),error=>error&&error.code==='DEPLOYMENT_TIMEOUT'&&error.step==='deployment-status');assert.equal(calls.filter(c=>(c.body.query||'').includes('InstallerDeployment')).length,7);
// Reuse an accessible workspace when Railway does not expose workspaceCreate.
mode='workspace-fallback';calls=[];let workspace=await mod.__test.ensureWorkspace({kind:'proxy',proxy:{hostname:'107.167.18.122',port:443}},RW,'tester');assert.equal(workspace.id,'w-default');assert.equal(workspace.mode,'reused-existing');
// Repeated runs reuse the dedicated Lumen workspace instead of creating duplicates.
mode='workspace-existing';calls=[];workspace=await mod.__test.ensureWorkspace({kind:'proxy',proxy:{hostname:'107.167.18.122',port:443}},RW,'tester');assert.equal(workspace.id,'w-existing');assert.equal(workspace.mode,'reused-lumen');assert.ok(!calls.some(c=>(c.body.query||'').includes('InstallerWorkspaceCapability')));
// Direct Railway egress is preferred when both direct and proxy routes are healthy.
mode='direct-preferred';calls=[];const preferred=await mod.__test.selectTransport();assert.equal(preferred.route.kind,'direct');assert.equal(preferred.checks.length,7);
// A publicly healthy proxy that blocks credentials is skipped before mutations.
mode='auth-failover';calls=[];const publicPool=await mod.__test.selectTransport();const qualified=await mod.__test.selectAuthenticatedTransport(publicPool,GH,RW);assert.equal(qualified.route.kind,'proxy');assert.equal(mod.__test.routeLabel(qualified.route),chosen);assert.equal(qualified.authChecks[0].label,primary);assert.equal(qualified.authChecks[0].ok,false);assert.equal(qualified.authChecks.at(-1).ok,true);assert.ok(calls.every(c=>c.probe||!c.url.includes('/starred/')));
// Direct fallback is only reached when proxy candidates do not work.
mode='direct';calls=[];const fallback=await mod.__test.selectTransport();assert.equal(fallback.route.kind,'direct');assert.equal(fallback.checks.length,7);assert.equal(fallback.checks.slice(0,6).filter(x=>x.ok).length,0);assert.equal(fallback.checks[6].ok,true);
await mod.__test.refreshDeploymentNetwork();assert.equal(mod.__test.publicNetworkState().status,'ready');assert.equal(mod.__test.publicNetworkState().selectedRoute.kind,'direct');
// A hung transport cannot leave deployment health on checking.
const working=globalThis.__LUMEN_TEST_ROUTE_FETCH__;globalThis.__LUMEN_TEST_ROUTE_FETCH__=async()=>await new Promise(()=>{});globalThis.__LUMEN_TEST_SELECTION_TIMEOUT_MS__=40;const started=Date.now();const hard=await mod.__test.refreshDeploymentNetwork();assert.equal(hard.status,'failed');assert.ok(Date.now()-started<1000);assert.match(hard.error,/hard deadline/);globalThis.__LUMEN_TEST_ROUTE_FETCH__=working;delete globalThis.__LUMEN_TEST_SELECTION_TIMEOUT_MS__;mode='direct';await mod.__test.refreshDeploymentNetwork();
// HTTP errors match the UI's bilingual structured envelope.
const server=mod.createInstallerServer();server.listen(0,'127.0.0.1');await once(server,'listening');const port=server.address().port;const base=`http://127.0.0.1:${port}`;
assert.equal((await fetch(base+'/')).status,200);assert.equal((await fetch(base+'/health')).status,200);
mode='deployment-seven';calls=[];globalThis.__LUMEN_TEST_DEPLOYMENT_POLL_MS__=10;let startedResponse=await fetch(base+'/api/install/start',{method:'POST',headers:{'content-type':'application/json','origin':base},body:JSON.stringify({githubToken:GH,railwayToken:RW})});let startedJson=await startedResponse.json();assert.equal(startedResponse.status,202);assert.equal(startedJson.accepted,true);assert.match(startedJson.installId,/^[A-Za-z0-9_-]{20,80}$/);let jobStates=[];let job;for(let index=0;index<80;index+=1){await new Promise(resolve=>setTimeout(resolve,5));job=await (await fetch(base+'/api/install/status?id='+encodeURIComponent(startedJson.installId))).json();jobStates.push(job);if(job.state!=='running')break}assert.equal(job.state,'completed');assert.equal(job.result.deploymentStatus,'SUCCESS');assert.ok(jobStates.some(item=>item.phase==='deployment-status'&&item.deploymentStatus));globalThis.__LUMEN_TEST_DEPLOYMENT_POLL_MS__=1;
let bad=await fetch(base+'/api/install',{method:'POST',headers:{'content-type':'application/json','origin':base},body:JSON.stringify({githubToken:'short',railwayToken:'short'})});let badJson=await bad.json();assert.equal(bad.status,400);assert.equal(badJson.error.code,'GITHUB_TOKEN_FORMAT');assert.ok(badJson.error.messageFa&&badJson.error.messageEn&&badJson.error.requestId);
mode='railway-auth-error';bad=await fetch(base+'/api/install',{method:'POST',headers:{'content-type':'application/json','origin':base},body:JSON.stringify({githubToken:GH,railwayToken:RW})});badJson=await bad.json();assert.equal(bad.status,401);assert.equal(badJson.error.code,'RAILWAY_TOKEN_INVALID');assert.match(badJson.error.messageEn,/No workspace/);
mode='service-error';bad=await fetch(base+'/api/install',{method:'POST',headers:{'content-type':'application/json','origin':base},body:JSON.stringify({githubToken:GH,railwayToken:RW})});badJson=await bad.json();assert.equal(bad.status,502);assert.equal(badJson.error.step,'service');assert.equal(badJson.error.code,'RAILWAY_GRAPHQL_ERROR');assert.match(badJson.error.details,/Unknown input field/);
server.close();await once(server,'close');
const source=await readFile(new URL('../railway-installer/server.js',import.meta.url),'utf8');for(const ip of ['176.111.37.216','107.167.18.122','130.110.103.245','176.111.37.5','94.249.197.220','13.203.138.32'])assert.ok(source.includes(ip));assert.ok(!source.includes('skipInitialDeploys'));for(const token of ['InstallerWorkspaces','InstallerWorkspaceCapability','InstallerWorkspaceCreate','workspaceId: workspace.id','railwayProjectName','invalid project name','ipv6EgressEnabled: true','us-east4-eqdc4a','multiRegionConfig','attempt <= 7','20_000','DEPLOYMENT_TIMEOUT','/api/install/start','/api/install/status','progress-title','InstallerVariables','InstallerSource','commitSha: $commitSha','selectAuthenticatedTransport','error: detail','No workspace'])assert.ok(source.includes(token));assert.ok(source.includes('rejectUnauthorized: true')&&!source.includes('Cloudflare')&&!source.includes('query InstallerIdentity'));assert.ok(source.includes('Direct is preferred for token-bearing control-plane operations')); 
delete globalThis.__LUMEN_TEST_ROUTE_FETCH__;delete globalThis.__LUMEN_TEST_DEPLOYMENT_POLL_MS__;
console.log('railway installer v28: async-status=OK ipv6=OK virginia=OK seven-polls=OK project-name-safe=OK workspace-first=OK direct-first=OK scoped-token-safe=OK official-schema=OK stage-five=OK authenticated-failover=OK structured-errors=OK direct-fallback=OK health=OK TLS=OK redaction=OK');
