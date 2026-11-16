// โพสต์อิทบนบอร์ดไม้ก๊อก — cork board, paper notes slapped on with pins
import { W, H, T, TW, G, F, en, ia, tex, grainTex, speckTex, rough, vig, rr, grad, ln, tick, star, scan, typed, seg, eo, eio, back, clamp, lerp, mulberry, pop, TAU } from '../sk.js';
const cork = tex(W, H, g => { g.fillStyle = '#b98a55'; g.fillRect(0, 0, W, H); const R = mulberry(4); for (let i = 0; i < 26000; i++) { g.fillStyle = ['rgba(90,55,20,.22)', 'rgba(230,190,130,.25)', 'rgba(60,35,10,.18)'][i % 3]; g.beginPath(); g.arc(R() * W, R() * H, 1 + R() * 5, 0, TAU); g.fill(); } });
const INK = '#2a2520';
const note = (ctx, x, y, w, h, col, rot, p, fn) => { if (p <= 0) return; const k = back(clamp(p)); ctx.save(); ctx.translate(x, y - (1 - k) * 60); ctx.rotate(rot + (1 - k) * .25); ctx.scale(.6 + .4 * k, .6 + .4 * k); ctx.globalAlpha *= clamp(p * 3); ctx.shadowColor = 'rgba(40,20,0,.45)'; ctx.shadowBlur = 26; ctx.shadowOffsetY = 14; ctx.fillStyle = col; ctx.fillRect(-w / 2, -h / 2, w, h); ctx.shadowColor = 'transparent'; ctx.fillStyle = 'rgba(0,0,0,.06)'; ctx.fillRect(-w / 2, h / 2 - 26, w, 26); fn(ctx); ctx.fillStyle = '#d6352b'; ctx.beginPath(); ctx.arc(0, -h / 2 + 30, 17, 0, TAU); ctx.fill(); ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.beginPath(); ctx.arc(-5, -h / 2 + 25, 6, 0, TAU); ctx.fill(); ctx.restore(); };
export default { name: 'sticky', th: 'โพสต์อิทบอร์ดไม้ก๊อก', fonts: ['400 80px Itim', '700 80px Mali'], music: { bpm: 104, prog: 'major', lead: 'pluck', arp: [0, 2, 1, 3, 2, 1, 3, null], drums: 'r', lead_v: .5 }, sfx: { item: 'paper', hit: 'paper' },
  sub: { font: '400 54px Itim', size: 54, color: INK, bg: 'rgba(255,255,255,.92)', radius: 6 },
  bg: ctx => ctx.drawImage(cork, 0, 0),
  hook: (ctx, S) => { const h = S.story.hook; note(ctx, 400, 480, 620, 250, '#fff7a8', -.05, seg(S.lt, .1, .5), g => T(g, h[0], 0, 14, { f: F('Itim', 78, 400), c: INK, max: 560 }));
    note(ctx, 640, 760, 680, 260, '#ffc9de', .04, seg(S.lt, .55, .95), g => T(g, h[1], 0, 14, { f: F('Itim', 88, 400), c: INK, max: 620 }));
    note(ctx, 540, 1080, 760, 330, '#a8e6ff', -.02, seg(S.lt, 1.1, 1.5), g => T(g, h[2], 0, 18, { f: F('Mali', 170), c: '#d6352b', max: 700 })); },
  list: (ctx, S) => { const l = S.story.list, C = ['#fff7a8', '#c8f7c5', '#ffd9a8']; note(ctx, 540, 390, 700, 230, '#fff', .01, seg(S.lt, 0, .4), g => T(g, l.title, 0, 14, { f: F('Mali', 110), c: INK, max: 640 }));
    l.items.forEach((s, i) => note(ctx, 380 + (i % 2) * 320, 690 + i * 235, 620, 215, C[i], [-.05, .04, -.03][i], seg(S.items[i], 0, .4), g => { T(g, '✓', -240, 12, { f: F('Mali', 90), c: '#1f9d55' }); T(g, s, 30, 14, { f: F('Itim', 82, 400), c: INK, max: 440 }); })); },
  stat: (ctx, S) => { const s = S.story.stat; note(ctx, 540, 420, 800, 190, '#fff', -.02, seg(S.lt, .1, .5), g => T(g, s.label, 0, 14, { f: F('Itim', 68, 400), c: INK, max: 740 }));
    note(ctx, 540, 850, 720, 600, '#fff7a8', .03, seg(S.statAge, -.25, .15), g => { T(g, S.N, 0, -50, { f: F('Mali', 420), c: '#d6352b' }); T(g, s.unit, 0, 210, { f: F('Mali', 110), c: INK }); });
    note(ctx, 700, 1270, 560, 170, '#c8f7c5', -.05, seg(S.endAge, 0, .4), g => T(g, S.story.end, 0, 14, { f: F('Itim', 64, 400), c: INK, max: 500 })); },
  post: ctx => vig(ctx, .3, '40,20,0') };
