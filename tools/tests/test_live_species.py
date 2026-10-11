#!/usr/bin/env python3
"""LIVE sweep: every species id 1..251 starts as a real wild battle (the shipped engine) and reaches
the battle menu without a crash screen, at a mid level, with Character Mode on. Species that cannot
be fought here are listed (a roster species that crashes the battle would be a Character Mode bug).
"""
import sys
sys.path.insert(0, "tools"); sys.path.insert(0, "tools/tests")
from cmlib import CM, species_names
from live_battle import give_mon, start_wild, wait_battle
from test_live_catch import text, STATE


def main():
    cm = CM()
    names = species_names()
    bad = []
    lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 and sys.argv[1].isdigit() else (1, 256)
    if "--tamper" in sys.argv:
        lo, hi = 0, 1          # species 0 is not a monster: the sweep must report it
    base = None
    for sp in range(lo, hi):
        cm.load(STATE)
        cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
        give_mon(cm, 25, 30)
        cm.set_char(9)
        start_wild(cm, sp, 20)
        ok = wait_battle(cm)
        if ok:
            for _ in range(60):
                if "Fight" in text(cm):
                    break
                cm.tap("a", 4, 40)
            ok = "Fight" in text(cm)
        if not ok:
            bad.append((sp, names.get(sp), text(cm)[:40]))
    print(f"species {lo}..{hi - 1}: {hi - lo - len(bad)} reached the battle menu, {len(bad)} did not")
    for b in bad:
        print("  ", b)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
