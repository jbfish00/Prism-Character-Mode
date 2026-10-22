#!/usr/bin/env python3
"""Character Mode quality-of-life rules, on the REAL routines in the built ROM:

  Exp. Share (0F:6C3A IsAnyMonHoldingExpShare):
    on AND off (user 2026-10-21): every alive party mon is a holder (fainted ones are not), item or not
  Field moves with no learner (2C:5924 CheckPartyMove):
    mode off  : unchanged (found only when a party mon knows the move)
    mode on   : Surf, Strength, Headbutt, Rock Smash, Cut answer 'found' (party slot 0);
                every other move is still decided by the party
  Reusable TMs: Prism's TeachTMHM (0B:47BB) never consumes the item (static evidence)
(--tamper makes the expected mask wrong and must FAIL.)
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM

STATE = "tools/emu_states/ck9.state"
PARTY = 0xDCDF
STRIDE = 0x30
EXP_SHARE = 0x39
HMS = {"Surf": 0x39, "Strength": 0x46, "Headbutt": 0x1D, "Rock Smash": 0xF9, "Cut": 0x0F}


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def party(species, hp, item, moves=None):
        cm.restore(base)
        cm.wb(0xDCD7, len(species))
        for i, s in enumerate(species):
            cm.wb(0xDCD8 + i, s)
        cm.wb(0xDCD8 + len(species), 0xFF)
        for i in range(len(species)):
            o = PARTY + i * STRIDE
            for k in range(STRIDE):
                cm.wb(o + k, 0)
            cm.wb(o, species[i])
            cm.wb(o + 1, item[i])
            cm.wb(o + 0x22, hp[i] >> 8)
            cm.wb(o + 0x23, hp[i] & 0xFF)
            for k, mv in enumerate((moves or {}).get(i, [])):
                cm.wb(o + 2 + k, mv)           # MON_MOVES (the engine reads them at +2... checked below)

    def exp(char, species, hp, item):
        party(species, hp, item)
        cm.set_char(char)
        r = cm.call((0x0F, 0x6C3A), frames=60)
        return r["D"], r["E"], bool(r["F"] & 0x80)

    # user 2026-10-21: party-wide with Character Mode OFF too (a normal game)
    d, e, z = exp(None, [1, 4, 7], [10, 0, 10], [0, 0, 0])
    check((d, e) == (0b101 ^ (2 if tamper else 0), 2) and not z, f"OFF, no items, middle mon fainted -> alive mons 1 and 3 share (d={d:03b}, e={e})")
    d, e, z = exp(None, [1, 4, 7], [10, 10, 10], [0, EXP_SHARE, 0])
    check((d, e, z) == (0b111, 3, False), f"OFF, one holder -> still the whole party (d={d:03b}, e={e})")
    d, e, z = exp(None, [1], [0], [EXP_SHARE])
    check(z and (d, e) == (0, 0), f"OFF, only mon fainted (holding the item) -> nobody (d={d:03b}, e={e})")
    want = (0b101 ^ (1 if tamper else 0), 2)
    d, e, z = exp(9, [1, 4, 7], [10, 0, 10], [0, 0, 0])
    check((d, e) == want and not z, f"ON, no items, middle mon fainted -> alive mons 1 and 3 share (d={d:03b}, e={e})")
    d, e, z = exp(9, [1, 4, 7, 10, 13, 16], [5] * 6, [0] * 6)
    check((d, e) == (0b111111, 6) and not z, f"ON, full party -> all six (d={d:06b}, e={e})")
    d, e, z = exp(9, [1], [0], [0])
    check(z and (d, e) == (0, 0), "ON, only mon fainted -> nobody (the faint case is unchanged)")

    def find(char, move, known_by=None):
        party([1, 4, 7], [10, 10, 10], [0, 0, 0], moves=({known_by: [move]} if known_by is not None else None))
        cm.set_char(char)
        cm.wb(0xD109, 0xAA)
        r = cm.call((0x2C, 0x5924), frames=60, d=move)
        return (not (r["F"] & 0x10)), cm.rb(0xD109)

    # which byte offset does the engine read for 'moves'? probe: put Surf in slot 2's move list at +2.
    found, slot = find(None, 0x39, known_by=2)
    check(found and slot == 2, f"off: a mon that knows Surf is found (slot {slot})")
    found, slot = find(None, 0x39)
    check(not found, "off: no learner -> not found (as shipped)")
    for nm, mv in HMS.items():
        found, slot = find(9, mv)
        check(found and slot == 0, f"ON: {nm} with no learner -> found, slot {slot}")
    found, slot = find(9, 0x50)
    check(not found, "ON: a non-HM move (0x50) with no learner is still not found")
    found, slot = find(9, 0x39, known_by=1)
    check(found, "ON: a real learner is still fine")

    rom = open("build/prism_cm.gbc", "rb").read()
    base_rom = open("rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc", "rb").read()
    o = 0x0B * 0x4000 + 0x47E6 - 0x4000
    seq = bytes.fromhex("fa06d1cd4812d80e05cf017250 37c9".replace(" ", ""))
    check(rom[o:o + len(seq)] == seq == base_rom[o:o + len(seq)],
          "TeachTMHM: after LearnMove/IsHM it only changes happiness (call $1248, ld c,5, ChangeHappiness) then scf/ret: no ConsumeTM -> TMs reusable")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
