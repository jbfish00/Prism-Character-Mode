#!/usr/bin/env python3
"""Live test of the scripted-gift gate (GiveGate, hooked into GivePoke 3C:48D4).

Two layers, both on the built ROM:
  1. WIRING: run the REAL GivePoke from a real in-game savestate and require that
     it reaches GiveGate (PC hook) -- proves the 3C:48D7 hook is live, not just
     assembled.
  2. DECISIONS: run GiveGate itself (real TryAddMonToParty inside) per rule:
       mode off                          -> species added as given, carry set
       on-roster gift                    -> added, carry set
       off-roster gift, party empty      -> the CHARACTER'S STARTER is added instead
       off-roster gift, party non-empty  -> NOT added (carry clear: the engine's own
                                            party-full path then boxes it), count restored
       every character: off-roster + empty party yields exactly its starter
Negative control: --tamper expects the wrong starter and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, char_info, species_names

STATE = "tools/emu_states/ck9.state"
CHAR = 9          # Brock


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    info, names = char_info(), species_names()
    starter = info[CHAR]["starter"]
    on = next(s for s in range(1, 252) if roster_has(CHAR, s) and s != starter)
    off = next(s for s in range(1, 252) if not roster_has(CHAR, s))
    print(f"{info[CHAR]['name']}: on-roster {on}={names[on]}, off-roster {off}={names[off]}, starter {starter}={names[starter]}")
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    # 1. wiring
    cm.restore(base)
    cm.set_char(CHAR)
    for a, v in ((0xDCD7, 0), (0xDCD8, 0xFF), (0xD108, off), (0xD143, 5), (0xD106, 0)):
        cm.wb(a, v)
    hit = []
    bank, addr = cm.sym["GiveGate"]
    cm.pb.hook_register(bank, addr, lambda c=None: hit.append(cm.pb.frame_count), None)
    try:
        cm.call((0x3C, 0x48D4), b=0, frames=60)
    except TimeoutError:
        pass                       # GivePoke goes on to the nickname prompt; we only need the hook
    check(bool(hit), "real GivePoke (3C:48D4) reaches GiveGate through the patched hook")

    def gate(species, char, party=()):
        cm.restore(base)
        cm.set_char(char)
        cm.wb(0xDCD7, len(party))
        for i, s in enumerate(party):
            cm.wb(0xDCD8 + i, s)
        cm.wb(0xDCD8 + len(party), 0xFF)
        for a, v in ((0xD108, species), (0xD143, 5), (0xD106, 0), (0xCF5F, 7)):
            cm.wb(a, v)
        r = cm.call("GiveGate", a=0, frames=60)
        return cm.party(), bool(r["F"] & 0x10), cm.rb(0xD108)

    p, c, _ = gate(off, None)
    check(p == [off] and c, f"mode off: gift added as given ({p}, carry={c})")
    p, c, _ = gate(on, CHAR)
    check(p == [on] and c, f"on-roster gift added ({p}, carry={c})")
    p, c, _ = gate(off, CHAR)
    want = [starter + (1 if tamper else 0)]
    check(p == want and c, f"off-roster gift with empty party -> starter {want} (got {p}, carry={c})")
    p, c, _ = gate(off, CHAR, party=(on,))
    check(p == [on] and not c, f"off-roster gift with a party is refused for the party -> box path (party {p}, carry={c})")
    check(cm.rb(0xDCD7) == 1, "...and the real party count was restored")
    p, c, _ = gate(on, CHAR, party=(on,))
    check(p == [on, on] and c, f"on-roster gift with a party added ({p})")

    bad = []
    for cid, ci in info.items():
        if not ci["selectable"]:
            continue
        sp = next(s for s in range(1, 252) if not roster_has(cid, s))
        p, c, _ = gate(sp, cid)
        if p != [ci["starter"]] or not c:
            bad.append((ci["name"], p, ci["starter"]))
    check(not bad, f"every selectable character: off-roster gift + empty party yields its starter (bad: {bad[:3]})")
    # literal pin (user, 2026-10-18): Sycamore's starter is Gible (Prism species 222), never derived from the tsv
    syc = next(c for c, ci in info.items() if ci["name"] == "Sycamore")
    sp = next(s for s in range(1, 252) if not roster_has(syc, s))
    p, c, _ = gate(sp, syc)
    gible = 222 + (1 if tamper else 0)
    check(names[222] == "Gible" and p == [gible] and c, f"Sycamore (id {syc}): off-roster gift + empty party -> Gible {[gible]} (got {p})")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
