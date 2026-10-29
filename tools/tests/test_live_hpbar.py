#!/usr/bin/env python3
"""LIVE instant HP bar (QoL A3, 2026-10-28; src/qol_options.asm "QolInstantHP"): a real wild battle, the lead hits the
full-HP wild mon with Tackle from the real Fight menu, and every HPBarAnim_UpdateVariables call ($40:40B7) is counted
against the animations that finish (.animdone, $40:40F3).

  shipped : at most 2 steps per finished animation (the bar goes straight to the target)
  CONTROL : the same ROM with the 3 replaced bytes put back ($79 $A7 $20) steps a pixel at a time (more than 4 each)
--tamper expects the shipped ROM to animate and must FAIL.
"""
import os
import sys
import tempfile
sys.path.insert(0, "tools"); sys.path.insert(0, "tools/tests")
from cmlib import CM, ROM, SYM
from live_battle import give_mon, start_wild, wait_battle
from test_live_catch import text, STATE

PARTY = 0xDCDF
SITE = 0x40 * 0x4000 + (0x40BA - 0x4000)


def fight(rom):
    cm = CM(rom, SYM)
    steps, done = [0], [0]
    cm.pb.hook_register(0x40, 0x40B7, lambda ctx: steps.__setitem__(0, steps[0] + 1), None)
    cm.pb.hook_register(0x40, 0x40F3, lambda ctx: done.__setitem__(0, done[0] + 1), None)
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    for i, mv in enumerate((33, 0, 0, 0)):                  # lead knows Tackle
        cm.wb(PARTY + 2 + i, mv); cm.wb(PARTY + 23 + i, 25)
    cm.set_char(None)
    start_wild(cm, 19, 10)
    assert wait_battle(cm)
    for _ in range(60):
        if "Fight" in text(cm):
            break
        cm.tap("a", 4, 40)
    cm.tick(30)
    steps[0] = done[0] = 0                                    # count from the first move on
    cm.tap("a", 4, 60)                                        # Fight
    cm.tap("a", 4, 60)                                        # move 1 (Tackle)
    for _ in range(30):
        cm.tap("a", 4, 40)
    cm.stop()
    return steps[0], done[0]


def main():
    tamper = "--tamper" in sys.argv
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    data = bytearray(open(ROM, "rb").read())
    check(data[SITE - 3:SITE + 3] == bytes.fromhex("21f1d1231836"),
          "$40:40B7 HPBarAnim_UpdateVariables: ld hl,wCurHPBarPixels / inc hl / jr .animdone")
    st, n = fight(ROM)
    instant = n > 0 and st <= 2 * n
    check(instant != tamper, f"shipped: {st} HP-bar steps over {n} finished animations (instant = at most 2 each)")
    with tempfile.TemporaryDirectory() as td:
        ctl = os.path.join(td, "control.gbc")
        data[SITE:SITE + 3] = bytes.fromhex("79a720")
        open(ctl, "wb").write(data)
        st, n = fight(ctl)
    check(n > 0 and st > 4 * n, f"CONTROL (base bytes restored): {st} HP-bar steps over {n} finished animations")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
