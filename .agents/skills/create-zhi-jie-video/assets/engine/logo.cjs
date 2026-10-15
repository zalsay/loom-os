// Original geometric Zhi Jie wordmark and interwoven circuit-window emblem.
const fs=require('fs'),path=require('path'),{createCanvas,Path2D}=require('@napi-rs/canvas');
const design=require('./logo-design.json'),LW=270,LH=100;
function makeLogo(scale=4){
 const c=createCanvas(LW*scale,LH*scale),g=c.getContext('2d');g.scale(scale,scale);
 g.lineJoin='round';g.lineCap='round';
 function rail(d,col,width=8,glow=true,blur=3){const p=new Path2D(d);
  if(glow){g.save();g.globalAlpha=.24;g.strokeStyle=col;g.lineWidth=width;g.shadowColor=col;g.shadowBlur=scale*blur;g.stroke(p);g.restore();}
  g.strokeStyle=col;g.lineWidth=width;g.stroke(p);
 }
 for(const p of design.rails)rail(p.d,p.color);
 for(const p of design.crossings)rail(p.d,p.color,8,false);
 for(const n of design.nodes){g.beginPath();g.arc(n.x,n.y,3,0,Math.PI*2);g.fillStyle='#e9ffff';g.fill();}
 rail(design.core.pins,'#a3fff7',1.2,false);
 rail(design.core.body,'#a3fff7',1.4,false);
 for(const t of design.core.tiles){g.fillStyle=t.color;g.fillRect(t.x,t.y,t.size,t.size);}
 g.lineWidth=5.4;g.strokeStyle='#f0fbff';g.lineCap='square';g.lineJoin='bevel';
 for(const p of design.wordmark){
  g.save();g.translate(p.x,18);g.stroke(new Path2D(p.d));
  if(p.circuit){
   g.lineCap='round';g.lineJoin='round';
   for(const r of p.circuit.rails)rail(r.d,r.color,p.circuit.width,true,1.6);
   for(const r of p.circuit.crossings)rail(r.d,r.color,p.circuit.width,false);
   for(const n of p.circuit.nodes){g.save();g.shadowColor='#e9ffff';g.shadowBlur=scale*1.6;g.beginPath();g.arc(n.x,n.y,1.15,0,Math.PI*2);g.fillStyle='#e9ffff';g.fill();g.restore();}
  }
  g.restore();
 }
 return c;
}
const logo=makeLogo();
function drawLogo(g,x=82,y=42,width=216){g.drawImage(logo,x,y,width,width*LH/LW);}
if(process.argv.includes('--export'))fs.writeFileSync(path.join(__dirname,'Zhi-Jie-logo.png'),logo.toBuffer('image/png'));
module.exports={drawLogo,makeLogo,LW,LH};
