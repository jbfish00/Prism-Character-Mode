#!/usr/bin/env python3
"""Read Pokemon Prism's battery-backed SRAM out of a running PyBoy instance.

⭐⭐ THE BLOCKER THIS REMOVES. game_plans/prism.md §0z recorded front 1 as
blocked on TOOLING: `pyboy.memory[0xA000:0xC000]` returns all $FF, because Gen 2
keeps SRAM LATCHED OFF outside OpenSRAM/CloseSRAM and a disabled MBC reads $FF;
and the banked accessor `pyboy.memory[bank, 0xA000:0xC000]` raises
"Out of bounds for reading cartridge RAM bank" for banks 0-3 even though the
header declares 32 KB ($0147=$10 MBC3+TIMER+RAM+BATTERY, $0149=$03).

The plan proposed hooking Checksum (05:52BE), where SRAM is guaranteed open.
That works but needs a save to FIRE. There is a one-line alternative: the latch
is just the MBC's RAMG register, and PyBoy routes a WRITE into $0000-$1FFF to
the MBC exactly as the cartridge would. So we open it ourselves:

    pyboy.memory[0x0000] = 0x0A     # RAMG: enable cartridge RAM
    pyboy.memory[0x4000] = bank     # RAMB: select the 8 KB bank

after which the ORDINARY unbanked window reads real data. No hook, no save, no
emulator patch. Measured: 8,157 of 8,192 bytes non-$FF where it had been 8,192
of 8,192 $FF.

⚠️ This is an OBSERVER. It leaves RAMG enabled, which the game itself would not,
so do not resume normal play from a PyBoy instance after calling read() and
expect byte-accurate MBC behaviour -- dump, then throw the instance away. Every
entry point here builds its own instance for that reason.
"""
import sys

RAMG_ADDR = 0x0000          # $0000-$1FFF: RAM enable
RAMB_ADDR = 0x4000          # $4000-$5FFF: RAM bank select
RAMG_ON = 0x0A
SRAM_LO, SRAM_HI = 0xA000, 0xC000

# Ranges the save actually checksums, measured 2026-09-04/05 (game_plans/prism.md
# §0z). The backup is the primary + $1200, exactly.
RANGES = {
    "primary game data":  (0xA009, 0xAB75, 0xAD0D),
    "primary extra area": (0xAB76, 0xAD05, 0xAD06),
    "backup game data":   (0xB209, 0xBD75, 0xBF0D),
    "backup extra area":  (0xBD76, 0xBF05, 0xBF06),
}


def read(pyboy, bank=0):
    """Real SRAM bytes for `bank`, opening the MBC latch first."""
    pyboy.memory[RAMG_ADDR] = RAMG_ON
    pyboy.memory[RAMB_ADDR] = bank
    pyboy.tick(1, False)
    return bytes(pyboy.memory[SRAM_LO:SRAM_HI])


def byte(sram, addr):
    return sram[addr - SRAM_LO]


def checksum(sram, lo, hi):
    """Prism's Checksum (05:52BE): a 16-bit byte sum over [lo, hi]."""
    total = 0
    for a in range(lo, hi + 1):
        total = (total + byte(sram, a)) & 0xFFFF
    return total


def verify(sram):
    """[(label, computed, stored, ok)] for all four checksummed ranges."""
    out = []
    for label, (lo, hi, at) in RANGES.items():
        got = checksum(sram, lo, hi)
        stored = byte(sram, at) | (byte(sram, at + 1) << 8)
        out.append((label, got, stored, got == stored))
    return out


def has_real_save(sram):
    """True only if the primary game-data checksum is present AND correct.

    ⚠️ A stored checksum of $0000 or $FFFF means the slot was never written --
    NOT that the save is corrupt. All 20 committed savestates read one of those
    two, i.e. none of them contains a completed in-game save.
    """
    lo, hi, at = RANGES["primary game data"]
    stored = byte(sram, at) | (byte(sram, at + 1) << 8)
    if stored in (0x0000, 0xFFFF):
        return False
    return checksum(sram, lo, hi) == stored


def from_state(rom, state, bank=0):
    """Dump SRAM from a savestate in a throwaway PyBoy instance."""
    from pyboy import PyBoy
    pb = PyBoy(rom, window="null")
    with open(state, "rb") as f:
        pb.load_state(f)
    pb.tick(2, False)
    try:
        return read(pb, bank)
    finally:
        pb.stop(save=False)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        print("usage: sram.py <rom> <state> [out.bin]")
        return 2
    rom, state = argv[1], argv[2]
    s = from_state(rom, state)
    non = sum(1 for b in s if b != 0xFF)
    print("%s: %d/%d bytes non-$FF" % (state, non, len(s)))
    for label, got, stored, ok in verify(s):
        print("  %-20s computed=%#06x stored=%#06x  %s"
              % (label, got, stored, "MATCH" if ok else "differ"))
    print("  completed in-game save present: %s" % has_real_save(s))
    if len(argv) > 3:
        open(argv[3], "wb").write(s)
        print("  wrote %s" % argv[3])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
