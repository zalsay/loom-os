const {createCanvas} = require('@napi-rs/canvas');

const C = {
  background: '#2b3b49',
  paper: '#fff3da',
  text: '#fff3da',
  secondary: '#d6e0e0',
  tealInk: '#217b68',
  coralInk: '#c64832',
  blueInk: '#28698c',
  ink: '#302924',
  coral: '#ff7961',
  blue: '#57bdeb',
  mustard: '#ffd052',
  green: '#8cd66a',
  olive: '#c5df81',
  teal: '#63ddc3',
  soil: '#c18b60',
  skin: '#ffd4aa',
  rose: '#ffaaa0',
  white: '#fffaf1',
};

const rnd = (n) => {
  let x = Math.sin(n * 127.1 + 91.7) * 43758.5453123;
  return x - Math.floor(x);
};

const patterns = new Map();
function wax(g, col, p = 0.8) {
  let key = col + '-' + p;
  if (!patterns.has(key)) {
    const c = createCanvas(128, 128);
    const cx = c.getContext('2d');
    const im = cx.createImageData(128, 128);
    const rgb = col.slice(1).match(/../g).map((x) => parseInt(x, 16));
    let state = 3187;
    for (let i = 0; i < 128 * 128; i++) {
      state = (Math.imul(state, 1664525) + 1013904223) | 0;
      let tooth = (state >>> 0) / 4294967296;
      let fibre = 0.09 * Math.sin((i % 128) * 0.13 + Math.floor(i / 128) * 0.8);
      let a = Math.max(0, Math.min(1, (tooth + fibre - (1 - p)) * 7));
      for (let j = 0; j < 3; j++) im.data[i * 4 + j] = rgb[j];
      im.data[i * 4 + 3] = Math.floor(a * 238);
    }
    cx.putImageData(im, 0, 0);
    patterns.set(key, c);
  }
  const patkey = 'pattern-' + key;
  if (!patterns.has(patkey)) {
    patterns.set(patkey, g.createPattern(patterns.get(key), 'repeat'));
  }
  return patterns.get(patkey);
}

function makePaper(w, h) {
  const c = createCanvas(w, h);
  const g = c.getContext('2d');
  const im = g.createImageData(w, h);
  const rgb = C.background.slice(1).match(/../g).map((x) => parseInt(x, 16));
  let state = 71923;
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      state = (Math.imul(state, 1664525) + 1013904223) | 0;
      let n = (state >>> 0) / 4294967296 - 0.5;
      let v =
        n * 5 +
        Math.sin(y * 1.87 + x * 0.09) * 0.6 +
        Math.sin(x * 0.03 + y * 0.02) * 0.6 +
        Math.cos(x * 0.008 - y * 0.014) * 0.8;
      let i = (y * w + x) * 4;
      for (let j = 0; j < 3; j++) im.data[i + j] = rgb[j] + v;
      im.data[i + 3] = 255;
    }
  }
  g.putImageData(im, 0, 0);
  const gr = g.createRadialGradient(w * 0.49, h * 0.43, h * 0.1, w * 0.49, h * 0.43, h * 0.7);
  gr.addColorStop(0, '#a4bfd00c');
  gr.addColorStop(0.55, '#a4bfd000');
  gr.addColorStop(1, '#09131c4a');
  g.fillStyle = gr;
  g.fillRect(0, 0, w, h);
  return c;
}

class Crayon {
  constructor(g, t = 0) {
    this.g = g;
    this.frame = Math.floor(t * 12);
    this.boil = this.frame % 3;
    this.id = 0;
  }

  line(points, col = C.ink, w = 4, p = 0.9, boil = 1) {
    const g = this.g;
    const id = this.id++;
    const seed = id * 11 + this.boil * 3;
    g.beginPath();
    let index = 0;
    for (let i = 1; i < points.length; i++) {
      const [x0, y0] = points[i - 1];
      const [x1, y1] = points[i];
      const dist = Math.hypot(x1 - x0, y1 - y0);
      const steps = Math.max(1, Math.ceil(dist / 18));
      for (let s = 0; s <= steps; s++) {
        const f = s / steps;
        const jx = (rnd(seed + index++) - 0.5) * 1.8 * boil;
        const jy = (rnd(seed + index++) - 0.5) * 1.8 * boil;
        const x = x0 + (x1 - x0) * f + jx;
        const y = y0 + (y1 - y0) * f + jy;
        if (i === 1 && s === 0) g.moveTo(x, y);
        else g.lineTo(x, y);
      }
    }
    g.strokeStyle = wax(g, col, p);
    g.lineWidth = w;
    g.lineCap = 'round';
    g.lineJoin = 'round';
    g.stroke();
  }

  poly(points, col, p = 0.75, outline = true, width = 3.5) {
    const g = this.g;
    g.beginPath();
    points.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
    g.closePath();
    g.fillStyle = C.paper;
    g.fill();
    g.save();
    g.globalAlpha = 0.22;
    g.fillStyle = col;
    g.fill();
    g.restore();
    g.fillStyle = wax(g, col, Math.max(0.2, p - 0.22));
    g.fill();
    g.save();
    let mx = points.reduce((s, v) => s + v[0], 0) / points.length;
    let my = points.reduce((s, v) => s + v[1], 0) / points.length;
    g.beginPath();
    points.forEach(([x, y], i) =>
      i
        ? g.lineTo(mx + (x - mx) * 1.018, my + (y - my) * 1.018)
        : g.moveTo(mx + (x - mx) * 1.018, my + (y - my) * 1.018)
    );
    g.closePath();
    g.clip();
    let xs = points.map((v) => v[0]);
    let ys = points.map((v) => v[1]);
    let x0 = Math.min(...xs) - 5;
    let x1 = Math.max(...xs) + 5;
    let y0 = Math.min(...ys) - 5;
    let y1 = Math.max(...ys) + 5;
    g.strokeStyle = wax(g, col, p);
    g.lineWidth = 4.6;
    g.lineCap = 'round';
    for (let y = y0; y <= y1; y += 7) {
      g.beginPath();
      g.moveTo(x0, y + (rnd(y + this.boil) - 0.5) * 2);
      g.lineTo(x1, y + (rnd(y + 9 + this.boil) - 0.5) * 2);
      g.stroke();
    }
    if (y1 - y0 > 65) {
      g.globalAlpha = 0.28;
      g.lineWidth = 2;
      for (let x = x0; x <= x1; x += 11) {
        g.beginPath();
        g.moveTo(x, y0);
        g.lineTo(x, y1);
        g.stroke();
      }
    }
    g.restore();
    if (outline) {
      if (x1 - x0 > 80 && y1 - y0 > 45) {
        this.line([...points, points[0]], C.paper, width + 2.3, 0.8, 0.35);
      }
      this.line([...points, points[0]], C.ink, width, 0.96);
    }
  }

  ellipse(x, y, rx, ry, col, p = 0.7, rotation = 0, outline = true) {
    let pts = [];
    for (let i = 0; i < 36; i++) {
      let a = (i / 36) * Math.PI * 2;
      let xx = Math.cos(a) * rx;
      let yy = Math.sin(a) * ry;
      pts.push([
        x + xx * Math.cos(rotation) - yy * Math.sin(rotation),
        y + xx * Math.sin(rotation) + yy * Math.cos(rotation),
      ]);
    }
    this.poly(pts, col, p, outline);
  }

  rect(x, y, w, h, col, p = 0.7) {
    this.poly(
      [
        [x, y],
        [x + w, y - 1],
        [x + w + 1, y + h],
        [x - 1, y + h + 1],
      ],
      col,
      p
    );
  }

  text(s, x, y, size = 54, col = C.text, align = 'center', reveal = 1, strokeWidth = 0) {
    const g = this.g;
    g.font = `${size}px WenKai`;
    let widths = [...s].map((a) => g.measureText(a).width);
    let total = widths.reduce((a, b) => a + b, 0);
    let xx = x - (align === 'center' ? total / 2 : align === 'right' ? total : 0);
    let num = Math.ceil(s.length * Math.min(1, reveal));
    g.textBaseline = 'middle';
    g.textAlign = 'center';
    for (let i = 0; i < num; i++) {
      let a = s[i];
      let ww = widths[i];
      g.save();
      g.translate(xx + ww / 2, y + (rnd(i * 17 + this.boil) - 0.5) * 1.2);
      g.rotate((rnd(i * 31 + this.boil) - 0.5) * 0.02);
      if (strokeWidth > 0) {
        g.strokeStyle = col;
        g.lineWidth = strokeWidth;
        g.lineJoin = 'round';
        g.strokeText(a, 0, 0);
      }
      g.fillStyle = wax(g, col, 0.98);
      g.fillText(a, 0, 0);
      g.restore();
      xx += ww;
    }
  }
}

function tire(q, x, y, r, t, near = true) {
  q.ellipse(x, y, r, r * 0.98, C.ink, 0.92);
  q.ellipse(x, y, r * 0.61, r * 0.61, C.mustard, 0.78);
  q.ellipse(x, y, r * 0.22, r * 0.22, C.paper, 0.9);
  for (let i = 0; i < 12; i++) {
    let a = (i / 12) * Math.PI * 2 + t;
    q.line(
      [
        [x + Math.cos(a) * r * 0.79, y + Math.sin(a) * r * 0.79],
        [x + Math.cos(a + 0.08) * r * 0.95, y + Math.sin(a + 0.08) * r * 0.95],
      ],
      C.paper,
      1.7,
      0.75
    );
  }
  for (let i = 0; i < 5; i++) {
    let a = (i / 5) * Math.PI * 2 + t;
    q.ellipse(x + Math.cos(a) * r * 0.43, y + Math.sin(a) * r * 0.43, 3, 3, C.ink, 0.9);
  }
}

function car(q, x, y, s = 1, t = 0, wide = false) {
  const g = q.g;
  g.save();
  g.translate(x, y);
  g.scale(s, s);
  let col = wide ? C.blue : C.mustard;
  let span = wide ? 145 : 125;
  tire(q, -span, -28, 30, t, false);
  tire(q, span, -25, 30, t, false);
  q.poly([[-173, -48], [143, -48], [203, -18], [-113, -18]], col, 0.68);
  q.poly([[-113, -18], [203, -18], [203, 28], [-113, 28]], col, 0.78);
  q.poly([[-173, -48], [-113, -18], [-113, 28], [-173, -1]], col, 0.7);
  for (let i = 0; i < 11; i++) {
    q.ellipse(-98 + i * 27, 4, 5.5, 5.5, C.ink, 0.96);
    q.ellipse(-129 + i * 27, -38, 5, 3.5, C.mustard, 0.94);
  }
  for (let i = 0; i < 8; i++) q.ellipse(-87 + i * 30, -24, 5, 3.5, C.mustard, 0.94);
  q.rect(-95, -83, 92, 42, C.blue, 0.8);
  q.line([[-48, -82], [-48, -42]], C.ink, 2);
  for (let xx of [-75, -28]) {
    q.ellipse(xx, -62, 11, 11, C.paper, 0.65);
    q.line([[xx - 5, -62], [xx + 5, -62]], C.ink, 2);
    q.line([[xx, -67], [xx, -57]], C.ink, 2);
  }
  q.rect(70, -83, 66, 36, C.coral, 0.7);
  for (let j = 0; j < 7; j++) q.line([[80 + j * 7, -82], [80 + j * 7, -50]], C.ink, 3);
  q.rect(145, -62, 32, 27, C.teal, 0.75);
  for (let i = 0; i < 4; i++) q.line([[143, -58 + i * 6], [137, -58 + i * 6]], C.ink, 1.7);
  q.line([[-3, -57], [17, -73], [43, -55], [70, -59]], C.coral, 2.5);
  q.line([[-3, -49], [22, -62], [49, -47], [70, -48]], C.ink, 2);
  q.rect(-6, -86, 37, 40, C.teal, 0.6);
  q.ellipse(12, -85, 19, 7, C.teal, 0.8);
  q.rect(0, -100, 25, 12, C.blue, 0.8);
  q.ellipse(12, -101, 13, 4, C.blue, 0.8);
  q.line([[4, -78], [4, -57]], C.paper, 3, 0.95);
  tire(q, -105, 29, 39, t);
  tire(q, 175, 29, 39, t);
  q.line([[-127, 27], [-149, 27]], C.ink, 4);
  q.rect(-143, 10, 18, 32, C.mustard, 0.8);
  q.ellipse(-137, 24, 8, 8, C.paper, 0.8);
  for (let i = 0; i < 7; i++) {
    let a = (i / 7) * Math.PI * 2;
    q.line(
      [
        [-137 + Math.cos(a) * 7, 24 + Math.sin(a) * 7],
        [-137 + Math.cos(a) * 12, 24 + Math.sin(a) * 12],
      ],
      C.ink,
      2
    );
  }
  g.restore();
}

function leaf(q, x, y, angle, length, width, col) {
  let g = q.g;
  g.save();
  g.translate(x, y);
  g.rotate(angle);
  let pts = [];
  for (let i = 0; i <= 14; i++) {
    let f = i / 14;
    pts.push([Math.sin(Math.PI * f) * width, -f * length]);
  }
  for (let i = 13; i >= 0; i--) {
    let f = i / 14;
    pts.push([-Math.sin(Math.PI * f) * width, -f * length]);
  }
  q.poly(pts, col, 0.72, true, 2.2);
  q.line([[0, 0], [0, -length]], C.olive, 2, 0.83);
  for (let j = 1; j < 4; j++) {
    q.line([[0, (-length * j) / 4], [width * 0.65, (-length * j) / 4 - 9]], C.olive, 1, 0.75);
  }
  g.restore();
}

function plant(q, x, y, height = 100, kind = 0, grow = 1) {
  height *= grow;
  q.line([[x, y], [x + 5, y - height]], C.green, 4, 0.9);
  let col = kind === 2 ? C.olive : C.green;
  for (let j = 0; j < 5; j++) {
    let yy = y - height * (0.2 + j * 0.15);
    leaf(q, x + 3, yy, j % 2 ? -0.9 : 0.9, (kind === 2 ? 66 : 56) * grow, (kind === 1 ? 16 : kind === 2 ? 7 : 11) * grow, col);
  }
  leaf(q, x + 5, y - height + 0.1, 0, 30 * grow, 11 * grow, C.green);
}

function plot(q, x, y, s = 1, grow = 1, id = 1, label = null) {
  let g = q.g;
  g.save();
  g.translate(x, y);
  g.scale(s, s);
  const tag = label || ('A' + id);
  q.poly([[-158, -15], [122, -15], [178, 22], [-102, 22]], C.olive, 0.7);
  q.poly([[-102, 22], [178, 22], [178, 92], [-102, 92]], C.green, 0.67);
  q.poly([[-158, -15], [-102, 22], [-102, 92], [-158, 52]], C.green, 0.6);
  q.poly([[-142, -13], [112, -13], [155, 14], [-96, 14]], C.soil, 0.53);
  for (let i = 0; i < 43; i++) {
    let xx = -135 + rnd(i + 61) * 264;
    let yy = -10 + rnd(i + 19) * 24;
    q.ellipse(xx, yy, 1.2 + rnd(i + 93) * 1.8, 1.2, C.soil, 0.82);
  }
  for (let xx of [-64, -26, 13, 50, 88, 128]) q.line([[xx, 31], [xx, 81]], C.olive, 2, 0.85);
  q.rect(8, 43, 76, 30, C.paper, 0.92);
  q.text(tag, 46, 59, 23, C.ink);
  q.line([[178, 41], [198, 49], [198, 70], [179, 62]], C.paper, 6.5, 0.85);
  q.line([[-155, 8], [-172, 11], [-172, 32], [-153, 30]], C.paper, 6.5, 0.85);
  q.line([[178, 41], [198, 49], [198, 70], [179, 62]], C.ink, 4);
  q.line([[-155, 8], [-172, 11], [-172, 32], [-153, 30]], C.ink, 4);
  for (let xx of [-83, 116]) q.line([[xx, 81], [xx + 11, 81]], C.ink, 2);
  for (let j = 0; j < 3; j++) plant(q, -100 + j * 101, 7 + j * 2, 100 + rnd(j + id * 8) * 30, id % 3, grow);
  q.line([[136, 6], [136, -116]], C.soil, 4);
  q.rect(115, -132, 60, 34, C.paper, 0.9);
  q.text(tag, 145, -115, 27, C.ink);
  g.restore();
}

function child(q, x, y, s = 1, which = 0, pose = 'happy', t = 0) {
  let g = q.g;
  g.save();
  g.translate(x, y);
  g.scale(s, s);
  let colour = which ? C.blue : C.coral;
  let bb = pose === 'happy' ? (Math.floor(t * 2) % 2) * 2 : 0;
  q.line([[-18, 37], [-29, 100]], C.paper, 17, 0.9);
  q.line([[18, 37], [29, 100]], C.paper, 17, 0.9);
  q.line([[-18, 37], [-29, 100]], C.ink, 13);
  q.line([[18, 37], [29, 100]], C.ink, 13);
  q.ellipse(-31, 104, 22, 10, C.mustard, 0.9);
  q.ellipse(33, 104, 22, 10, C.mustard, 0.9);
  q.poly([[-39, -46], [39, -46], [50, 40], [-46, 40]], colour, 0.8);
  q.line([[-35, -35], [-60, -8], [-81, pose === 'think' ? -65 : 12 - bb]], C.skin, 18);
  q.line([[37, -33], [60, -3], [91, pose === 'build' ? -22 : pose === 'happy' ? -77 : 11]], C.skin, 18);
  q.ellipse(-81, pose === 'think' ? -65 : 12 - bb, 12, 13, C.skin, 0.85);
  q.ellipse(91, pose === 'build' ? -22 : pose === 'happy' ? -77 : 11, 12, 13, C.skin, 0.85);
  q.ellipse(0, -104, 45, 47, C.skin, 0.67);
  let hair = which
    ? [[-44, -109], [-42, -143], [-18, -154], [11, -151], [39, -132], [42, -108], [20, -130], [-12, -127], [-29, -110]]
    : [[-44, -107], [-47, -139], [-22, -158], [16, -154], [43, -139], [46, -111], [25, -119], [20, -139], [-5, -125], [-22, -134]];
  q.poly(hair, C.ink, 0.94);
  q.ellipse(-15, -103, 4, 5, C.ink, 0.96);
  q.ellipse(17, -103, 4, 5, C.ink, 0.96);
  q.ellipse(-16, -105, 1, 1, C.white, 0.99, 0, false);
  q.ellipse(16, -105, 1, 1, C.white, 0.99, 0, false);
  q.ellipse(-29, -86, 7, 4, C.rose, 0.6, 0, false);
  q.ellipse(29, -86, 7, 4, C.rose, 0.6, 0, false);
  q.line([[-10, -81], [0, pose === 'think' ? -83 : -74], [10, -80]], C.ink, 2.5);
  if (pose === 'think') {
    q.line([[-24, -116], [-10, -121]], C.ink, 2);
    q.line([[12, -121], [25, -116]], C.ink, 2);
  }
  q.line([[-6, -38], [-6, 22]], C.paper, 1.5);
  q.ellipse(7, 3, 2, 2, C.mustard, 0.9);
  g.restore();
}

function thought(q, x, y, lines) {
  q.poly(
    [
      [x - 175, y - 57],
      [x + 180, y - 53],
      [x + 184, y + 55],
      [x - 85, y + 57],
      [x - 137, y + 89],
      [x - 127, y + 54],
      [x - 180, y + 51],
    ],
    C.paper,
    0.95
  );
  for (let i = 0; i < lines.length; i++) {
    q.text(lines[i], x + 4, y - 18 + (i - (lines.length - 1) / 2) * 48, 42, C.ink);
  }
}

function makeWash() {
  const c = createCanvas(1560, 1560);
  const g = c.getContext('2d');
  const im = g.createImageData(1560, 1560);
  const rgb = C.teal.slice(1).match(/../g).map((x) => parseInt(x, 16));
  const lerp = (a, b, f) => a + (b - a) * f;
  for (let y = 0; y < 1560; y++) {
    for (let x = 0; x < 1560; x++) {
      let dx = Math.abs(x - 780) - 420;
      let dy = Math.abs(y - 780) - 620;
      let d = -(Math.hypot(Math.max(dx, 0), Math.max(dy, 0)) + Math.min(Math.max(dx, dy), 0) - 48);
      if (d <= 0) continue;
      let ix = Math.floor(x / 40);
      let iy = Math.floor(y / 40);
      let fx = x / 40 - ix;
      let fy = y / 40 - iy;
      let no = lerp(
        lerp(rnd(ix + iy * 73), rnd(ix + 1 + iy * 73), fx),
        lerp(rnd(ix + (iy + 1) * 73), rnd(ix + 1 + (iy + 1) * 73), fx),
        fy
      );
      let pool = Math.exp(-d / 7) * 0.18;
      let alpha = (0.58 + 0.14 * no + pool + 0.05 * (rnd(x + y * 1560) - 0.5)) * Math.min(1, d / 3);
      let i = (y * 1560 + x) * 4;
      for (let j = 0; j < 3; j++) im.data[i + j] = rgb[j];
      im.data[i + 3] = Math.round(alpha * 255);
    }
  }
  g.putImageData(im, 0, 0);
  return c;
}

module.exports = {C, Crayon, makePaper, makeWash, car, plot, plant, child, thought, rnd};