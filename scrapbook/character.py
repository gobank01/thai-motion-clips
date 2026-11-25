"""สร้างตัวละครผู้เล่า (พื้นใส) -> characters/<ชื่อ>.png  ใช้ใน spec: {"sticker": "<ชื่อ>", ...}
วิธีใช้:
    python3 scrapbook/character.py detective "นักสืบการ์ตูนน่ารัก ใส่หมวก ถือแว่นขยาย หน้าสงสัย"
    python3 scrapbook/character.py chef "เชฟใส่หมวกขาว ถือตะหลิว ยิ้ม" --ref characters/detective.png   (ตัวเดิม เปลี่ยนชุด)
    python3 scrapbook/character.py me "การ์ตูนสติกเกอร์จากรูปนี้" --ref ~/Desktop/my-photo.png           (ทำจากรูปตัวเอง)
--ref = ภาพตัวละครต้นแบบ หน้าตาจะคงเดิม เปลี่ยนแค่ชุด/ท่าทาง · ชุดสีเขียวให้เติม --magenta"""
import subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import voice; voice.load_env()
import make

a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
name, desc, mag = a[0], a[1], "--magenta" in a
ref = Path(a[a.index("--ref") + 1]).expanduser() if "--ref" in a else None
bg = "pure magenta background (#FF00FF)" if mag else "pure green background (#00FF00)"
same = ("Keep EXACTLY the same character from the reference image: same face, same hairstyle, same skin tone, same proportions. "
        "Only change the outfit, props and pose as described. ") if ref else ""
prompt = (f"Cute chibi cartoon sticker character: {desc}. {same}Full body standing, thick white sticker outline, flat clean colors. "
          f"Plain solid {bg}, nothing else, no shadows on the background, no text, no logos. Vertical 3:4.")
out = Path(__file__).resolve().parents[1] / "characters" / f"{name}.png"; out.parent.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory() as t:
    raw = Path(t) / "raw.png"
    cost = make.gen_image(prompt, raw, aspect="3:4", ref=ref)
    # ตัดพื้นเขียว/ม่วงออก ให้เป็นพื้นใส
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(raw), "-vf",
                    f"colorkey={'0xFF00FF' if mag else '0x00FF00'}:0.32:0.08,despill=type={'blue' if mag else 'green'}", str(out)], check=True)
print(f"✓ {out}  (${cost:.3f})  เปิดดูภาพก่อนใช้ ถ้าหน้าเพี้ยนสั่งใหม่ได้")
