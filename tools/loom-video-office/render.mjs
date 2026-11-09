#!/usr/bin/env node
import http from 'node:http';
import fs from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {normalize,checkBounds,assertSafeOutput,VERSION,LAYOUT} from './config.mjs';
const args=process.argv.slice(2), configArg=args[0];
if(!configArg||configArg==='--help'){console.log('Usage: node tools/loom-video-office/render.mjs EP.json [--root PROJECT] [--validate | --preview]\nAll asset paths and outputDir are relative to PROJECT (default cwd). Render refuses existing final output or frame directory.');process.exit(0);}
const allowed=new Set(['--root','--validate','--preview']);for(let i=1;i<args.length;i++){if(!allowed.has(args[i]))throw Error('Unknown option '+args[i]);if(args[i]==='--root')i++;}
const root=path.resolve(args.includes('--root')?args[args.indexOf('--root')+1]:process.cwd()),here=path.dirname(fileURLToPath(import.meta.url));
const c=normalize(JSON.parse(await fs.readFile(path.resolve(configArg),'utf8'))),resolve=p=>path.resolve(root,p);
const ffmpeg=process.env.FFMPEG??'ffmpeg',ffprobe=process.env.FFPROBE??'ffprobe';
function run(bin,argv,opts={}){const r=spawnSync(bin,argv,{encoding:'utf8',maxBuffer:32*1024*1024,...opts});if(r.error||r.status!==0)throw Error(`${bin} failed: ${r.error?.message??r.stderr??r.status}`);return r.stdout;}
function probe(p){return JSON.parse(run(ffprobe,['-v','error','-show_streams','-show_format','-of','json',p]));}
const inputs=[c.model,c.cameraVideo.path,c.terminalVideo.path,c.audio.path,c.footer.path,...(c.header.source?[c.header.source.path]:[]),...(c.subtitleAss?[c.subtitleAss]:[])].map(resolve);
for(const p of inputs){if(!(await fs.stat(p)).isFile())throw Error('Input not a file: '+p);}
checkBounds(c.cameraVideo,probe(resolve(c.cameraVideo.path)),'cameraVideo',c.duration);
checkBounds(c.terminalVideo,probe(resolve(c.terminalVideo.path)),'terminalVideo',c.duration);
if(c.header.source){checkBounds(c.header.source,probe(resolve(c.header.source.path)),'header.source',c.duration);if(!c.header.source.crop)throw Error('header.source.crop required');}
checkBounds(c.footer,probe(resolve(c.footer.path)),'footer',c.footer.kind==='video'?c.duration:null);
const ap=probe(resolve(c.audio.path));if(!ap.streams.some(s=>s.codec_type==='audio')||Number(ap.format.duration)<c.audio.start+c.duration-.04)throw Error('audio: complete mixed audio shorter than requested duration');
const deps=resolve(c.dependencies);for(const p of ['three/build/three.module.js','playwright/package.json'])if(!existsSync(path.join(deps,p)))throw Error('Missing installed dependency '+p+'; install separately, not automatically');
const outDir=resolve(c.outputDir),output=path.join(outDir,c.outputName);assertSafeOutput(output,inputs);
if(args.includes('--validate')){console.log(JSON.stringify({valid:true,episode:c.episode,duration:c.duration,frames:Math.round(c.duration*30),aiLabel:c.aiLabel,output},null,2));process.exit(0);}
const preview=args.includes('--preview');if(!preview&&existsSync(output))throw Error('Output exists; choose a new revision: '+output);
await fs.mkdir(outDir,{recursive:true});const frames=path.join(outDir,'frames');
if(!preview)await fs.mkdir(frames); // exclusive frame directory prevents stale/partial reuse
const sceneText=await fs.readFile(path.join(here,'scene.js'),'utf8'),html=await fs.readFile(path.join(here,'scene.html'),'utf8');
const routes={'/':{data:html,type:'text/html'},'/scene.js':{data:sceneText,type:'text/javascript'},'/panda.glb':{file:resolve(c.model),type:'model/gltf-binary'}};
for(const n of ['three.module.js','three.core.js'])routes['/three/'+n]={file:path.join(deps,'three/build',n),type:'text/javascript'};
for(const n of ['loaders/GLTFLoader.js','utils/BufferGeometryUtils.js','utils/SkeletonUtils.js'])routes['/addons/'+n]={file:path.join(deps,'three/examples/jsm',n),type:'text/javascript'};
const server=http.createServer(async(req,res)=>{try{const u=new URL(req.url,'http://localhost').pathname;if(!Object.hasOwn(routes,u)){res.writeHead(404).end();return}const r=routes[u];res.writeHead(200,{'Content-Type':r.type}).end(r.data??await fs.readFile(r.file));}catch(e){console.error(e.message);res.writeHead(500).end();}});
await new Promise(ok=>server.listen(0,'127.0.0.1',ok));let browser;const pageErrors=[];
try{
 const {chromium}=createRequire(path.join(deps,'playwright/package.json'))('playwright');
 const browserPath=process.env.CHROME_PATH??(process.platform==='darwin'?'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome':undefined);
 browser=await chromium.launch({headless:true,...(browserPath?{executablePath:browserPath}:{}),args:['--enable-webgl','--use-angle=swiftshader','--enable-unsafe-swiftshader','--disable-background-timer-throttling']});
 const page=await browser.newPage({viewport:{width:720,height:1280},deviceScaleFactor:c.pixelRatio});
 await page.addInitScript(config=>{window.__OFFICE_CONFIG=config},c);page.on('pageerror',e=>pageErrors.push(e.message));
 await page.goto(`http://127.0.0.1:${server.address().port}/`);await page.waitForFunction(()=>window.__sceneReady,null,{timeout:60000});
 const label=await page.locator('.note').textContent();if(label!==c.aiLabel)throw Error('AI label mismatch');
 if(preview){for(const t of [0,c.duration/2,c.duration-1/30]){await page.evaluate(t=>window.setSceneTime(t),t);await page.screenshot({path:path.join(outDir,`preview-${t.toFixed(2)}.png`)});}console.log('Preview only: '+outDir);}
 else{
  for(let i=0;i<Math.round(c.duration*30);i++){await page.evaluate(t=>window.setSceneTime(t),i/30);if(pageErrors.length)throw Error(pageErrors.join('\n'));await page.screenshot({path:path.join(frames,`f${String(i).padStart(5,'0')}.png`)});if(i%120===0)console.log(`frame ${i}/${Math.round(c.duration*30)}`);}
  const argv=['-nostdin','-hide_banner','-v','error','-n','-framerate','30','-i',path.join(frames,'f%05d.png'),'-i',resolve(c.cameraVideo.path),'-i',resolve(c.terminalVideo.path),'-i',resolve(c.audio.path)];
  if(c.footer.kind==='image')argv.push('-loop','1','-framerate','30');argv.push('-i',resolve(c.footer.path));if(c.header.source)argv.push('-i',resolve(c.header.source.path));
  function sourceFilter(n,v,w,h){let f=`[${n}:v]trim=start=${v.start}:duration=${c.duration},setpts=PTS-STARTPTS`;for(const [x,y,rw,rh] of v.masks??[])f+=`,drawbox=x=${x}:y=${y}:w=${rw}:h=${rh}:color=0x101713:t=fill`;if(v.crop){let [x,y,rw,rh]=v.crop;f+=`,crop=${rw}:${rh}:${x}:${y}`;}return f+`,scale=${w}:${h}:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=${w}:${h}:(ow-iw)/2:(oh-ih)/2:0x101713,fps=30,setsar=1`;}
  const f=[`[0:v]scale=1080:1920:flags=lanczos,setsar=1[base]`,sourceFilter(1,c.cameraVideo,464,264)+'[cam]',sourceFilter(2,c.terminalVideo,464,264)+'[term]','[base][cam]overlay=51:320:shortest=1[b1]','[b1][term]overlay=564:320:shortest=1[b2]',sourceFilter(4,c.footer,1080,232)+'[foot]'];
  if(c.header.source){f.push(sourceFilter(5,c.header.source,1080,280)+'[head]','[b2][head]overlay=0:0:shortest=1[b3]');}
  else{
   const clean=x=>x.replaceAll('\\','').replaceAll('{','').replaceAll('}','');
   const ass=`[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: H,Hiragino Sans GB,74,&H00F8FFF8,&H00101B22,1,1,1,8,30,30,0,1\n[Events]\nFormat: Layer,Start,End,Style,Text\nDialogue: 0,0:00:00.00,0:03:00.00,H,{\\pos(540,25)\\fs40\\c&H64C8FA&}── 织界探索日记 · ${clean(c.episode)} ──\nDialogue: 0,0:00:00.00,0:03:00.00,H,{\\pos(540,95)\\fs${Math.min(74,Math.floor(980/c.header.lines[0].length))}}${clean(c.header.lines[0])}\nDialogue: 0,0:00:00.00,0:03:00.00,H,{\\pos(540,174)\\fs${Math.min(80,Math.floor(980/c.header.lines[1].length))}\\c&H64C8FA&}${clean(c.header.lines[1])}\n`;
   await fs.writeFile(path.join(outDir,'header.ass'),ass,{flag:'wx'});f.push("[b2]drawbox=x=0:y=0:w=1080:h=280:color=0x0a1014:t=fill,ass=header.ass[b3]");
  }
  if(c.footer.kind==='image'){f.push('[b3]drawbox=x=0:y=1688:w=1080:h=232:color=0x1a2227:t=fill[brandbase]','[brandbase][foot]overlay=0:1688:shortest=1[b4]');}else f.push('[b3][foot]overlay=0:1688:shortest=1[b4]');
  if(c.subtitleAss){await fs.copyFile(resolve(c.subtitleAss),path.join(outDir,'captions.ass'));f.push('[b4]ass=captions.ass[v]');}else f.push('[b4]null[v]');
  f.push(`[3:a]atrim=start=${c.audio.start}:duration=${c.duration},asetpts=PTS-STARTPTS,aresample=44100[a]`);
  argv.push('-filter_complex',f.join(';'),'-map','[v]','-map','[a]','-t',String(c.duration),'-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-ac','2','-b:a','192k','-movflags','+faststart',output);
  run(ffmpeg,argv,{cwd:outDir});run(ffmpeg,['-v','error','-xerror','-i',output,'-f','null','-']);
  const digest=buf=>createHash('sha256').update(buf).digest('hex');
  const verification={framework:VERSION,episode:c.episode,aiLabel:label,config:c,layout:LAYOUT,outputSha256:digest(await fs.readFile(output)),probe:probe(output),sourceHashes:{},pageErrors,status:'draft-not-release-approved'};
  for(const p of new Set(inputs))verification.sourceHashes[path.relative(root,p)]=digest(await fs.readFile(p));
  verification.sceneSha256=digest(Buffer.from(sceneText));await fs.writeFile(path.join(outDir,'render-manifest.json'),JSON.stringify(verification,null,2),{flag:'wx'});
  await fs.writeFile(path.join(outDir,'config.resolved.json'),JSON.stringify(c,null,2),{flag:'wx'});console.log('OUTPUT '+output);
 }
 if(pageErrors.length)throw Error(pageErrors.join('\n'));
}finally{if(browser)await browser.close();await new Promise(ok=>server.close(ok));}
