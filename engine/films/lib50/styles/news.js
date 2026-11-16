// หนังสือพิมพ์ — newsprint, masthead, serif headline, column rules, halftone block
import { W, H, T, TW, G, F, en, ia, tex, grainTex, speckTex, rough, vig, rr, grad, ln, tick, star, scan, typed, seg, eo, eio, back, clamp, lerp, mulberry, pop, TAU } from '../sk.js';
const paper = tex(W, H, g => { g.fillStyle = '#e9e3d2'; g.fillRect(0, 0, W, H); const R = mulberry(8); for (let i = 0; i < 50000; i++) { g.fillStyle = R() < .5 ? 'rgba(60,50,30,.05)' : 'rgba(255,255,255,.12)'; g.fillRect(R() * W, R() * H, 1 + R() * 2, 1 + R() * 2); } });
const INK = '#1b1a17', RED = '#b3261e', sp = speckTex(21, 30000, .45, 2);
const mast = (ctx, S) => { T(ctx, 'ข่าวร้านออนไลน์', 540, 190, { f: F('Pridi', 96, 600), c: INK }); ctx.fillStyle = INK; ctx.fillRect(70, 255, 940, 8); ctx.fillRect(70, 270, 940, 2); T(ctx, 'ฉบับพิเศษ', 70, 305, { f: F('Sarabun', 30), c: INK, a: 'left' }); T(ctx, 'ราคา 0 บาท', 1010, 305, { f: F('Sarabun', 30), c: INK, a: 'right' }); ctx.fillRect(70, 332, 940, 2); };
const greek = (ctx, x, y, w, n, p) => { ctx.fillStyle = 'rgba(27,26,23,.28)'; for (let i = 0; i < n * clamp(p); i++) ctx.fillRect(x, y + i * 26, w * (i % 4 === 3 ? .6 : 1), 9); };
export default { name: 'news', th: 'หนังสือพิมพ์', fonts: ['600 80px Pridi', '400 80px Pridi', '700 40px Sarabun'], music: { bpm: 108, prog: 'dorian', lead: 'piano', arp: [0, null, 2, 1, null, 3, null, 2], drums: 'b', bass: 'bass', lead_v: .5 }, sfx: { item: 'key', hit: 'paper', turn: 'paper' },
  sub: { font: '700 50px Sarabun', size: 50, color: '#fff', bg: 'rgba(27,26,23,.9)', radius: 0 },
  bg: (ctx, S) => { ctx.drawImage(paper, 0, 0); },
  hook: (ctx, S) => rough(ctx, sp, g => { const h = S.story.hook; mast(g, S); const u = en(S, .1, .3); g.fillStyle = RED; g.fillRect(70, 400, 260 * u, 64); T(g, 'ด่วน!', 200, 432, { f: F('Sarabun', 44), c: '#fff', al: u });
    T(g, h[0], 70, 580, { f: F('Pridi', 96, 600), c: INK, a: 'left', al: en(S, .3), max: 940 }); T(g, h[1], 70, 730, { f: F('Pridi', 118, 600), c: INK, a: 'left', al: en(S, .7), max: 940 });
    T(g, h[2], 70, 930, { f: F('Pridi', 210, 600), c: RED, a: 'left', al: en(S, 1.2, .2), max: 940 }); g.fillStyle = INK; g.fillRect(70, 1050, 940 * en(S, 1.4), 4); greek(g, 70, 1090, 450, 9, en(S, 1.5, .6)); greek(g, 560, 1090, 450, 9, en(S, 1.7, .6)); }),
  list: (ctx, S) => rough(ctx, sp, g => { const l = S.story.list; mast(g, S); T(g, l.title, 540, 470, { f: F('Pridi', 130, 600), c: INK, al: en(S, 0), max: 940 }); g.fillStyle = INK; g.fillRect(70, 570, 940, 4);
    l.items.forEach((s, i) => { const a = ia(S, i), y = 700 + i * 190; if (a <= 0) return; T(g, String(i + 1), 150, y, { f: F('Pridi', 150, 600), c: RED, al: a }); T(g, s, 250, y - 14, { f: F('Pridi', 88, 600), c: INK, a: 'left', al: a, max: 740 }); greek(g, 252, y + 48, 700, 2, a); g.fillStyle = 'rgba(27,26,23,.5)'; g.fillRect(70, y + 108, 940 * a, 2); }); }),
  stat: (ctx, S) => rough(ctx, sp, g => { const s = S.story.stat; mast(g, S); T(g, s.label, 540, 450, { f: F('Pridi', 78, 600), c: INK, al: en(S, .1), max: 940 });
    T(g, S.N, 400, 800, { f: F('Pridi', 560, 600), c: RED, al: eo(seg(S.statAge, -.1, .15)) }); T(g, s.unit, 800, 900, { f: F('Pridi', 110, 600), c: INK, al: eo(seg(S.statAge, .3, .6)), max: 380 });
    g.fillStyle = INK; g.fillRect(70, 1110, 940, 6); const e = eo(seg(S.endAge, 0, .3)); g.fillStyle = INK; g.fillRect(70, 1160, 940 * e, 120); T(g, S.story.end, 540, 1220, { f: F('Pridi', 70, 600), c: '#e9e3d2', al: e }); }),
  post: ctx => vig(ctx, .22, '60,40,10') };
