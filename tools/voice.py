#!/usr/bin/env python3
"""ทำเสียงพากย์ 3 ประโยคจาก story.json -> โฟลเดอร์ voice/ (vo0.mp3 vo1.mp3 vo2.mp3)

วิธีใช้:
    python3 tools/voice.py my-clips/ชื่อคลิป                   # มี OPENROUTER_API_KEY ใน .env = ใช้ OpenRouter, ไม่มี = เสียงฟรี
    python3 tools/voice.py my-clips/ชื่อคลิป --provider edge     # บังคับใช้เสียงฟรี edge-tts

อ่านบทจาก story.json ช่อง "speak" (ถ้ามี ใช้กำหนดคำอ่าน เช่น "เอไอ") ไม่งั้นใช้ช่อง "say"
ตั้งค่าใน .env ที่โฟลเดอร์หลักของ repo (setup.sh คัดลอกจาก .env.example ให้):
    OPENROUTER_API_KEY=...        key ของตัวเองจาก openrouter.ai (ใส่แค่อันนี้อันเดียว)
    VOICE_ID=...                  (ไม่บังคับ) รหัสเสียง ElevenLabs ที่อยากใช้ ไม่ใส่ = เสียงผู้ชายภาษาไทย
    EDGE_VOICE=th-TH-NiwatNeural  เสียงฟรี: th-TH-NiwatNeural (ชาย) หรือ th-TH-PremwadeeNeural (หญิง)
key ถูกส่งไปที่ openrouter.ai เท่านั้น และไม่ถูกเขียนลงไฟล์อื่น
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VOICE = "tAV9ucNkXgK2k9TLxWkM"   # เสียงผู้ชายภาษาไทยจาก Voice Library ของ ElevenLabs (เปลี่ยนได้ด้วย VOICE_ID)
OR_MODEL = "elevenlabs/eleven-v3"


def load_env():
    f = ROOT / ".env"
    if not f.exists():
        return
    for ln in f.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln or ln.startswith("#") or "=" not in ln:
            continue
        k, v = ln.removeprefix("export ").split("=", 1)
        v = v.strip().strip('"').strip("'")
        if v:
            os.environ.setdefault(k.strip(), v)


TRIM = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,areverse,"
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.08,areverse")


def to_mp3(raw: Path, dst: Path):
    """แปลงเป็น mp3 44.1k และตัดช่วงเงียบหัว-ท้าย (รับได้ทั้งไฟล์เสียงปกติ และ PCM ดิบ 24kHz ที่ OpenRouter ส่งมา)"""
    head = raw.read_bytes()[:12]
    is_file = head[:3] == b"ID3" or head[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2") or head[:4] in (b"RIFF", b"OggS", b"fLaC")
    src = ["-i", str(raw)] if is_file else ["-f", "s16le", "-ar", "24000", "-ac", "1", "-i", str(raw)]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *src, "-af", TRIM, "-ar", "44100", "-b:a", "160k", str(dst)], check=True)


def openrouter(text: str, out: Path):
    body = json.dumps({"model": OR_MODEL, "input": text, "voice": os.environ.get("VOICE_ID") or DEFAULT_VOICE}, ensure_ascii=False).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/audio/speech", data=body,
                                 headers={"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    try:
        out.write_bytes(urllib.request.urlopen(req, timeout=180).read())
    except urllib.error.HTTPError as e:
        msg = e.read()[:400].decode("utf-8", "replace")
        hint = {401: "key ผิดหรือถูกยกเลิก: ตรวจ OPENROUTER_API_KEY ในไฟล์ .env",
                402: "เครดิต OpenRouter หมด: เติมที่ openrouter.ai/settings/credits หรือใช้ --provider edge (ฟรี)",
                429: "เรียกถี่เกินไป: รอสักครู่แล้วลองใหม่"}.get(e.code, "")
        if not hint and "voice" in msg.lower():
            hint = "ไม่พบเสียงนี้: ลบค่า VOICE_ID ใน .env เพื่อใช้เสียงเริ่มต้น"
        sys.exit(f"OpenRouter ตอบกลับ {e.code}: {msg}" + (f"\n  -> {hint}" if hint else ""))
    except urllib.error.URLError as e:
        sys.exit(f"ต่อ OpenRouter ไม่ได้ (ตรวจอินเทอร์เน็ต): {e.reason}")


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
    ap.add_argument("--provider", choices=["auto", "openrouter", "edge"], default="auto")
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
        prov = "openrouter" if os.environ.get("OPENROUTER_API_KEY") else "edge"
    if prov == "openrouter" and not os.environ.get("OPENROUTER_API_KEY"):
        sys.exit("ยังไม่มี OPENROUTER_API_KEY: เปิดไฟล์ .env แล้ววาง key ของตัวเองหลัง OPENROUTER_API_KEY=")
    out = clip / "voice"
    out.mkdir(exist_ok=True)
    print("ทำเสียงด้วย " + ("OpenRouter (ElevenLabs v3)" if prov == "openrouter" else "edge-tts (ฟรี)") + " ...")
    with tempfile.TemporaryDirectory() as tmp:
        for i, text in enumerate(lines):
            raw = Path(tmp) / f"raw{i}"
            (openrouter if prov == "openrouter" else edge)(text, raw)
            to_mp3(raw, out / f"vo{i}.mp3")
            d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out / f"vo{i}.mp3")],
                               capture_output=True, text=True).stdout.strip()
            print(f"  vo{i}.mp3  {float(d or 0):.1f} วิ  {text}")
    print(f"เสร็จ -> {out}")


if __name__ == "__main__":
    main()
