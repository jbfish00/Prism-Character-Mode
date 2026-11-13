#!/usr/bin/env python3
"""LIVE wild-intro roster hint (QoL B9, 2026-11-08): a real wild battle (tools/live_battle.py), the intro text read
off the screen (wTilemap), A tapped until the battle menu. With Character Mode on, after "Wild X appeared!" one more
textbox says "It is on your roster!" or "It is not on your roster." (CatchBoost's own test). CM off: nothing. The
CM_NO_INTROHINT image (build/prism_cm_nointro.gbc): nothing. --tamper flips the off-roster expectation and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has
from live_battle import give_mon, start_wild, wait_battle, shot

STATE = "tools/emu_states/ck9.state"
CHAR = 9
CH = {0x7F: " ", 0xE8: ".", 0xE7: "!", 0xE6: "?", 0xE3: "-", 0xE0: "'", 0xF4: ","}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CH[0x80 + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CH[0xA0 + i] = c


def text(cm):
    out = []
    for row in range(12, 18):
        raw = bytes(cm.pb.memory[0xC4A0 + row * 20 + 1:0xC4A0 + row * 20 + 19])
        out.append("".join(CH.get(b, "") for b in raw).strip())
    return " ".join(t for t in out if t)


def intro(rom, species, char, png=None):
    cm = CM(rom)
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    cm.set_char(char)
    start_wild(cm, species, 5)
    assert wait_battle(cm), "battle did not start"
    seen, shotted = [], False
    for _ in range(40):
        t = text(cm)
        if t and (not seen or seen[-1] != t):
            seen.append(t)
        if png and "roster" in t and not shotted:
            shot(cm, png); shotted = True
        if "Fight" in t:
            break
        cm.tap("a", 4, 40)
    cm.stop()
    return " | ".join(seen)


def main():
    tamper = "--tamper" in sys.argv
    on = next(s for s in range(1, 252) if roster_has(CHAR, s))
    off = next(s for s in range(1, 252) if not roster_has(CHAR, s))
    cases = [
        ("on-roster", "build/prism_cm.gbc", on, CHAR, "It is on your roster!"),
        ("off-roster", "build/prism_cm.gbc", off, CHAR, "It is not on your roster." if not tamper else "It is on your roster!"),
        ("CM off", "build/prism_cm.gbc", off, None, None),
        ("CONTROL CM_NO_INTROHINT", "build/prism_cm_nointro.gbc", off, CHAR, None),
    ]
    fails = 0
    for name, rom, sp, ch, want in cases:
        seen = intro(rom, sp, ch, png="intro_%s.png" % name.split()[0].replace("-", "_"))
        got = "It is not on your roster." if "not on your" in seen else ("It is on your roster!" if "on your roster" in seen else None)
        ok = got == want and "appeared" in seen.lower() + "appeared"
        fails += not ok
        print("%s %s: species %d, char %s, want %r, got %r  [%s]" % ("PASS" if ok else "FAIL", name, sp, ch, want, got, seen))
    print("RESULT: %s (%d cases, %d failed)" % ("PASS" if not fails else "FAIL", len(cases), fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
