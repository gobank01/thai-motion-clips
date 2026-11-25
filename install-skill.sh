#!/bin/sh
# ติดตั้ง repo นี้เป็นสกิลของ Claude Code (เรียกใช้ได้จากทุกโฟลเดอร์):  sh install-skill.sh
cd "$(dirname "$0")" || exit 1
mkdir -p "$HOME/.claude/skills"
ln -sfn "$PWD" "$HOME/.claude/skills/thai-motion-clips" && echo "✓ ติดตั้งสกิลแล้ว เปิด claude ที่ไหนก็ได้ แล้วพิมพ์ เช่น: ทำคลิปสมุดภาพเรื่องกาแฟ"
