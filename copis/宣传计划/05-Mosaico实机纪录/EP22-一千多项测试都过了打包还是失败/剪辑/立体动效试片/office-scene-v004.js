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
// Aluminum laptop illustration: rounded shell, dark bezel, keyboard and trackpad.
function roundedPanel(w,h,depth,r,material){const s=new THREE.Shape();const x=-w/2,y=-h/2;s.moveTo(x+r,y);s.lineTo(x+w-r,y);s.quadraticCurveTo(x+w,y,x+w,y+r);s.lineTo(x+w,y+h-r);s.quadraticCurveTo(x+w,y+h,x+w-r,y+h);s.lineTo(x+r,y+h);s.quadraticCurveTo(x,y+h,x,y+h-r);s.lineTo(x,y+r);s.quadraticCurveTo(x,y,x+r,y);const o=new THREE.Mesh(new THREE.ExtrudeGeometry(s,{depth,bevelEnabled:true,bevelSize:.018,bevelThickness:.012,bevelSegments:3,curveSegments:8}),material);o.castShadow=true;o.receiveShadow=true;return o;}
const aluminum=new THREE.MeshStandardMaterial({color:'#b9c0ba',metalness:.62,roughness:.31});
const bezel=material('#111a1b',.48), keyMat=material('#1f2928',.68), trackMat=material('#a5b1ac',.5);
const deck=roundedPanel(2.3,1.48,.055,.075,aluminum);deck.rotation.x=-Math.PI/2;deck.position.set(.15,2.19,-.35);scene.add(deck);
const lid=roundedPanel(2.3,1.5,.06,.08,aluminum);lid.position.set(.15,2.96,-1.10);scene.add(lid);
const glass=roundedPanel(2.17,1.37,.012,.055,bezel);glass.position.set(.15,2.97,-1.028);scene.add(glass);
// The laptop display is animated illustration, never a reconstruction of real log text.
const screenArt=document.createElement('canvas');screenArt.width=1024;screenArt.height=640;
const ctx=screenArt.getContext('2d');const texture=new THREE.CanvasTexture(screenArt);texture.colorSpace=THREE.SRGBColorSpace;
function drawScreen(t){
  ctx.fillStyle='#142326';ctx.fillRect(0,0,1024,640);
  ctx.fillStyle='#283a3a';ctx.fillRect(0,0,1024,45);
  ctx.fillStyle='#213031';ctx.fillRect(0,45,190,595);
  ctx.fillStyle='#57706a';for(let i=0;i<8;i++)ctx.fillRect(28,85+i*50,100+(i%3)*18,8);
  // Move up one row at a time; the deterministic pattern is illustrative, not a real terminal log.
  const step=36, phase=Math.max(0,t)*1.55, whole=Math.floor(phase), fraction=phase-whole;
  const smooth=fraction*fraction*(3-2*fraction);
  ctx.save();ctx.beginPath();ctx.rect(200,48,824,592);ctx.clip();
  for(let i=0;i<19;i++){
    const row=i+whole, y=82+i*step-smooth*step;
    ctx.fillStyle=['#82b8a6','#d0aa72','#8ca49e'][row%3];
    ctx.fillRect(228+(row%3)*28,y,160+(row*83)%320,7);
  }
  ctx.restore();texture.needsUpdate=true;
}
drawScreen(0);
const display=new THREE.Mesh(new THREE.PlaneGeometry(2.03,1.23),new THREE.MeshBasicMaterial({map:texture}));display.position.set(.15,2.97,-.975);scene.add(display);
ball(.015,black,.15,3.665,-.999,[1,1,.3]);
box(2.03,.018,.72,keyMat,.15,2.257,-.52);
const keyTop=material('#2a3432',.52);for(let row=0;row<5;row++)for(let col=0;col<13;col++){box(.115,.012,.105,keyTop,-.75+col*.15,2.27,-.80+row*.135);}
box(.75,.008,.34,trackMat,.15,2.258,.13);box(.67,.003,.26,aluminum,.15,2.264,.13);
const hinge=new THREE.Mesh(new THREE.CylinderGeometry(.033,.033,2.1,24),dark);hinge.rotation.z=Math.PI/2;hinge.position.set(.15,2.25,-1.045);scene.add(hinge);
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
const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};window.setSceneTime=t=>{const p=ease(t/8);cam.position.x=5.5-.3*p;cam.position.z=14-.35*p;cam.lookAt(-.5,1.7,-.3);panda.rotation.y=Math.PI+.18+Math.sin(t*1.3)*.025;panda.position.y=1.12+Math.sin(t*2.1)*.014;paws.forEach((paw,i)=>{paw.position.y=2.29+Math.max(0,Math.sin(t*4.8+i*2.4))*.04});drawScreen(t);renderer.render(scene,cam);};window.setSceneTime(0);window.__sceneReady=true;
