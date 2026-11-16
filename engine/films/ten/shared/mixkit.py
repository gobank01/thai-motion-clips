"""Shared mixer for the ten films: VO lines + a synthesized score preset + foley from the page's events -> mix.wav."""
import sys, os, json, subprocess, numpy as np, soundfile as sf
LIB = os.environ['LIB']; sys.path.insert(0, LIB)
from core.audio.sfx import SR, bp, lp, hp, add, compress, limit
from core.audio import sampler as S
rng = np.random.default_rng(5)
def tt(d): return np.arange(int(d * SR)) / SR
def db(x): return 10 ** (x / 20)
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
def adsr(n, a=.005, r=.05): e = np.ones(n); na, nr = max(1, int(a * SR)), max(1, int(r * SR)); e[:na] = np.linspace(0, 1, na)[:len(e[:na])]; e[-nr:] *= np.linspace(1, 0, nr)[-len(e[-nr:]):]; return e

def tone(kind, f, d, v=1.):
    t = tt(d); n = len(t)
    if kind == 'mallet': x = np.sin(2*np.pi*f*t)*np.exp(-t/.3) + .35*np.sin(2*np.pi*f*4*t)*np.exp(-t/.05) + .12*np.sin(2*np.pi*f*10*t)*np.exp(-t/.015)
    elif kind == 'bell': x = (np.sin(2*np.pi*f*t) + .5*np.sin(2*np.pi*f*2.76*t) + .25*np.sin(2*np.pi*f*5.4*t)) * np.exp(-t/.6)
    elif kind == 'square': x = np.sign(np.sin(2*np.pi*f*t)) * .5 * np.exp(-t/max(.08, d*.6))
    elif kind == 'pulse': x = (((f*t) % 1) < .25).astype(float) - .25; x *= np.exp(-t/max(.08, d*.7)) * .8
    elif kind == 'tri': x = 2*np.abs(2*((f*t) % 1)-1)-1; x *= .8
    elif kind == 'saw': x = lp(2*((f*t) % 1)-1, min(8000, f*6)) * .5 * np.exp(-t/max(.1, d*.8))
    elif kind == 'pad': x = sum(lp(2*(((f*(1+dt))*t) % 1)-1, f*3.5) for dt in (-.006, 0, .007)) / 3 * np.minimum(1, t/.25) * .6
    elif kind == 'pluck': x = (np.sin(2*np.pi*f*t) + .4*np.sin(4*np.pi*f*t) + .2*np.sin(6*np.pi*f*t)) * np.exp(-t/.16)
    elif kind == 'epiano': x = (np.sin(2*np.pi*f*t + 1.2*np.sin(2*np.pi*f*t)*np.exp(-t/.25))) * np.exp(-t/.9)
    elif kind == 'piano': x = sum(np.sin(2*np.pi*f*k*t)*a for k, a in ((1, 1), (2, .45), (3, .22), (4, .12), (5, .06))) * np.exp(-t/1.1) * .7
    elif kind == 'bass': x = (np.sin(2*np.pi*f*t) + .3*np.sin(4*np.pi*f*t) + .12*np.sin(6*np.pi*f*t)) * np.exp(-t/.6)
    elif kind == 'sub': x = np.sin(2*np.pi*f*t) * np.exp(-t/.35)
    else: x = np.sin(2*np.pi*f*t)
    return (x * adsr(n) * v).astype(np.float32)
def kick(v=1.): t = tt(.28); return (np.sin(2*np.pi*np.cumsum(45 + 110*np.exp(-t/.03))/SR) * np.exp(-t/.09) * v).astype(np.float32)
def hat(v=1., d=.05): n = int(d*SR); return (hp(rng.standard_normal(n), 7000) * np.exp(-tt(d)[:n]/(d*.3)) * .35 * v).astype(np.float32)
def snare(v=1.): t = tt(.18); return ((bp(rng.standard_normal(len(t)), 1200, 6000)*np.exp(-t/.05) + np.sin(2*np.pi*190*t)*np.exp(-t/.04)*.5) * .6 * v).astype(np.float32)
def block(v=1., f=900): t = tt(.08); return (np.sin(2*np.pi*f*t)*np.exp(-t/.012) * .8 * v).astype(np.float32)
def shaker(v=1.): n = int(.07*SR); return (bp(rng.standard_normal(n), 4000, 9000) * np.sin(np.pi*np.linspace(0, 1, n))**2 * .3 * v).astype(np.float32)

# foley
def whoosh(d=.4, v=1., lo=300, hi=2600): n = int(d*SR); return (bp(rng.standard_normal(n), lo, hi) * np.sin(np.pi*np.linspace(0, 1, n))**2 * .4 * v).astype(np.float32)
def click(v=1., f=2400): t = tt(.03); return ((bp(rng.standard_normal(len(t)), 1500, 7000)*np.exp(-t/.004) + np.sin(2*np.pi*f*t)*np.exp(-t/.006)*.4) * .6 * v).astype(np.float32)
def popfx(v=1., f=520): t = tt(.12); return (np.sin(2*np.pi*np.cumsum(f*(1+2.2*np.exp(-t/.02)))/SR) * np.exp(-t/.035) * .7 * v).astype(np.float32)
def ding(v=1., f=1320): return tone('bell', f, 1.2, .5*v)
def thump(v=1., f=70): t = tt(.35); return ((np.sin(2*np.pi*f*t)*np.exp(-t/.09) + lp(rng.standard_normal(len(t)), 500)*np.exp(-t/.03)*.4) * .9 * v).astype(np.float32)
def zap(v=1.): t = tt(.25); return (np.sin(2*np.pi*np.cumsum(2400*np.exp(-t/.06)+200)/SR) * np.exp(-t/.08) * .4 * v).astype(np.float32)
def coin(v=1.): return np.concatenate([tone('square', 988, .07, .5*v), tone('square', 1319, .32, .5*v)])
def rise(d=.8, v=1.): t = tt(d); return (np.sin(2*np.pi*np.cumsum(300 + 900*(t/d)**2)/SR) * np.sin(np.pi*t/d)**1.5 * .3 * v).astype(np.float32)
def buzz(d=.3, v=1.): t = tt(d); g = (rng.random(len(t)) < .6); return ((np.sin(2*np.pi*120*t) + .5*np.sin(2*np.pi*240*t) + bp(rng.standard_normal(len(t)), 3000, 9000)*.6) * g * np.exp(-t/(d*.6)) * .25 * v).astype(np.float32)
def scratch(d=.4, v=1., lo=1800, hi=7000): n = max(64, int(d*SR)); u = np.linspace(0, 1, n); return (bp(rng.standard_normal(n), lo, hi) * (1-.8*np.cos(2*np.pi*u))/1.8 * np.minimum(1, u*d/.01) * np.minimum(1, (1-u)*d/.02) * .3 * v).astype(np.float32)
def blip(v=1., f=880): return tone('square', f, .06, .45*v)
def keytick(v=1.): t = tt(.025); return (bp(rng.standard_normal(len(t)), 900, 5000)*np.exp(-t/.005)*.5*v + np.sin(2*np.pi*180*t)*np.exp(-t/.008)*.3*v).astype(np.float32)
def paper(v=1.): n = int(.3*SR); return (bp(rng.standard_normal(n), 800, 5000) * np.exp(-np.linspace(0, 1, n)*5) * .4 * v).astype(np.float32)
FX = {'whoosh': lambda e: whoosh(e.get('d', .4), e.get('v', 1)), 'click': lambda e: click(e.get('v', 1)), 'pop': lambda e: popfx(e.get('v', 1), e.get('f', 520)),
      'ding': lambda e: ding(e.get('v', 1), e.get('f', 1320)), 'thump': lambda e: thump(e.get('v', 1)), 'zap': lambda e: zap(e.get('v', 1)), 'coin': lambda e: coin(e.get('v', 1)),
      'rise': lambda e: rise(e.get('d', .8), e.get('v', 1)), 'buzz': lambda e: buzz(e.get('d', .3), e.get('v', 1)), 'draw': lambda e: scratch(e.get('d', .4), e.get('v', 1)),
      'blip': lambda e: blip(e.get('v', 1), e.get('f', 880)), 'key': lambda e: keytick(e.get('v', 1)), 'paper': lambda e: paper(e.get('v', 1)), 'kick': lambda e: kick(e.get('v', 1)),
      'block': lambda e: block(e.get('v', 1), e.get('f', 900)), 'snare': lambda e: snare(e.get('v', 1))}

PROGS = {'minor': [(45, [57, 60, 64, 69]), (41, [53, 57, 60, 65]), (48, [55, 60, 64, 67]), (43, [55, 59, 62, 67])],
         'major': [(48, [60, 64, 67, 72]), (45, [57, 60, 64, 69]), (41, [57, 60, 65, 69]), (43, [55, 59, 62, 67])],
         'dorian': [(50, [57, 62, 65, 69]), (43, [55, 59, 62, 67]), (48, [55, 60, 64, 67]), (45, [57, 60, 64, 67])],
         'lydian': [(41, [57, 60, 65, 71]), (43, [59, 62, 67, 71]), (45, [57, 60, 64, 72]), (43, [55, 59, 62, 69])],
         'sus': [(50, [62, 67, 69, 74]), (50, [62, 66, 69, 74]), (55, [62, 67, 71, 74]), (57, [61, 64, 69, 73])]}

class Mix:
    def __init__(s, here):
        s.here = here; ev = json.load(open(os.path.join(here, 'events.json'))); s.E, s.DUR = ev['ev'], ev['dur']
        s.vo_meta = json.load(open(os.path.join(here, 'vo.json')))
        s.NS = int((s.DUR + 1) * SR); s.mus = np.zeros((s.NS, 2), np.float32); s.fol = np.zeros((s.NS, 2), np.float32); s.vo = np.zeros(s.NS, np.float32)
        for i, l in enumerate(s.vo_meta['lines']):
            fp = os.path.join(here, 'vo', f'vo{i}.mp3')
            if not os.path.exists(fp): continue
            raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', fp, '-f', 'f32le', '-ac', '1', '-ar', str(SR), '-'])
            y = np.frombuffer(raw, np.float32); a = int(l['t0'] * SR); s.vo[a:a + len(y)] += y[:s.NS - a]
    def put(s, buf, x, t, g=1., pan=0.):
        if 0 <= t < s.DUR: add(buf, np.asarray(x, np.float32), t, g, pan)
    def score(s, bpm=100, prog='major', lead='mallet', arp=(0, 1, 2, 3, 2, 1, 2, 3), div=2, bass='bass', pad=None, drums='', oct=0, swing=0., t0=.2, lead_v=.6, silences=(), lift=None, bars_per_chord=1):
        """drums: letters k(kick 4-on-floor) h(hats) s(snare 2&4) b(woodblock offbeat) r(shaker). silences=[(a,b)] mute. lift=t after which lead goes up an octave on offbeats."""
        BT = 60 / bpm; t = t0; bar = 0; P = PROGS[prog]
        mute = lambda x: any(a <= x < b for a, b in silences) or x > s.DUR - .4
        while t < s.DUR - .3:
            root, ch = P[(bar // bars_per_chord) % len(P)]
            steps = 4 * div
            for k in range(steps):
                tk = t + k * BT / div + (swing * BT / div if k % 2 else 0)
                if mute(tk): continue
                if lead and arp:
                    a = arp[k % len(arp)]
                    if a is not None:
                        n = ch[a % 4] + 12 * (a // 4) + oct + (12 if lift is not None and tk >= lift and k % 2 else 0)
                        s.put(s.mus, tone(lead, hz(n), BT * 1.6, lead_v * (.75 if k % 2 else 1)), tk, 1, -.35 if k % 2 else .35)
                beat = k / div
                if 'k' in drums and k % div == 0: s.put(s.mus, kick(.9), tk)
                if 'h' in drums and k % max(1, div // 2 if div > 2 else 1) == 0: s.put(s.mus, hat(.5 if beat % 1 else .8), tk + (BT / 2 if div == 1 else 0), 1, .2)
                if 's' in drums and k % div == 0 and int(beat) % 2 == 1: s.put(s.mus, snare(.7), tk)
                if 'b' in drums and k % div == div // 2: s.put(s.mus, block(.5), tk, 1, -.3)
                if 'r' in drums: s.put(s.mus, shaker(.8 if k % 2 == 0 else .5), tk, 1, .4)
            if not mute(t):
                if bass: s.put(s.mus, tone(bass, hz(root), BT * 3.2, .8), t); 
                if bass and not mute(t + 2.5 * BT): s.put(s.mus, tone(bass, hz(root), BT * 1.2, .5), t + 2.5 * BT)
                if pad:
                    for n in ch[:3]: s.put(s.mus, tone(pad, hz(n + oct), BT * 4.4, .22), t, 1, 0)
            t += 4 * BT; bar += 1
        return s
    def foley(s, gains=None):
        g = gains or {}
        for e in s.E:
            f = FX.get(e['type'])
            if f: s.put(s.fol, f(e), e['t'], g.get(e['type'], 1.) * e.get('g', 1.), e.get('pan', 0))
        return s
    def write(s, music_db=-15, foley_db=-9, verb=.25, extra=None):
        vo = hp(s.vo, 70); vo = compress(vo / (np.abs(vo).max() + 1e-9) * .8, thr=.2, ratio=3.)
        env = np.abs(vo); win = int(.05 * SR); env = np.convolve(env, np.ones(win) / win, 'same'); on = (env > .02).astype(np.float32)
        dk = np.zeros(s.NS, np.float32); g = 0.; att, rel = int(.06 * SR), int(.4 * SR)
        for j in range(0, s.NS, 240): tgt = on[j]; g += (tgt - g) * (240 / att if tgt > g else 240 / rel); dk[j:j + 240] = g
        mus = S.room(s.mus, size=verb, mix=.22); fa = int((s.DUR - 1.6) * SR); mus[fa:] *= (np.linspace(1, 0, s.NS - fa) ** 1.5)[:, None]
        mus = mus * (1 - (1 - db(-7)) * dk)[:, None]
        if extra is not None: mus = mus + extra[:s.NS]
        rms = lambda x: float(np.sqrt(np.mean(x[np.abs(x) > 1e-4] ** 2))) if np.any(np.abs(x) > 1e-4) else 1.
        vr = rms(vo); st = np.stack([vo, vo], 1); st = st * .9 + S.room(st, size=.15, mix=.08) * .1
        fol = s.fol; pk = np.abs(fol).max() + 1e-9
        mix = st + mus * (vr / rms(mus)) * db(music_db) + fol * (vr / max(rms(fol), pk * .08)) * db(foley_db)
        mix = np.stack([limit(mix[:, c], .95) for c in range(2)], 1)
        sf.write(os.path.join(s.here, 'mix.wav'), mix[:int(s.DUR * SR)].astype(np.float32), SR)
        print('mix', os.path.basename(s.here), round(s.DUR, 2), 's')
