#!/usr/bin/env python3
"""LIVE Exp. Share: a real battle against a 1-HP wild mon, lead mon KOs it with a real move from the
real Fight menu; the bench mon's experience is read from the party struct afterwards.

  CM on : the bench mon (which never fought, no Exp. Share held) gains experience
  CM off: it gains nothing (the engine as shipped, no item)
--tamper expects the bench mon to gain nothing with CM on and must FAIL.
"""
import sys
sys.path.insert(0, "tools"); sys.path.insert(0, "tools/tests")
from cmlib import CM
from live_battle import give_mon, start_wild, wait_battle
from test_live_catch import text, STATE

PARTY = 0xDCDF


def exp(cm, slot):
    o = PARTY + slot * 0x30 + 8
    return cm.rb(o) << 16 | cm.rb(o + 1) << 8 | cm.rb(o + 2)


def fight(cm, char):
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    give_mon(cm, 1, 30)
    for i, mv in enumerate((33, 0, 0, 0)):                  # lead knows Tackle
        cm.wb(PARTY + 2 + i, mv); cm.wb(PARTY + 23 + i, 25)
    cm.set_char(char)
    start_wild(cm, 19, 10)
    assert wait_battle(cm)
    for _ in range(60):
        if "Fight" in text(cm):
            break
        cm.tap("a", 4, 40)
    cm.tick(30)
    cm.wb(0xD216, 0); cm.wb(0xD217, 1)                        # enemy at 1 HP
    before = (exp(cm, 0), exp(cm, 1))
    cm.tap("a", 4, 60)                                        # Fight
    cm.tap("a", 4, 60)                                        # move 1
    for _ in range(40):                                       # A through the faint / experience / level-up text
        cm.tap("a", 4, 40)
    cm.tick(120)
    return before, (exp(cm, 0), exp(cm, 1)), text(cm)


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    b, a, t = fight(cm, 9)
    check(a[0] > b[0], f"CM on: lead gained exp {b[0]} -> {a[0]}")
    check((a[1] > b[1]) != tamper, f"CM on: bench mon (no item, never fought) gained exp {b[1]} -> {a[1]}")
    b, a, t = fight(cm, None)
    check(a[0] > b[0], f"CM off: lead gained exp {b[0]} -> {a[0]}")
    check(a[1] == b[1], f"CM off: bench mon gained nothing ({b[1]} -> {a[1]})")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
