import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { createPanda, disposePanda } from './model.js';
import { createStudio, frameModel, viewPosition } from './studio.js';

export function mountViewer() {
  const stage = document.querySelector('#stage');
  const viewport = document.querySelector('#viewport');
  const status = document.querySelector('#status');
  const rotateButton = document.querySelector('#rotate');
  const viewButtons = [...document.querySelectorAll('[data-view]')];
  const pngButton = document.querySelector('#export-png'), glbButton = document.querySelector('#export-glb');
  const renderer = new THREE.WebGLRenderer({ antialias:true, preserveDrawingBuffer:true, powerPreference:'high-performance' });
  const canvas = renderer.domElement;
  canvas.setAttribute('aria-label','立体熊猫，拖动可旋转，滚轮可缩放；也可使用右侧视角按钮');
  canvas.setAttribute('role','img'); canvas.tabIndex=0;
  viewport.append(canvas);
  const scene = createStudio(renderer, window.devicePixelRatio);
  const panda = createPanda(); scene.add(panda);
  const bounds = new THREE.Box3().setFromObject(panda);
  const camera = new THREE.PerspectiveCamera(32,1,0.1,100);
  const controls = new OrbitControls(camera,canvas);
  controls.enableDamping=true; controls.dampingFactor=0.08; controls.enablePan=false;
  controls.minPolarAngle=0.34; controls.maxPolarAngle=Math.PI/2+0.12;
  controls.autoRotateSpeed=0.65;
  const motionQuery=window.matchMedia('(prefers-reduced-motion: reduce)');
  let activeView='quarter', lastDistance=null, visible=true, destroyed=false, frame=0, lastTime=0;
  let goalPosition=null, goalTarget=null;
  const message=(text,error=false)=>{status.textContent=text;status.dataset.error=String(error);};
  const setRotation=value=>{
    controls.autoRotate=value;
    rotateButton.setAttribute('aria-pressed',String(value));
    rotateButton.lastChild.textContent=value?' 停止旋转':' 自动旋转';
  };
  const setView=(name,animate=true)=>{
    const fit=frameModel(bounds,camera.aspect,camera.fov);
    const p=viewPosition(name,fit.distance).add(fit.target);
    activeView=name;setRotation(false);
    viewButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
    canvas.dataset.view=name;
    if(animate&&!motionQuery.matches){goalPosition=p;goalTarget=fit.target;}
    else{goalPosition=null;goalTarget=null;camera.position.copy(p);controls.target.copy(fit.target);controls.update();}
  };
  const resize=()=>{
    const width=viewport.clientWidth,height=viewport.clientHeight;
    if(!width||!height)return;
    camera.aspect=width/height;camera.updateProjectionMatrix();renderer.setSize(width,height,false);
    const fit=frameModel(bounds,camera.aspect,camera.fov);
    controls.minDistance=fit.distance*0.60;controls.maxDistance=fit.distance*1.7;
    if(lastDistance===null)setView(activeView,false);
    else{
      const offset=camera.position.clone().sub(controls.target);
      offset.multiplyScalar(fit.distance/lastDistance);camera.position.copy(controls.target).add(offset);
      if(goalPosition) goalPosition.copy(viewPosition(activeView,fit.distance).add(fit.target));
      controls.update();
    }
    lastDistance=fit.distance;
    renderer.render(scene,camera);
  };
  const observer=new ResizeObserver(resize);observer.observe(viewport);resize();
  const onControlStart=()=>{
    goalPosition=null;goalTarget=null;setRotation(false);
    viewButtons.forEach(b=>b.setAttribute('aria-pressed','false'));canvas.dataset.view='custom';
  };
  controls.addEventListener('start',onControlStart);
  viewButtons.forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
  rotateButton.addEventListener('click',()=>{
    goalPosition=null;goalTarget=null;setRotation(!controls.autoRotate);
    if(controls.autoRotate){viewButtons.forEach(b=>b.setAttribute('aria-pressed','false'));canvas.dataset.view='custom';}
  });
  document.querySelector('#reference-toggle').addEventListener('change',e=>{document.querySelector('#reference').hidden=!e.target.checked;});
  const motionChange=()=>{if(motionQuery.matches){setRotation(false);if(goalPosition){camera.position.copy(goalPosition);controls.target.copy(goalTarget);goalPosition=null;goalTarget=null;}}};
  motionQuery.addEventListener('change',motionChange);
  const render=time=>{
    if(destroyed)return;
    frame=requestAnimationFrame(render);
    if(!visible||document.hidden){lastTime=time;return;}
    const dt=Math.min((time-lastTime)/1000||0.016,0.05);lastTime=time;
    if(goalPosition){
      const t=1-Math.exp(-dt*8);camera.position.lerp(goalPosition,t);controls.target.lerp(goalTarget,t);
      if(camera.position.distanceTo(goalPosition)<0.002){camera.position.copy(goalPosition);controls.target.copy(goalTarget);goalPosition=null;goalTarget=null;}
    }
    controls.update(dt);renderer.render(scene,camera);
  };
  const intersection=new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;},{threshold:0});intersection.observe(stage);
  frame=requestAnimationFrame(render);

  const save=(blob,name)=>{
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
  };
  const settleCamera=()=>{if(goalPosition){camera.position.copy(goalPosition);controls.target.copy(goalTarget);goalPosition=null;goalTarget=null;}controls.update();};
  pngButton.addEventListener('click',()=>{
    pngButton.disabled=true;
    try{
      settleCamera();renderer.render(scene,camera);
      canvas.toBlob(blob=>{
        try{if(!blob)throw new Error('PNG 编码失败');save(blob,'LoomOS-panda-3d.png');message('已保存当前视角 · PNG');}
        catch(e){message(`图片保存失败：${e.message}`,true);}
        finally{pngButton.disabled=false;}
      },'image/png');
    }catch(e){pngButton.disabled=false;message(`图片保存失败：${e.message}`,true);}
  });
  glbButton.addEventListener('click',async()=>{
    glbButton.disabled=true;message('正在打包立体模型…');
    try{
      // Export only the character, never the floor, camera, lights or viewer UI.
      const result=await new GLTFExporter().parseAsync(panda,{binary:true,onlyVisible:true});
      save(new Blob([result],{type:'model/gltf-binary'}),'LoomOS-panda-3d.glb');message('已导出独立立体模型 · GLB');
    }catch(e){message(`模型导出失败：${e.message}`,true);}
    finally{glbButton.disabled=false;}
  });
  const contextLost=e=>{
    e.preventDefault();cancelAnimationFrame(frame);stage.dataset.state='error';
    document.querySelector('#error-message').textContent='浏览器的图形上下文已中断，请重新加载页面。';
    document.querySelector('#error').hidden=false;[...viewButtons,rotateButton,pngButton,glbButton].forEach(b=>b.disabled=true);
    message('图形上下文已中断',true);
  };
  canvas.addEventListener('webglcontextlost',contextLost);
  const dispose=()=>{
    destroyed=true;cancelAnimationFrame(frame);observer.disconnect();intersection.disconnect();
    motionQuery.removeEventListener('change',motionChange);canvas.removeEventListener('webglcontextlost',contextLost);
    controls.dispose();disposePanda(panda);
    scene.traverse(obj=>{if(obj.isMesh&&!obj.parent?.isGroup){obj.geometry.dispose();obj.material.dispose();}});
    renderer.dispose();
  };
  window.addEventListener('pagehide',e=>{if(!e.persisted)dispose();});
  [...viewButtons,rotateButton,pngButton,glbButton].forEach(b=>b.disabled=false);
  document.querySelector('#loading').hidden=true;stage.dataset.state='ready';
  message(motionQuery.matches?'已就绪 · 遵循系统减少动态效果设置':'已就绪 · 拖动，看看它的每一面');
}
