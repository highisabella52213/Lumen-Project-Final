#!/usr/bin/env node
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';

const source=await readFile(new URL('../pages.py',import.meta.url),'utf8');
const start=source.indexOf('const apiDiagnostics=');
const end=source.indexOf('/* ===== Protected installer',start);
assert.ok(start>0&&end>start,'dashboard request state machine not found');
const block=source.slice(start,end)+"\nglobalThis.__apiRequest=apiRequest;globalThis.__checkAuth=checkAuth;globalThis.__diag=apiDiagnostics;";
function makeContext({diagnostics=false}={}){
 const redirects=[],store=new Map();if(diagnostics)store.set('code-dashboard-forensic-enabled','1');
 const context={console,AbortController,URL,URLSearchParams,Response,Blob,
  setTimeout:(fn,ms)=>setTimeout(fn,ms===8000||ms===10000?0:ms),clearTimeout,
  performance:{now:()=>Date.now(),getEntriesByType:()=>[]},
  location:{search:'',origin:'https://test.invalid',pathname:'/dashboard',replace:v=>redirects.push(['replace',v]),assign:v=>redirects.push(['assign',v])},
  document:{getElementById:()=>({addEventListener(){}}),addEventListener(){},visibilityState:'visible'},
  sessionStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,String(v))},
  addEventListener(){},toast(){},fetch:async()=>new Response('{}',{status:200}),
 };
 context.window=context;context.__redirects=redirects;vm.createContext(context);vm.runInContext(block,context);return context;
}
const c=makeContext();let calls=0;
c.fetch=async()=>{calls++;throw new TypeError('Network Error')};
await assert.rejects(()=>c.__apiRequest('/api/update/status'),e=>e.kind==='NETWORK_ERROR');assert.equal(calls,3);assert.deepEqual(c.__redirects,[],'feature network error must not navigate');
c.__redirects.length=0;calls=0;c.fetch=(_url,opts)=>new Promise((_resolve,reject)=>{calls++;opts.signal.addEventListener('abort',()=>reject(Object.assign(new Error('aborted'),{name:'AbortError'}))) });
await assert.rejects(()=>c.__apiRequest('/api/update/status',{}, {retries:0,timeoutMs:1}),e=>e.kind==='NETWORK_TIMEOUT');assert.equal(calls,1);assert.deepEqual(c.__redirects,[],'feature timeout must not navigate');
for(const path of ['/api/update/status','/api/proxy-catalog','/api/subs','/stats']){
 c.__redirects.length=0;calls=0;c.fetch=async()=>{calls++;return new Response('{}',{status:401})};
 const r=await c.__apiRequest(path,{}, {retries:0});assert.equal(r.status,401);assert.equal(calls,1);assert.deepEqual(c.__redirects,[],`${path} 401 must not navigate`);
}
c.__redirects.length=0;calls=0;c.fetch=async()=>{calls++;return new Response('{}',{status:500})};
const failure=await c.__apiRequest('/api/update/status');assert.equal(failure.status,500);assert.equal(calls,3);assert.deepEqual(c.__redirects,[],'feature 500 must not navigate');
c.__redirects.length=0;c.window.__codeAuthRedirecting=false;c.fetch=async()=>new Response('{}',{status:401});
await assert.rejects(()=>c.__apiRequest('/api/me',{}, {authoritativeAuth:true,retries:0}),e=>e.kind==='AUTH_EXPIRED');assert.deepEqual(c.__redirects,[['replace','/login']]);
c.__redirects.length=0;c.window.__codeAuthRedirecting=false;c.fetch=async()=>new Response('{"authenticated":true}',{status:200});assert.equal(await c.__checkAuth(),true);assert.deepEqual(c.__redirects,[],'authenticated /api/me must stay open');
const d=makeContext({diagnostics:true});assert.equal(d.__codeDashboardDiagnostics.enabled,true);assert.ok(d.__codeDashboardDiagnostics.events.some(e=>e.kind==='DOCUMENT_BOOT'),'diagnostics ON records boot');
assert.equal(c.__codeDashboardDiagnostics.enabled,false,'diagnostics OFF remains optional');
assert.ok(!source.includes('location.reload()'));assert.ok(source.includes('authoritativeAuth:true'));assert.ok(source.includes('FEATURE_UNAUTHORIZED'));assert.ok(source.includes('function forensicNavigate('),'diagnostic navigation compatibility function must remain defined');
console.log('dashboard loop regression: feature-401/500/network=stay authoritative-api-me-401=one-redirect authenticated=true=stay diagnostics=on+off OK');
