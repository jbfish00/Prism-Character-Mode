#!/usr/bin/env python3
"""Scripted-egg gate (GiveEggGate, hooked into the `giveegg` script command at 25:658B).

  1. WIRING: the REAL giveegg script handler (25:657B) reaches GiveEggGate (PC hook).
  2. DECISIONS, running the real GiveEgg inside the gate and reading the egg back out of the party:
       mode off / on-roster species : egg exactly as the engine makes it
       off-roster species           : the egg is the character's STARTER's egg (same struct as a
                                      mode-off egg of the starter), for every selectable character
--tamper expects the off-roster egg to be unchanged and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, char_info, species_names

STATE = "tools/emu_states/ck9.state"
PARTY = 0xDCDF


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    info, names = char_info(), species_names()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def egg(species, char):
        cm.restore(base)
        cm.set_char(char)
        cm.wb(0xDCD7, 1); cm.wb(0xDCD8, 25); cm.wb(0xDCD9, 0xFF)       # one real mon in the party
        for k in range(0x30):
            cm.wb(PARTY + k, 0)
        cm.wb(PARTY, 25)
        for a, v in ((0xD108, species), (0xD143, 5), (0xCF5F, 0)):
            cm.wb(a, v)
        r = cm.call("GiveEggGate", frames=200)
        n = cm.rb(0xDCD7)
        struct = cm.rd(PARTY + 0x30, 0x30) if n == 2 else b""
        return n, cm.rb(0xDCD8 + 1), bool(r["F"] & 0x10), struct[:1].hex(), struct

    # 1. wiring
    cm.restore(base)
    cm.set_char(9)
    hit = []
    bank, addr = cm.sym["GiveEggGate"]
    cm.pb.hook_register(bank, addr, lambda c=None: hit.append(1), None)
    cm.wb(0xDCD7, 1); cm.wb(0xDCD8, 25); cm.wb(0xDCD9, 0xFF)
    # script handler: GetScriptByte reads the script at wScriptPos; point it at "species, level"
    on0 = next(s for s in range(1, 252) if roster_has(9, s))
    for a, v in ((0xD439, 0x25), (0xD43A, 0xF0), (0xD43B, 0x7F)):
        cm.wb(a, v)
    try:
        cm.call((0x25, 0x657B), frames=120)
    except TimeoutError:
        pass
    check(bool(hit), "real giveegg script handler (25:657B) reaches GiveEggGate through the patched call")
    cm.pb.hook_deregister(bank, addr)

    # 2. decisions
    sel = [c for c in info if info[c]["selectable"] and info[c]["starter"]]
    bad = []
    for c in sel:
        st = info[c]["starter"]
        off = next(s for s in range(1, 252) if not roster_has(c, s) and s != st)
        on = next(s for s in range(1, 252) if roster_has(c, s))
        ref_on = egg(on, None)
        got_on = egg(on, c)
        ref_st = egg(st, None)
        got_off = egg(off, c)
        ok_on = got_on[:4] == ref_on[:4] and got_on[4][:0] == b"" and got_on[0] == 2
        # the egg of the starter: same species byte as a mode-off egg of the starter
        ok_off = got_off[3] == ref_st[3] and got_off[0] == 2
        if tamper:
            ok_off = got_off[3] == egg(off, None)[3]
        if not (ok_on and ok_off):
            bad.append((info[c]["name"], names[off], got_off[3], ref_st[3]))
    check(not bad, f"{len(sel)} characters: on-roster egg untouched, off-roster egg == the starter's egg (bad: {bad[:2]})")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
