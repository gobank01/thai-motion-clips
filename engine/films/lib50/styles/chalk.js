// กระดานดำชอล์ก — green board, dusty chalk handwriting, yellow chalk for the point
import { W, H, T, TW, G, F, en, ia, tex, grainTex, speckTex, rough, vig, rr, grad, ln, tick, star, scan, typed, seg, eo, eio, back, clamp, lerp, mulberry, pop, TAU } from '../sk.js';
const board = tex(W, H, g => { g.fillStyle = '#21402f'; g.fillRect(0, 0, W, H); const R = mulberry(3); for (let i = 0; i < 700; i++) { g.strokeStyle = `rgba(255,255,255,${.01 + R() * .028})`; g.lineWidth = 20 + R() * 70; const x = R() * W, y = R() * H; g.beginPath(); g.moveTo(x, y); g.lineTo(x + (R() - .5) * 520, y + (R() - .5) * 90); g.stroke(); } g.strokeStyle = '#8a5a2b'; g.lineWidth = 46; g.strokeRect(23, 23, W - 46, H - 46); g.strokeStyle = '#5f3c1a'; g.lineWidth = 6; g.strokeRect(48, 48, W - 96, H - 96); });
const sp = speckTex(11, 90000, .75, 3), CH = '#f3f0e6', YL = '#ffd84d', PK = '#ff9db0';
export default { name: 'chalk', th: 'กระดานดำชอล์ก', fonts: ['700 80px Mali', '600 80px Mali'], music: { bpm: 92, prog: 'major', lead: 'mallet', arp: [0, 2, 1, 3, 2, null, 1, null], drums: 'b', lead_v: .5 }, sfx: { item: 'draw', hit: 'draw' },
  sub: { font: '600 52px Mali', size: 52, color: CH, bg: 'rgba(15,32,22,.78)' },
  bg: ctx => ctx.drawImage(board, 0, 0),
  hook: (ctx, S) => rough(ctx, sp, g => { const h = S.story.hook; T(g, S.story.kicker, 540, 330, { f: F('Mali', 46, 600), c: PK, al: en(S, 0) });
    T(g, h[0], 540, 560, { f: F('Mali', 92, 600), c: CH, al: en(S, .15), max: 900 }); T(g, h[1], 540, 720, { f: F('Mali', 104), c: CH, al: en(S, .6), max: 900 });
    T(g, h[2], 540, 930, { f: F('Mali', 190), c: YL, al: en(S, 1.15, .25), s: .85 + .15 * en(S, 1.15), max: 900 }); ln(g, 250, 1060, 830, 1048, en(S, 1.5, .35), YL, 14); ln(g, 270, 1088, 800, 1080, en(S, 1.7, .3), YL, 9); }),
  list: (ctx, S) => rough(ctx, sp, g => { const l = S.story.list; T(g, l.title, 540, 380, { f: F('Mali', 120), c: YL, al: en(S, 0), max: 900 }); ln(g, 300, 470, 780, 464, en(S, .25), CH, 8);
    l.items.forEach((s, i) => { const a = ia(S, i), y = 660 + i * 190; if (a <= 0) return; g.globalAlpha = a; g.strokeStyle = CH; g.lineWidth = 8; g.strokeRect(170, y - 44, 88, 88); g.globalAlpha = 1; tick(g, 220, y - 4, 80, seg(S.items[i], .2, .55), YL, 14); T(g, s, 310, y, { f: F('Mali', 92, 600), c: CH, a: 'left', al: a, max: 640 }); }); }),
  stat: (ctx, S) => rough(ctx, sp, g => { const s = S.story.stat; T(g, s.label, 540, 330, { f: F('Mali', 72, 600), c: CH, al: en(S, .1), max: 900 });
    T(g, S.N, 540, 760, { f: F('Mali', 520), c: YL, al: eo(seg(S.statAge, -.1, .15)) }); const p = eo(seg(S.statAge, .5, 1.1)); if (p > 0) { g.strokeStyle = PK; g.lineWidth = 12; g.lineCap = 'round'; g.beginPath(); g.ellipse(540, 740, 330, 310, -.1, -1.2, -1.2 + TAU * 1.04 * p); g.stroke(); }
    T(g, s.unit, 540, 1130, { f: F('Mali', 130), c: CH, al: eo(seg(S.statAge, .3, .6)) }); T(g, '★ ' + S.story.end + ' ★', 540, 1300, { f: F('Mali', 60, 600), c: PK, al: eo(seg(S.endAge, 0, .3)) }); }),
  post: ctx => vig(ctx, .35) };
