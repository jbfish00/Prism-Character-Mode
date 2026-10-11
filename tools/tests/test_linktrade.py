#!/usr/bin/env python3
"""Link-cable trade veto (LinkTradeGate, hooked into LinkTrade's confirm at 0A:4AA5).

PyBoy has no link cable, so the REAL decision code runs from a savestate with the offered species
planted in the other side's party ($D281 + $D003) and the cursor on the Trade row ($CFA9 = 1); the
branch the patched routine takes is read with PC hooks on the two real targets
(0A:4AC8 = trade goes ahead, 0A:4AAB = canceled).

  mode off / on-roster offer / egg offer : trade goes ahead
  off-roster offer                       : canceled, for every selectable character
  cursor on Cancel                       : canceled whatever is offered (the engine's own branch)
--tamper expects off-roster to go ahead and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, char_info, species_names

STATE = "tools/emu_states/ck9.state"
TRADE, CANCEL = (0x0A, 0x4AC8), (0x0A, 0x4AAB)


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    info = char_info()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    hit = []
    for tag, (b, a) in (("trade", TRADE), ("cancel", CANCEL)):
        cm.pb.hook_register(b, a, lambda c=None, t=tag: hit.append(t), None)

    def decide(char, species, cursor=1):
        cm.restore(base)
        cm.set_char(char)
        cm.wb(0xCFA9, cursor)
        cm.wb(0xD003, 2)
        cm.wb(0xD281 + 2, species)
        hit.clear()
        try:
            cm.call((0x0A, 0x4AA5), frames=120)
        except TimeoutError:
            pass
        return hit[0] if hit else None

    c0 = 9
    on = next(s for s in range(1, 252) if roster_has(c0, s))
    off = next(s for s in range(1, 252) if not roster_has(c0, s))
    check(decide(None, off) == "trade", "mode off, any offer: trade goes ahead")
    check(decide(c0, on) == "trade", "CM on, on-roster offer: trade goes ahead")
    check(decide(c0, 0xFD) == "trade", "CM on, egg offered: trade goes ahead (eggs exempt)")
    check((decide(c0, off) == "cancel") != tamper, "CM on, off-roster offer: canceled")
    check(decide(c0, on, cursor=2) == "cancel", "cursor on Cancel: the engine's own cancel branch")
    bad = []
    for c in info:
        if not info[c]["selectable"]:
            continue
        o = next(s for s in range(1, 252) if not roster_has(c, s))
        n = next(s for s in range(1, 252) if roster_has(c, s))
        if decide(c, o) != "cancel" or decide(c, n) != "trade":
            bad.append(info[c]["name"])
    check(not bad, f"all selectable characters: off-roster canceled, on-roster goes ahead (bad: {bad[:3]})")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
