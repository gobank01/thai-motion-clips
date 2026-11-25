"""เสียงเอฟเฟกต์ + เพลงเบาๆ สร้างด้วยโค้ดทั้งหมด (ไม่ติดลิขสิทธิ์) -> scrapbook/sounds/*.wav
ทำครั้งเดียว make.py เรียกให้เอง:  engine/.venv/bin/python scrapbook/sounds.py"""
import sys
from pathlib import Path
import numpy as np, soundfile as sf
R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "engine/core/audio"))
import sfx as S

O = Path(__file__).resolve().parent / "sounds"; O.mkdir(exist_ok=True)
pad = lambda a, b: np.concatenate([a, np.zeros(max(0, len(b) - len(a)))])[:max(len(a), len(b))] + np.concatenate([b, np.zeros(max(0, len(a) - len(b)))])
FX = {
    "whoosh": S.whoosh(.35), "pop": S.pop(), "tap": S.step(),
    "shutter": pad(S.click(.8), np.pad(S.step(.6), (int(.06 * S.SR), 0))),
    "stamp": pad(S.thump(1, 95), S.clack(.7, .8)),
    "boom": pad(S.thump(1, 48), S.rumble(.9, .6)),
    "sparkle": S.ding(.8),
}
for n, x in FX.items(): sf.write(O / f"{n}.wav", (S.norm(x, .9)).astype(np.float32), S.SR)

def box(note, v):  # เสียงกล่องดนตรี: ไซน์ + ฮาร์มอนิก ดังแล้วจางเร็ว
    f = 440 * 2 ** (("C C#D D#E F F#G G#A A#B ".index(note[:-1].ljust(2)) // 2 - 9) / 12 + int(note[-1]) - 4); tt = S.t_(1.4)
    return sum(a * np.sin(2 * np.pi * f * m * tt) * S.env_exp(1.4, tau) for m, a, tau in [(1, 1, .5), (2, .35, .25), (3, .15, .12)]) * v * .3


# เพลง: อาร์เปจจิโอ music box 4 คอร์ด 90 bpm วนได้ (~10.7 วิ)
beat = 60 / 90; bar = beat * 4
song = np.zeros(int(bar * 4 * S.SR) + S.SR, np.float32)
for b, ch in enumerate([["C4", "E4", "G4", "C5"], ["A3", "C4", "E4", "A4"], ["F3", "A3", "C4", "F4"], ["G3", "B3", "D4", "G4"]]):
    for k in range(8):
        x = box(ch[k % 4], .5 + .2 * (k % 2 == 0)); s = int((b * bar + k * beat / 2) * S.SR)
        song[s:s + len(x)] += x[:len(song) - s]
tail = song[int(bar * 4 * S.SR):]; song = song[:int(bar * 4 * S.SR)]; song[:len(tail)] += tail  # วนต่อเนื่อง ไม่มีรอยต่อ
sf.write(O / "music.wav", S.norm(song, .8), S.SR)
print("sounds ->", O)
