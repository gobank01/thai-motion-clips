#!/usr/bin/env python3
"""คลิปสมุดภาพเล่าเรื่อง (scrapbook) แนวตั้ง 9:16 ยาว 60-90 วิ จาก spec.json ไฟล์เดียว

วิธีใช้ (รันจากโฟลเดอร์หลักของ repo):
    python3 scrapbook/make.py my-clips/<ชื่อคลิป>            ทำครบ: ตรวจ -> ภาพ -> เสียง -> ประกอบ -> เรนเดอร์ -> ปก
    python3 scrapbook/make.py my-clips/<ชื่อคลิป> check      ตรวจ spec อย่างเดียว (ฟรี ทำก่อนเสมอ)
    python3 scrapbook/make.py my-clips/<ชื่อคลิป> render     แก้ spec แล้วเรนเดอร์ใหม่ (ไม่เสียเงินเพิ่ม ภาพ/เสียงเดิมเก็บไว้)

ใช้ key เดียว OPENROUTER_API_KEY ใน .env (ภาพฉาก + เสียงพากย์) ไม่มี key = เสียงฟรี edge-tts แต่ภาพฉากต้องมี key
รูปแบบ spec.json ดู .claude/skills/scrapbook-clip/SKILL.md
"""
import base64, concurrent.futures as cf, json, os, re, shutil, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tools"))
import voice as V  # noqa: E402  ใช้ระบบเสียงเดียวกับคลิป 50 สไตล์ (OpenRouter / edge-tts)

IMG_MODEL = "google/gemini-3.1-flash-lite-image"   # ถูกสุดใน OpenRouter ราว 1 บาท/ภาพ (เปลี่ยนได้ด้วย "image_model" ใน spec)
SPEED, GAP, TAIL = 1.1, 0.35, 2.4
NOFACE = "No text, no letters, no logos, no brand names, no signage, no visible faces. Vertical 9:16, {style}."
DESKS = {"desk_wood": "Top-down photo of a warm wooden desk, a pencil and a ruler near the edges, empty middle. Horizontal 16:9, realistic photo, no text.",
         "desk_mat": "Top-down photo of a green cutting mat with white grid lines on a wooden desk, empty middle. Horizontal 16:9, realistic photo, no text."}
SFX_VOL = {"whoosh": .5, "pop": .35, "tap": .35, "shutter": .4, "stamp": .6, "boom": .8, "sparkle": .35}


def die(msg): sys.exit("✗ " + msg)


def run(*a, **k): return subprocess.run([str(x) for x in a], check=True, **k)


def dur(f): return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                        capture_output=True, text=True).stdout.strip() or 0)


# ---------- ตรวจ spec (ฟรี) ----------
def check(S):
    bad = []
    for k in ("title", "lines", "scenes"):
        if k not in S: bad.append(f'ไม่มีช่อง "{k}"')
    L = S.get("lines", [])
    for si, sc in enumerate(S.get("scenes", [])):
        if not 0 <= sc.get("from", -1) < len(L): bad.append(f"ฉาก {si}: from ต้องเป็นเลขบรรทัด 0-{len(L) - 1}")
        bg = sc.get("bg", "wood")
        if bg.startswith("img:") and bg[4:] not in S.get("images", {}): bad.append(f'ฉาก {si}: ไม่มีภาพ "{bg[4:]}" ในช่อง images')
        for it in sc.get("items", []):
            for k in ("at", "at2"):
                a = it.get(k)
                if isinstance(a, list) and (a[0] >= len(L) or a[1] not in L[a[0]]):
                    bad.append(f'ฉาก {si}: คำ "{a[1]}" ไม่มีในบรรทัด {a[0]} (ต้องสะกดตรงกับในบทเป๊ะ)')
                elif k == "at" and isinstance(a, list) and it.get("logo") and L[a[0]].rindex(a[1]) > len(L[a[0]]) * .75:
                    print(f"  ⚠ ฉาก {si}: โลโก้ผูกกับคำท้ายบรรทัด จะโผล่แป๊บเดียว ย้ายไปคำที่อยู่ต้นๆ บรรทัด")
            if "pol" in it and it["pol"] not in S.get("images", {}): bad.append(f'ฉาก {si}: ไม่มีภาพ "{it["pol"]}" ในช่อง images')
            if "sticker" in it and not char_file(S, it["sticker"]).exists():
                bad.append(f'ฉาก {si}: ไม่พบตัวละคร {char_file(S, it["sticker"])} (สร้างด้วย scrapbook/character.py หรือใส่ไฟล์ PNG เอง)')
            if "logo" in it and not list((CLIP / "assets").glob(f'logo_{it["logo"]}.*')):
                bad.append(f'ฉาก {si}: ไม่มีโลโก้ assets/logo_{it["logo"]}.* (ดึงด้วย scrapbook/logo.py)')
    emo = [l for l in L if re.search("[\U0001F300-\U0001FAFF☀-➿]", l)]
    if emo: bad.append("ห้ามมีอีโมจิในบท: " + emo[0][:30])
    print(f"  ตรวจ: {len(L)} บรรทัด · {sum(map(len, L))} ตัวอักษร · " + ("OK" if not bad else f"{len(bad)} จุดต้องแก้"))
    for b in bad: print("   ✗", b)
    if bad: sys.exit(1)


def char_file(S, name):
    d = Path(S["char_dir"]).expanduser() if S.get("char_dir") else ROOT / "characters"
    return d / f"{name}.png"


# ---------- ภาพ ----------
def key():
    k = os.environ.get("OPENROUTER_API_KEY")
    if not k: die("ยังไม่มี OPENROUTER_API_KEY: เปิดไฟล์ .env แล้ววาง key หลัง OPENROUTER_API_KEY= (ภาพฉากต้องใช้ key)")
    return k


def gen_image(prompt, out, model=None, aspect="9:16", ref=None):
    content = [{"type": "text", "text": prompt}]
    if ref: content.append({"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(Path(ref).read_bytes()).decode()}})
    body = json.dumps({"model": model or IMG_MODEL, "modalities": ["image", "text"], "image_config": {"aspect_ratio": aspect},
                       "messages": [{"role": "user", "content": content}]}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", body,
                                 {"Authorization": "Bearer " + key(), "content-type": "application/json"})
    for i in range(3):
        try:
            d = json.loads(urllib.request.urlopen(req, timeout=300).read())
            Path(out).write_bytes(base64.b64decode(d["choices"][0]["message"]["images"][0]["image_url"]["url"].split(",", 1)[1]))
            return d.get("usage", {}).get("cost", 0) or 0
        except urllib.error.HTTPError as e:
            if e.code in (401, 402): die({401: "key OpenRouter ผิด ตรวจไฟล์ .env", 402: "เครดิต OpenRouter หมด เติมที่ openrouter.ai/settings/credits"}[e.code])
            print(f"  ลองใหม่ ({e.code})", out.name if hasattr(out, "name") else out, flush=True)
        except Exception as e:
            print("  ลองใหม่", Path(out).name, str(e)[:80], flush=True)
    die("ทำภาพไม่สำเร็จ: " + Path(out).name)


def images(S):
    A = CLIP / "assets"; A.mkdir(exist_ok=True)
    style = S.get("image_style", "realistic photo")
    todo = [(n, p + " " + NOFACE.format(style=style), A / f"{n}.png", "9:16") for n, p in S.get("images", {}).items() if not (A / f"{n}.png").exists()]
    used = {sc.get("bg", "wood") for sc in S["scenes"]}
    for n, p in DESKS.items():  # พื้นโต๊ะ ทำครั้งเดียวเก็บไว้ใช้ทุกคลิป
        if n.split("_")[1] in used and not (HERE / f"assets/{n}.png").exists(): todo.append((n, p, HERE / f"assets/{n}.png", "16:9"))
    (HERE / "assets").mkdir(exist_ok=True)
    with cf.ThreadPoolExecutor(6) as ex:
        cost = sum(ex.map(lambda t: gen_image(t[1], t[2], S.get("image_model"), t[3]), todo))
    for n in DESKS:
        if (HERE / f"assets/{n}.png").exists(): shutil.copy(HERE / f"assets/{n}.png", A / f"{n}.png")
    for sc in S["scenes"]:
        for it in sc.get("items", []):
            if "sticker" in it: shutil.copy(char_file(S, it["sticker"]), A / f"st_{it['sticker']}.png")
    print(f"  ภาพใหม่ {len(todo)} ภาพ · ${cost:.3f}")


# ---------- เสียงพากย์ + จังหวะ ----------
def voices(S):
    A = CLIP / "audio"; A.mkdir(exist_ok=True)
    lock = json.loads((A / "lock.json").read_text()) if (A / "lock.json").exists() else {}
    prov = "openrouter" if os.environ.get("OPENROUTER_API_KEY") and S.get("voice") != "edge" else "edge"
    if isinstance(S.get("voice"), str) and S["voice"] != "edge": os.environ["VOICE_ID"] = S["voice"]
    say = S.get("say", {})  # คำที่เสียงอ่านผิด เช่น {"AI": "เอไอ"}
    with tempfile.TemporaryDirectory() as tmp:
        for i, line in enumerate(S["lines"]):
            text = line
            for k, v in say.items(): text = text.replace(k, v)
            sig = f"{prov}|{os.environ.get('VOICE_ID', '')}|{text}"
            if lock.get(str(i)) == sig and (A / f"vo{i}.mp3").exists(): continue
            raw = Path(tmp) / f"raw{i}"
            (V.openrouter if prov == "openrouter" else V.edge)(text, raw)
            V.to_mp3(raw, A / f"vo{i}.mp3"); lock[str(i)] = sig
            (A / "lock.json").write_text(json.dumps(lock, ensure_ascii=False))
            print(f"  เสียง {i}: {dur(A / f'vo{i}.mp3'):.1f} วิ  {line[:40]}", flush=True)
    # จังหวะ: บรรทัดต่อกันเว้น GAP วิ (บรรทัดใน "long" เว้น 1 วิ) · เวลาแต่ละคำประมาณตามสัดส่วนตัวอักษร
    # ponytail: เวลาคำเป็นค่าประมาณ (คลาดได้ ~0.2 วิ) ถ้าอยากเป๊ะต้องใช้ API ที่ส่ง timestamps มาด้วย
    long, t, VO = set(S.get("long", [0])), 0.3, []
    for i, line in enumerate(S["lines"]):
        if i: t += 1.0 if i in long else GAP
        d = dur(A / f"vo{i}.mp3"); n = max(1, len(line))
        VO.append({"t": round(t, 2), "end": round(t + d, 3), "chars": line, "st": [round(d * k / n, 3) for k in range(n)]})
        t += d
    (A / "timing.js").write_text("window.VO=" + json.dumps(VO, ensure_ascii=False) + ";\n")
    return VO, round(t + TAIL, 2)


def cues_for(S, VO):
    def vo(i, w): L = VO[i]; return L["t"] + L["st"][L["chars"].index(w)]
    cuts = [max(0, VO[sc["from"]]["t"] - 0.3) for sc in S["scenes"]]; cuts[0] = 0
    C = []
    for si, sc in enumerate(S["scenes"]):
        t0 = cuts[si]
        if si: C.append(["whoosh", t0 - 0.1])
        for it in sc.get("items", []):
            a = it.get("at"); t = (t0 + 0.2 if a is None else t0 + a if isinstance(a, (int, float)) else vo(a[0], a[1]) + (a[2] if len(a) > 2 else 0)) - 0.1
            if "sticker" in it or "logo" in it or "badge" in it or "bub" in it: C.append(["pop", t])
            elif "pol" in it: C.append(["shutter", t])
            elif "line" in it: C.append(["tap", t])
            elif "card" in it: a2 = it.get("at2"); C.append(["stamp", (vo(a2[0], a2[1]) - 0.1) if a2 else t0 + 1.2])
            else: C.append(["boom" if it.get("boom") else "stamp", t + 0.1])
    C.append(["sparkle", VO[-1]["t"] + 0.3])
    C.sort(key=lambda c: c[1]); out = []
    for c in C:
        if not out or c[1] - out[-1][1] > 0.12: out.append([c[0], round(max(0, c[1]), 2)])
    return out


def mix(S, VO, D, sp):
    snd = HERE / "sounds"
    if not (snd / "music.wav").exists():
        run(ROOT / "engine/.venv/bin/python", HERE / "sounds.py", stdout=subprocess.DEVNULL)
    RD = round(D / sp, 3); ins, f = [], []
    for i, L in enumerate(VO):
        ins += ["-i", CLIP / f"audio/vo{i}.mp3"]
        f.append(f"[{i}:a]atempo={sp},adelay={int(L['t'] / sp * 1000)}:all=1[v{i}]")
    n = len(VO)
    f.append("".join(f"[v{i}]" for i in range(n)) + f"amix=inputs={n}:normalize=0,apad=whole_dur={RD},asplit=2[vo][sc]")
    ins += ["-stream_loop", "-1", "-i", snd / "music.wav"]
    mv = S.get("music_volume", 0.12)  # เพลงเบาแทบไม่ได้ยิน ใส่ 0 = ไม่มีเพลง
    f.append(f"[{n}:a]atrim=0:{RD},volume={mv},afade=t=out:st={RD - 1.6}:d=1.6[mu]")
    f.append("[mu][sc]sidechaincompress=threshold=0.02:ratio=8:attack=30:release=500[duck]")
    cues = cues_for(S, VO)
    for j, (name, t) in enumerate(cues):
        ins += ["-i", snd / f"{name}.wav"]
        f.append(f"[{n + 1 + j}:a]adelay={int(t / sp * 1000)}:all=1,volume={SFX_VOL[name]}[s{j}]")
    f.append("".join(f"[s{j}]" for j in range(len(cues))) + f"amix=inputs={len(cues)}:normalize=0[fx]")
    f.append(f"[vo][duck][fx]amix=inputs=3:normalize=0,apad=whole_dur={RD},atrim=0:{RD},loudnorm=I=-14:TP=-1.5:LRA=11,apad=whole_dur={RD},atrim=0:{RD}[out]")
    run("ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(f), "-map", "[out]", "-ar", "48000", CLIP / "audio.wav")
    print(f"  มิกซ์เสียง {RD} วิ · เอฟเฟกต์ {len(cues)} จุด")


# ---------- ประกอบ + เรนเดอร์ ----------
def cover_html(S):
    """ปก = เฟรมแรกของคลิป (ภาพฉากแรก + ตัวละคร + ฮุกตัวใหญ่) ทำด้วย HTML จึงฟรีและตัวหนังสือไทยไม่เพี้ยน"""
    hook = S.get("cover", S["title"])
    hook = re.sub(r"\[(.+?)\]", r'<em>\1</em>', hook)
    sc = S["scenes"][0]; bg = sc.get("bg", "wood")
    img = f"assets/{bg[4:]}.png" if bg.startswith("img:") else f"assets/{next(iter(S.get('images', {})), 'desk_wood')}.png"
    st = next((it["sticker"] for it in sc.get("items", []) if "sticker" in it), None)
    return f"""<div id="cover" style="position:absolute;inset:0;z-index:99;background:#111 url({img}) center/cover">
  <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.65),rgba(0,0,0,.1) 55%,rgba(0,0,0,.5))"></div>
  <div style="position:absolute;left:70px;right:70px;top:230px;font:900 118px/1.12 Kanit;color:#fff;text-align:center;-webkit-text-stroke:6px #000;paint-order:stroke fill;text-shadow:0 10px 0 rgba(0,0,0,.4)">{hook}</div>
  {f'<img src="assets/st_{st}.png" style="position:absolute;left:30px;bottom:260px;width:620px">' if st else ''}
</div><style>#cover em{{font-style:normal;color:#ff2b2b}}</style>"""


def build(S, D, sp):
    RD = round(D / sp, 2)
    (CLIP / "spec.js").write_text("window.SPEC=" + json.dumps(dict(S, duration=D, speed=sp), ensure_ascii=False) + ";\n")
    for f in ("engine.js", "engine.css"): shutil.copy(HERE / f, CLIP / f)
    (CLIP / "index.html").write_text(f"""<!doctype html>
<html lang="th"><head><meta charset="utf-8" /><title>{S['title']}</title>
<link href="https://fonts.googleapis.com/css2?family=Kanit:wght@500;700;800;900&display=swap" rel="stylesheet" crossorigin="anonymous" />
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<link rel="stylesheet" href="engine.css" />
<style>html,body{{margin:0;background:#2a1d14;}} #root{{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:Kanit,sans-serif;background:#2a1d14;}} #stage{{position:absolute;inset:0;}}</style>
</head><body>
<div id="root" data-composition-id="main" data-width="1080" data-height="1920" data-start="0" data-duration="{RD}">
  <div id="stage"></div>
  {cover_html(S)}
  <audio id="mix" src="audio.wav" data-start="0" data-duration="{RD}" data-track-index="10" data-volume="1"></audio>
</div>
<script src="audio/timing.js"></script><script src="spec.js"></script><script src="engine.js"></script>
</body></html>
""")


def render():
    name = CLIP.name; out = CLIP / f"{name}.mp4"
    print("  กำลังเรนเดอร์ (คลิป 1 นาที ใช้ราว 3-8 นาที)...", flush=True)
    shutil.rmtree(CLIP / "snapshots", ignore_errors=True)
    r = subprocess.run(["npx", "--yes", "hyperframes@0.8.144", "render", "-o", "raw.mp4"], cwd=CLIP, capture_output=True, text=True)
    if r.returncode: print((r.stdout + r.stderr)[-1500:]); die("เรนเดอร์ไม่สำเร็จ (ดูข้อความด้านบน)")
    # ใส่เสียงที่มิกซ์ไว้กลับเข้าไปตรงๆ (ตัวเรนเดอร์ปรับระดับเสียงเอง)
    run("ffmpeg", "-v", "error", "-y", "-i", CLIP / "raw.mp4", "-i", CLIP / "audio.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
        "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", out)
    (CLIP / "raw.mp4").unlink()
    run("ffmpeg", "-v", "error", "-y", "-i", out, "-frames:v", "1", CLIP / "cover.png")
    run("ffmpeg", "-v", "error", "-y", "-i", out, "-vf", "fps=1/3,scale=150:-1,tile=11x3", "-frames:v", "1", CLIP / "sheet.jpg")
    print(f"  ✓ เสร็จ {out.relative_to(ROOT)} ({dur(out):.0f} วิ) · ปก cover.png · ภาพรวม sheet.jpg")


if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    CLIP = Path(sys.argv[1]).resolve(); step = sys.argv[2] if len(sys.argv) > 2 else "all"
    if not (CLIP / "spec.json").exists(): die(f"ไม่พบ {CLIP}/spec.json")
    V.load_env()
    S = json.loads((CLIP / "spec.json").read_text(encoding="utf-8"))
    check(S)
    if step == "check": sys.exit(0)
    for tool in ("ffmpeg", "npx"):
        if not shutil.which(tool): die(f"ไม่พบ {tool}: รัน sh setup.sh ก่อน")
    images(S)
    VO, D = voices(S)
    sp = S.get("speed", SPEED)
    mix(S, VO, D, sp)
    build(S, D, sp)
    render()
