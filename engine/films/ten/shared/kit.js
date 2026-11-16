// Shared kit for the ten Thai vertical films: VO timeline, Thai text wrap, subtitles, cue collector, boot.
export * from '/core/lib.js';
import { clamp, seg } from '/core/lib.js';
export const W = 1080, H = 1920;
export const clean = s => s.replace(/\[[^\]]*\]\s*/g, '').replace(/\.\.\./g, '…').trim();
export async function loadVO() {
  const v = await (await fetch('vo.json')).json();
  v.lines.forEach(l => { l.say = clean(l.text); });
  v.cur = t => v.lines.find(l => t >= l.t0 - .05 && t < l.t1 + .35);
  return v;
}
// wrap on spaces to lines no wider than maxW (ctx.font must be set); balanced for two lines
export function wrap(ctx, text, maxW) {
  const words = text.split(' '), lines = []; let cur = '';
  for (const w of words) { const n = cur ? cur + ' ' + w : w; if (cur && ctx.measureText(n).width > maxW) { lines.push(cur); cur = w; } else cur = n; }
  if (cur) lines.push(cur);
  if (lines.length === 2) {                       // balance
    let best = lines, bd = Math.abs(ctx.measureText(lines[0]).width - ctx.measureText(lines[1]).width);
    for (let i = 1; i < words.length; i++) { const a = words.slice(0, i).join(' '), b = words.slice(i).join(' '), wa = ctx.measureText(a).width, wb = ctx.measureText(b).width; if (wa <= maxW && wb <= maxW && Math.abs(wa - wb) < bd) { bd = Math.abs(wa - wb); best = [a, b]; } }
    return best;
  }
  return lines;
}
// burned subtitle of the current VO line. o: {font:'600 54px X', size, y (centre of block), color, bg, pad, radius, stroke, maxW, draw(ctx, lines, box)}
export function subs(ctx, t, vo, o = {}) {
  const l = vo.cur(t); if (!l) return;
  const size = o.size ?? 54, lh = size * 1.32, maxW = o.maxW ?? 880;
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.font = o.font || `600 ${size}px Kanit`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  const lines = wrap(ctx, l.say, maxW), bw = Math.max(...lines.map(s => ctx.measureText(s).width)), bh = lines.length * lh;
  const cy = o.y ?? 1250, a = Math.min(seg(t, l.t0 - .05, l.t0 + .1), 1 - seg(t, l.t1 + .2, l.t1 + .35));
  ctx.globalAlpha = a; const pad = o.pad ?? 26, box = [W / 2 - bw / 2 - pad, cy - bh / 2 - pad * .55, bw + pad * 2, bh + pad * 1.1];
  if (o.box) o.box(ctx, box);
  else if (o.bg) { ctx.fillStyle = o.bg; ctx.beginPath(); ctx.roundRect(...box, o.radius ?? 16); ctx.fill(); }
  lines.forEach((s, i) => { const y = cy - bh / 2 + lh * (i + .5);
    if (o.stroke) { ctx.lineWidth = o.strokeW ?? 10; ctx.strokeStyle = o.stroke; ctx.lineJoin = 'round'; ctx.strokeText(s, W / 2, y); }
    if (o.glow) { ctx.shadowColor = o.glow; ctx.shadowBlur = o.glowBlur ?? 18; }
    ctx.fillStyle = o.color || '#fff'; ctx.fillText(s, W / 2, y); ctx.shadowBlur = 0; });
  ctx.restore();
}
export const EV = [];
export const cue = (t, type, x = {}) => EV.push({ t: +(+t).toFixed(3), type, ...x });
export async function boot(fonts, build) {
  await Promise.all(fonts.map(f => document.fonts.load(f, 'กขคง ABC 123')));
  const ctx = document.getElementById('c').getContext('2d');
  const vo = await loadVO(), F = await build(vo, ctx);
  window.DUR = vo.dur; window.EV = EV.sort((a, b) => a.t - b.t);
  window.render = t => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none'; ctx.shadowBlur = 0; F(ctx, t); };
  window.READY = true;
}
// fit text to a width by shrinking the font size; returns size used. fontFn = px => css font
export function fitText(ctx, text, maxW, px, fontFn) { ctx.font = fontFn(px); const w = ctx.measureText(text).width; if (w > maxW) { px = px * maxW / w; ctx.font = fontFn(px); } return px; }
export const pop = (t, t0, d = .35) => { const u = clamp((t - t0) / d); return u <= 0 ? 0 : 1 + Math.sin(u * Math.PI) * .18 * (1 - u) - (1 - u) ** 3; };
