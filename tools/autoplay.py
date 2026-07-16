#!/usr/bin/env python3
"""Semi-autonomous Prism playthrough driver (ROWE-debug-menu-inspired rig).

Reads the on-screen textbox straight out of Prism's shadow tilemap (base
0xC4A0, found via RE this session) so dialogue can be transcribed and mashed
through automatically instead of eyeballing screenshots. Movement phases are
supplied as a plan; dialogue phases auto-advance.

Usage:
  autoplay.py --load ST --save ST --shots DIR --prefix P \
      --moves "down*3,left*2,a" --autotext 40 [--log FILE]

--moves: comma-separated tokens, btn or btn*N (18 frames/step for walking)
--autotext N: after moves, loop up to N times: if textbox visible, tap A;
              transcribe every new line seen. Stops early after 8 consecutive
              idle iterations with no textbox.
"""
import argparse
import os

from pyboy import PyBoy

TILEMAP = 0xC4A0
COLS = 20

CH = {0x7F: " ", 0xE0: "'", 0xE3: "-", 0xE6: "?", 0xE7: "!", 0xE8: ".",
      0xF4: ",", 0x9C: ":", 0xE9: "&", 0xF3: "/", 0xEA: "e", 0x54: "#",
      0xF0: "$", 0xF5: "F", 0xEF: "M"}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CH[0x80 + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CH[0xA0 + i] = c
for i, c in enumerate("0123456789"):
    CH[0xF6 + i] = c


def read_textbox(pb):
    """Return the two dialogue lines from the shadow tilemap (rows 14, 16)."""
    lines = []
    for row in (14, 16):
        base = TILEMAP + row * COLS + 1
        raw = bytes(pb.memory[base:base + 18])
        lines.append("".join(CH.get(b, "") for b in raw).strip())
    return [l for l in lines if l]


def textbox_frame_visible(pb):
    """True if the textbox border row (13) holds border tiles (0x79-0x7E)."""
    base = TILEMAP + 13 * COLS
    raw = bytes(pb.memory[base:base + COLS])
    return any(0x79 <= b <= 0x7E for b in raw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc")
    ap.add_argument("--load")
    ap.add_argument("--save", required=True)
    ap.add_argument("--shots", required=True)
    ap.add_argument("--prefix", default="ap")
    ap.add_argument("--moves", default="")
    ap.add_argument("--autotext", type=int, default=0)
    ap.add_argument("--log")
    args = ap.parse_args()

    os.makedirs(args.shots, exist_ok=True)
    pb = PyBoy(args.rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    if args.load:
        with open(args.load, "rb") as f:
            pb.load_state(f)
        pb.tick()

    transcript = []

    def note(msg):
        transcript.append(msg)
        print(msg)

    def tap(btn, hold=12, wait=90):
        pb.button_press(btn)
        for _ in range(hold):
            pb.tick()
        pb.button_release(btn)
        for _ in range(wait):
            pb.tick()

    for token in [t.strip() for t in args.moves.split(",") if t.strip()]:
        if "*" in token:
            btn, n = token.split("*")
            n = int(n)
        else:
            btn, n = token, 1
        if btn in ("up", "down", "left", "right"):
            for _ in range(n):
                pb.button_press(btn)
                for _ in range(18):
                    pb.tick()
                pb.button_release(btn)
                for _ in range(8):
                    pb.tick()
        else:
            for _ in range(n):
                tap(btn)

    seen = set()
    idle = 0
    for it in range(args.autotext):
        if textbox_frame_visible(pb):
            idle = 0
            lines = read_textbox(pb)
            key = tuple(lines)
            if lines and key not in seen:
                seen.add(key)
                note(f"[text {it}] " + " / ".join(lines))
            tap("a", wait=140)
        else:
            idle += 1
            if idle >= 8:
                note(f"[idle-stop after iter {it}]")
                break
            for _ in range(60):
                pb.tick()

    pb.screen.image.save(os.path.join(args.shots, f"{args.prefix}_end.png"))
    with open(args.save, "wb") as f:
        pb.save_state(f)
    if args.log:
        with open(args.log, "a") as f:
            f.write("\n".join(transcript) + "\n")
    pb.stop(save=False)
    print("ok")


if __name__ == "__main__":
    main()
