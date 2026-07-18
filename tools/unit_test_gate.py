#!/usr/bin/env python3
"""CPU-level unit test of the injected Character Mode catch gate.

Invokes the REAL assembled gate-decision code in build/prism_cm.gbc directly,
with fully controlled inputs, instead of needing to reach a wild battle:

  * Boot the ROM to a stable frame.
  * Disable interrupts (IE=0) so nothing re-banks or touches RAM mid-call.
  * Map ROM bank 118 (write 0x2000); CatchGate lives at $4000 there.
  * Plant a parking loop `jr -2` in WRAM at $C000 and point the stack return
    at it, so the routine's `ret` spins harmlessly in place (interrupts off,
    so nothing touches $C64E after the routine finishes — no hook needed;
    hooking the spin loop would fire the callback thousands of times/frame
    and stall, so we just tick once and read $C64E straight back).
  * Set $C64E (incoming catch verdict: 1 = "caught") and $D206
    (wEnemyMonSpecies) to the test species.
  * Set PC = $4002 — i.e. CatchGate + 2, SKIPPING the 2-byte
    `rst $20 / db $1E` calc replay so $C64E is a pure input. (Those 2 bytes
    are the displaced original instructions, separately verified by the
    byte-delta check; the gate DECISION logic is what this exercises.)
  * Tick once; the routine runs to completion (~200 cycles) then spins at
    PARK for the rest of the frame; read the resulting $C64E.

$C64E after the call: nonzero = catch allowed, 0 = gate blocked it.

The active character is chosen by patching the dev id byte (file 0x1DBFFE) in
a temp copy of the ROM per case ($FF = mode off).

Run: tools/emu_venv/bin/python3 tools/unit_test_gate.py
"""
import os
import shutil
import tempfile

from pyboy import PyBoy

ROM = "build/prism_cm.gbc"
CHARID_FILE_OFF = 0x1DBFFE
CATCHGATE_ENTRY = 0x4002          # bank 118, past the 2-byte calc replay
PARK = 0xC000
VERDICT = 0xC64E
ENEMY_SPECIES = 0xD206


def load_species_names():
    names = {}
    for line in open("tools/character_mode/prism_species_table.tsv"):
        if line.startswith("#") or not line.strip():
            continue
        i, nm = line.rstrip("\n").split("\t")
        names[int(i)] = nm
    return names


def load_roster_bit(char_index, species_id):
    """Ground truth from the emitted rosters.asm bitmap."""
    import re
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
    bm = rows[char_index]
    return (bm[species_id >> 3] >> (species_id & 7)) & 1


def _boot(char_id):
    """Boot a patched-ROM PyBoy for a fixed character id; return (pb, tmpname)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".gbc", delete=False)
    shutil.copyfile(ROM, tmp.name)
    with open(tmp.name, "r+b") as f:
        f.seek(CHARID_FILE_OFF)
        f.write(bytes([char_id & 0xFF]))
    pb = PyBoy(tmp.name, window="null", cgb=True)
    pb.set_emulation_speed(0)
    for _ in range(400):
        pb.tick()
    pb.memory[0xFFFF] = 0x00          # IE = 0: no interrupts serviced
    pb.memory[0xFF0F] = 0x00
    pb.memory[PARK] = 0x18            # jr
    pb.memory[PARK + 1] = 0xFE        # -2 (spin)
    pb.memory[0x2000] = 118           # map bank 118
    return pb, tmp.name


def _invoke(pb, species, verdict_in):
    rf = pb.register_file
    pb.memory[VERDICT] = verdict_in & 0xFF
    pb.memory[ENEMY_SPECIES] = species & 0xFF
    rf.SP = 0xDFEE
    pb.memory[0xDFEE] = PARK & 0xFF
    pb.memory[0xDFEF] = PARK >> 8
    rf.PC = CATCHGATE_ENTRY
    pb.tick()             # routine runs then spins at PARK
    return pb.memory[VERDICT]


def run_gate(char_id, species, verdict_in=1):
    pb, name = _boot(char_id)
    try:
        return _invoke(pb, species, verdict_in)
    finally:
        pb.stop(save=False)
        os.unlink(name)


def main():
    names = load_species_names()
    # Brock = index 8 (from roster_index.tsv). Pick an on-roster and an
    # off-roster species for Brock, plus mode-off control.
    # Determine dynamically from the bitmap so the test is self-checking.
    import re
    brock = 8
    on_species = None
    off_species = None
    for sid in range(1, 256):
        bit = load_roster_bit(brock, sid)
        if bit and on_species is None:
            on_species = sid
        if not bit and off_species is None and sid < 252:
            off_species = sid
        if on_species and off_species:
            break

    print(f"Brock (idx {brock}) on-roster sample: {on_species} "
          f"({names.get(on_species,'?')}), off-roster sample: {off_species} "
          f"({names.get(off_species,'?')})")
    print()

    cases = [
        ("mode OFF ($FF), off-roster species -> should ALLOW (verdict kept)",
         0xFF, off_species, True),
        ("mode OFF ($FF), on-roster species  -> should ALLOW",
         0xFF, on_species, True),
        ("Brock, ON-roster species  -> should ALLOW (verdict kept nonzero)",
         brock, on_species, True),
        ("Brock, OFF-roster species -> should BLOCK (verdict -> 0)",
         brock, off_species, False),
        ("Brock, incoming verdict already 0 -> stays 0 (early ret)",
         brock, on_species, None),  # verdict_in=0
    ]
    fails = 0
    for desc, cid, sp, expect_allow in cases:
        vin = 0 if expect_allow is None else 1
        v = run_gate(cid, sp, verdict_in=vin)
        allowed = (v is not None and v != 0)
        if expect_allow is None:
            ok = (v == 0)
            verdict_str = "stayed 0" if ok else f"CHANGED to {v}"
        else:
            ok = (allowed == expect_allow)
            verdict_str = f"verdict={v} ({'ALLOW' if allowed else 'BLOCK'})"
        print(f"[{'PASS' if ok else 'FAIL'}] {desc}\n        -> {verdict_str}")
        if not ok:
            fails += 1

    # Exhaustive sweep: for Brock, EVERY species id 1..251 must match its
    # roster bitmap bit (allow iff bit set). Boundary species 252-255 (Egg/
    # Debug/fakemon slots) included too.
    print("\n--- exhaustive sweep: Brock, all species 1..255 vs bitmap ---")
    sweep_fail = 0
    pb, name = _boot(brock)
    try:
        for sid in range(1, 256):
            expect = load_roster_bit(brock, sid)
            v = _invoke(pb, sid, 1)
            got = 1 if (v and v != 0) else 0
            if got != expect:
                sweep_fail += 1
                if sweep_fail <= 10:
                    print(f"  MISMATCH species {sid} ({names.get(sid,'?')}): "
                          f"bitmap={expect} gate={got}")
    finally:
        pb.stop(save=False)
        os.unlink(name)
    print(f"sweep: {255 - sweep_fail}/255 species correct, {sweep_fail} mismatches")
    fails += sweep_fail

    print()
    print("ALL PASS" if fails == 0 else f"{fails} FAILURE(S)")
    return fails


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
