#!/usr/bin/env node
import assert from 'node:assert/strict';
import {pathToFileURL} from 'node:url';
const mod=await import(pathToFileURL(new URL('../cloudflare-installer/worker.js',import.meta.url).pathname).href);
const GH='ghp_abcdefghijklmnopqrstuvwxyz1234567890';const RW='railway_abcdefghijklmnopqrstuvwxyz1234567890';const calls=[];
globalThis.fetch=async (url,options={})=>{calls.push({url:String(url),options});const u=String(url);const body=options.body?JSON.parse(options.body):{};
 const response=(data,status=200)=>new Response(data===null?null:JSON.stringify(data),{status,headers:{'content-type':'application/json'}});
 if(u.endsWith('/user'))return response({login:'tester'});
 if(u.includes('/user/starred/'))return response(null,204);
 if(u.endsWith('/repos/tester/Lumen-Project-Final'))return response({fork:true,full_name:'tester/Lumen-Project-Final',html_url:'https://github.com/tester/Lumen-Project-Final',default_branch:'main',owner:{login:'tester'},parent:{full_name:'highisabella52213/Lumen-Project-Final'}});
 if(u.endsWith('/commits/main'))return response({sha:'a'.repeat(40)});
 if(u.includes('backboard.railway.com')){const q=body.query||'';
  if(q.includes('InstallerIdentity'))return response({data:{me:{id:'u1'}}});
  if(q.includes('InstallerProject('))return response({data:{projectCreate:{id:'p1',name:'Lumen',environments:{edges:[{node:{id:'e1',name:'production'}}]}}}});
  if(q.includes('InstallerService('))return response({data:{serviceCreate:{id:'s1',name:'Lumen'}}});
  if(q.includes('InstallerServiceSettings'))return response({data:{serviceInstanceUpdate:true}});
  if(q.includes('InstallerVolume'))return response({data:{volumeCreate:{id:'v1',name:'data'}}});
  if(q.includes('InstallerDomain'))return response({data:{serviceDomainCreate:{domain:'lumen-production.up.railway.app'}}});
  if(q.includes('InstallerDeploy'))return response({data:{serviceInstanceDeployV2:'d1'}});
  if(q.includes('InstallerDeployment'))return response({data:{deployment:{id:'d1',status:'SUCCESS'}}});
 }
 throw new Error('unexpected '+u+' '+JSON.stringify(body));};
const result=await mod.__test.installPayload({githubToken:GH,railwayToken:RW});
assert.equal(result.ok,true);assert.equal(result.panelUrl,'https://lumen-production.up.railway.app/dashboard');assert.equal(result.forkRepository,'tester/Lumen-Project-Final');assert.ok(result.adminPassword.length>=20);
const serviceCall=calls.find(c=>c.options.body&&JSON.parse(c.options.body).query.includes('InstallerService('));const vars=JSON.parse(serviceCall.options.body).variables.input.variables;
assert.equal(vars.LUMEN_GITHUB_TOKEN,GH);assert.equal(vars.LUMEN_RAILWAY_TOKEN,RW);assert.equal(vars.LUMEN_UPSTREAM_REPO,'highisabella52213/Lumen-Project-Final');assert.equal(vars.DATA_DIR,'/data');assert.equal(vars.LUMEN_REQUIRE_PERSISTENT_STORAGE,'1');assert.ok(vars.SECRET_KEY.length>=40);assert.ok(vars.PROXY_REPOSITORY_MANUAL_REFRESH_KEY.length>=24);
const html=mod.__test.htmlResponse();assert.match(html.headers.get('content-security-policy'),/frame-ancestors 'none'/);assert.match(html.headers.get('content-security-policy'),/fonts.googleapis.com/);assert.match(html.headers.get('cache-control'),/no-store/);const text=await html.text();assert.equal((text.match(/<input /g)||[]).length,2);assert.ok(!text.includes('__NONCE__'));assert.ok(text.includes('Vazirmatn')&&text.includes('fonts.googleapis.com'));
const serialized=JSON.stringify(result);assert.ok(!serialized.includes(GH)&&!serialized.includes(RW));
console.log('worker v19: github=OK railway=OK volume=OK domain=OK deploy=OK redaction=OK csp=OK');
