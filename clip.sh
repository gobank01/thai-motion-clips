#!/bin/sh
# ทำคลิปจากโฟลเดอร์ที่มี story.json ในคำสั่งเดียว: เสียงพากย์ -> ภาพตัวอย่าง -> คลิป
#   sh clip.sh my-clips/ชื่อคลิป 25          (25 = เลขสไตล์ ดูได้จาก catalog/ หรือ node make.mjs --list)
#   sh clip.sh my-clips/ชื่อคลิป 25 --no-voice   ไม่มีเสียงพากย์ มีแต่เพลง
set -e
cd "$(dirname "$0")"
DIR="${1:?ใส่โฟลเดอร์คลิป เช่น sh clip.sh my-clips/ร้านกาแฟ 25}"; STYLE="${2:-25}"
[ -f "$DIR/story.json" ] || { echo "ไม่พบ $DIR/story.json"; exit 1; }
NAME="$(basename "$DIR")"
if [ "$3" = "--no-voice" ]; then VO=""; else
  [ -f "$DIR/voice/vo2.mp3" ] || python3 tools/voice.py "$DIR"
  VO="--vo $DIR/voice"
fi
echo "ภาพตัวอย่าง -> $DIR/preview-$STYLE.jpg"
node make.mjs --style "$STYLE" --story "$DIR/story.json" --still 9 --out "$DIR/preview-$STYLE.jpg" >/dev/null
echo "กำลังเรนเดอร์ (ประมาณ 1-3 นาที)..."
node make.mjs --style "$STYLE" --story "$DIR/story.json" $VO --out "$DIR/$NAME-$STYLE.mp4"
