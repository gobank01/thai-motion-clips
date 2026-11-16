#!/usr/bin/env node
// lemo-styles: one command -> one clip.   node make.mjs --style <name|number> [options]     (node make.mjs --help)
import fs from 'fs'; import path from 'path'; import { spawnSync } from 'child_process'; import { fileURLToPath } from 'url';
const HERE = path.dirname(fileURLToPath(import.meta.url)), ENG = path.join(HERE, 'engine'), LIB50 = path.join(ENG, 'films', 'lib50');
const HELP = `lemo-styles: code-drawn motion graphics in 50 styles (1080x1920, 30 fps)

  node make.mjs --list                               list the 50 styles
  node make.mjs --style 25 --out clip.mp4            full clip (hook > list > stat), music + SFX, sample story
  node make.mjs --style dash --story my.json --vo voice/ --out clip.mp4
                                                     your story + your voice (voice/vo0.mp3 vo1.mp3 vo2.mp3)
  node make.mjs --style 33 --story my.json --scene stat --dur 4 --out insert.mp4
                                                     INSERT: one scene only, silent, for dropping into an edit
options
  --style <name|number>   required (see --list or catalog/*.jpg)
  --story <file.json>     content; default = engine/films/lib50/story.json (copy it as a template)
  --vo <dir>              folder with vo0.mp3 vo1.mp3 vo2.mp3 (hook, list, stat lines). Subtitles = story.say[0..2]
  --scene hook|list|stat  insert mode: render only this scene
  --dur <sec>             insert length (default 4, min 2.5)
  --audio                 insert mode: add that style's music + SFX (default silent)
  --no-music              full mode: voice + SFX only
  --wide                  1920x1080 output: the vertical card centred over a blurred copy of itself
  --size <WxH>            scale the final video (e.g. 720x1280)
  --still <sec>           write one JPG frame at this time instead of a video (fast preview)
  --label                 burn the "#NN name" chip (catalogue use)
  --out <path>            output file (default ./out/<style>[-scene].mp4)`;
const A = process.argv.slice(2), has = k => A.includes(k), opt = (k, d) => { const i = A.indexOf(k); return i >= 0 ? A[i + 1] : d; };
const die = m => { console.error('lemo-styles: ' + m); process.exit(1); };
const STYLES = fs.readFileSync(path.join(LIB50, 'styles.txt'), 'utf8').trim().split('\n').map(l => { const [num, name] = l.trim().split(/\s+/); const src = fs.readFileSync(path.join(LIB50, 'styles', name + '.js'), 'utf8'); return { num, name, th: (/th: '([^']+)'/.exec(src) || [])[1] || name }; });
if (has('--help') || has('-h') || !A.length) { console.log(HELP); process.exit(0); }
if (has('--list')) { STYLES.forEach(s => console.log(`${s.num}  ${s.name.padEnd(10)} ${s.th}`)); process.exit(0); }
const want = String(opt('--style', '')), sty = STYLES.find(s => s.name === want || +s.num === +want); if (!sty) die(`unknown style "${want}" (node make.mjs --list)`);
const scene = opt('--scene'), dur = Math.max(2.5, +opt('--dur', 4)); if (scene && !['hook', 'list', 'stat'].includes(scene)) die('--scene must be hook, list or stat');
const storyFile = path.resolve(opt('--story', path.join(LIB50, 'story.json'))); if (!fs.existsSync(storyFile)) die('story not found: ' + storyFile);
let story; try { story = JSON.parse(fs.readFileSync(storyFile, 'utf8')); } catch (e) { die('story is not valid JSON: ' + e.message); }
for (const k of ['hook', 'list', 'stat']) if (!story[k]) die(`story.${k} is missing (see engine/films/lib50/story.json)`);
if (!Array.isArray(story.hook) || story.hook.length !== 3) die('story.hook must be 3 short lines (the 3rd is the big word)');
if (!Array.isArray(story.list.items) || story.list.items.length !== 3) die('story.list.items must be exactly 3 items');
story.kicker ||= ''; story.end ||= ''; story.stat.unit ||= ''; story.stat.label ||= '';
const still = opt('--still'), tag = sty.name + (scene ? '-' + scene : ''), out = path.resolve(opt('--out', path.join('out', tag + (still ? '.jpg' : '.mp4'))));
const O = path.join(LIB50, 'out', tag + '-' + process.pid); fs.rmSync(O, { recursive: true, force: true }); fs.mkdirSync(path.join(O, 'vo'), { recursive: true }); fs.mkdirSync(path.dirname(out), { recursive: true });
const env = { ...process.env, LIB: ENG };
if (!env.PLAYWRIGHT_CHROME && !env.PLAYWRIGHT_BROWSERS_PATH && process.platform === 'darwin') { const c = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'; if (fs.existsSync(c)) env.PLAYWRIGHT_CHROME = c; }
const run = (cmd, args, o = {}) => { const r = spawnSync(cmd, args, { cwd: ENG, env, encoding: 'utf8', maxBuffer: 1 << 26, ...o }); if (r.error) die(`cannot run ${cmd}: ${r.error.message}`); if (r.status !== 0) die(`${cmd} ${path.basename(String(args[0]))} failed\n${(r.stderr || '') + (r.stdout || '')}`.slice(0, 3000)); return (r.stdout || '') + (r.stderr || ''); };
const probe = f => +run('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).trim();
// voice timeline
let vo = null, voiced = false;
if (!scene) {
  const say = story.say || [story.hook.join(' '), [story.list.title, ...story.list.items].join(' '), [story.stat.label, (story.stat.prefix || '') + story.stat.num, story.stat.unit].join(' ')];
  const dir = opt('--vo'); let t = .5; const lines = [];
  if (dir) { for (let i = 0; i < 3; i++) { const f = path.join(path.resolve(dir), `vo${i}.mp3`); if (!fs.existsSync(f)) die(`voice file missing: ${f} (need vo0.mp3 vo1.mp3 vo2.mp3)`); fs.copyFileSync(f, path.join(O, 'vo', `vo${i}.mp3`)); const d = probe(f); lines.push({ text: say[i] || '', t0: +t.toFixed(3), t1: +(t + d).toFixed(3) }); t += d + .4; } voiced = true; }
  else [2.5, 4, 2.2].forEach((d, i) => { lines.push({ text: story.say ? say[i] : '', t0: +t.toFixed(3), t1: +(t + d).toFixed(3) }); t += d + .4; });
  vo = { dur: +(lines[2].t1 + 2.1).toFixed(2), lines };
}
fs.writeFileSync(path.join(O, 'vo.json'), JSON.stringify(vo || { dur, lines: [] }));
const qs = new URLSearchParams({ s: sty.name, story: JSON.stringify(story) }); if (vo) qs.set('vo', JSON.stringify(vo)); if (scene) { qs.set('scene', scene); qs.set('dur', String(dur)); } if (has('--label')) qs.set('n', sty.num);
const Q = qs.toString(), node = process.execPath;
if (still) { run(node, ['core/render/still.mjs', LIB50, String(+still), '--q', Q, '--out', O, '--prefix', 'f_', '--size', '1080x1920']); const f = fs.readdirSync(O).find(x => x.startsWith('f_')); if (!f) die('no still was written'); fs.copyFileSync(path.join(O, f), out); fs.rmSync(O, { recursive: true, force: true }); console.log(out); process.exit(0); }
const audio = scene ? has('--audio') : true;
if (audio) {
  run(node, ['core/render/events.mjs', LIB50, '--q', Q, '--out', path.join(O, 'events.json'), '--size', '1080x1920']);
  if (has('--no-music')) { const e = JSON.parse(fs.readFileSync(path.join(O, 'events.json'), 'utf8')); const m = e.ev.find(x => x.type === '_music'); if (m) { m.lead = null; m.bass = null; m.pad = null; m.drums = ''; } fs.writeFileSync(path.join(O, 'events.json'), JSON.stringify(e)); }
  const venv = path.join(ENG, '.venv', 'bin', 'python'), py = env.LEMO_PY || (fs.existsSync(venv) ? venv : 'python3');
  run(py, [path.join(LIB50, 'mix50.py'), O]);
}
run(node, ['core/render/video.mjs', LIB50, '--q', Q, '--fps', '30', '--workers', '4', '--size', '1080x1920', '--out', path.join(O, 'video.mp4')]);
let cur = path.join(O, 'final.mp4');
if (audio) run('sh', ['core/render/mux.sh', path.join(O, 'video.mp4'), path.join(O, 'mix.wav'), cur, '30', '0']);
else run('ffmpeg', ['-y', '-v', 'error', '-i', path.join(O, 'video.mp4'), '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', '-movflags', '+faststart', cur]);
const size = opt('--size'), vf = [];
if (has('--wide')) vf.push('split[a][b];[a]scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,boxblur=28:4,eq=brightness=-0.12[bg];[b]scale=-2:1080[fg];[bg][fg]overlay=(W-w)/2:0');
if (size) { if (!/^\d+x\d+$/.test(size)) die('--size must look like 720x1280'); vf.push((vf.length ? '[w];[w]' : '') + `scale=${size.replace('x', ':')}`); }
if (vf.length) { const nxt = path.join(O, 'post.mp4'); run('ffmpeg', ['-y', '-v', 'error', '-i', cur, '-filter_complex', '[0:v]' + vf.join('') + ',format=yuv420p[v]', '-map', '[v]', ...(audio ? ['-map', '0:a', '-c:a', 'copy'] : []), '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-movflags', '+faststart', nxt]); cur = nxt; }
fs.copyFileSync(cur, out); fs.rmSync(O, { recursive: true, force: true });
console.log(`${out}  (${sty.num} ${sty.name} ${sty.th}, ${probe(out).toFixed(2)}s${scene ? ', insert ' + scene : voiced ? ', voiced' : ', no voice'}${audio ? '' : ', silent'})`);
