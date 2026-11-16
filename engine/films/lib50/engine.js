// One story, any style:  index.html?s=<style>[&story=<json>][&vo=<json>][&scene=hook|list|stat&dur=4][&n=NN]
// styles/<style>.js draws bg / hook / list / stat / post. story and vo may be inline JSON (URL-encoded) or default to story.json / vo.json.
import { subs, cue, EV, clean, seg, eo, W, H, T, TW, F, rr } from './sk.js';
const q = new URLSearchParams(location.search), name = q.get('s') || 'chalk';
const mod = (await import(`./styles/${name}.js`)).default;
const J = async (k, def) => q.get(k) ? JSON.parse(q.get(k)) : await (await fetch(def)).json();
const story = await J('story', 'story.json'), NUM = q.get('n'), SCENE = ['hook', 'list', 'stat'].indexOf(q.get('scene'));
const vo = SCENE >= 0 ? { dur: +(q.get('dur') || 4), lines: [] } : await J('vo', 'vo.json');
vo.lines.forEach(l => { l.say = clean(l.text || ''); }); vo.cur = t => vo.lines.find(l => l.say && t >= l.t0 - .05 && t < l.t1 + .35);
story.list.at ||= [.3, .5, .74]; story.stat.prefix ||= '';
const fonts = NUM ? [...mod.fonts, '500 40px Kanit'] : mod.fonts;
await Promise.all([...fonts, mod.sub?.font || '600 54px Kanit'].map(f => document.fonts.load(f, 'กขคง ABC 123')));
const ctx = document.getElementById('c').getContext('2d'), L = vo.lines, D = vo.dur, sx = { item: 'pop', hit: 'thump', turn: 'whoosh', win: 'ding', ...(mod.sfx || {}) };
let T0, it, tStat, tEnd;
if (SCENE >= 0) { T0 = [0, 0, 0, D]; it = story.list.items.map((_, i) => Math.min(.5 + i * .7, D * (.15 + .2 * i))); tStat = .7; tEnd = 1.8; cue(0, '_music', mod.music); cue(.1, sx.hit); if (SCENE === 1) it.forEach((x, i) => cue(x, sx.item, { f: 520 + i * 90 })); if (SCENE === 2) { cue(tStat - .45, 'rise', { d: .5, v: .7 }); cue(tStat + .55, sx.win, { f: 1320 }); cue(tEnd, sx.item, { f: 880 }); } }
else { T0 = [0, L[1].t0 - .25, L[2].t0 - .25, D]; it = story.list.at.map(f => L[1].t0 + (L[1].t1 - L[1].t0) * f); tStat = L[2].t0 + (L[2].t1 - L[2].t0) * .4; tEnd = L[2].t1 + .3;
  cue(0, '_music', mod.music); cue(L[0].t0 - .2, sx.hit); cue(T0[1], sx.turn, { d: .35 }); cue(T0[2], sx.turn, { d: .35 });
  it.forEach((x, i) => cue(x, sx.item, { f: 520 + i * 90, pan: -.2 + i * .2 })); cue(tStat - .45, 'rise', { d: .5, v: .7 }); cue(tStat + .55, sx.win, { f: 1320 }); cue(tEnd, sx.item, { f: 880 }); }
const st = mod.init ? mod.init(ctx, story) : {};
function frame(t) {
  const sc = SCENE >= 0 ? SCENE : t < T0[1] ? 0 : t < T0[2] ? 1 : 2, lt = t - T0[sc], len = T0[sc + 1] - T0[sc], n = story.stat.num * eo(seg(t, tStat, tStat + .6));
  const S = { t, sc, lt, len, D, story, st, items: it.map(x => t - x), n, N: story.stat.prefix + Math.round(n).toLocaleString('en-US'), statAge: t - tStat, endAge: t - tEnd, out: SCENE < 0 && sc < 2 ? seg(lt, len - .2, len) : 0 };
  mod.bg(ctx, S); ctx.save(); ctx.globalAlpha = 1 - S.out; [mod.hook, mod.list, mod.stat][sc](ctx, S); ctx.restore();
  if (mod.post) mod.post(ctx, S);
  subs(ctx, t, vo, { y: 1500, ...mod.sub });
  if (NUM) { const lab = `#${NUM}  ${mod.th}`, w = TW(ctx, lab, F('Kanit', 38, 500)) + 56; ctx.globalAlpha = 1; rr(ctx, 30, 40, w, 76, 38, 'rgba(0,0,0,.72)', 'rgba(255,255,255,.85)', 2); T(ctx, lab, 58, 80, { f: F('Kanit', 38, 500), c: '#fff', a: 'left' }); }
}
window.DUR = D; window.EV = EV.sort((a, b) => a.t - b.t);
window.render = t => { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none'; ctx.shadowBlur = 0; frame(t); };
window.READY = true;
