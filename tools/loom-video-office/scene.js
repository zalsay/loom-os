import * as THREE from 'three';
import {GLTFLoader} from '/addons/loaders/GLTFLoader.js';
const config=window.__OFFICE_CONFIG;
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});renderer.setSize(720,1280);renderer.setPixelRatio(config.pixelRatio);renderer.setClearColor('#203938');renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;document.body.prepend(renderer.domElement);
const scene=new THREE.Scene();const frontFill=new THREE.DirectionalLight('#e5f1ec',.9);frontFill.position.set(0,5,-8);scene.add(frontFill);scene.background=new THREE.Color('#203938');scene.fog=new THREE.Fog('#203938',13,25);
const cam=new THREE.PerspectiveCamera(40,720/1280,.1,100);cam.position.set(5.5,5.1,14);cam.lookAt(-.5,1.7,-.3);
scene.add(new THREE.HemisphereLight(0xfff2e1,0x385050,2));const lamp=new THREE.DirectionalLight('#ffe8ce',2.65);lamp.position.set(-3,9,6);lamp.castShadow=true;lamp.shadow.mapSize.set(2048,2048);lamp.shadow.bias=-.00035;lamp.shadow.normalBias=.025;lamp.shadow.radius=3;Object.assign(lamp.shadow.camera,{left:-9,right:9,top:9,bottom:-9});scene.add(lamp);
const material=(color,roughness=.85)=>new THREE.MeshStandardMaterial({color,roughness});const wood=material('#b58c64'), pale=material('#e8d4b2'), dark=material('#263e3c'), metal=material('#9caeab',.48), black=material('#152521'), screen=material('#142c29'), coral=material('#df9170');
function box(w,h,d,m,x,y,z,rot=0,parent=scene){const o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);o.position.set(x,y,z);o.rotation.y=rot;o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
function ball(r,m,x,y,z,s=[1,1,1],parent=scene){const o=new THREE.Mesh(new THREE.SphereGeometry(r,24,16),m);o.scale.set(...s);o.position.set(x,y,z);o.castShadow=true;parent.add(o);return o;}

// Seeded surface textures are attached to objects, not regenerated per frame.
function grainTexture(kind){
 const c=document.createElement('canvas');c.width=1024;c.height=512;const q=c.getContext('2d');
 let seed=28522;function rand(){seed=(1664525*seed+1013904223)>>>0;return seed/4294967296;}
 q.fillStyle=kind==='wood'?'#b5a087':'#708078';q.fillRect(0,0,1024,512);
 if(kind==='wood'){
  for(let i=0;i<520;i++){const y=rand()*512;q.beginPath();q.moveTo(0,y);q.bezierCurveTo(300,y+Math.sin(i)*8,700,y+Math.cos(i)*10,1024,y+Math.sin(i*.3)*4);q.strokeStyle=`rgba(68,45,23,${.018+rand()*.075})`;q.lineWidth=.3+rand();q.stroke();}
 }else{
  for(let y=0;y<512;y+=3){q.strokeStyle=y%2?'#77877c':'#697a70';q.lineWidth=.55;q.beginPath();q.moveTo(0,y);q.lineTo(1024,y);q.stroke();}
  for(let x=0;x<1024;x+=3){q.strokeStyle='rgba(20,38,30,.12)';q.fillRect(x,0,1,512);}
 }
 const tex=new THREE.CanvasTexture(c);tex.colorSpace=THREE.SRGBColorSpace;tex.anisotropy=8;return tex;
}
const oak=new THREE.MeshStandardMaterial({map:grainTexture('wood'),color:'#e5ccab',roughness:.61});
const upholstery=new THREE.MeshStandardMaterial({map:grainTexture('fabric'),color:'#b9c3b5',roughness:.95});
const powder=material('#334745',.66), trim=material('#71857d',.63);
function slab(w,d,h,r,m,x,y,z){const o=roundedPanel(w,d,h,r,m);o.rotation.x=-Math.PI/2;o.position.set(x,y-h/2,z);scene.add(o);return o;}
function tube(points,r,m,parent=scene){const curve=new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));const o=new THREE.Mesh(new THREE.TubeGeometry(curve,48,r,8,false),m);o.castShadow=true;parent.add(o);return o;}
box(50,.16,50,material('#52665c'),0,-.1,0); // Open studio backdrop permits an unobstructed camera orbit.
slab(7,3.7,.22,.14,oak,0,2,-.55);
slab(6.85,3.56,.07,.13,material('#776652'),0,1.89,-.55);
for(const x of [-3,3])for(const z of [-1.8,.8]){box(.15,1.84,.15,powder,x,.96,z);box(.17,.07,.17,black,x,.055,z);}
for(const x of [-3,3])box(.12,.12,2.64,powder,x,.18,-.5);
box(6,.12,.1,powder,0,1.72,-1.8);
slab(3.05,1.9,.015,.09,material('#415752'),.18,2.126,-.36);
// A closed cable sleeve under the desk is decorative, not a device connection.
box(2.0,.16,.28,powder,.2,1.72,-1.45);

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
  const step=36, phase=Math.max(0,t)*config.scrollRowsPerSecond, whole=Math.floor(phase), fraction=phase-whole;
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

slab(1.9,1.65,.12,.22,oak,-.65,1.05,2.35);
slab(1.78,1.51,.18,.24,upholstery,-.65,1.15,2.32);
// Rounded back shell with a modest lumbar curve and upholstered inset.
const back=roundedPanel(1.9,1.38,.11,.25,oak);back.position.set(-.65,1.96,3.04);back.rotation.x=-.07;scene.add(back);
const fabric=roundedPanel(1.70,1.18,.065,.23,upholstery);fabric.position.set(-.65,1.96,3.17);fabric.rotation.x=-.07;scene.add(fabric);
const piping=roundedPanel(1.77,1.25,.012,.24,trim);piping.position.set(-.65,1.96,3.145);piping.rotation.x=-.07;scene.add(piping);
for(const x of [-1.35,.05])for(const z of [1.8,2.96]){box(.10,.98,.10,powder,x,.52,z);ball(.075,black,x,.065,z,[1,.45,1]);}
for(const x of [-1.35,.05])box(.07,.075,1.17,powder,x,.34,2.38);
// Chair rear fasteners: small, physically anchored details.
for(const x of [-1.32,.02])for(const y of [1.55,2.35])ball(.023,metal,x,y,3.24,[1,1,.35]);

const gltf=await new GLTFLoader().loadAsync('/panda.glb');const panda=gltf.scene;panda.scale.setScalar(.58);panda.position.set(-.65,1.12,2.30);panda.rotation.y=Math.PI+.18;scene.add(panda);panda.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}if(/^(eye|pupil)-(left|right)$/.test(o.name))o.material=new THREE.MeshStandardMaterial({color:0xffffff,roughness:.55});});

// Keep the supplied faceted head, ears, white eye treatment and torso.
// Hide straight standing limbs: seated limbs below are purpose-built for this shot.
panda.traverse(o=>{if(/^(arm|paw|leg|foot|toe)-/.test(o.name))o.visible=false;});
// Head nod pivots around the neck; no geometric changes to the supplied head.
panda.updateMatrixWorld(true);
const nod=new THREE.Group();panda.add(nod);nod.position.set(0,2.55,0);panda.updateMatrixWorld(true);
const faceNames=['head','ear-left','ear-inner-left','ear-right','ear-inner-right','eye-patch-left','eye-left','pupil-left','catchlight-left','catchlight-small-left','eye-patch-right','eye-right','pupil-right','catchlight-right','catchlight-small-right','nose','nose-soft-highlight','philtrum','smile-left','smile-right'];
for(const name of faceNames){const p=panda.getObjectByName(name);if(p)nod.attach(p);}
// Rounded thighs sit on the cushion; lower legs drop toward the desk.
for(const x of [-.94,-.35]){
 ball(.26,dark,x,1.44,1.92,[.90,.83,1.45]);
 ball(.21,dark,x,1.10,1.59,[.85,1.15,.85]);
 ball(.23,dark,x,.91,1.42,[1,.60,1.4]);
}

// Book and mug add depth without presenting them as evidence.

slab(1.12,.82,.09,.035,material('#718b80'),-2.35,2.18,-.6);
slab(1.06,.76,.045,.025,material('#e7dec9'),-2.35,2.225,-.6);
for(let i=0;i<4;i++)box(.96,.004,.007,material('#b9aa90'),-2.35,2.21+i*.008,-.215);
const cupMat=material('#d9cab4',.34);const cup=new THREE.Mesh(new THREE.CylinderGeometry(.22,.19,.42,48,1,true),cupMat);cup.position.set(-2.4,2.36,.35);cup.castShadow=true;scene.add(cup);
const rim=new THREE.Mesh(new THREE.TorusGeometry(.217,.018,8,48),cupMat);rim.rotation.x=Math.PI/2;rim.position.set(-2.4,2.57,.35);scene.add(rim);
const coffee=new THREE.Mesh(new THREE.CircleGeometry(.198,48),material('#463329',.23));coffee.rotation.x=-Math.PI/2;coffee.position.set(-2.4,2.53,.35);scene.add(coffee);
const handle=new THREE.Mesh(new THREE.TorusGeometry(.12,.032,10,28),cupMat);handle.position.set(-2.12,2.39,.35);handle.scale.x=.80;scene.add(handle);
slab(.58,.58,.014,.22,material('#856e54'),-2.4,2.13,.35);
tube([[-2.7,2.26,-.8],[-2.1,2.26,-.4]],.022,material('#e0b568'));


// Connected two-segment arms. Elbows bend naturally; wrists and forearms share the same animation.
const paws=[ball(.14,dark,-.48,2.30,-.05,[1,.55,1.25]),ball(.14,dark,.12,2.30,-.05,[1,.55,1.25])];
const joints=[];
function bone(radius){const m=new THREE.Mesh(new THREE.CylinderGeometry(radius*.85,radius,1,16),dark);m.castShadow=true;scene.add(m);return m;}
function fitBone(m,a,b){const v=b.clone().sub(a);m.position.copy(a).add(b).multiplyScalar(.5);m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),v.clone().normalize());m.scale.y=v.length();}
for(let i=0;i<2;i++){joints.push({upper:bone(.125),fore:bone(.115),elbow:ball(.135,dark,0,0,0),shoulder:new THREE.Vector3(i?-.20:-1.13,2.14,1.98),base:new THREE.Vector3(i?.12:-.48,2.30,-.05),elbowBase:new THREE.Vector3(i?.20:-1.04,2.14,.92)});}
function typePose(t){joints.forEach((j,i)=>{const lift=Math.max(0,Math.sin(t*4.8+i*2.4))*.027;const wrist=j.base.clone();wrist.y+=lift;paws[i].position.copy(wrist);const e=j.elbowBase.clone();e.y+=lift*.35;j.elbow.position.copy(e);fitBone(j.upper,j.shoulder,e);fitBone(j.fore,e,wrist);});nod.rotation.x=.025+Math.sin(t*1.5)*.018;}
const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
function walkingMotion(t){
 const u=Math.max(0,Math.min(1,(t-config.camera.holdStart)/config.camera.travelDuration));
 const envelope=Math.sin(Math.PI*u)**2*config.camera.gaitStrength;
 // A complete left/right cycle is ~1.82s; each footfall produces a small height change.
 const phase=2*Math.PI*config.camera.gaitHz*(t-config.camera.holdStart)+.045*Math.sin(t*.65);
 return {sway:.040*Math.sin(phase)*envelope,
   bob:(.028*Math.cos(2*phase)+.004*Math.sin(4*phase))*envelope,
   fore:.008*Math.sin(2*phase)*envelope,
   roll:.0014*Math.sin(phase+.35)*envelope};
}
window.__walkingMotion=walkingMotion;
window.setSceneTime=t=>{
// Fixed lens, rear approach: actual camera translation rather than orbit or digital zoom.
const p=ease((t-config.camera.holdStart)/config.camera.travelDuration);
// Gentle walking cadence; no per-frame randomness or shake on the UI overlays.
const gait=walkingMotion(t);
const mix=(a,b)=>a+(b-a)*p;
cam.position.set(mix(config.camera.from[0],config.camera.to[0])+gait.sway,mix(config.camera.from[1],config.camera.to[1])+gait.bob,mix(config.camera.from[2],config.camera.to[2])+gait.fore);
cam.lookAt(mix(config.camera.lookFrom[0],config.camera.lookTo[0]),mix(config.camera.lookFrom[1],config.camera.lookTo[1])+gait.bob*.25,mix(config.camera.lookFrom[2],config.camera.lookTo[2]));
cam.rotateZ(gait.roll);
panda.rotation.y=Math.PI+.18+Math.sin(t*1.3)*.025;panda.position.y=1.12+Math.sin(t*2.1)*.014;typePose(t);drawScreen(t);renderer.render(scene,cam);};window.setSceneTime(0);window.__sceneReady=true;
