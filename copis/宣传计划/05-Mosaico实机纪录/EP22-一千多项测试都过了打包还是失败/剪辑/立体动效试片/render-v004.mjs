import http from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
const dir=path.dirname(fileURLToPath(import.meta.url));
const root=process.cwd();
const deps=path.resolve(root,'logo/panda-3d/node_modules');
const req=createRequire(path.join(deps,'playwright/package.json'));
const {chromium}=req('playwright');
const files={'/':'scene-v004.html','/scene.js':'scene-v004.js'};
const addons={'/addons/loaders/GLTFLoader.js':'loaders/GLTFLoader.js','/addons/utils/BufferGeometryUtils.js':'utils/BufferGeometryUtils.js','/addons/utils/SkeletonUtils.js':'utils/SkeletonUtils.js'};
const server=http.createServer(async (request,response)=>{try{const u=new URL(request.url,'http://localhost').pathname;let target;if(files[u])target=path.join(dir,files[u]);else if(u==='/three/three.module.js'||u==='/three/three.core.js')target=path.join(deps,'three/build',path.basename(u));else if(addons[u])target=path.join(deps,'three/examples/jsm',addons[u]);else if(u==='/panda.glb')target=path.resolve(root,'logo/panda-3d/assets/panda-faceted-standing.glb');else {response.writeHead(404).end();return}let data=await readFile(target);response.writeHead(200,{'Content-Type':u.endsWith('.js')?'text/javascript':u.endsWith('.glb')?'model/gltf-binary':'text/html'});response.end(data)}catch(e){console.error('server error',e.message);response.writeHead(500).end()}});
await new Promise(ok=>server.listen(0,'127.0.0.1',ok));
const frames=path.join(dir,'frames-v004'); await mkdir(frames,{recursive:true});
let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
 const page=await browser.newPage({viewport:{width:1080,height:608},deviceScaleFactor:1});
 page.on('pageerror',e=>console.error('browser:',e.message));
 await page.goto(`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>window.__sceneReady,{timeout:60000});
 for(let i=0;i<240;i++){await page.evaluate(t=>window.setSceneTime(t),i/30);await page.screenshot({path:path.join(frames,`f${String(i).padStart(4,'0')}.png`)});if(i%60===0)console.log('frame',i,'/ 240');}
 const v5=path.resolve(dir,'../EP22-初稿-v005-待验收.mp4');
 const output=path.join(dir,'EP22-熊猫头白眼动效试片-v004.mp4');
 const filter="[0:v]trim=duration=8,setpts=PTS-STARTPTS[base];[1:v]trim=duration=8,setpts=PTS-STARTPTS[anim];[base][anim]overlay=0:280:shortest=1,drawbox=x=0:y=1550:w=1080:h=138:color=0x101713:t=fill,drawtext=fontfile='/System/Library/Fonts/Hiragino Sans GB.ttc':text='电脑端测试通过，实际打包仍失败':fontcolor=white:fontsize=47:x=(w-text_w)/2:y=1580:enable='between(t,3.2,7.9)'[v];[0:a]atrim=0:6.25,afade=t=out:st=5.8:d=0.45,apad=whole_dur=8[a]";
 const ff=spawnSync('/opt/homebrew/bin/ffmpeg',['-nostdin','-hide_banner','-loglevel','error','-y','-i',v5,'-framerate','30','-i',path.join(frames,'f%04d.png'),'-filter_complex',filter,'-map','[v]','-map','[a]','-t','8','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',output],{stdio:'inherit'});
 if(ff.status!==0)throw Error(`ffmpeg failed ${ff.status}`);console.log('OUTPUT',output);
} finally {if(browser)await browser.close(); await new Promise(ok=>server.close(ok));}
