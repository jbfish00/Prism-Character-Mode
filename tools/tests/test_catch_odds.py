#!/usr/bin/env python3
"""Catch odds: runs the REAL PokeBallEffect segment 03:788C..03:78CA (capture value X in
HRAM $FFB3..$FFB6 -> the engine's own >=256 test -> $C64E verdict -> the success roll at
03:7D59 -> $D1EC) up to the point where the ball animation would start, for every species.

  CM on, on-roster species  : verdict always set (the engine's guaranteed-catch branch),
                              X raised to >= 256 (and $FFB6 = $FF), even when X starts at 1
  CM on, off-roster species : $FFB3..$FFB6 zeroed and verdict 0, even when X starts at 255
  CM off                    : untouched (X bytes exactly as computed, verdict 0 for X < 256)
(--tamper expects the opposite for on-roster and must FAIL.)
The animation itself needs a live battle, which this port's harness cannot start (see
docs/SELECTION_MECHANISM.md 'not verified'); the verdict/roll are what drive it.
"""
import sys, random
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, species_names

STATE = "tools/emu_states/ck9.state"
CHAR = 9


def main():
    tamper = "--tamper" in sys.argv
    random.seed(7)
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    names = species_names()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def trial(char, species, x):
        cm.restore(base)
        for _ in range(random.randrange(1, 40)):
            cm.pb.tick()
        cm.set_char(char)
        cm.wb(0xD206, species)
        cm.wb(0xC64E, 0)
        for i, v in enumerate((0, 0, 0, x)):
            cm.wb(0xFFB3 + i, v)
        got = {}

        def at_gate(c=None):
            got["verdict"] = cm.rb(0xC64E)
            got["roll"] = cm.rb(0xD1EC)
            got["x"] = bytes(cm.pb.memory[0xFFB3:0xFFB7])
        cm.pb.hook_register(3, 0x78CA, at_gate, None)
        try:
            cm.call((3, 0x788C), frames=200, buttons=())
        except TimeoutError:
            pass
        cm.pb.hook_deregister(3, 0x78CA)
        return got

    on_sp = [s for s in range(1, 252) if roster_has(CHAR, s)]
    off_sp = [s for s in range(1, 252) if not roster_has(CHAR, s)]
    bad = []
    for s in on_sp:
        for x in (1, 255):
            g = trial(CHAR, s, x)
            ok = g.get("verdict") == s and g.get("x") == bytes((0, 0, 1, 255))
            if tamper:
                ok = not ok
            if not ok:
                bad.append((names[s], x, g))
    check(not bad, f"all {len(on_sp)} on-roster species: guaranteed at X=1 and X=255 (bad: {bad[:2]})")
    bad = []
    for s in off_sp[:60]:
        for x in (1, 255):
            g = trial(CHAR, s, x)
            if not (g.get("verdict") == 0 and g.get("x") == bytes(4)):
                bad.append((names[s], x, g))
    check(not bad, f"60 off-roster species: never caught, X zeroed, even at X=255 (bad: {bad[:2]})")
    ok = all(trial(None, 16, x).get("verdict") == 0 and trial(None, 16, x).get("x") == bytes((0, 0, 0, x))
             for x in (1, 100, 255))
    check(ok, "CM off: X untouched and no forced verdict (engine odds as shipped)")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
