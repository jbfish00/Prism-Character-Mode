#!/usr/bin/env python3
"""Byte-delta check: the built ROM may differ from the untouched base ROM ONLY at the documented
hook sites, the home-bank filler we claim, bank 56's text filler, and banks 118/119 (which the base
ROM leaves entirely $FF). Also pins the ORIGINAL bytes at every hook (a wrong ROM revision or a
mis-sized hook shows up here before it shows up as a crash).
Negative control (--tamper): change one extra byte of a copy and the check must FAIL.
"""
import sys

BASE = "rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
BUILT = "build/prism_cm.gbc"

# (bank, addr, original hex, what it is). Lengths are the number of bytes the hook rewrites.
HOOKS = [
    (1, 0x5B86, "218d5dc3572f", "intro: ld hl,$5D8D / jp $2F57  -> jp CharSelectHook + 3 nops"),
    (0x3C, 0x48D7, "ea5fcfcd0040", "GivePoke: ld [$CF5F],a / call TryAddMonToParty -> GiveGate + 2 nops"),
    (0x3F, 0x4092, "3e00cd9f43", "NPCTrade: ld a,0 / call PrintTradeText -> TradeGate (4 bytes) + 1 dead byte"),
    (0x38, 0x6DA7, "cd5763d781", "PC withdraw: call $6357 / rst $10 $81 -> WithdrawGate (4 bytes) + 1 dead byte"),
    (3, 0x788C, "21b3ff2a", "PokeBallEffect: ld hl,$FFB3 / ld a,[hl+] -> CatchBoost"),
    (3, 0x78CA, "e71e fa4ec6".replace(" ", ""), "PokeBallEffect: rst $20 $1E / ld a,[$C64E] -> CatchGate + nop"),
    (0x0F, 0x6C3A, "fad7dc47", "IsAnyMonHoldingExpShare entry -> ExpShareHolders"),
    (0x2C, 0x5924, "1e00afea09d1", "CheckPartyMove entry -> CheckPartyMoveCM (4 bytes; 09 d1 dead)"),
    (9, 0x4707, "3e0fcd7347", "GetMonSubmenuItems: ld a,$0F / call AddMonMenuItem -> MonSubmenuCM (Fly/Flash rows)"),
    (0x25, 0x658B, "cf3c3246", "script giveegg: rst $08 / db $3C / dw GiveEgg -> GiveEggGate (makes the same call)"),
    (0x0A, 0x4AA5, "faa9cf3d", "LinkTrade confirm: ld a,[wMenuCursorY] / dec a -> LinkTradeGate (veto off-roster offers)"),
    (4, 0x60E0, "2197cf2a", "START menu item lookup -> GetMenuItemCM"),
    (0x71, 0x423D, "ea2ed2c9", "wild grass/water species write -> stub"),
    (0x14, 0x4F73, "2aea2ed2", "wild tree/rock species write -> stub"),
    (0x2C, 0x59A3, "ea2ed27b", "wild fishing species write -> stub"),
]
# the bytes each hook actually rewrites (4 for rst $08, 6 or 5 where noted)
HOOK_LEN = {(1, 0x5B86): 6, (0x3C, 0x48D7): 6, (0x3F, 0x4092): 4, (0x38, 0x6DA7): 4,
            (3, 0x788C): 4, (3, 0x78CA): 5, (0x0F, 0x6C3A): 4, (0x2C, 0x5924): 4, (9, 0x4707): 5, (0x25, 0x658B): 4, (0x0A, 0x4AA5): 4,
            (4, 0x60E0): 4, (0x71, 0x423D): 4, (0x14, 0x4F73): 4, (0x2C, 0x59A3): 4}


def off(bank, addr):
    return addr if bank == 0 else bank * 0x4000 + addr - 0x4000


def main():
    tamper = "--tamper" in sys.argv
    base = open(BASE, "rb").read()
    built = bytearray(open(BUILT, "rb").read())
    if tamper:
        built[off(0x20, 0x5000)] ^= 0x55          # an unrelated byte in a vanilla bank
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    check(len(base) == len(built), f"ROM size unchanged ({len(built)} bytes)")
    allowed = []
    for bank, addr, orig, what in HOOKS:
        o = off(bank, addr)
        want = bytes.fromhex(orig)
        check(base[o:o + len(want)] == want, f"base bytes at {bank:02X}:{addr:04X} are {orig} ({what})")
        n = HOOK_LEN[(bank, addr)]
        first = 0xC3 if (bank, addr) == (1, 0x5B86) else 0xCF
        check(built[o] == first, f"{bank:02X}:{addr:04X} now starts with "
              f"{'jp (C3)' if first == 0xC3 else 'rst $08 (CF)'}")
        allowed.append((o, n))
    # filler the overlay owns: banks 118/119 whole, home bank free run, bank 56 text filler
    allowed.append((118 * 0x4000, 0x4000))
    allowed.append((119 * 0x4000, 0x4000))
    allowed.append((120 * 0x4000, 0x4000))      # the roster bitmaps
    allowed.append((0x3CC7, 0x3FFF - 0x3CC7 + 1))
    allowed.append((off(0x38, 0x7FC3), 20))
    # the START-menu / jp hook for home filler already covered; collect real diffs
    diffs = [i for i in range(len(base)) if base[i] != built[i]]
    out = []
    for i in diffs:
        if not any(a <= i < a + n for a, n in allowed):
            out.append(i)
    check(not out, f"every changed byte is inside a documented region ({len(diffs)} changed; stray: "
          f"{[hex(i) for i in out[:6]]})")
    # banks 118/119 must have been $FF in the base ROM (we may only write into emptiness)
    for b in (118, 119, 120):
        seg = base[b * 0x4000:(b + 1) * 0x4000]
        check(set(seg) == {0xFF}, f"base bank {b} ($76/$77) is entirely $FF")
    home = base[0x3CC7:0x4000]
    check(set(home) == {0xFF}, "base home-bank run $3CC7-$3FFF is entirely $FF")
    t = base[off(0x38, 0x7FC3):off(0x38, 0x7FC3) + 20]
    check(set(t) == {0xFF}, "base bank 56 $7FC3.. (20 bytes) is $FF")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
