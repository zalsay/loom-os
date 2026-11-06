import * as THREE from 'three';
import {GLTFLoader} from '/addons/loaders/GLTFLoader.js';
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(720,1280);renderer.setPixelRatio(1);renderer.setClearColor('#203938');renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;document.body.prepend(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#203938');scene.fog=new THREE.Fog('#203938',13,25);
const cam=new THREE.PerspectiveCamera(40,720/1280,.1,100);cam.position.set(5.5,5.1,14);cam.lookAt(-.5,1.7,-.3);
scene.add(new THREE.HemisphereLight(0xffead0,0x385050,2));const lamp=new THREE.DirectionalLight('#ffe3b6',3);lamp.position.set(-3,9,6);lamp.castShadow=true;lamp.shadow.mapSize.set(1024,1024);Object.assign(lamp.shadow.camera,{left:-9,right:9,top:9,bottom:-9});scene.add(lamp);
const material=(color,roughness=.85)=>new THREE.MeshStandardMaterial({color,roughness});const wood=material('#b58c64'), pale=material('#e8d4b2'), dark=material('#263e3c'), metal=material('#9caeab',.48), black=material('#152521'), screen=material('#142c29'), coral=material('#df9170');
function box(w,h,d,m,x,y,z,rot=0,parent=scene){const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);o.position.set(x,y,z);o.rotation.y=rot;o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
function ball(r,m,x,y,z,s=[1,1,1],parent=scene){const o=new THREE.Mesh(new THREE.SphereGeometry(r,24,16),m);o.scale.set(...s);o.position.set(x,y,z);o.castShadow=true;parent.add(o);return o;}
box(18,.16,18,material('#58716a'),0,-.1,0);box(10,7,.12,material('#284643'),0,3,-5);box(7,.25,3.7,wood,0,2,-.55);for(const x of [-3,3])for(const z of [-1.8,.8])box(.22,1.95,.22,dark,x,.97,z);
// MacBook-like laptop: modeled as an illustration, not actual footage.
box(2.05,.10,1.35,metal,.15,2.19,-.35);box(2.05,1.35,.09,metal,.15,2.88,-1.03);box(1.87,1.14,.025,screen,.15,2.89,-.973);for(let y=0;y<5;y++){box(.85-y*.06,.018,.01,teal(),-.18,3.22-y*.18,-.954);}function teal(){return material('#67b6a6')}
for(let y=0;y<4;y++)for(let x=0;x<10;x++)box(.13,.013,.10,dark,-.65+x*.18,2.25,-.05+y*.20);
// Device silhouette; screen is deliberately blank, no implication about device state.
box(.95,.68,.35,pale,2.07,2.55,-.54);box(.53,.49,.03,black,2.17,2.56,-.345);ball(.105,coral,1.77,2.57,-.32,[1,1,.3]);box(.58,.1,.4,metal,2.07,2.15,-.55);
// Chair and panda positioned facing the laptop; the mesh is the supplied model.
box(2,.18,1.8,wood,-.65,1.05,2.4);box(2,1.9,.18,wood,-.65,1.65,3.1);for(const x of [-1.4,.1])for(const z of [1.8,3])box(.14,1.03,.14,dark,x,.5,z);
const gltf=await new GLTFLoader().loadAsync('/panda.glb');const panda=gltf.scene;panda.scale.setScalar(.58);panda.position.set(-.65,1.12,2.30);panda.rotation.y=Math.PI+.18;scene.add(panda);panda.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}if(/^(eye|pupil)-(left|right)$/.test(o.name))o.material=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.55});});
// Book and mug add depth without presenting them as evidence.
box(1.2,.10,.85,pale,-2.3,2.18,-.5,.14);const cup=new THREE.Mesh(new THREE.CylinderGeometry(.22,.19,.45,32),material('#d9bd8b'));cup.position.set(-2.4,2.43,.30);cup.castShadow=true;scene.add(cup);
// Paws illustrate typing; no device interaction is implied.
const paws=[ball(.18,dark,-.50,2.29,.20,[1,.48,1.2]),ball(.18,dark,.12,2.29,.20,[1,.48,1.2])];
function arm(a,b){const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b),v=end.clone().sub(start);const mesh=new THREE.Mesh(new THREE.CapsuleGeometry(.12,Math.max(.01,v.length()-.24),4,12),dark);mesh.position.copy(start).add(end).multiplyScalar(.5);mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),v.normalize());mesh.castShadow=true;scene.add(mesh);}
arm([-1.0,2.0,1.55],[-.50,2.29,.28]);arm([-.25,2.0,1.55],[.12,2.29,.28]);
const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};window.setSceneTime=t=>{const p=ease(t/8);cam.position.x=5.5-.3*p;cam.position.z=14-.35*p;cam.lookAt(-.5,1.7,-.3);panda.rotation.y=Math.PI+.18+Math.sin(t*1.3)*.025;panda.position.y=1.12+Math.sin(t*2.1)*.014;paws.forEach((paw,i)=>{paw.position.y=2.29+Math.max(0,Math.sin(t*4.8+i*2.4))*.04});renderer.render(scene,cam);};window.setSceneTime(0);window.__sceneReady=true;
