"""ดึงโลโก้/ภาพจริงจาก Wikimedia Commons (ภาพสาธารณะ) มาใส่คลิป -> my-clips/<คลิป>/assets/logo_<ชื่อ>.<ext>
    python3 scrapbook/logo.py find "Toyota logo"                        ค้นชื่อไฟล์
    python3 scrapbook/logo.py my-clips/<คลิป> toyota "file:<ชื่อไฟล์จากผลค้น>"
    python3 scrapbook/logo.py my-clips/<คลิป> toyota "url:https://..."  (ภาพที่มีสิทธิ์ใช้)
ใน spec ใช้ {"logo": "toyota"} (ถ้าไฟล์เป็น svg ใส่ "ext": "svg" เพิ่ม)"""
import json, sys, urllib.parse, urllib.request
from pathlib import Path
UA = {"User-Agent": "ThaiMotionClips/1.0 (student video tool) python-urllib"}
get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
a = sys.argv[1:]
if len(a) < 2: sys.exit(__doc__)
if a[0] == "find":
    r = json.loads(get("https://commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srlimit=8&format=json&srsearch=" + urllib.parse.quote(a[1])))
    for x in r["query"]["search"]: print(" ", x["title"][5:])
    sys.exit()
clip, name, src = Path(a[0]), a[1], a[2]
kind, _, rest = src.partition(":")
if kind == "file": url, ext = "https://commons.wikimedia.org/wiki/Special:FilePath/" + urllib.parse.quote(rest) + "?width=900", "png"
elif kind == "url": url, ext = rest, rest.split("?")[0].rsplit(".", 1)[-1].lower()[:4]
else: sys.exit('ที่มาต้องขึ้นต้นด้วย "file:" หรือ "url:"')
out = clip / "assets" / f"logo_{name}.{ext}"; out.parent.mkdir(parents=True, exist_ok=True); out.write_bytes(get(url))
print("✓", out, " เปิดดูภาพก่อนใช้ทุกครั้ง")
