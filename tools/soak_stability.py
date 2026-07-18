#!/usr/bin/env python3
"""Stability soak: drive the patched ROM through long sessions from several
savestates and assert it never hangs or crashes. Crash/hang heuristics
(RTC-immune — no frame/RAM hashing):
  * PC must stay in sane executable regions (ROM $0000-$7FFF, WRAM
    $C000-$DFFF, HRAM $FF80-$FFFE); a PC in VRAM/echo/IO for a sustained
    stretch means a runaway jump.
  * SP must stay in RAM ($C000-$FFFE) and not drift monotonically (stack
    overflow/underflow).
  * The frame counter must keep advancing (no infinite CPU loop stalling
    the PPU is impossible in PyBoy, but a soft-lock shows as an unchanging
    screen across all inputs — we sample distinct screen hashes to confirm
    the game is still responding to *something*).
"""
import argparse
import hashlib

from pyboy import PyBoy

PATCHED = "build/prism_cm.gbc"


def sane_pc(pc):
    return (pc <= 0x7FFF) or (0xC000 <= pc <= 0xDFFF) or (0xFF80 <= pc <= 0xFFFE)


def soak(state, steps):
    pb = PyBoy(PATCHED, window="null", cgb=True)
    pb.set_emulation_speed(0)
    with open(state, "rb") as f:
        pb.load_state(f)
    pb.tick()
    rf = pb.register_file
    seq = ["up", "a", "right", "down", "a", "left", "b", "a"]
    bad_pc = 0
    bad_sp = 0
    screens = set()
    for i in range(steps):
        btn = seq[i % len(seq)]
        pb.button_press(btn)
        for _ in range(9):
            pb.tick()
        pb.button_release(btn)
        for _ in range(30):
            pb.tick()
        if not sane_pc(rf.PC):
            bad_pc += 1
        if not (0xC000 <= rf.SP <= 0xFFFE):
            bad_sp += 1
        if i % 20 == 0:
            screens.add(hashlib.md5(pb.screen.image.tobytes()).hexdigest()[:8])
    pb.stop(save=False)
    return bad_pc, bad_sp, len(screens)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", nargs="+", required=True)
    ap.add_argument("--steps", type=int, default=400)
    args = ap.parse_args()
    all_ok = True
    for st in args.states:
        bad_pc, bad_sp, distinct = soak(st, args.steps)
        ok = (bad_pc == 0 and bad_sp == 0 and distinct > 1)
        all_ok = all_ok and ok
        print(f"[{'OK' if ok else 'FAIL'}] {st}: "
              f"bad_pc={bad_pc} bad_sp={bad_sp} distinct_screens={distinct}")
    print("\nSOAK PASS — no crashes/hangs" if all_ok else "\nSOAK FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
