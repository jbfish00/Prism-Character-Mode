#!/usr/bin/env python3
"""Behaviour cards batch 1 (2026-11-25): run the new bank-$0D routines in the emulator (PyBoy, the shipping ROM).
  CM_DisableTurns: 400 calls -> a in 5..8 (Disable 4-7 turns), every value seen, c incremented (the displaced inc c)
  CM_EncoreTurns:  400 calls -> a in 5..9 (Encore 4-8 turns), every value seen
  CM_ProtectCap:   entered with hl = its own address ([hl] = $7E = 126 uses) -> b = 4 (3 halvings, 1/8 floor)
(the hooks' bytes are pinned by check_behaviour.py; CheckHit's never-miss branch is static-only.)
--tamper expects Disable 4..7 instead and must FAIL."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cmlib import CM

N = 400


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load("tools/emu_states/ck9.state")
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg); fails += not ok

    seen, cbad = {}, 0
    for i in range(N):
        r = cm.call("CM_DisableTurns", c=i & 0x0F)
        a = r["A"]; seen[a] = seen.get(a, 0) + 1
        cbad += r["C"] != ((i & 0x0F) + 1)
    want = {4, 5, 6, 7} if tamper else {5, 6, 7, 8}
    check(set(seen) == want, "Disable counter values %s (want exactly %s)" % (sorted(seen.items()), sorted(want)))
    check(cbad == 0, "c = slot + 1 after every call (%d wrong)" % cbad)
    seen = {}
    for i in range(N):
        a = cm.call("CM_EncoreTurns")["A"]; seen[a] = seen.get(a, 0) + 1
    check(set(seen) == {5, 6, 7, 8, 9}, "Encore counter values %s (want exactly 5..9)" % sorted(seen.items()))
    r = cm.call("CM_ProtectCap")
    check(r["B"] == 4, "Protect after 126 uses: b = %d halvings+1 (want 4)" % r["B"])
    print("RESULT:", "FAIL" if fails else "ALL PASS", "(%d failed)" % fails)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
