// Style kit for the 50-style library: every style draws the same story (hook / list / stat) with these helpers.
export * from '../ten/shared/kit.js';
import { W, H, clamp, seg, eo, mulberry } from '../ten/shared/kit.js';
const SG = new Intl.Segmenter('th', { granularity: 'grapheme' });
export const glyphs = s => [...SG.segment(s)].map(x => x.segment);
export const F = (fam, px, w = 700) => `${w} ${px}px ${fam}`;
// text. o: f font, c colour (null = no fill), a align, b baseline, sc/sw stroke, sh [colour, blur, dx, dy], al alpha, r rot, s scale, max width
export function T(ctx, s, x, y, o = {}) {
  ctx.save(); ctx.font = o.f; ctx.textAlign = o.a || 'center'; ctx.textBaseline = o.b || 'middle';
  let k = o.s ?? 1; if (o.max) { const w = ctx.measureText(s).width; if (w * k > o.max) k = o.max / w; }
  ctx.translate(x, y); if (o.r) ctx.rotate(o.r); if (k !== 1) ctx.scale(k, k);
  if (o.al != null) ctx.globalAlpha *= clamp(o.al);
  if (o.sh) { ctx.shadowColor = o.sh[0]; ctx.shadowBlur = o.sh[1]; ctx.shadowOffsetX = o.sh[2] || 0; ctx.shadowOffsetY = o.sh[3] || 0; }
  if (o.sc) { ctx.lineWidth = o.sw || 8; ctx.strokeStyle = o.sc; ctx.lineJoin = 'round'; ctx.strokeText(s, 0, 0); if (o.sh) ctx.shadowColor = 'transparent'; }
  if (o.c !== null) { ctx.fillStyle = o.c || '#fff'; ctx.fillText(s, 0, 0); }
  ctx.restore();
}
export function TW(ctx, s, f) { ctx.save(); ctx.font = f; const w = ctx.measureText(s).width; ctx.restore(); return w; }
// per-glyph text: fn(i, n) -> {dx, dy, al, c, s} ; aligned like T (center default)
export function G(ctx, s, x, y, o, fn) {
  const g = glyphs(s); ctx.save(); ctx.font = o.f; ctx.textBaseline = o.b || 'middle'; ctx.textAlign = 'left';
  let k = 1; const tw = ctx.measureText(s).width; if (o.max && tw > o.max) k = o.max / tw;
  ctx.translate(x, y); ctx.scale(k, k); const x0 = (o.a || 'center') === 'center' ? -tw / 2 : o.a === 'right' ? -tw : 0; let pre = '';
  g.forEach((ch, i) => { const px = x0 + ctx.measureText(pre).width; pre += ch; const q = fn(i, g.length) || {}; if (q.al <= 0) return;
    ctx.save(); ctx.globalAlpha *= clamp(q.al ?? 1); ctx.translate(px + (q.dx || 0), q.dy || 0); if (q.s != null && q.s !== 1) { const cw = ctx.measureText(ch).width / 2; ctx.translate(cw, 0); ctx.scale(q.s, q.s); ctx.translate(-cw, 0); }
    if (o.sc) { ctx.lineWidth = o.sw || 8; ctx.strokeStyle = o.sc; ctx.lineJoin = 'round'; ctx.strokeText(ch, 0, 0); }
    ctx.fillStyle = q.c || o.c || '#fff'; ctx.fillText(ch, 0, 0); ctx.restore(); });
  ctx.restore();
}
export const typed = (s, p) => glyphs(s).slice(0, Math.round(glyphs(s).length * clamp(p))).join('');
export const en = (S, d0 = 0, d = .4) => eo(seg(S.lt, d0, d0 + d));
export const ia = (S, i, d = .35) => eo(seg(S.items[i], 0, d));
export function tex(w, h, fn) { const c = new OffscreenCanvas(w, h); fn(c.getContext('2d'), w, h); return c; }
export const grainTex = (seed = 1, n = 30000, cols = ['rgba(0,0,0,.06)', 'rgba(255,255,255,.06)'], sz = 2) => tex(W, H, g => { const R = mulberry(seed); for (let i = 0; i < n; i++) { g.fillStyle = cols[i % cols.length]; g.fillRect(R() * W, R() * H, 1 + R() * sz, 1 + R() * sz); } });
export function vig(ctx, a = .4, col = '0,0,0') { const g = ctx.createRadialGradient(W / 2, H / 2, H * .3, W / 2, H / 2, H * .72); g.addColorStop(0, `rgba(${col},0)`); g.addColorStop(1, `rgba(${col},${a})`); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); }
export function rr(ctx, x, y, w, h, r, fill, stroke, lw) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw || 4; ctx.stroke(); } }
export function grad(ctx, x0, y0, x1, y1, stops) { const g = ctx.createLinearGradient(x0, y0, x1, y1); stops.forEach((c, i) => g.addColorStop(i / (stops.length - 1), c)); return g; }
export function ln(ctx, x0, y0, x1, y1, p, col, lw = 6) { if (p <= 0) return; ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x0 + (x1 - x0) * clamp(p), y0 + (y1 - y0) * clamp(p)); ctx.stroke(); ctx.restore(); }
export function tick(ctx, x, y, s, p, col, lw = 10) { if (p <= 0) return; p = clamp(p); ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.beginPath(); ctx.moveTo(x - s * .5, y); const a = Math.min(1, p * 2.5), b = clamp((p - .4) / .6); ctx.lineTo(x - s * .5 + s * .35 * a, y + s * .35 * a); if (b > 0) ctx.lineTo(x - s * .15 + s * .75 * b, y + s * .35 - s * .85 * b); ctx.stroke(); ctx.restore(); }
export function star(ctx, x, y, r1, r2, n, rot = 0) { ctx.beginPath(); for (let i = 0; i < n * 2; i++) { const a = rot + Math.PI * i / n, r = i % 2 ? r2 : r1; ctx.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r); } ctx.closePath(); }
// draw through a scratch layer then knock speckles out of it (chalk, stamp, worn print)
let scratch;
export function rough(ctx, speck, fn) { scratch ||= new OffscreenCanvas(W, H); const g = scratch.getContext('2d'); g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; g.clearRect(0, 0, W, H); fn(g); g.globalCompositeOperation = 'destination-out'; g.globalAlpha = 1; g.drawImage(speck, 0, 0); ctx.drawImage(scratch, 0, 0); }
export const speckTex = (seed = 5, n = 60000, a = .5, sz = 3) => tex(W, H, g => { const R = mulberry(seed); for (let i = 0; i < n; i++) { g.fillStyle = `rgba(0,0,0,${R() * a})`; g.fillRect(R() * W, R() * H, 1 + R() * sz, 1 + R() * sz); } });
export function scan(ctx, gap = 4, a = .18) { ctx.fillStyle = `rgba(0,0,0,${a})`; for (let y = 0; y < H; y += gap) ctx.fillRect(0, y, W, gap / 2); }
