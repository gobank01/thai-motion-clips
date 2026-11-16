#!/usr/bin/env python3
"""ทำเสียงพากย์ 3 ประโยคจาก story.json -> โฟลเดอร์ voice/ (vo0.mp3 vo1.mp3 vo2.mp3)

วิธีใช้:
    python3 tools/voice.py my-clips/ชื่อคลิป                # เลือกผู้ให้บริการอัตโนมัติ
    python3 tools/voice.py my-clips/ชื่อคลิป --provider edge  # ฟรี (ต้อง pip install edge-tts)
    python3 tools/voice.py my-clips/ชื่อคลิป --provider elevenlabs

อ่านบทจาก story.json ช่อง "speak" (ถ้ามี ใช้กำหนดคำอ่าน เช่น "เอไอ") ไม่งั้นใช้ช่อง "say"
ตั้งค่าใน .env ที่โฟลเดอร์หลักของ repo (คัดลอกจาก .env.example):
    ELEVENLABS_API_KEY=...        ถ้ามี จะใช้ ElevenLabs (เสียงดีที่สุด เสียเงินตามจำนวนตัวอักษร)
    ELEVENLABS_VOICE_ID=...       รหัสเสียงที่เลือกจาก Voice Library (ไม่ใส่ = เสียงตัวอย่างภาษาไทย)
    ELEVENLABS_MODEL=eleven_v3
    EDGE_VOICE=th-TH-NiwatNeural  เสียงฟรี: th-TH-NiwatNeural (ชาย) หรือ th-TH-PremwadeeNeural (หญิง)
    EDGE_RATE=+10%
ไม่มีการส่งข้อมูลไปที่อื่นนอกจากผู้ให้บริการเสียงที่เลือก และไม่มีการเก็บ key ไว้ในไฟล์อื่น
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EL_VOICE = "tAV9ucNkXgK2k9TLxWkM"   # เสียงผู้ชายภาษาไทยจาก Voice Library ของ ElevenLabs (เปลี่ยนได้ใน .env)


def load_env():
    f = ROOT / ".env"
    if not f.exists():
        return
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        k, v = ln.removeprefix("export ").split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def trim(src: Path, dst: Path):
    """ตัดช่วงเงียบหัว-ท้าย แล้วเซฟเป็น mp3 44.1k"""
    af = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse,"
          "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af, "-ar", "44100", "-b:a", "160k", str(dst)], check=True)


def eleven(text: str, out: Path):
    key = os.environ["ELEVENLABS_API_KEY"]
    vid = os.environ.get("ELEVENLABS_VOICE_ID") or DEFAULT_EL_VOICE
    model = os.environ.get("ELEVENLABS_MODEL") or "eleven_v3"
    body = json.dumps({"text": text, "model_id": model}, ensure_ascii=False).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}?output_format=mp3_44100_128", data=body,
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        out.write_bytes(urllib.request.urlopen(req, timeout=180).read())
    except urllib.error.HTTPError as e:
        msg = e.read()[:400].decode("utf-8", "replace")
        hint = ""
        if e.code == 401:
            hint = "\n  -> key ผิดหรือหมดอายุ: ตรวจ ELEVENLABS_API_KEY ในไฟล์ .env"
        elif e.code in (400, 404) and "voice" in msg.lower():
            hint = "\n  -> ไม่พบเสียงนี้: เข้า Voice Library ใน ElevenLabs กด Add เสียงที่ชอบ แล้วคัดลอก Voice ID มาใส่ ELEVENLABS_VOICE_ID"
        elif e.code == 402 or "quota" in msg.lower():
            hint = "\n  -> เครดิตหมด: เติมเครดิต หรือใช้ --provider edge (ฟรี)"
        sys.exit(f"ElevenLabs ตอบกลับ {e.code}: {msg}{hint}")


def edge(text: str, out: Path):
    voice = os.environ.get("EDGE_VOICE") or "th-TH-NiwatNeural"
    rate = os.environ.get("EDGE_RATE") or "+10%"
    venv = ROOT / "engine" / ".venv" / "bin" / "python"
    py = str(venv) if venv.exists() else sys.executable
    r = subprocess.run([py, "-m", "edge_tts", "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        if "No module named" in r.stderr:
            sys.exit("ยังไม่ได้ติดตั้ง edge-tts: รัน  sh setup.sh  อีกครั้ง แล้วลองใหม่")
        sys.exit("edge-tts ทำเสียงไม่สำเร็จ (ตรวจอินเทอร์เน็ต หรือชื่อเสียงใน EDGE_VOICE):\n" + r.stderr[-600:])


def main():
    ap = argparse.ArgumentParser(description="ทำเสียงพากย์จาก story.json")
    ap.add_argument("clip", help="โฟลเดอร์คลิปที่มี story.json")
    ap.add_argument("--provider", choices=["auto", "elevenlabs", "edge"], default="auto")
    a = ap.parse_args()
    load_env()
    if not shutil.which("ffmpeg"):
        sys.exit("ไม่พบ ffmpeg: ติดตั้งก่อน (Mac: brew install ffmpeg)")
    clip = Path(a.clip).resolve()
    story = json.loads((clip / "story.json").read_text(encoding="utf-8"))
    lines = story.get("speak") or story.get("say")
    if not lines or len(lines) != 3:
        sys.exit('story.json ต้องมีช่อง "say" (หรือ "speak") เป็นบทพูด 3 ประโยค')
    prov = a.provider
    if prov == "auto":
        prov = "elevenlabs" if os.environ.get("ELEVENLABS_API_KEY") else "edge"
    if prov == "elevenlabs" and not os.environ.get("ELEVENLABS_API_KEY"):
        sys.exit("ยังไม่มี ELEVENLABS_API_KEY: คัดลอก .env.example เป็น .env แล้วใส่ key ของตัวเอง")
    out = clip / "voice"
    out.mkdir(exist_ok=True)
    print(f"ทำเสียงด้วย {prov} ...")
    with tempfile.TemporaryDirectory() as tmp:
        for i, text in enumerate(lines):
            raw = Path(tmp) / f"raw{i}.mp3"
            (eleven if prov == "elevenlabs" else edge)(text, raw)
            trim(raw, out / f"vo{i}.mp3")
            d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / f"vo{i}.mp3")],
                               capture_output=True, text=True).stdout.strip()
            print(f"  vo{i}.mp3  {float(d or 0):.1f} วิ  {text}")
    print(f"เสร็จ -> {out}")


if __name__ == "__main__":
    main()
