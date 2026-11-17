import { test } from 'node:test';
import assert from 'node:assert/strict';
import { apply, restoreControl } from './index.js';
const P='9080635F-0A64-4ECC-9969-58C9618B5072', C='809A5D77-13E0-4DF3-8792-9EA5F596DF22';
function setup(missing, launchFails=false) {
 let tool; let count=0;
 const ctx={effect:f=>f(),tools:{register:d=>{tool=d;return ()=>{};}},sandboxPolicy:{resolve:()=>({mode:'danger-full-access'})},workingDirectory:{ensure:async()=>'/tmp'},subprocess:{resolveExecutable:async p=>p,spawn(spec){count++; const a=spec.argv; const d=a.includes('connect')?{status:'ok',connection:C}:a.includes('release')?{status:'ok',controlReleased:{inputReleased:true,artifactsCleaned:true,browserRetained:true,manualInteractionEnabled:!missing}}:{status:'ok'};return {done:Promise.resolve({exitCode:a.includes('launch')&&launchFails?1:0,signal:null}),collected:{stdout:{readFrom:()=>({text:JSON.stringify(d),lossy:false})},stderr:{readFrom:()=>({text:'',lossy:false})}}};}}};
 apply(ctx);const exec={agent:{id:'owner',session:{snapshotEvents:()=>[]}},signal:new AbortController().signal};return {tool,exec,count:()=>count};
}
test('unpaired historical call alone is not connection ownership',()=>{
 const events=[{type:'tool/call',data:{name:'sfa',callId:'old',arguments:'{"action":"connect"}'}}];
 assert.equal(restoreControl({snapshotEvents:()=>events},'current'),null);
 assert.equal(restoreControl({},'current'),null);
});
test('missing release proof is reported and does not stop daemon or block next call',async()=>{
 const h=setup(true);await h.tool.execute({action:'connect',profile_id:P},h.exec);
 const n=h.count();const r=await h.tool.execute({action:'release'},h.exec);assert.equal(r.releaseVerified,false);assert.equal(h.count(),n+1);
 await h.tool.execute({action:'state'},h.exec);assert.equal(h.count(),n+2);
});
test('another agent cannot use an owned connection',async()=>{
 const h=setup(false);await h.tool.execute({action:'connect',profile_id:P},h.exec);const e={...h.exec,agent:{id:'different',session:{snapshotEvents:()=>[]}}};await assert.rejects(h.tool.execute({action:'observe'},e),/No connection/);
});
test('successful explicit launch permits subsequent connect',async()=>{
 const h=setup(false);const l=await h.tool.execute({action:'launch',profile_id:P,url:'https://example.com'},h.exec);assert.equal(l.exitCode,0);const c=await h.tool.execute({action:'connect',profile_id:P},h.exec);assert.equal(c.data.connection,C);
});
test('failed launch is not repeated automatically',async()=>{
 const h=setup(false,true);const l=await h.tool.execute({action:'launch',profile_id:P},h.exec);assert.equal(l.exitCode,1);const count=h.count();assert.equal(count,1);await h.tool.execute({action:'launch',profile_id:P},h.exec);assert.equal(h.count(),count+1);
});
