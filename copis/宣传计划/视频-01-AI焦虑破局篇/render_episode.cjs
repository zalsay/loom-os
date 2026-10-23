let canvasLib;
try {
  canvasLib = require('@napi-rs/canvas');
} catch (err) {
  const {spawnSync} = require('child_process');
  const path = require('path');
  const script = path.join(__dirname, 'tools', 'render_engine.py');
  const res = spawnSync('python3', [script, __dirname, ...process.argv.slice(2)], {stdio: 'inherit'});
  process.exit(res.status ?? 1);
}

const fs = require('fs');
const path = require('path');
const {createCanvas, GlobalFonts} = canvasLib;
const {C, Crayon, makePaper, makeWash, car, plot, plant, child, thought} = require('./crayon_contrast.cjs');
const {drawLogo} = require('./logo.cjs');

const fontPath = path.join(__dirname, 'fonts/LXGWWenKai-Regular.ttf');
if (fs.existsSync(fontPath)) {
  GlobalFonts.registerFromPath(fontPath, 'WenKai');
}

const cfg = JSON.parse(fs.readFileSync(path.join(__dirname, 'episode.json'), 'utf8'));
const W = 1080, H = 1920, FPS = 24, scenes = [];
let duration = 0;
for (const s of cfg.scenes) {
  scenes.push({...s, a: duration, b: duration + s.duration});
  duration += s.duration;
}
const paper = makePaper(W, H);
const wash = makeWash();
const page = createCanvas(W, H);
const output = createCanvas(W, H);
const g = page.getContext('2d');
const og = output.getContext('2d');
const clamp = (x) => Math.max(0, Math.min(1, x));
const ease = (x) => {
  x = clamp(x);
  return x * x * (3 - 2 * x);
};
fs.mkdirSync(path.join(__dirname, 'out'), {recursive: true});

function lines(q, ss, x, y, size = 52, gap = 78, col = C.text, reveal = 1) {
  let total = ss.join('').length;
  let count = Math.ceil(total * clamp(reveal));
  for (let i = 0; i < ss.length; i++) {
    if (count <= 0) break;
    let part = ss[i].slice(0, count);
    count -= ss[i].length;
    q.text(part, x, y + i * gap, size, col, 'center', 1);
  }
}

function card(q, body = [], x = 150, y = 500, w = 780, h = 320) {
  q.rect(x, y, w, h, C.paper, 0.94);
  const gap = 62;
  const startY = y + h / 2 - ((body.length - 1) * gap) / 2;
  for (let i = 0; i < body.length; i++) {
    q.text(body[i], x + w / 2, startY + i * gap, 44, C.ink);
  }
}

function object(q, kind, x, y, scale = 1.5, step = 0) {
  if (kind === 'car') {
    car(q, x, y, scale, step);
  } else if (kind === 'garden') {
    plot(q, x, y, scale, 1, 1);
  } else {
    car(q, x - 165, y + 20, scale * 0.72, step);
    plot(q, x + 175, y + 10, scale * 0.72, 1, 1);
  }
}

function scene(t, k, u) {
  const s = scenes[k];
  const step = Math.floor(t * 12) / 12;
  const q = new Crayon(g, t);
  g.clearRect(0, 0, W, H);
  drawLogo(g, 82, 106, 216);
  q.text(`织界 · ${cfg.header || '创造日记'}`, 560, 146, 38, C.secondary);
  q.text(`${k + 1} / ${scenes.length}`, 960, 147, 36, C.secondary, 'right');

  if (s.type !== 'end') {
    const two = s.title.length > 1;
    lines(q, s.title, 540, two ? 264 : 304, 66, 84, C.text, u / 0.65);
    const yy = two ? 411 : 366;
    q.line([[327, yy], [455, yy + 3], [590, yy - 2], [758, yy + 2]], C.mustard, 8, 0.86);
  }

  if (s.type === 'idea') {
    child(q, 270, 765, 1.5, 0, 'think', step);
    thought(q, 745, 680, (s.body || []).slice(0, 2));
    object(q, s.illustration, 525, 1190, 1.65, step);
  }
  if (s.type === 'build') {
    card(q, s.body);
    object(q, s.illustration, 520, 1140, 1.8, step);
    child(q, 218, 1390, 0.9, 0, 'build', step);
    child(q, 858, 1390, 0.9, 1, 'build', step);
  }
  if (s.type === 'test') {
    q.line([[185, 960], [450, 960], [700, 1010], [890, 1130]], C.olive, 6, 0.7);
    object(q, s.illustration, 340 + 330 * ease(u / s.duration), 830 + 210 * ease(u / s.duration), 1.5, step);
    card(q, s.body, 180, 1210, 720, 310);
  }
  if (s.type === 'compare') {
    card(q, s.before || [], 130, 615, 385, 380);
    card(q, s.after || [], 565, 615, 385, 380);
    q.text(s.before_label || '方案 A', 320, 544, 44, C.coral);
    q.text(s.after_label || '方案 B', 757, 544, 44, C.teal);
    object(q, s.illustration, 520, 1250, 1.5, step);
    child(q, 210, 1430, 0.75, 0, 'think', step);
    child(q, 872, 1430, 0.75, 1, 'build', step);
  }
  if (s.type === 'ai') {
    child(q, 240, 757, 1.35, 0, u < s.duration * 0.4 ? 'think' : 'happy', step);
    card(q, s.body || [], 420, 560, 520, 340);
    q.rect(580, 495, 200, 54, C.teal, 0.88);
    q.text('交互示意', 680, 522, 34, C.ink);
    object(q, s.illustration, 520, 1240, 1.55, step);
    child(q, 860, 1390, 0.85, 1, 'build', step);
  }
  if (s.type === 'garden') {
    const tags = ['A1', 'A2', 'B1', 'B2'];
    const coords = [[310, 740], [770, 740], [310, 1210], [770, 1210]];
    for (let i = 0; i < 4; i++) {
      const [px, py] = coords[i];
      plot(q, px, py, 0.95, 1, i + 1, tags[i]);
      if (s.body && s.body[i]) {
        q.rect(px - 150, py + 108, 300, 62, C.paper, 0.92);
        q.text(s.body[i], px, py + 139, 36, C.ink);
      }
    }
  }
  if (s.type === 'growth') {
    const gFactor = 0.35 + 0.65 * ease(u / s.duration);
    plot(q, 540, 960, 1.75, gFactor, 1);
    card(q, s.body || [], 180, 1220, 720, 260);
  }
  if (s.type === 'record') {
    card(q, s.body || [], 150, 520, 780, 420);
    object(q, s.illustration, 540, 1250, 1.55, step);
    child(q, 210, 1410, 0.82, 0, 'happy', step);
    child(q, 870, 1410, 0.82, 1, 'happy', step);
  }
  if (s.type === 'end') {
    lines(q, s.title, 540, 320, 58, 76, C.secondary, u / 0.65);
    q.text('织界', 540, 660, 260, C.mustard, 'center', 1, 8);
    q.line([[280, 820], [540, 824], [800, 818]], C.teal, 8, 0.9);
    q.text('AI 引导，孩子思考，共同实现', 540, 920, 52, C.text);
    card(q, s.body || [], 160, 1080, 760, 250);
    child(q, 280, 1450, 0.85, 0, 'happy', step);
    child(q, 800, 1450, 0.85, 1, 'happy', step);
  }

  if (s.caption && s.caption.length) {
    const cy = s.caption.length > 1 ? 1595 : 1635;
    lines(q, s.caption, 540, cy, 52, 74, C.text, 1);
  }
}

const previous = new Map();
function render(t) {
  let k = scenes.findIndex((s) => t >= s.a && t < s.b);
  if (k < 0) k = scenes.length - 1;
  const u = t - scenes[k].a;
  if (k > 0 && u < 0.55 && !previous.has(k)) {
    scene(scenes[k].a - 0.1, k - 1, scenes[k - 1].duration - 0.1);
    let old = createCanvas(W, H);
    old.getContext('2d').drawImage(page, 0, 0);
    previous.set(k, old);
  }
  scene(t, k, u);
  og.drawImage(paper, 0, 0);
  og.save();
  const z = 1 + 0.008 * ease(u / scenes[k].duration);
  og.translate(W / 2, H / 2);
  og.scale(z, z);
  og.drawImage(page, -W / 2, -H / 2);
  og.restore();
  if (k > 0 && u < 0.55) {
    const p = ease(u / 0.55);
    const x = W * (1 - p);
    const fold = 34 + Math.sin(p * Math.PI) * 92;
    og.save();
    og.beginPath();
    og.rect(0, 0, x, H);
    og.clip();
    og.drawImage(previous.get(k), 0, 0);
    og.restore();
    og.beginPath();
    og.moveTo(x, 0);
    og.bezierCurveTo(x - fold, H * 0.27, x + fold * 0.22, H * 0.69, x, H);
    og.lineTo(x - fold * 0.63, H);
    og.bezierCurveTo(x - fold * 1.05, H * 0.64, x - fold * 0.86, H * 0.27, x, 0);
    let gr = og.createLinearGradient(x - fold, 0, x + 15, 0);
    gr.addColorStop(0, '#142331');
    gr.addColorStop(0.55, '#657a85');
    gr.addColorStop(1, '#344b5c');
    og.fillStyle = gr;
    og.fill();
  }
}

if (process.argv.includes('--stills')) {
  for (let k = 0; k < scenes.length; k++) {
    render(scenes[k].a + Math.min(2, scenes[k].duration * 0.65));
    fs.writeFileSync(path.join(__dirname, 'out', `scene-${String(k + 1).padStart(2, '0')}.png`), output.toBuffer('image/png'));
    if (k > 0) {
      render(scenes[k].a + 0.24);
      fs.writeFileSync(path.join(__dirname, 'out', `turn-${String(k + 1).padStart(2, '0')}.png`), output.toBuffer('image/png'));
    }
  }
  process.exit(0);
}

if (!process.argv.includes('--raw')) throw Error('Use --stills or --raw');

async function main() {
  for (let f = 0; f < Math.round(duration * FPS); f++) {
    render(f / FPS);
    if (!process.stdout.write(output.data())) {
      await new Promise((r) => process.stdout.once('drain', r));
    }
    if (f % 120 === 119 && global.gc) global.gc();
    if (f % 120 === 0) process.stderr.write(`Episode ${f / FPS}s\n`);
  }
  await new Promise((r) => process.stdout.end(r));
}

main().catch((e) => {
  process.stderr.write(String(e));
  process.exitCode = 1;
});