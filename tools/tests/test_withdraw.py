#!/usr/bin/env python3
"""Live test of the PC-withdraw gate (hook at 56:6DA7, gate in bank 118).

Runs Prism's REAL withdraw routine (56:6DA7) from a real in-game state with a box
we build in SRAM bank 1 ($AD10 count, $AD11 species list):
  mode off / on-roster mon  -> withdraw proceeds (party grows, box shrinks)
  off-roster mon            -> refused: carry set, 'Not on the roster!' on screen,
                               party and box UNCHANGED
Negative control: --tamper makes the expected on-roster mon an off-roster one and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, char_info, species_names

STATE = "tools/emu_states/ck9.state"
CHAR = 9
TILEMAP = 0xC4A0
CHARS = {}
for i in range(26):
    CHARS[chr(65 + i)] = 0x80 + i
    CHARS[chr(97 + i)] = 0xA0 + i
CHARS.update({" ": 0x7F, "!": 0xE7})


def enc(s):
    return bytes(CHARS[c] for c in s)


def set_box(cm, species):
    m = cm.pb.memory
    m[0x0000] = 0x0A
    m[0x4000] = 1
    m[0xAD10] = len(species)
    for i, s in enumerate(species):
        m[0xAD11 + i] = s
    m[0xAD11 + len(species)] = 0xFF
    m[0x0000] = 0x00
    cm.tick(1)


def box(cm):
    s = cm.sram(1)
    n = s[0xAD10 - 0xA000]
    return n, list(s[0xAD11 - 0xA000: 0xAD11 - 0xA000 + n])


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    info, names = char_info(), species_names()
    starter = info[CHAR]["starter"]
    on = [s for s in range(1, 252) if roster_has(CHAR, s)][:3]
    off = [s for s in range(1, 252) if not roster_has(CHAR, s)][:3]
    print(f"on-roster {on}, off-roster {off}")
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def withdraw(char, species, idx, party=(starter,)):
        cm.restore(base)
        cm.set_char(char)
        cm.wb(0xDCD7, len(party))
        for i, s in enumerate(party):
            cm.wb(0xDCD8 + i, s)
        cm.wb(0xDCD8 + len(party), 0xFF)
        set_box(cm, species)
        cm.wb(0xCB2A, idx)       # scroll
        cm.wb(0xCB2B, 0)         # cursor
        cm.wb(0xD10B, 0)
        r = cm.call((0x38, 0x6DA7), frames=1200, buttons=("a", "b"))
        tm = bytes(cm.pb.memory[TILEMAP:TILEMAP + 360])
        return r, tm, cm.party(), box(cm)

    r, tm, party, (n, bx) = withdraw(None, [off[0], on[0], off[1]], 0)
    check(bool(r["F"] & 0x10) is False and len(party) == 2 and n == 2,
          f"mode off: off-roster mon withdraws ({party}, box {bx}, carry={bool(r['F'] & 0x10)})")
    mon = off[0] if tamper else on[0]
    r, tm, party, (n, bx) = withdraw(CHAR, [off[0], mon, off[1]], 1)
    check(len(party) == 2 and bx == [off[0], off[1]],
          f"on-roster mon withdraws ({party}, box {bx})")
    r, tm, party, (n, bx) = withdraw(CHAR, [on[0], off[0], on[1]], 1)
    check(bool(r["F"] & 0x10) and party == [starter] and bx == [on[0], off[0], on[1]],
          f"off-roster mon refused: carry set, party {party}, box {bx}")
    check(enc("Not on the roster!") in tm, "...and the refusal text is on screen")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
