#!/bin/sh
# ติดตั้งครั้งเดียว (รันซ้ำได้ไม่พัง):  sh setup.sh
cd "$(dirname "$0")/engine" || exit 1
ok=1
node -e 'process.exit(+process.versions.node.split(".")[0] >= 20 ? 0 : 1)' 2>/dev/null || { echo "✗ ต้องมี Node.js 20 ขึ้นไป (Mac: brew install node)"; exit 1; }
FV=$(ffmpeg -version 2>/dev/null | sed -n '1s/^ffmpeg version n\{0,1\}\([0-9][0-9]*\)\..*/\1/p')
if [ -z "$FV" ] || [ "$FV" -lt 7 ]; then echo "✗ ต้องมี ffmpeg 7 ขึ้นไป (Mac: brew install ffmpeg) ตอนนี้เจอ: ${FV:-ไม่มี}"; ok=0; fi
[ -d node_modules/playwright-core ] || npm install --omit=dev --no-audit --no-fund || { echo "✗ npm install ไม่สำเร็จ"; exit 1; }
[ -x .venv/bin/python ] || python3 -m venv .venv || { echo "✗ ต้องมี Python 3.11 ขึ้นไป (Mac: brew install python)"; exit 1; }
.venv/bin/python -c 'import numpy, scipy, soundfile, soxr' 2>/dev/null || .venv/bin/pip install -q numpy scipy soundfile soxr
.venv/bin/python -c 'import edge_tts' 2>/dev/null || .venv/bin/pip install -q edge-tts || echo "(ติดตั้งเสียงฟรี edge-tts ไม่สำเร็จ ข้ามได้ถ้าจะใช้ ElevenLabs)"
if [ "$(uname)" != Darwin ] || [ ! -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then [ -n "$PLAYWRIGHT_CHROME$PLAYWRIGHT_BROWSERS_PATH" ] || node node_modules/playwright-core/cli.js install chromium-headless-shell; fi
[ -f ../.env ] || cp ../.env.example ../.env
[ $ok = 1 ] && echo "✓ ติดตั้งเสร็จ ลองเลย:  sh clip.sh examples/ai-online-shop 25" || echo "ติดตั้งส่วนอื่นเสร็จแล้ว เหลือแก้ข้อ ✗ ด้านบน"
