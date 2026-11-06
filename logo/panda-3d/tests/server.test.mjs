import { test } from 'node:test';
import assert from 'node:assert/strict';
import { resolveRequest } from '../server.mjs';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));

test('viewer entry and local dependencies resolve within the project',()=>{
 assert.equal(resolveRequest('/').path,root+'index.html');
 assert.ok(resolveRequest('/src/model.js').path.endsWith('/src/model.js'));
 assert.ok(resolveRequest('/node_modules/three/build/three.module.js').path.startsWith(root));
});
test('server serves only two named read-only image references outside viewer',()=>{
 assert.ok(resolveRequest('/reference/panda.png').path.endsWith('/logo/LoomOS-panda-ink-clean.png'));
 assert.ok(resolveRequest('/reference/logo.svg').path.endsWith('/logo/Zhi-Jie-logo.svg'));
 assert.equal(resolveRequest('/reference/other.png'),null);
});
test('server rejects traversal, dotfiles and private/source-control paths',()=>{
 for(const p of ['/../.env','/%2e%2e/.env','/%2E%2E%2F.env','/.env','/.git/config','/%00','/src/../../README.md','/package-lock.json','/node_modules/../.env','/node_modules/playwright/package.json','/src/%ZZ']) {
  assert.equal(resolveRequest(p),null,p);
 }
});

test('live server enforces read-only HTTP behavior and returns proper asset MIME',async t=>{
 const {startServer}=await import('../server.mjs');
 const {once}=await import('node:events');
 const server=startServer(0);await once(server,'listening');
 t.after(()=>new Promise(resolve=>server.close(resolve)));
 const origin=`http://127.0.0.1:${server.address().port}`;
 const html=await fetch(origin+'/');assert.equal(html.status,200);assert.match(html.headers.get('content-type'),/text\/html/);
 const head=await fetch(origin+'/src/model.js',{method:'HEAD'});assert.equal(head.status,200);assert.equal(await head.text(),'');assert.match(head.headers.get('content-type'),/javascript/);
 const post=await fetch(origin+'/',{method:'POST'});assert.equal(post.status,405);
 for(const p of ['/.env','/.git/config','/src/%2e%2e%2f%2e%2e%2f.env','/reference/other.png','/package-lock.json']) assert.equal((await fetch(origin+p)).status,404,p);
});
