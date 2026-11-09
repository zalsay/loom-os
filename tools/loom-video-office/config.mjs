// Pure configuration validation. Paths are project-relative, not relative to this module.
export const VERSION='1.0.0';
export const LAYOUT={width:1080,height:1920,fps:30,header:[0,0,1080,280],footer:[0,1688,1080,232],left:[51,320,464,264],right:[564,320,464,264]};
function number(v,label,min,max){if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw Error(`${label}: expected finite ${min}..${max}`);return v;}
function vector(v,label,n){if(!Array.isArray(v)||v.length!==n)throw Error(`${label}: expected ${n} numbers`);v.forEach(x=>number(x,label,-100,100));return v;}
function text(v,label){if(typeof v!=='string'||!v.trim()||/[\x00-\x1f]/.test(v))throw Error(`${label}: missing or invalid string`);return v;}
function rect(v,label){if(!Array.isArray(v)||v.length!==4||!v.every(Number.isInteger)||v[0]<0||v[1]<0||v[2]<=0||v[3]<=0)throw Error(`${label}: expected [x,y,width,height] integer rectangle`);return v;}
function media(v,label,{start=true}={}){if(!v||typeof v!=='object')throw Error(`${label}: required`);text(v.path,label+'.path');if(start)number(v.start??0,label+'.start',0,86400);if(v.crop)rect(v.crop,label+'.crop');for(const r of v.masks??[])rect(r,label+'.masks');return {...v,start:v.start??0};}
export function normalize(raw){
 const c=structuredClone(raw);if(c.schemaVersion!==1)throw Error('schemaVersion must be 1');
 number(c.duration,'duration',2,120);if(Math.abs(c.duration*30-Math.round(c.duration*30))>1e-6)throw Error('duration must align to 30fps');
 text(c.episode,'episode');text(c.outputDir,'outputDir');c.outputName=c.outputName??`${c.episode}-office.mp4`;
 if(!/^[^/\\]+\.mp4$/.test(c.outputName)||c.outputName.includes('..'))throw Error('outputName must be a plain .mp4 filename');
 text(c.model,'model');c.dependencies=c.dependencies??'logo/panda-3d/node_modules';text(c.dependencies,'dependencies');
 c.cameraVideo=media(c.cameraVideo,'cameraVideo');c.terminalVideo=media(c.terminalVideo,'terminalVideo');c.audio=media(c.audio,'audio');
 if(c.header?.source)c.header.source=media(c.header.source,'header.source');
 else {if(!Array.isArray(c.header?.lines)||c.header.lines.length!==2)throw Error('header requires source or two lines');c.header.lines.forEach(x=>text(x,'header.lines'));}
 c.footer=media(c.footer,'footer');if(!['image','video'].includes(c.footer.kind))throw Error('footer.kind must be image or video');
 if(c.subtitleAss)text(c.subtitleAss,'subtitleAss');
 c.pixelRatio=number(c.pixelRatio??1,'pixelRatio',1,2);c.scrollRowsPerSecond=number(c.scrollRowsPerSecond??1.55,'scrollRowsPerSecond',0,5);
 c.camera={from:[5,5.2,18.5],to:[3.2,4.35,11.8],lookFrom:[-.5,1.7,-.3],lookTo:[-.25,2.1,.45],holdStart:.8,travelDuration:c.duration-1.8,gaitHz:.55,gaitStrength:1,...c.camera};
 for(const k of ['from','to','lookFrom','lookTo'])vector(c.camera[k],'camera.'+k,3);
 number(c.camera.holdStart,'camera.holdStart',0,c.duration);number(c.camera.travelDuration,'camera.travelDuration',.1,c.duration);
 if(c.camera.holdStart+c.camera.travelDuration>c.duration)throw Error('camera travel exceeds duration');
 number(c.camera.gaitHz,'camera.gaitHz',.1,1.5);number(c.camera.gaitStrength,'camera.gaitStrength',0,2);
 // Persistent on-screen label is a project-level default, not a per-episode toggle.
 c.aiLabel='含AI生成视频';return c;
}
export function checkBounds(input,probe,label,duration){
 const v=probe.streams.find(s=>s.codec_type==='video');if(!v)throw Error(label+': no video stream');
 for(const r of [input.crop,...(input.masks??[])].filter(Boolean))if(r[0]+r[2]>v.width||r[1]+r[3]>v.height)throw Error(label+': crop/mask exceeds source dimensions');
 if(duration!==null){const available=Number(probe.format.duration);if(!Number.isFinite(available)||input.start+duration>available+.04)throw Error(label+': source duration insufficient');}
}
export function assertSafeOutput(output,inputs){if(inputs.includes(output))throw Error('output must not overwrite an input');}
