#!/usr/bin/env python3
"""'Normal game' must behave like the untouched ROM. Differential test: the same random inputs
through the BASE ROM's routine and the patched ROM's routine with Character Mode OFF; outputs
(registers, flags and the WRAM the routine writes) must be identical.

  * IsAnyMonHoldingExpShare (0F:6C3A): 400 random parties (species, HP incl. fainted, held items
    incl. the Exp. Share, 1-6 mons): d, e, Z must match
  * CheckPartyMove (2C:5924): 400 random parties x random move: carry, and $D109 on success, must match
  * START-menu item lookup (04:60E0): items 0-8, hl must match
(--tamper turns the patched side's Character Mode ON and must FAIL.)
"""
import random, sys, tempfile
sys.path.insert(0, "tools")
from cmlib import CM

STATE = "tools/emu_states/ck9.state"
BASE_ROM = "rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
PARTY = 0xDCDF


def seed_party(cm, rnd):
    n = rnd.randint(1, 6)
    cm.wb(0xDCD7, n)
    for i in range(n):
        cm.wb(0xDCD8 + i, rnd.randint(1, 250))
        o = PARTY + i * 0x30
        for k in range(0x30):
            cm.wb(o + k, rnd.randint(0, 255) if k >= 2 else 0)
        cm.wb(o, rnd.randint(1, 250))
        cm.wb(o + 1, rnd.choice([0, 0x39, 0x39, 0x10, 0x4A]))
        hp = rnd.choice([0, 0, 20, 300])
        cm.wb(o + 0x22, hp >> 8)
        cm.wb(o + 0x23, hp & 0xFF)
    cm.wb(0xDCD8 + n, 0xFF)


def main():
    tamper = "--tamper" in sys.argv
    B = CM()
    # Base side: patched ROM image whose hook sites are restored to the base bytes (everything else kept,
    # so the test scaffolding still exists). Equivalent to running the unmodified routine.
    base = open(BASE_ROM, "rb").read()
    built = bytearray(open("build/prism_cm.gbc", "rb").read())
    for bank, addr, n in ((0x0F, 0x6C3A, 4), (0x2C, 0x5924, 6), (4, 0x60E0, 4)):
        o = addr if bank == 0 else bank * 0x4000 + addr - 0x4000
        built[o:o + n] = base[o:o + n]
    tmp = tempfile.NamedTemporaryFile(suffix=".gbc", delete=False)
    tmp.write(bytes(built)); tmp.close()
    A = CM(rom=tmp.name)
    A.load(STATE); B.load(STATE)
    snapA, snapB = A.snapshot(), B.snapshot()
    rnd = random.Random(11)
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def both(fn):
        res = []
        for cm, snap in ((A, snapA), (B, snapB)):
            cm.restore(snap)
            res.append(fn(cm))
        return res

    bad = 0
    for t in range(400):
        seed = rnd.random()
        def run(cm, seed=seed):
            r = random.Random(seed)
            seed_party(cm, r)
            cm.set_char(9 if (tamper and cm is B) else None)
            x = cm.call((0x0F, 0x6C3A), frames=60)
            return (x["D"], x["E"], bool(x["F"] & 0x80))
        ra, rb = both(run)
        bad += ra != rb
    check(bad == 0, f"Exp. Share holders: 400 random parties, mode off == shipped ({bad} differ)")

    bad = 0
    for t in range(400):
        seed = rnd.random()
        mv = rnd.choice([0x39, 0x46, 0x1D, 0xF9, 0x0F, 0x50, 0x20])
        def run(cm, seed=seed, mv=mv):
            r = random.Random(seed)
            seed_party(cm, r)
            for i in range(cm.rb(0xDCD7)):          # sprinkle the move into some mons
                if r.random() < 0.3:
                    cm.wb(PARTY + i * 0x30 + 2 + r.randint(0, 3), mv)
            cm.set_char(9 if (tamper and cm is B) else None)
            cm.wb(0xD109, 0xAA)
            x = cm.call((0x2C, 0x5924), frames=60, d=mv)
            return (bool(x["F"] & 0x10), cm.rb(0xD109) if not (x["F"] & 0x10) else None)
        ra, rb = both(run)
        bad += ra != rb
    check(bad == 0, f"CheckPartyMove: 400 random parties x moves, mode off == shipped ({bad} differ)")

    bad = 0
    for item in range(9):
        def run(cm, item=item):
            cm.wb(0xCF97, 0x6F); cm.wb(0xCF98, 0x60)
            cm.set_char(9 if (tamper and cm is B) else None)
            return cm.call((4, 0x60E0), frames=30, d=0, e=item)["HL"]
        ra, rb = both(run)
        bad += ra != rb
    check(bad == 0, f"START-menu item lookup: items 0-8, mode off == shipped ({bad} differ)")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
