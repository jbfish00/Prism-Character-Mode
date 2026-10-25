"""Live unit test of the QoL relearner (2026-10-17): the relearner is free and also teaches egg moves.

Calls the REAL relearner list builder (bank 2 $768F) for party slot 0 in the test image (build/prism_cm_test.gbc) and in
the CM_NO_EGGRELEARN control image (build/prism_cm_test_noegg.gbc), from the same savestate. Pass when the control
list is the vanilla list, the QoL list is that list followed by >= 1 moves, every added move is an egg move of the
mon's family in EggMovePointers (bank 8 $4100, read from the ROM), and nothing is listed twice. Also checks the free
relearner bytes (no Heart Scale jump, no toss, no 'handed over' message) in the shipping ROM.

QoL A2 (2026-10-24): the same cases on build/prism_cm_test_nolv.gbc (CM_NO_ANYLEVEL: the level cut kept): the test image's
list must hold every move of that list plus >= 1 more, each a level-up move above the mon's level of the species or a
pre-evolution (EvosAttacksPointers, bank $10 $5DEF, read from the ROM).

Run: tools/emu_venv/bin/python3 tools/tests/test_relearner.py [--tamper]
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cmlib import CM
from live_battle import give_mon

TAMPER = "--tamper" in sys.argv     # negative control: the vanilla-list image stands in for the shipping one -> FAIL

STATE = "tools/emu_states/ck9.state"
CASES = [(26, 30), (6, 40)]          # Raichu Lv30 (base Pichu/Pikachu), Charizard Lv40 (base Charmander)


def egg_moves(rom, species):
    bank = 8 * 0x4000
    p = bank + (0x4100 - 0x4000) + 2 * (species - 1)
    ptr = rom[p] | rom[p + 1] << 8
    o = bank + (ptr - 0x4000)
    out = []
    while rom[o] != 0xFF and len(out) < 40:
        out.append(rom[o]); o += 1
    return out


def learnset_family(rom, species):
    """{move: lowest level} over the species and its pre-evolutions (method 6 location entries skipped by layout)."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "character_mode"))
    import emit_mart_evo as e
    edges, _ = e.evolutions(rom)
    fam, todo = {species}, [species]
    while todo:
        t = todo.pop()
        for s_, m, _p, tt in edges:
            if tt == t and s_ not in fam:
                fam.add(s_); todo.append(s_)
    out = {}
    for sp in fam:
        p = rom[e.rom_off(e.EVOS_BANK, e.EVOS_PTRS) + 2 * (sp - 1)] | rom[e.rom_off(e.EVOS_BANK, e.EVOS_PTRS) + 2 * (sp - 1) + 1] << 8
        o = e.rom_off(e.EVOS_BANK, p)
        while rom[o]:                                   # skip the evolution entries
            m = rom[o]
            if m == e.LOCATION:
                o += 1
                while rom[o] != 0xFF:
                    o += 2
                o += 2
            else:
                o += e.ENTRY_LEN[m]
        o += 1
        while rom[o]:
            lv, mv = rom[o], rom[o + 1]
            out[mv] = min(out.get(mv, 999), lv)
            o += 2
    return out


def run(rom, sym, species, level):
    cm = CM(rom, sym)
    cm.load(STATE)
    give_mon(cm, species, level)         # the game's own TryAddMonToParty
    cm.wb(0xD109, cm.rb(0xDCD7) - 1)     # wCurPartyMon = the new mon
    sp = cm.rb(0xDCD8 + cm.rb(0xD109))
    cm.call((2, 0x768F))
    n = cm.rb(0xD002)
    lst = list(cm.rd(0xD003, n)) if n else []
    cm.pb.stop(save=False)
    return sp, lst


def main():
    rom = open("build/prism_cm.gbc", "rb").read()
    base = open("rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc", "rb").read()
    fails = 0
    ok = rom[0xB50F:0xB512] == b"\0\0\0" and rom[0xB590:0xB59C] == b"\0" * 12 \
        and base[0xB50F:0xB512] == bytes.fromhex("d25975") and base[0xB590:0xB593] == bytes.fromhex("cddb12")
    print(("PASS" if ok else "FAIL") + " free relearner: no Heart Scale jump, no TossItem, no 'handed over' (base had all three)")
    fails += not ok
    for species, level in CASES:
        img = "build/prism_cm_test_noegg" if TAMPER else "build/prism_cm_test"
        sp, on = run(img + ".gbc", img + ".sym", species, level)
        _, off = run("build/prism_cm_test_noegg.gbc", "build/prism_cm_test_noegg.sym", species, level)
        st = "species %d Lv%d" % (species, level)
        extra = on[len(off):]
        allowed = set(egg_moves(rom, sp))
        # walk back through the families the ROM lists (base species are the ones with egg lists): accept any species'
        # egg list that contains every added move (the hook used the mon's base species)
        cands = [s for s in range(1, 255) if extra and set(extra) <= set(egg_moves(rom, s))]
        ok = on[:len(off)] == off and len(extra) >= 1 and len(set(on)) == len(on) and bool(cands)
        print(("PASS" if ok else "FAIL") + " %s: species %d, vanilla %s, QoL adds %s (egg list of species %s)"
              % (st, sp, off, extra, cands[:3]))
        fails += not ok
    for species, level in CASES:            # QoL A2: any level vs the CM_NO_ANYLEVEL image
        img = "build/prism_cm_test_nolv" if TAMPER else "build/prism_cm_test"
        sp, on = run(img + ".gbc", img + ".sym", species, level)
        _, cut = run("build/prism_cm_test_nolv.gbc", "build/prism_cm_test_nolv.sym", species, level)
        fam = learnset_family(rom, sp)
        extra = [m for m in on if m not in cut]
        ok = set(cut) <= set(on) and extra and all(m in fam and fam[m] > level for m in extra) and len(set(on)) == len(on)
        print(("PASS" if ok else "FAIL") + " any level, species %d Lv%d: level cut %s; any level adds %s (learnset levels %s)"
              % (sp, level, cut, extra, [fam.get(m) for m in extra]))
        fails += not ok
    print("RESULT: %s" % ("PASS" if not fails else "FAIL"))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
