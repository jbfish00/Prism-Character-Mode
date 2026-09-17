#!/usr/bin/env python3
"""Self-test for tools/sram.py -- the SRAM reader that unblocked front 1.

⭐ WHY A TEST AT ALL. The capability is one line (`memory[0x0000] = 0x0A`), but
the thing it replaced -- "SRAM is unreadable in PyBoy" -- was recorded as a hard
blocker in game_plans/prism.md for weeks. A one-line capability that silently
stops working would put the blocker back with no signal, so it is pinned here.

Every check is negative-testable by construction: each asserts a value that is
WRONG if the latch is not actually open.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import sram  # noqa: E402

ROM = os.path.join(ROOT, "rom", "Pokemon Prism (v0.95 build 254 Hotfix 5).gbc")
STATE_BLANK = os.path.join(ROOT, "tools", "emu_states", "ck8.state")
STATE_INIT = os.path.join(ROOT, "tools", "emu_states", "after_intro.state")

# An all-$FF primary-game-data range sums to this. 0xAB75-0xA009+1 = 2925 bytes;
# 2925 * 0xFF = 0xB6193, truncated to 16 bits = 0x6193. A pure arithmetic
# identity, so it pins the checksum implementation independently of any ROM.
ALL_FF_PRIMARY_SUM = 0x6193

# How many checks this layer must run. A deliberate LITERAL.
EXPECT_CHECKS = 6

failures = []
ran = 0


def check(ok, label):
    global ran
    ran += 1
    print("  [%s] %s" % ("PASS" if ok else "FAIL", label))
    if not ok:
        failures.append(label)


def main():
    from pyboy import PyBoy

    print("sram.py self-test")

    # [1] Without the latch, the window is all $FF -- the documented blocker.
    pb = PyBoy(ROM, window="null")
    with open(STATE_INIT, "rb") as f:
        pb.load_state(f)
    pb.tick(2, False)
    closed = bytes(pb.memory[sram.SRAM_LO:sram.SRAM_HI])
    check(all(b == 0xFF for b in closed),
          "latch CLOSED: the $A000-$BFFF window reads all $FF (the blocker)")

    # [2] Opening RAMG makes the SAME window return real data.
    opened = sram.read(pb, 0)
    non_ff = sum(1 for b in opened if b != 0xFF)
    check(non_ff > 1000,
          "latch OPEN: the same window returns real data (%d non-$FF bytes)"
          % non_ff)
    pb.stop(save=False)

    # [3] The banked accessor still raises -- recorded so nobody "fixes"
    #     sram.py by switching to it.
    pb = PyBoy(ROM, window="null")
    with open(STATE_INIT, "rb") as f:
        pb.load_state(f)
    pb.tick(2, False)
    try:
        bytes(pb.memory[0, sram.SRAM_LO:sram.SRAM_HI])
        raised = False
    except Exception:
        raised = True
    check(raised, "pyboy.memory[bank, ...] still raises -- use read(), not it")
    pb.stop(save=False)

    # [4] Checksum arithmetic, pinned by an identity independent of the ROM.
    blank = sram.from_state(ROM, STATE_BLANK)
    lo, hi, _ = sram.RANGES["primary game data"]
    check(sram.checksum(blank, lo, hi) == ALL_FF_PRIMARY_SUM,
          "checksum of an all-$FF primary range == %#06x (2925 * 0xFF & 0xFFFF)"
          % ALL_FF_PRIMARY_SUM)

    # [5] The backup is the primary + $1200, exactly -- the cheap invariant
    #     game_plans/prism.md §0z calls out.
    p_lo, p_hi, p_at = sram.RANGES["primary game data"]
    b_lo, b_hi, b_at = sram.RANGES["backup game data"]
    check(b_lo - p_lo == 0x1200 and b_hi - p_hi == 0x1200
          and b_at - p_at == 0x1200,
          "backup ranges are primary + $1200 exactly")

    # [6] No committed savestate contains a COMPLETED in-game save. This is a
    #     real measurement, not an absence: it is why the dump-and-diff that
    #     front 1 still needs cannot be run from the existing fixtures.
    init = sram.from_state(ROM, STATE_INIT)
    check(not sram.has_real_save(blank) and not sram.has_real_save(init),
          "no completed in-game save in the fixtures (stored checksum $0000/$FFFF)")

    print("\n%d/%d" % (ran - len(failures), ran))
    # ⚠️ `ran` is computed from what actually ran, so the printed tally agrees
    # with itself and a deleted check would still report "5/5 ALL PASS".
    # Measured across the four GBA repos 2026-09-17: 28 negative tests all had
    # this hole. The literal is what makes a shrunken check list a failure.
    rc = 1 if failures else 0
    if ran != EXPECT_CHECKS:
        print("sram_selftest: ran %d checks, expected %d. Either a check "
              "stopped running or one was added without bumping the literal."
              % (ran, EXPECT_CHECKS))
        rc = 1
    print("ALL PASS" if rc == 0 else "FAILED")
    return rc


if __name__ == "__main__":
    sys.exit(main())
