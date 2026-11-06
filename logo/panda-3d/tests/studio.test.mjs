import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { viewPosition, frameModel } from '../src/studio.js';

test('camera presets show genuinely different sides at a constant radius', () => {
  const front=viewPosition('front',8),side=viewPosition('side',8),back=viewPosition('back',8);
  assert.ok(front.z>7 && Math.abs(front.x)<0.001);
  assert.ok(side.x>7 && Math.abs(side.z)<0.001);
  assert.ok(back.z< -7);
  assert.ok(Math.abs(front.length()-side.length())<1e-8);
  for(const invalid of ['wrong','toString','constructor','__proto__']) assert.throws(()=>viewPosition(invalid),/Unknown view/);
});

test('framing fits portrait and landscape aspect ratios without cropping feet or ears',()=>{
  const bounds=new THREE.Box3(new THREE.Vector3(-1.5,0,-1),new THREE.Vector3(1.5,4.3,1));
  const wide=frameModel(bounds,1.8,35),portrait=frameModel(bounds,0.65,35);
  assert.ok(wide.distance>0 && portrait.distance>wide.distance);
  assert.ok(wide.target.equals(bounds.getCenter(new THREE.Vector3())));
  assert.throws(()=>frameModel(bounds,0,35),/aspect/);
});

test('studio uses current Three.js shadows and a horizon-free shadow receiver', async()=>{
  const { createStudio }=await import('../src/studio.js');
  const renderer={setPixelRatio(){},shadowMap:{}};
  const scene=createStudio(renderer,1);
  assert.equal(renderer.shadowMap.type,THREE.PCFShadowMap);
  const floor=scene.getObjectByName('studio floor');
  assert.ok(floor.material.isShadowMaterial,'floor should not create a lit-background horizon');
  assert.ok(floor.receiveShadow);
  scene.traverse(o=>{if(o.isMesh){o.geometry.dispose();o.material.dispose();}});
});
