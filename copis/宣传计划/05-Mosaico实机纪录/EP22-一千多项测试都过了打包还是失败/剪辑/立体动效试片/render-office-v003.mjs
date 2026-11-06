import http from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const dir=path.dirname(fileURLToPath(import.meta.url)), root=process.cwd(), deps=path.resolve(root,'logo/panda-3d/node_modules');
const {chromium}=createRequire(path.join(deps,'playwright/package.json'))('playwright');
const routes={'/':path.join(dir,'office-scene-v003.html'),'/scene.js':path.join(dir,'office-scene-v003.js'),'/three/three.module.js':path.join(deps,'three/build/three.module.js'),'/three/three.core.js':path.join(deps,'three/build/three.core.js'),'/addons/loaders/GLTFLoader.js':path.join(deps,'three/examples/jsm/loaders/GLTFLoader.js'),'/addons/utils/BufferGeometryUtils.js':path.join(deps,'three/examples/jsm/utils/BufferGeometryUtils.js'),'/addons/utils/SkeletonUtils.js':path.join(deps,'three/examples/jsm/utils/SkeletonUtils.js'),'/panda.glb':path.join(root,'logo/panda-3d/assets/panda-faceted-standing.glb')};
const server=http.createServer(async(req,res)=>{try{const u=new URL(req.url,'http://localhost').pathname;if(!Object.hasOwn(routes,u)){res.writeHead(404).end();return}const data=await readFile(routes[u]);res.writeHead(200,{'Content-Type':u.endsWith('.js')?'text/javascript':u.endsWith('.glb')?'model/gltf-binary':'text/html'}).end(data)}catch(e){console.error(e);res.writeHead(500).end()}});
await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
const frames=path.join(dir,'frames-office-v003');await mkdir(frames,{recursive:true});let browser;
try {
 browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
 const page=await browser.newPage({viewport:{width:720,height:1280},deviceScaleFactor:1});page.on('pageerror',e=>console.error('page error:',e.message));
 await page.goto(`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>window.__sceneReady,{timeout:60000});
 if(process.env.PREVIEW==='1'){await page.evaluate(()=>window.setSceneTime(4));await page.screenshot({path:path.join(dir,'office-preview-v003.png')});console.log('preview ready');}
 else {
 if(process.env.REUSE_FRAMES!=='1') for(let i=0;i<240;i++){await page.evaluate(t=>window.setSceneTime(t),i/30);await page.screenshot({path:path.join(frames,`f${String(i).padStart(4,'0')}.png`)});if(i%60===0)console.log('frame',i,'/ 240');}
 const ep=path.resolve(dir,'../../素材/285'), old=path.resolve(dir,'../EP22-初稿-v005-待验收.mp4');
 const input0=path.join(frames,'f%04d.png'),camera=path.join(ep,'MAC-camera-preview.mp4'),otty=path.join(ep,'Otty.mp4'),out=path.join(dir,'EP22-熊猫办公场景试片-v003.mp4');
 const filter="[0:v]scale=1080:1920:flags=lanczos,setsar=1[base];[1:v]trim=start=55:duration=8,setpts=PTS-STARTPTS,crop=1238:697:77:68,scale=464:264:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=464:264:(ow-iw)/2:(oh-ih)/2:black,setsar=1[cam];[2:v]trim=start=55:duration=8,setpts=PTS-STARTPTS,drawbox=x=60:y=230:w=48:h=220:color=0x101713:t=fill,crop=840:220:60:230,scale=464:264:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=464:264:(ow-iw)/2:(oh-ih)/2:0x101713,setsar=1[term];[base][cam]overlay=51:320:shortest=1[b1];[b1][term]overlay=564:320:shortest=1[b2];[3:v]trim=duration=8,setpts=PTS-STARTPTS,split=2[hs][fs];[hs]crop=1080:280:0:0[header];[fs]crop=1080:232:0:1688[footer];[b2][header]overlay=0:0:shortest=1[b3];[b3][footer]overlay=0:1688:shortest=1[v];[3:a]atrim=0:6.25,afade=t=out:st=5.8:d=0.45,apad=whole_dur=8[a]";
 const ff=spawnSync('/opt/homebrew/bin/ffmpeg',['-nostdin','-hide_banner','-loglevel','error','-y','-framerate','30','-i',input0,'-i',camera,'-i',otty,'-i',old,'-filter_complex',filter,'-map','[v]','-map','[a]','-t','8','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out],{stdio:'inherit'});if(ff.status!==0)throw Error(`ffmpeg failed ${ff.status}`);console.log('OUTPUT',out);
 }
}finally{if(browser)await browser.close();await new Promise(resolve=>server.close(resolve));}
