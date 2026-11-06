import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { createPanda, disposePanda, headSurfaceZ, bodySurfaceZ } from '../src/model.js';

// Tests are executable scene-graph contracts, not screenshots of a flat image.
test('panda is genuinely volumetric and has the recognizable mascot parts', () => {
  const panda = createPanda();
  assert.equal(panda.name, 'LoomOS Panda');
  for (const name of ['head', 'torso', 'ear-left', 'ear-right', 'arm-left', 'arm-right', 'foot-left', 'foot-right', 'tail', 'tuft', 'belly', 'eye-patch-left', 'eye-patch-right', 'eye-left', 'eye-right', 'nose', 'smile-left', 'smile-right', 'loom-emblem']) {
    assert.ok(panda.getObjectByName(name), name);
  }
  const bounds = new THREE.Box3().setFromObject(panda);
  const size = bounds.getSize(new THREE.Vector3());
  assert.ok(size.y > 3.5 && size.y < 4.8, `height ${size.y}`);
  assert.ok(size.x > 2 && size.x < 3.5, `width ${size.x}`);
  assert.ok(size.z > 1.5, `depth ${size.z}`);
  assert.ok(bounds.min.y >= -0.03, `feet below floor: ${bounds.min.y}`);
  disposePanda(panda);
});

test('every geometry and transform is finite and materials need no external assets', () => {
  const panda = createPanda(); let count = 0;
  panda.traverse(o => {
    if (!o.isMesh) return;
    count++;
    const p = o.geometry.getAttribute('position');
    assert.ok(p && p.count > 0, o.name);
    assert.ok([...p.array].every(Number.isFinite), o.name);
    const normals=o.geometry.getAttribute('normal');
    assert.ok(normals, o.name);
    for(let i=0;i<normals.count;i++){
      const length=normals.getX(i)**2+normals.getY(i)**2+normals.getZ(i)**2;
      assert.ok(Math.abs(length-1)<0.0005, `${o.name}: non-unit normal at ${i}`);
    }
    assert.ok(o.scale.toArray().every(v => Number.isFinite(v) && v > 0), o.name);
    assert.ok(o.material.isMeshStandardMaterial || o.material.isMeshPhysicalMaterial, o.name);
    for (const key of ['map', 'normalMap', 'bumpMap']) {
      const texture=o.material[key];
      assert.ok(texture===null||(texture.isDataTexture&&texture.image.data instanceof Uint8Array),`${o.name}.${key}: external image`);
    }
  });
  assert.ok(count > 30 && count < 160, `mesh count ${count}`);
  disposePanda(panda);
});

test('eye patches and belly actually follow the curved surface, not flat billboards', () => {
  const panda = createPanda();
  for (const [name,surface] of [['eye-patch-left',headSurfaceZ], ['eye-patch-right',headSurfaceZ], ['belly',bodySurfaceZ]]) {
    const p = panda.getObjectByName(name).geometry.getAttribute('position');
    let zmin=Infinity, zmax=-Infinity;
    for(let i=0;i<p.count;i++) {
      const x=p.getX(i),y=p.getY(i),z=p.getZ(i);
      assert.ok(Math.abs(z-surface(x,y)) < 0.025, `${name}: not attached`);
      zmin=Math.min(zmin,z);zmax=Math.max(zmax,z);
    }
    assert.ok(zmax-zmin > 0.04, `${name}: flat`);
  }
  disposePanda(panda);
});

test('disposal releases each shared geometry and material exactly once', () => {
  const panda=createPanda();const geometries=new Set(),materials=new Set();
  panda.traverse(o=>{if(o.isMesh){geometries.add(o.geometry);materials.add(o.material);}});
  let gd=0,md=0;
  geometries.forEach(g=>g.addEventListener('dispose',()=>gd++));
  materials.forEach(m=>m.addEventListener('dispose',()=>md++));
  disposePanda(panda);
  assert.equal(gd,geometries.size);assert.equal(md,materials.size);
});

test('belly emblem follows the source SVG instead of replacing detail with smooth tubes',async()=>{
  const {readFile}=await import('node:fs/promises');const {createHash}=await import('node:crypto');
  const source=await readFile(new URL('../../LoomOS-panda-ink-clean.svg',import.meta.url));
  const panda=createPanda(),emblem=panda.getObjectByName('loom-emblem');
  assert.equal(emblem.userData.source,'LoomOS-panda-ink-clean.svg');
  assert.equal(emblem.userData.sourceSha256,createHash('sha256').update(source).digest('hex'));
  const patches=emblem.children.filter(o=>o.isMesh);
  assert.ok(patches.length>=100,'preserve original painted paths, including chip pins and pigment detail');
  assert.ok(patches.every(o=>o.geometry.type!=='TubeGeometry'),'no simplified replacement tubing');
  assert.ok(new Set(patches.map(o=>o.material.color.getHex())).size>35,'retain source color variation');
  disposePanda(panda);
});

test('all logo details sit tightly on the belly, with no floating overpass or posts',()=>{
  const panda=createPanda();panda.updateMatrixWorld(true);
  const emblem=panda.getObjectByName('loom-emblem'),v=new THREE.Vector3();
  let min=Infinity,max=-Infinity;
  emblem.traverse(o=>{
    if(!o.isMesh)return;const p=o.geometry.getAttribute('position');
    for(let i=0;i<p.count;i++){
      v.fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld);
      const gap=v.z-bodySurfaceZ(v.x,v.y);
      min=Math.min(min,gap);max=Math.max(max,gap);
    }
  });
  assert.ok(min>=0.009-1e-5,`logo sinks into the belly: ${min}`);
  assert.ok(max<=0.022,`logo has floating parts: ${max}`);
  disposePanda(panda);
});

test('all four crossings preserve the source over-under order without open gaps',()=>{
  const panda=createPanda(),emblem=panda.getObjectByName('loom-emblem');panda.updateMatrixWorld(true);
  const mapping=emblem.userData.svgToModel;
  assert.ok(mapping,'emblem must retain source-coordinate mapping for regression checks');
  for(const [x,y,expected] of [[463,642,'gold'],[562,642,'teal'],[463,741,'teal'],[562,741,'gold']]){
    const px=(x-mapping.origin[0])*mapping.scale+mapping.center[0];
    const py=(mapping.origin[1]-y)*mapping.scale+mapping.center[1];
    const ray=new THREE.Raycaster(new THREE.Vector3(px,py,2),new THREE.Vector3(0,0,-1));
    const hits=ray.intersectObject(emblem,true);assert.ok(hits.length,`open crossing at ${x},${y}`);
    const color=hits[0].object.material.color;
    if(expected==='gold')assert.ok(color.r>color.g&&color.g>color.b,`gold must cover teal at ${x},${y}`);
    else assert.ok(color.g>color.r&&color.b>color.r,`teal must cover gold at ${x},${y}`);
  }
  disposePanda(panda);
});

test('logo triangle interiors remain on the belly without oversubdividing the SVG',()=>{
  const panda=createPanda(),emblem=panda.getObjectByName('loom-emblem');let vertices=0;
  emblem.traverse(o=>{
    if(!o.isMesh)return;const p=o.geometry.getAttribute('position');vertices+=p.count;
    for(let i=0;i<p.count;i+=3){
      const x=(p.getX(i)+p.getX(i+1)+p.getX(i+2))/3;
      const y=(p.getY(i)+p.getY(i+1)+p.getY(i+2))/3;
      const z=(p.getZ(i)+p.getZ(i+1)+p.getZ(i+2))/3;
      assert.ok(z-bodySurfaceZ(x,y)>=0.009,'large triangle cuts into belly');
    }
  });
  assert.ok(vertices<200000,`unnecessary logo subdivision: ${vertices} vertices`);
  disposePanda(panda);
});

test('head and torso have rounded front-to-back volume, not flattened silhouettes',()=>{
  const panda=createPanda();
  const head=new THREE.Box3().setFromObject(panda.getObjectByName('head')).getSize(new THREE.Vector3());
  const torso=new THREE.Box3().setFromObject(panda.getObjectByName('torso')).getSize(new THREE.Vector3());
  assert.ok(head.z/head.x>=0.90,`head depth/width ${head.z/head.x}`);
  assert.ok(torso.z/torso.x>=0.96,`torso depth/width ${torso.z/torso.x}`);
  assert.ok(head.z>=2.20&&torso.z>=2.0,'real part geometry must grow, not just a camera change');
  assert.ok(headSurfaceZ(0,2.78)-headSurfaceZ(0.5,2.78)>0.18,'side profile needs a forward muzzle');
  disposePanda(panda);
});

test('short fur is real instanced geometry and fine normal detail is generated locally',()=>{
  const panda=createPanda(),fur=panda.getObjectByName('short-fur');
  assert.ok(fur,'short-fur geometry missing');
  let count=0;
  fur.traverse(o=>{if(o.isInstancedMesh){count+=o.count;assert.ok([...o.instanceMatrix.array].every(Number.isFinite));}});
  assert.ok(count>=30000&&count<=60000,`fur strand budget ${count}`);
  const normal=panda.getObjectByName('head').material.normalMap;
  assert.ok(normal?.isDataTexture&&normal.image.data instanceof Uint8Array,'fur microdetail must not require network images');
  disposePanda(panda);
});

test('procedural normal maps have explicit UV tangents for portable GLB export',()=>{
  const panda=createPanda();
  panda.traverse(o=>{if(o.isMesh&&o.material.normalMap){assert.ok(o.geometry.getAttribute('uv'),o.name);assert.ok(o.geometry.getAttribute('tangent'),`${o.name}: missing tangent frame`);assert.equal(o.material.normalScale.x,o.material.normalScale.y);}});
  disposePanda(panda);
});

test('fur texture and instanced GPU buffers are released with the character',()=>{
  const panda=createPanda(),textures=new Set(),instances=[];
  panda.traverse(o=>{if(o.isMesh&&o.material.normalMap)textures.add(o.material.normalMap);if(o.isInstancedMesh)instances.push(o);});
  let td=0,id=0;textures.forEach(t=>t.addEventListener('dispose',()=>td++));instances.forEach(o=>o.addEventListener('dispose',()=>id++));
  assert.ok(textures.size>0&&instances.length===2);disposePanda(panda);assert.equal(td,textures.size);assert.equal(id,instances.length);
});

test('charcoal pelt stays matte rather than using a bright frosted sheen',()=>{
  const panda=createPanda(),pelt=panda.getObjectByName('torso').material;
  assert.ok(pelt.roughness>=0.9);assert.ok(pelt.sheen<=0.45);disposePanda(panda);
});
