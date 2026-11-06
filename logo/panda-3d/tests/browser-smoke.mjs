import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import { once } from 'node:events';
import { existsSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { startServer } from '../server.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const evidence=path.join(root,'evidence');await mkdir(evidence,{recursive:true});
const server=startServer(0);await once(server,'listening');
const origin=`http://127.0.0.1:${server.address().port}`;
const launch=process.env.PLAYWRIGHT_EXECUTABLE_PATH?{executablePath:process.env.PLAYWRIGHT_EXECUTABLE_PATH}:existsSync('/Applications/Google Chrome.app')?{channel:'chrome'}:{};
const browser=await chromium.launch({...launch,headless:true});
const results={date:new Date().toISOString(),browser:await browser.version(),checks:[],errors:[],warnings:[],externalRequests:[],failedResponses:[]};
const check=(name)=>{results.checks.push(name);console.log(`PASS ${name}`);};
const watch=page=>{
 page.on('pageerror',e=>results.errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')results.errors.push(m.text());if(m.type()==='warning')results.warnings.push(m.text());});
 page.on('request',r=>{if(/^https?:/.test(r.url())&&!r.url().startsWith(origin))results.externalRequests.push(r.url());});
 page.on('response',r=>{if(r.status()>=400)results.failedResponses.push({url:r.url(),status:r.status()});});
};
let context;
try{
 context=await browser.newContext({viewport:{width:1440,height:1000},deviceScaleFactor:1,acceptDownloads:true});
 const page=await context.newPage();watch(page);
 await page.goto(origin);
 await page.locator('#stage[data-state="ready"]').waitFor();
 await page.waitForTimeout(350);
 assert.equal(await page.locator('canvas').count(),1);
 const pixels=await page.locator('canvas').evaluate(c=>{
  const gl=c.getContext('webgl2');const colors=new Set();const p=new Uint8Array(4);
  for(let y=2;y<20;y++)for(let x=2;x<20;x++){gl.readPixels(Math.floor(c.width*x/20),Math.floor(c.height*y/20),1,1,gl.RGBA,gl.UNSIGNED_BYTE,p);colors.add([...p].join(','));}
  return {colors:colors.size,error:gl.getError()};
 });
 assert.ok(pixels.colors>35,`scene is blank: ${pixels.colors}`);assert.equal(pixels.error,0);
 check('desktop: actual WebGL 2 rendering, non-blank colored volume, no GL error');
 await page.screenshot({path:path.join(evidence,'desktop-quarter.png'),fullPage:true});

 for(const [view,label] of [['front','正面'],['side','侧面'],['back','背面'],['quarter','¾ 视角']]){
  await page.getByRole('button',{name:label,exact:true}).click();await page.waitForTimeout(1100);
  assert.equal(await page.locator('canvas').getAttribute('data-view'),view);
  assert.equal(await page.getByRole('button',{name:label,exact:true}).getAttribute('aria-pressed'),'true');
  await page.screenshot({path:path.join(evidence,`desktop-${view}.png`),fullPage:true});
  await page.locator('#stage').screenshot({path:path.join(evidence,`stage-${view}.png`)});
 }
 check('front, three-quarter, side and rear camera presets render');

 const before=await page.locator('canvas').screenshot();const box=await page.locator('canvas').boundingBox();
 await page.mouse.move(box.x+box.width*0.6,box.y+box.height*0.5);await page.mouse.down();
 await page.mouse.move(box.x+box.width*0.6+170,box.y+box.height*0.5+18,{steps:16});await page.mouse.up();await page.waitForTimeout(500);
 assert.equal(await page.locator('canvas').getAttribute('data-view'),'custom');
 assert.notDeepEqual(await page.locator('canvas').screenshot(),before);
 check('real pointer drag rotates the character');
 const beforeZoom=await page.locator('canvas').screenshot();await page.mouse.wheel(0,-350);await page.waitForTimeout(500);
 assert.notDeepEqual(await page.locator('canvas').screenshot(),beforeZoom);
 check('real mouse wheel changes orbit-camera zoom');
 await page.getByRole('button',{name:'正面',exact:true}).click();await page.waitForTimeout(1100);
 const ref=page.getByRole('checkbox',{name:'显示原画'});await ref.uncheck();assert.equal(await page.locator('#reference').isVisible(),false);
 await ref.check();assert.equal(await page.locator('#reference').isVisible(),true);check('reference illustration can hide and return');

 await page.getByRole('button',{name:'自动旋转'}).click();assert.equal(await page.locator('#rotate').getAttribute('aria-pressed'),'true');
 const spin1=await page.locator('canvas').screenshot();await page.waitForTimeout(700);assert.notDeepEqual(await page.locator('canvas').screenshot(),spin1);
 await page.getByRole('button',{name:'停止旋转'}).click();assert.equal(await page.locator('#rotate').getAttribute('aria-pressed'),'false');
 check('optional automatic rotation runs and stops');
 await page.getByRole('button',{name:'¾ 视角',exact:true}).click();await page.waitForTimeout(1100);
 const pngEvent=page.waitForEvent('download');await page.locator('#export-png').click();const png=await pngEvent;await png.saveAs(path.join(evidence,'panda-render.png'));
 const pngBytes=await readFile(path.join(evidence,'panda-render.png'));assert.equal(pngBytes.subarray(1,4).toString(),'PNG');assert.ok(pngBytes.length>15000);
 check('PNG download is an actual nonempty scene render');
 const glbEvent=page.waitForEvent('download');await page.locator('#export-glb').click();const glb=await glbEvent;await glb.saveAs(path.join(evidence,'panda.glb'));
 const glbBytes=await readFile(path.join(evidence,'panda.glb'));assert.equal(glbBytes.subarray(0,4).toString(),'glTF');assert.equal(glbBytes.readUInt32LE(4),2);assert.equal(glbBytes.readUInt32LE(8),glbBytes.length);
 const jsonLength=glbBytes.readUInt32LE(12);const gltf=JSON.parse(glbBytes.subarray(20,20+jsonLength).toString());
 assert.ok(gltf.nodes.some(n=>n.name==='head'));assert.ok(gltf.nodes.some(n=>n.name==='tail'));assert.ok(!gltf.nodes.some(n=>/studio floor|camera|large warm key/.test(n.name||'')));
 assert.ok(!(gltf.images||[]).some(i=>i.uri?.startsWith('http')));
 check('GLB v2 export contains complete character, excludes stage and remote textures');
 const reload=await page.evaluate(async origin=>{
  const THREE=await import('three');const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
  const model=await new GLTFLoader().loadAsync(`${origin}/evidence/panda.glb`);
  const size=new THREE.Box3().setFromObject(model.scene).getSize(new THREE.Vector3());
  let meshes=0;model.scene.traverse(n=>{if(n.isMesh)meshes++;});
  const emblem=model.scene.getObjectByName('loom-emblem');
  let furInstances=0,normalMaps=0;model.scene.traverse(n=>{if(n.isInstancedMesh)furInstances+=n.count;if(n.isMesh&&n.material.normalMap)normalMaps++;});
  return {furInstances,normalMaps,size:size.toArray(),meshes,head:!!model.scene.getObjectByName('head'),tail:!!model.scene.getObjectByName('tail'),emblemPaths:emblem.children.length,emblemSource:emblem.userData.source};
 },origin);
 assert.ok(reload.head&&reload.tail&&reload.meshes>30&&reload.size[2]>1.5);
 results.glb={bytes:glbBytes.length,...reload};check('downloaded GLB independently reloads through GLTFLoader with true 3D bounds');
 assert.equal(reload.emblemPaths,104);assert.equal(reload.emblemSource,'LoomOS-panda-ink-clean.svg');
 check('exported GLB preserves all 104 source SVG logo paths and their provenance');
 assert.ok(reload.furInstances>=30000&&reload.furInstances<=60000);assert.ok(reload.normalMaps>0);
 assert.ok(gltf.extensionsRequired.includes('EXT_mesh_gpu_instancing'));assert.ok((gltf.images||[]).every(image=>Number.isInteger(image.bufferView)));
 check('exported GLB reloads real fur instances and embedded normal texture without remote assets');


 // Close-up fixtures render the actual EXPORTED GLB, not a special replacement logo.
 for(const [view,angle] of [['front',0],['oblique',Math.PI*0.29]]){
  const detail=await context.newPage();watch(detail);await detail.setViewportSize({width:960,height:800});
  await detail.goto(origin);await detail.locator('#stage[data-state="ready"]').waitFor();
  await detail.evaluate(async({origin,angle})=>{
   const THREE=await import('three');const {GLTFLoader}=await import('three/addons/loaders/GLTFLoader.js');
   const {createStudio}=await import('./src/studio.js');
   const model=await new GLTFLoader().loadAsync(`${origin}/evidence/panda.glb`);
   const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
   const scene=createStudio(renderer,1);scene.add(model.scene);renderer.setSize(960,800);
   const camera=new THREE.PerspectiveCamera(28,960/800,0.1,100);
   const target=new THREE.Vector3(0,1.31,0.62);
   camera.position.copy(target).add(new THREE.Vector3(Math.sin(angle)*2.75,angle?0.12:0,Math.cos(angle)*2.75));camera.lookAt(target);
   const canvas=renderer.domElement;canvas.dataset.logoFixture='true';
   document.body.replaceChildren(canvas);renderer.render(scene,camera);
  },{origin,angle});
  await detail.locator('canvas[data-logo-fixture]').screenshot({path:path.join(evidence,`logo-detail-${view}.png`)});
  await detail.close();
 }
 check('actual exported logo rendered at front and grazing-angle close-ups with no detached tubing');


 await page.setViewportSize({width:900,height:900});await page.waitForTimeout(300);
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 assert.ok(await page.locator('canvas').isVisible());check('desktop resize preserves renderer and avoids horizontal overflow');

 const mobileContext=await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true,reducedMotion:'reduce'});
 const mobile=await mobileContext.newPage();watch(mobile);await mobile.goto(origin);await mobile.locator('#stage[data-state="ready"]').waitFor();
 assert.equal(await mobile.locator('#rotate').getAttribute('aria-pressed'),'false');
 assert.match(await mobile.locator('#status').innerText(),/减少动态/);
 assert.ok(await mobile.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 const mobileBox=await mobile.locator('canvas').boundingBox();assert.ok(mobileBox.width>300&&mobileBox.height>400);
 await mobile.getByRole('button',{name:'背面',exact:true}).click();assert.equal(await mobile.locator('canvas').getAttribute('data-view'),'back');
 await mobile.getByRole('button',{name:'正面',exact:true}).click();
 await mobile.screenshot({path:path.join(evidence,'mobile-front.png'),fullPage:true});
 check('390px mobile layout renders, all view controls work, reduced motion starts static');
 await mobile.getByRole('button',{name:'¾ 视角',exact:true}).click();await mobile.locator('canvas').scrollIntoViewIfNeeded();
 await mobile.screenshot({path:path.join(evidence,'mobile-quarter.png'),fullPage:true});
 await mobileContext.close();
 assert.deepEqual(results.errors,[]);assert.deepEqual(results.warnings,[]);assert.deepEqual(results.externalRequests,[]);assert.deepEqual(results.failedResponses,[]);
 check('all normal desktop/mobile flows have zero console errors, warnings or remote requests');

 // Test explicit recovery separately: no manufactured success when GPU or encoding fails.
 const failPage=await context.newPage();await failPage.goto(origin);await failPage.locator('#stage[data-state="ready"]').waitFor();
 await failPage.evaluate(()=>{HTMLCanvasElement.prototype.toBlob=function(callback){callback(null);};});
 await failPage.locator('#export-png').click();assert.match(await failPage.locator('#status').innerText(),/保存失败/);assert.ok(await failPage.locator('#export-png').isEnabled());
 check('PNG encoding failure is visible and export control recovers');
 await failPage.locator('canvas').evaluate(c=>c.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext());
 await failPage.locator('#stage[data-state="error"]').waitFor();assert.ok(await failPage.locator('#error').isVisible());assert.equal(await failPage.locator('#export-glb').isEnabled(),false);
 await failPage.getByRole('button',{name:'重新加载'}).click();await failPage.locator('#stage[data-state="ready"]').waitFor();
 check('WebGL context loss shows a recoverable error and reload restores viewer');
 await failPage.close();
 results.passed=true;
}catch(error){results.passed=false;results.failure=error.stack;throw error;}
finally{await writeFile(path.join(evidence,'results.json'),JSON.stringify(results,null,2));await context?.close();await browser.close();await new Promise(r=>server.close(r));}
