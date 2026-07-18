#!/usr/bin/env python3
"""A/B test harness for the Character Mode catch gate.

Loads a savestate positioned IN a wild battle with at least one ball in the
bag, drives the bag menu to throw a ball, and reports the outcome — under
either the original ROM or the patched build/prism_cm.gbc (savestates are
compatible: only banks 3/118 differ).

Outcome detection is RAM-first (not screenshot-based):
  $C64E (wWildMon verdict)  nonzero right after the calc = caught
  $DCD7 (wPartyCount) / box count growth = mon actually landed somewhere
  plus the textbox transcript from the shadow tilemap for human review.

Usage:
  test_catch_gate.py --state BATTLE_STATE --rom build/prism_cm.gbc \
      [--char-id N] [--menu-plan "..."] [--shots DIR]

--char-id N: patch the dev character-id byte (file 0x1DBFFE) in a TEMP COPY
             of the ROM before running ($FF = mode off). Never edits in place.
--menu-plan: input plan to reach & throw the ball from the battle menu
             (default tries: PACK -> first pocket item -> use).
"""
import argparse
import os
import shutil
import tempfile

from pyboy import PyBoy

TILEMAP, COLS = 0xC4A0, 20
CHARID_FILE_OFF = 0x1DBFFE

CH = {0x7F: " ", 0xE0: "'", 0xE3: "-", 0xE6: "?", 0xE7: "!", 0xE8: ".",
      0xF4: ",", 0x9C: ":", 0xE9: "&", 0xF3: "/", 0xEA: "e", 0x54: "#"}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CH[0x80 + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CH[0xA0 + i] = c
for i, c in enumerate("0123456789"):
    CH[0xF6 + i] = c


def read_text(pb):
    out = []
    for row in (14, 16):
        base = TILEMAP + row * COLS + 1
        raw = bytes(pb.memory[base:base + 18])
        line = "".join(CH.get(b, "") for b in raw).strip()
        if line:
            out.append(line)
    return " / ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--char-id", type=lambda v: int(v, 0), default=None)
    ap.add_argument("--menu-plan",
                    default="down,right,a,a,a")  # FIGHT->PACK varies; override per state
    ap.add_argument("--shots", default=None)
    ap.add_argument("--post-frames", type=int, default=2400)
    args = ap.parse_args()

    rom = args.rom
    tmp = None
    if args.char_id is not None:
        tmp = tempfile.NamedTemporaryFile(suffix=".gbc", delete=False)
        shutil.copyfile(rom, tmp.name)
        with open(tmp.name, "r+b") as f:
            f.seek(CHARID_FILE_OFF)
            f.write(bytes([args.char_id & 0xFF]))
        rom = tmp.name

    pb = PyBoy(rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    with open(args.state, "rb") as f:
        pb.load_state(f)
    pb.tick()

    party_before = pb.memory[0xDCD7]

    def tap(btn, hold=12, wait=90):
        pb.button_press(btn)
        for _ in range(hold):
            pb.tick()
        pb.button_release(btn)
        for _ in range(wait):
            pb.tick()

    transcript = []
    for i, token in enumerate([t.strip() for t in args.menu_plan.split(",") if t.strip()]):
        tap(token, wait=140)
        t = read_text(pb)
        if t and (not transcript or transcript[-1][1] != t):
            transcript.append((f"after {token}", t))
        if args.shots:
            os.makedirs(args.shots, exist_ok=True)
            pb.screen.image.save(os.path.join(args.shots, f"step_{i:02d}_{token}.png"))

    # let the throw resolve, transcribing text as it goes
    last = None
    for i in range(args.post_frames):
        pb.tick()
        if i % 60 == 0:
            t = read_text(pb)
            if t and t != last:
                transcript.append((f"frame {i}", t))
                last = t
    # dismiss trailing boxes (nickname prompt etc. answered 'no' with B)
    for _ in range(6):
        tap("b", wait=140)
        t = read_text(pb)
        if t and t != last:
            transcript.append(("after b", t))
            last = t

    party_after = pb.memory[0xDCD7]
    verdict = pb.memory[0xC64E]
    print(f"party {party_before} -> {party_after}   $C64E verdict now: {verdict}")
    print("--- transcript ---")
    for tag, t in transcript:
        print(f"[{tag}] {t}")
    if args.shots:
        pb.screen.image.save(os.path.join(args.shots, "final.png"))
    pb.stop(save=False)
    if tmp:
        os.unlink(tmp.name)


if __name__ == "__main__":
    main()
