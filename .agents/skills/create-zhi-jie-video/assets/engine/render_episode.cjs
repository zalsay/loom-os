const fs=require('fs'),path=require('path'),{createCanvas,GlobalFonts}=require('@napi-rs/canvas');
const {C,Crayon,makePaper,makeWash,car,plot,child,thought}=require('./crayon_contrast.cjs');
const {drawLogo}=require('./logo.cjs');
GlobalFonts.registerFromPath(path.join(__dirname,'fonts/LXGWWenKai-Regular.ttf'),'WenKai');
const cfg=JSON.parse(fs.readFileSync(path.join(__dirname,'episode.json'),'utf8'));
const W=1080,H=1920,FPS=24,scenes=[];let duration=0;
for(const s of cfg.scenes){scenes.push({...s,a:duration,b:duration+s.duration});duration+=s.duration;}
const paper=makePaper(W,H),wash=makeWash(),page=createCanvas(W,H),output=createCanvas(W,H),g=page.getContext('2d'),og=output.getContext('2d');
const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>{x=clamp(x);return x*x*(3-2*x)};
fs.mkdirSync(path.join(__dirname,'out'),{recursive:true});
function lines(q,ss,x,y,size=52,gap=78,col=C.text,reveal=1){let total=ss.join('').length,count=Math.ceil(total*clamp(reveal));for(let i=0;i<ss.length;i++){q.text(ss[i],x,y+i*gap,size,col,'center',clamp(count/(ss[i].length||1)));count-=ss[i].length;}}
function card(q,ss,x=155,y=570,w=770,h=380){q.poly([[x,y],[x+w,y+7],[x+w-9,y+h],[x-8,y+h-6]],C.paper,.94);lines(q,ss,x+w/2,y+70,44,64,C.ink);}
function object(q,kind,x,y,scale,u){if(kind==='car')car(q,x,y,scale,u*.4,true);else if(kind==='garden')plot(q,x,y,scale,.85,1);else {q.rect(x-90*scale,y-50*scale,180*scale,110*scale,C.teal,.75);q.line([[x-70*scale,y+10*scale],[x,y-30*scale],[x+70*scale,y+10*scale]],C.paper,6);}}
function scene(t,k,u){
 const s=scenes[k],q=new Crayon(g,t),step=Math.floor(u*12)/12;
 g.drawImage(paper,0,0);drawLogo(g,82,106,216);
 if(s.type!=='end'){
  q.text('· '+cfg.header,318,146,31,C.secondary,'left');q.text(String(k+1).padStart(2,'0'),993,147,32,C.secondary,'right');
  const two=s.title.length>1;lines(q,s.title,540,two?264:304,66,84,C.text,u/.65);
  const yy=two?411:366;q.line([[327,yy],[455,yy+3],[590,yy-2],[758,yy+2]],C.mustard,8,.86);
 }
 if(s.type==='idea'){
  child(q,270,765,1.5,0,'think',step);thought(q,745,680,(s.body||[]).slice(0,2));
  object(q,s.illustration,525,1190,1.65,step);
 }
 if(s.type==='build'){
  card(q,s.body);object(q,s.illustration,520,1140,1.8,step);
  child(q,218,1390,.9,0,'build',step);child(q,858,1390,.9,1,'build',step);
 }
 if(s.type==='test'){
  q.line([[185,960],[450,960],[700,1010],[890,1130]],C.olive,6,.7);
  object(q,s.illustration,340+330*ease(u/s.duration),830+210*ease(u/s.duration),1.5,step);
  card(q,s.body,180,1210,720,310);
 }
 if(s.type==='compare'){
  card(q,s.before||[],130,615,385,380);card(q,s.after||[],565,615,385,380);
  q.text(s.before_label||'方案 A',320,544,44,C.coral);q.text(s.after_label||'方案 B',757,544,44,C.teal);
  object(q,s.illustration,520,1250,1.5,step);child(q,210,1430,.75,0,'think',step);child(q,872,1430,.75,1,'build',step);
 }
 if(s.type==='ai'){
  child(q,240,757,1.35,0,u<s.duration*.5?'think':'build',step);card(q,(s.body||[]).slice(0,3),420,535,505,335);
  q.line([[540,930],[540,1020]],C.mustard,5);q.line([[519,997],[540,1020],[561,997]],C.mustard,5);
  card(q,['提问题 · 想办法','一起试 · 共同实现'],155,1090,770,310);
  q.text('Mosaico / Codex · 交互示意',540,1460,32,C.secondary);
 }
 if(s.type==='garden'){
  for(let j=0;j<4;j++){const x=280+j%2*465,y=j<2?715:1160;plot(q,x,y,1.16,.8,j+1);q.text((s.body||[])[j]||'',x+20,y+175,43);}
 }
 if(s.type==='growth'){
  plot(q,534,865,1.55,.85,1);const edge=110+865*ease(u/Math.min(4,s.duration));
  g.save();g.beginPath();g.rect(95,1008,edge-95,486);g.clip();g.drawImage(wash,80,1001,920,525);
  for(let j=0;j<3;j++){let x=382+j*158;q.line([[x,1005],[x+5,1130],[x-21,1232],[x+13,1372],[x-5,1472]],C.paper,8,.98,.3);q.line([[x-11,1204],[x-67,1243],[x-87,1325]],C.paper,5,.98,.3);}g.restore();
  lines(q,(s.body||[]).slice(0,2),540,535,44,60);
 }
 if(s.type==='record'){card(q,s.body,155,565,770,570);child(q,265,1390,1.1,0,'think',step);object(q,s.illustration,740,1340,1.0,step);}
 if(s.type==='end'){
  q.text('织界',540,487,312,C.mustard,'center',clamp(u/.6),6);q.line([[194,675],[421,671],[644,679],[886,675]],C.coral,10,.95);
  lines(q,(s.body||[]).slice(0,2),540,750,60,90);q.text('AI 引导 · 孩子思考 · 共同实现',540,978,36,C.teal);
  object(q,s.illustration,540,1225,1.1,step);child(q,216,1440,.85,0,'happy',step);child(q,864,1440,.85,1,'happy',step);
 }
 lines(q,s.caption||[],540,1607,52,78,C.text,u/.4);
 return page;
}
const previous=new Map();
function render(t){let k=scenes.findIndex(s=>t<s.b);if(k<0)k=scenes.length-1;const u=t-scenes[k].a;
 if(k>0&&u<.55&&!previous.has(k)){scene(scenes[k].a-.1,k-1,scenes[k-1].duration-.1);let old=createCanvas(W,H);old.getContext('2d').drawImage(page,0,0);previous.set(k,old);}
 scene(t,k,u);og.drawImage(paper,0,0);og.save();const z=1+.008*ease(u/scenes[k].duration);og.translate(W/2,H/2);og.scale(z,z);og.drawImage(page,-W/2,-H/2);og.restore();
 if(k>0&&u<.55){const p=ease(u/.55),x=W*(1-p),fold=34+Math.sin(p*Math.PI)*92;og.save();og.beginPath();og.rect(0,0,x,H);og.clip();og.drawImage(previous.get(k),0,0);og.restore();og.beginPath();og.moveTo(x,0);og.bezierCurveTo(x-fold,H*.27,x+fold*.22,H*.69,x,H);og.lineTo(x-fold*.63,H);og.bezierCurveTo(x-fold*1.05,H*.64,x-fold*.86,H*.27,x,0);let gr=og.createLinearGradient(x-fold,0,x+15,0);gr.addColorStop(0,'#142331');gr.addColorStop(.55,'#657a85');gr.addColorStop(1,'#344b5c');og.fillStyle=gr;og.fill();}
}
if(process.argv.includes('--stills')){for(let k=0;k<scenes.length;k++){const t=scenes[k].a+Math.min(2,scenes[k].duration*.65);render(t);fs.writeFileSync(path.join(__dirname,'out',`scene-${String(k+1).padStart(2,'0')}.png`),output.toBuffer('image/png'));if(k>0){render(scenes[k].a+.24);fs.writeFileSync(path.join(__dirname,'out',`turn-${String(k+1).padStart(2,'0')}.png`),output.toBuffer('image/png'));}}process.exit(0);}
if(!process.argv.includes('--raw'))throw Error('Use --stills or --raw');
async function main(){for(let f=0;f<Math.round(duration*FPS);f++){render(f/FPS);if(!process.stdout.write(output.data()))await new Promise(r=>process.stdout.once('drain',r));if(f%120===119&&global.gc)global.gc();if(f%120===0)process.stderr.write(`Episode ${f/FPS}s\n`);}await new Promise(r=>process.stdout.end(r));}
main().catch(e=>{process.stderr.write(String(e));process.exitCode=1;});
