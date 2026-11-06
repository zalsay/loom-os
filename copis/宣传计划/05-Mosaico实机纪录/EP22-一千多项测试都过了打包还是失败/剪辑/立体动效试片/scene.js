import * as THREE from 'three';
// Procedural tabletop scene. Interpretive graphic, not footage or a live log.
const W=1080,H=608;
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setSize(W,H); renderer.setPixelRatio(1); renderer.setClearColor(0x172c30); renderer.shadowMap.enabled=true; renderer.shadowMap.type=THREE.PCFSoftShadowMap;
renderer.outputColorSpace=THREE.SRGBColorSpace; renderer.toneMapping=THREE.ACESFilmicToneMapping; renderer.toneMappingExposure=1.15;
document.body.prepend(renderer.domElement);
const scene=new THREE.Scene(); scene.background=new THREE.Color('#172c30');
const camera=new THREE.PerspectiveCamera(36,W/H,0.1,100); camera.position.set(0,5.0,12.0);
scene.add(new THREE.HemisphereLight(0xffedcd,0x234546,2.1));
const light=new THREE.DirectionalLight(0xffdfa7,3); light.position.set(-5,10,8); light.castShadow=true; light.shadow.mapSize.set(1024,1024); Object.assign(light.shadow.camera,{left:-10,right:10,top:10,bottom:-10}); scene.add(light);
const mat=(c,r=0.88)=>new THREE.MeshStandardMaterial({color:c,roughness:r});
const ivory=mat('#f3ead5'), ink=mat('#263e3b'), paper=mat('#e7d5b5'), gold=mat('#f4bf60'), teal=mat('#72bcb0'), dark=mat('#1d3432'), peach=mat('#df8e76');
function box(w,h,d,m,x,y,z,parent=scene){let o=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),m);o.position.set(x,y,z);o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
function orb(r,m,x,y,z,parent=scene,s=[1,1,1]){const o=new THREE.Mesh(new THREE.SphereGeometry(r,24,16),m);o.scale.set(...s);o.position.set(x,y,z);o.castShadow=true;parent.add(o);return o;}
box(20,.3,9,mat('#476862'),0,-.27,0); box(12.8,.22,5.4,paper,0,-.03,.2); box(12.4,.06,5.05,ivory,0,.11,.2);
// Paper seams and underlying spreads give a restrained tactile background.
box(.035,.012,4.9,mat('#c3ae8c'),0,.15,.2); for(let i=0;i<8;i++)box(10,.007,.014,mat('#ded0b5'),0,.15,-1.75+i*.48);
function canvasLabel(text,sub,fg='#233b36',bg='#f2e3bd') {let c=document.createElement('canvas');c.width=960;c.height=400;let x=c.getContext('2d');x.fillStyle=bg;x.fillRect(0,0,960,400);x.strokeStyle='#c5a676';x.lineWidth=10;x.strokeRect(6,6,948,388);x.textAlign='center';x.fillStyle=fg;x.font='bold 132px "Hiragino Sans GB", sans-serif';x.fillText(text,480,185);x.font='52px "Hiragino Sans GB", sans-serif';x.fillText(sub,480,290);let tx=new THREE.CanvasTexture(c);tx.colorSpace=THREE.SRGBColorSpace;return tx;}
function sign(text,sub){let g=new THREE.Group(); box(3.65,1.55,.15,paper,0,1.03,0,g); let plane=new THREE.Mesh(new THREE.PlaneGeometry(3.4,1.38),new THREE.MeshBasicMaterial({map:canvasLabel(text,sub)}));plane.position.set(0,1.03,.09);g.add(plane);box(.16,1.35,.14,dark,0,.14,-.08,g);scene.add(g);return g;}
const board=sign('1253','电脑端测试通过');board.position.set(-2.7,.20,-1.1);
const pack=sign('20  /  1','成功 / pack 失败');pack.position.set(3,.2,-1.1);pack.scale.setScalar(.001);
// Panda-like LoomOS original shape; semantic mascot, not a real device.
const panda=new THREE.Group();scene.add(panda);
orb(.55,ink,0,.55,0,panda,[1,1.15,.75]); orb(.55,ivory,0,1.40,0,panda,[1.12,.94,.84]);
for(const side of [-1,1]){orb(.22,ink,side*.46,1.80,-.06,panda);orb(.22,ink,side*.28,1.46,.41,panda,[.80,1.25,.22]);orb(.075,ivory,side*.28,1.45,.47,panda);orb(.13,ink,side*.48,.54,.05,panda,[1,1.5,1]);orb(.15,ink,side*.26,.17,.13,panda,[1,.7,1.3]);}
orb(.085,ink,0,1.27,.46,panda,[1,.65,.55]); orb(.26,ivory,0,.56,.32,panda,[1,1.1,.22]);
const emblem=new THREE.Mesh(new THREE.TorusGeometry(.14,.035,8,32),gold);emblem.position.set(0,.57,.40);panda.add(emblem);
const arms=[]; for(const side of [-1,1]){let a=new THREE.Group();a.position.set(side*.48,.83,.03);orb(.12,ink,side*.10,-.17,0,a,[1,1.7,1]);panda.add(a);arms.push(a);}
// 21 tokens represent combined build/pack invocations, not 21 pack operations.
const tokens=[];for(let i=0;i<21;i++){const col=i%7,row=Math.floor(i/7);let t=box(.35,.13,.35,i===20?peach:teal,1.58+col*.44,.25,.05+row*.47);t.scale.setScalar(.001);tokens.push(t);}
let lastTime=0;const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*(3-2*x)};
window.setSceneTime=(t)=>{lastTime=t;
 let walk=ease((t-.25)/3.4); panda.position.set(-5.4+walk*4.55,0,1.1);panda.rotation.y=.18+Math.sin(t*2)*.10;panda.rotation.z=Math.sin(t*7)*.045*(1-ease((t-3.2)/.5));panda.position.y=Math.abs(Math.sin(t*6))*.12*(1-ease((t-3.2)/.5));arms.forEach((a,i)=>a.rotation.z=(i?1:-1)*(.18+Math.sin(t*6)*.35)*(1-ease((t-3.2)/.5)));
 const reveal=ease((t-4.0)/.9);board.position.y=.2-reveal*.3; board.scale.setScalar(1-reveal*.92);pack.scale.setScalar(Math.max(.001,reveal));
 tokens.forEach((o,i)=>{let q=ease((t-4.35-i*.105)/.3);o.scale.setScalar(Math.max(.001,q));});
 camera.position.x=-.4+ease((t-3.6)/2.1)*1.15;camera.position.z=12.0-ease((t-3.6)/2.1)*.55;camera.lookAt(.1,0.65,0);
 document.querySelector('#status').textContent=t<4?'本轮 · 电脑端测试':'本轮 · 构建与打包记录'; renderer.render(scene,camera);
};
window.setSceneTime(0);window.__sceneReady=true;
