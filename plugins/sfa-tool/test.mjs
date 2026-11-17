import { test } from 'node:test';
import assert from 'node:assert/strict';
import { apply, argumentsFor } from './index.js';
const P='9080635F-0A64-4ECC-9969-58C9618B5072', C='809A5D77-13E0-4DF3-8792-9EA5F596DF22', F='FBA8FD55-2CE3-49E9-9C68-BEF7C44EACCB';
function harness() {
 let tool, mode='danger-full-access', calls=[], response=()=>({status:'ok'}), gate;
 const ctx={effect:f=>f(), tools:{register:d=>{tool=d;return ()=>{};}}, sandboxPolicy:{resolve:()=>({mode})}, workingDirectory:{ensure:async()=>'/tmp'}, subprocess:{resolveExecutable:async p=>p,spawn(spec){calls.push(spec);const argv=spec.argv; let d=response(argv); const output=JSON.stringify(d);return {done:gate ? gate.then(()=>({exitCode:0,signal:null})) : Promise.resolve({exitCode:0,signal:null}),collected:{stdout:{readFrom:()=>({text:output,lossy:false})},stderr:{readFrom:()=>({text:'',lossy:false})}}};}}};
 apply(ctx); const exec={agent:{id:'agent-a',session:{snapshotEvents:()=>[]}},signal:new AbortController().signal}; return {tool,exec,calls,setMode:m=>mode=m,setResponse:f=>response=f,setGate:p=>gate=p};
}
test('argument construction refuses arbitrary parameters and URL schemes',()=>{
 assert.deepEqual(argumentsFor({action:'connect',profile_id:P}),['connect','--profile',P]);
 assert.deepEqual(argumentsFor({action:'launch',profile_id:P,url:'https://example.com'},null),['launch',P,'--url','https://example.com']);
 assert.throws(()=>argumentsFor({action:'launch',profile_id:P,url:'file:///tmp/a'},null),/http/);
 assert.deepEqual(argumentsFor({action:'profiles',profile_id:'',url:'',frame:'',x:0,y:0,text:'',key:''}),['profile','list']);
 assert.throws(()=>argumentsFor({action:'profiles',url:'https://example.com'},C),/Unexpected/);
 assert.throws(()=>argumentsFor({action:'navigate',url:'file:///etc/passwd'},C),/http/);
 assert.throws(()=>argumentsFor({action:'observe',extra:'x'},C),/Unexpected/);
 assert.throws(()=>argumentsFor({action:'click',frame:F,x:-1,y:1},C),/coordinates/);
 assert.deepEqual(argumentsFor({action:'type',frame:F,text:'secret'},C),['type','--connection',C,'--frame',F,'--text-stdin']);
});
test('restricted session cannot spawn',async()=>{const h=harness();h.setMode('workspace-write');await assert.rejects(h.tool.execute({action:'profiles'},h.exec),/danger-full-access/);assert.equal(h.calls.length,0);});
test('frames are forwarded; release requires all four confirmations',async()=>{
 const h=harness(); h.setResponse(argv=>argv.includes('connect')?{status:'ok',connection:C}:argv.includes('observe')?{status:'ok',frame:F,screenshotPath:'/tmp/example.png'}:argv.includes('release')?{status:'ok',controlReleased:{inputReleased:true,artifactsCleaned:true,browserRetained:true,manualInteractionEnabled:true}}:{status:'ok'});
 await h.tool.execute({action:'connect',profile_id:P},h.exec); await h.tool.execute({action:'observe'},h.exec);
 await h.tool.execute({action:'click',frame:P,x:1,y:1},h.exec);
 await h.tool.execute({action:'click',frame:F,x:1,y:1},h.exec);
 await h.tool.execute({action:'click',frame:F,x:1,y:1},h.exec);
 const r=await h.tool.execute({action:'release'},h.exec); assert.equal(r.releaseVerified,true);
});
test('backend error is returned and later explicit commands are dispatched',async()=>{
 const h=harness();h.setResponse(argv=>argv.includes('connect')?{status:'ok',connection:C}:argv.includes('navigate')?{status:'error',error:'INDETERMINATE_RESULT'}:{status:'ok'});
 await h.tool.execute({action:'connect',profile_id:P},h.exec);
 const r=await h.tool.execute({action:'navigate',url:'https://example.com'},h.exec);assert.equal(r.data.error,'INDETERMINATE_RESULT');
 const n=h.calls.length;await h.tool.execute({action:'release'},h.exec);assert.equal(h.calls.length,n+1);
 await h.tool.execute({action:'authorize'},h.exec);assert.equal(h.calls.length,n+2);
});
test('concurrent calls cannot create competing operations',async()=>{
 const h=harness();let resolve;h.setGate(new Promise(r=>resolve=r)); const p=h.tool.execute({action:'profiles'},h.exec);await new Promise(r=>setImmediate(r));await assert.rejects(h.tool.execute({action:'authorize'},h.exec),/in progress/);resolve();await p;
});
