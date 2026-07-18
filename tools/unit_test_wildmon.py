#!/usr/bin/env python3
"""CPU-level unit test of the injected wild-encounter override (Phase 5).

Mirrors tools/unit_test_gate.py's technique: invoke the REAL assembled
routines in build/prism_cm.gbc directly via controlled registers/PC, with
interrupts off and a WRAM `jr -2` park loop as the return target, instead
of needing to reach a real wild battle of each of the 4 encounter types.

Covers, cross-checked against independent Python reference models built
from the same source data the ROM tables were generated from
(rosters.asm bitmap + wildmon_families.tsv):

  1. CheckEligible: exhaustive 1..255 sweep for one character vs. the
     roster-bitmap-AND-NOT-legendary reference.
  2. PickFamilyStage: hand-picked cases spanning a clean linear chain
     (Charmander line), a branching/tied family (Eevee), a trade/no-level
     tie (Duskull/Dusclops/Dusknoir), and a standalone species.
  3. OverrideWildSpecies with Character Mode OFF ($FF): must be carry-
     clear (no override) on every call, deterministically, since the
     off-check happens before any RNG use.
  4. OverrideWildSpecies with Character Mode ON: statistical hit-rate
     sanity check (~10%) plus a pool-membership check on every hit (the
     returned species' family must trace back to a real eligible roster
     member).
  5. End-to-end through each of the 3 real hook stubs (WildStubGrassWater/
     TreeRock/Fish) with their site-specific register conventions, driving
     each until both a miss (species byte-for-byte unchanged) and a hit
     (species changed to something eligible) are observed.

Run: tools/emu_venv/bin/python3 tools/unit_test_wildmon.py
"""
import os
import re
import shutil
import tempfile

from pyboy import PyBoy

ROM = "build/prism_cm.gbc"
CHARID_FILE_OFF = 0x1DBFFE
PARK = 0xC000
WILD_SPECIES = 0xD22E
WILD_LEVEL = 0xD143
BANK_REG = 0x2000
CM_BANK = 118

# Addresses from the linker symbol file (tools/bin/rgblink -n), bank 76 hex
# = 118 decimal.
ADDR = {
    "OverrideWildSpecies": 0x4900,
    "CheckEligible": 0x492B,
    "GetFamilyRecord": 0x496B,
    "PickFamilyStage": 0x4975,
    "WildStubGrassWater": 0x4F00,
    "WildStubTreeRock": 0x4F40,
    "WildStubFish": 0x4F80,
}

FLAG_C = 0x10


def load_species_names():
    names = {}
    for line in open("tools/character_mode/prism_species_table.tsv"):
        if line.startswith("#") or not line.strip():
            continue
        i, nm = line.rstrip("\n").split("\t")
        names[int(i)] = nm
    return names


def load_rosters():
    """[char_index] -> 32-byte bitmap, from the emitted rosters.asm."""
    rows = []
    cur = []
    capture = False
    for line in open("tools/character_mode/rosters.asm"):
        m = re.match(r"^; +(\d+):", line)
        if m:
            if cur:
                rows.append(cur)
            cur = []
            capture = True
            continue
        if capture and line.strip().startswith("db "):
            cur += [int(x, 16) for x in re.findall(r"\$([0-9A-Fa-f]{2})", line)]
    if cur:
        rows.append(cur)
    return rows


def roster_bit(rosters, char_index, species_id):
    bm = rosters[char_index]
    return (bm[species_id >> 3] >> (species_id & 7)) & 1


def load_families():
    """species_id -> (family_root, stage_min, stage_max, is_legendary)."""
    fams = {}
    for line in open("tools/character_mode/wildmon_families.tsv"):
        if line.startswith("#") or line.startswith("id\t") or not line.strip():
            continue
        parts = line.rstrip("\n").split("\t")
        sid, name, root, smin, smax, legend = (
            int(parts[0]), parts[1], int(parts[2]), int(parts[3]),
            int(parts[4]), int(parts[5]))
        fams[sid] = (root, smin, smax, bool(legend))
    return fams


def expected_eligible(rosters, fams, char_index, species_id):
    if species_id == 0:
        return False
    if not roster_bit(rosters, char_index, species_id):
        return False
    if fams[species_id][3]:  # legendary
        return False
    return True


def expected_pick_family_stage(fams, species_id, level):
    root = fams[species_id][0]
    best = species_id
    for sid in range(1, 256):
        f = fams.get(sid)
        if not f or f[0] != root:
            continue
        _, smin, smax, _ = f
        if smin <= level <= smax:
            best = sid  # last match wins, matching the asm's scan order
    return best


def _boot(char_id):
    tmp = tempfile.NamedTemporaryFile(suffix=".gbc", delete=False)
    shutil.copyfile(ROM, tmp.name)
    with open(tmp.name, "r+b") as f:
        f.seek(CHARID_FILE_OFF)
        f.write(bytes([char_id & 0xFF]))
    pb = PyBoy(tmp.name, window="null", cgb=True)
    pb.set_emulation_speed(0)
    for _ in range(400):
        pb.tick()
    pb.memory[0xFFFF] = 0x00
    pb.memory[0xFF0F] = 0x00
    pb.memory[PARK] = 0x18
    pb.memory[PARK + 1] = 0xFE
    pb.memory[BANK_REG] = CM_BANK
    return pb, tmp.name


def _park_return(pb):
    rf = pb.register_file
    rf.SP = 0xDFEE
    pb.memory[0xDFEE] = PARK & 0xFF
    pb.memory[0xDFEF] = PARK >> 8


def call_check_eligible(pb, species, char_id):
    rf = pb.register_file
    rf.A = species & 0xFF
    rf.D = char_id & 0xFF
    _park_return(pb)
    rf.PC = ADDR["CheckEligible"]
    pb.tick()
    return bool(pb.register_file.F & FLAG_C)


def call_pick_family_stage(pb, species, level):
    rf = pb.register_file
    rf.HL = species & 0xFF          # l = species (h unused by the routine)
    rf.B = level & 0xFF
    _park_return(pb)
    rf.PC = ADDR["PickFamilyStage"]
    pb.tick()
    return pb.register_file.A


def call_override(pb, level, orig_species=1):
    rf = pb.register_file
    rf.B = level & 0xFF
    rf.C = orig_species & 0xFF
    _park_return(pb)
    rf.PC = ADDR["OverrideWildSpecies"]
    pb.tick()
    carry = bool(pb.register_file.F & FLAG_C)
    return carry, pb.register_file.A


def call_stub_grasswater(pb, species, level):
    pb.memory[WILD_LEVEL] = level & 0xFF
    rf = pb.register_file
    rf.A = species & 0xFF
    _park_return(pb)
    rf.PC = ADDR["WildStubGrassWater"]
    pb.tick()
    return pb.memory[WILD_SPECIES]


def call_stub_treerock(pb, species, level, table_addr=0xC100):
    # hl -> [species byte][level byte] in scratch WRAM, matching what the
    # real SelectTreeMon-equivalent's table layout looks like at the hook.
    pb.memory[table_addr] = species & 0xFF
    pb.memory[table_addr + 1] = level & 0xFF
    rf = pb.register_file
    rf.HL = table_addr
    _park_return(pb)
    rf.PC = ADDR["WildStubTreeRock"]
    pb.tick()
    return pb.memory[WILD_SPECIES]


def call_stub_fish(pb, species, level):
    rf = pb.register_file
    rf.A = species & 0xFF
    rf.E = level & 0xFF
    _park_return(pb)
    rf.PC = ADDR["WildStubFish"]
    pb.tick()
    return pb.memory[WILD_SPECIES]


def main():
    names = load_species_names()
    rosters = load_rosters()
    fams = load_families()
    fails = 0

    # Pick a character with a reasonably large, non-all-legendary roster
    # for the statistical/stub tests. Brock (idx 8, used by the catch-gate
    # tests already) works fine here too.
    brock = 8

    # --- 1. CheckEligible exhaustive sweep -------------------------------
    print("--- CheckEligible: exhaustive 1..255 sweep, Brock ---")
    pb, name = _boot(0xFF)  # char id irrelevant to boot; we pass d= per call
    mism = 0
    try:
        for sid in range(1, 256):
            got = call_check_eligible(pb, sid, brock)
            exp = expected_eligible(rosters, fams, brock, sid)
            if got != exp:
                mism += 1
                if mism <= 10:
                    print(f"  MISMATCH species {sid} ({names.get(sid,'?')}): "
                          f"expected={exp} got={got}")
    finally:
        pb.stop(save=False)
        os.unlink(name)
    print(f"  {255-mism}/255 correct, {mism} mismatches")
    fails += mism

    # --- 2. PickFamilyStage hand-picked cases ----------------------------
    print("\n--- PickFamilyStage: hand-picked family/level cases ---")
    cases = [
        (4, 1, "Charmander family, level 1 -> Charmander"),
        (4, 20, "Charmander family, level 20 -> Charmeleon"),
        (4, 90, "Charmander family, level 90 -> Charizard"),
        (6, 1, "handed Charizard directly, level 1 -> Charmander"),
        (133, 50, "Eevee family, level 50 -> tied, last-in-table-order wins"),
        (90, 10, "Duskull family, level 10 -> Duskull"),
        (90, 50, "Duskull family, level 50 -> Dusclops/Dusknoir tie"),
        (86, 42, "Sableye (standalone), any level -> itself"),
    ]
    pb, name = _boot(0xFF)
    try:
        for sid, level, desc in cases:
            got = call_pick_family_stage(pb, sid, level)
            exp = expected_pick_family_stage(fams, sid, level)
            ok = got == exp
            if not ok:
                fails += 1
            print(f"  [{'PASS' if ok else 'FAIL'}] {desc}: "
                  f"got={got}({names.get(got,'?')}) expected={exp}({names.get(exp,'?')})")
    finally:
        pb.stop(save=False)
        os.unlink(name)

    # --- 3. Mode OFF determinism -----------------------------------------
    print("\n--- OverrideWildSpecies: Character Mode OFF -> always no-op ---")
    pb, name = _boot(0xFF)
    off_fail = 0
    try:
        for i in range(30):
            pb.tick()  # let the clock advance between calls
            carry, _ = call_override(pb, level=20)
            if carry:
                off_fail += 1
    finally:
        pb.stop(save=False)
        os.unlink(name)
    print(f"  {30-off_fail}/30 calls correctly did not override"
          f"{'' if off_fail == 0 else f' ({off_fail} FAILED)'}")
    fails += off_fail

    # --- 4. Mode ON statistical + pool-membership check -------------------
    print(f"\n--- OverrideWildSpecies: Character Mode ON (Brock, idx {brock}) ---")
    eligible_roots = {fams[s][0] for s in range(1, 256)
                       if expected_eligible(rosters, fams, brock, s)}
    print(f"  Brock has {sum(1 for s in range(1,256) if expected_eligible(rosters,fams,brock,s))} "
          f"eligible species across {len(eligible_roots)} families")
    pb, name = _boot(brock)
    hits = 0
    trials = 600
    bad_pool = 0
    test_level = 25
    try:
        for i in range(trials):
            pb.tick()
            carry, species = call_override(pb, level=test_level, orig_species=1)
            if carry:
                hits += 1
                root = fams.get(species, (None,))[0]
                is_legend = fams.get(species, (0, 0, 0, False))[3]
                if root not in eligible_roots or is_legend:
                    bad_pool += 1
                    if bad_pool <= 5:
                        print(f"  BAD OVERRIDE: got species {species} "
                              f"({names.get(species,'?')}) root={root} "
                              f"legendary={is_legend}")
    finally:
        pb.stop(save=False)
        os.unlink(name)
    rate = 100.0 * hits / trials
    print(f"  {hits}/{trials} trials overrode ({rate:.1f}%, expect ~10%)")
    print(f"  pool-membership: {hits-bad_pool}/{hits} overrides drew from an "
          f"eligible family{'' if bad_pool == 0 else f' ({bad_pool} FAILED)'}")
    if bad_pool:
        fails += bad_pool
    if not (3.0 <= rate <= 20.0):
        print(f"  FAIL: hit rate {rate:.1f}% is outside the sanity band [3,20]%")
        fails += 1

    # --- 5. End-to-end through each real hook stub -------------------------
    print("\n--- End-to-end through each hook stub (Brock) ---")
    stub_fns = {
        "A grass/cave+surf": call_stub_grasswater,
        "B headbutt/rocksmash": call_stub_treerock,
        "C fishing (all rods)": call_stub_fish,
    }
    orig_species = 1  # Bulbasaur - not on Brock's roster, so any change we
                        # see back must be either "unchanged" (miss) or an
                        # eligible override (hit), never anything else.
    for label, fn in stub_fns.items():
        pb, name = _boot(brock)
        saw_hit = False
        saw_miss = False
        bad = 0
        try:
            for i in range(300):
                pb.tick()
                got = fn(pb, orig_species, test_level)
                if got == orig_species:
                    saw_miss = True
                else:
                    saw_hit = True
                    root = fams.get(got, (None,))[0]
                    is_legend = fams.get(got, (0, 0, 0, False))[3]
                    if root not in eligible_roots or is_legend:
                        bad += 1
                if saw_hit and saw_miss and i > 50:
                    break
        finally:
            pb.stop(save=False)
            os.unlink(name)
        ok = saw_hit and saw_miss and bad == 0
        if not ok:
            fails += 1
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: saw_hit={saw_hit} "
              f"saw_miss={saw_miss} bad_overrides={bad}")

    print()
    print("ALL PASS" if fails == 0 else f"{fails} FAILURE(S)")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
