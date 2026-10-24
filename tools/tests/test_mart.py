"""Live unit test of the QoL Mart evolution items (2026-10-24, src/mart_evo.asm).

Calls the REAL ReadMart (45:6E78) on a real Mart list (the first entry of GetMart's table $7DE0) from savestate ck9, in
the test image and in the CM_NO_MART control image, and reads wCurMart ($D0F0: count, items, $FF) and the price buffer
($D002, 3-byte BCD per item). Characters are chosen from the roster bitmaps so each case discriminates:
  * a character with Weavile but not Gliscor on the roster: stock + Razor Claw, priced 2100
  * a character with both: stock + Razor Fang + Razor Claw (MartEvoPairs order)
  * a character with neither: stock
  * Character Mode off: stock
  * the Weavile character on the CM_NO_MART image: stock (control)
Live: the REAL Mart dialog (OpenMartDialog 45:6A5B, the routine the `pokemart` script command farcalls) for the
Weavile + Gliscor character, Buy, cursor scrolled to the bottom: the list holds both items while the menu is open
(screenshot build/test_mart_buy.png). Also pins the hook bytes (base: ld hl,$D002 / ld de,$D0F1) in the shipping ROM.

Run: tools/emu_venv/bin/python3 tools/tests/test_mart.py [--tamper]
"""
import os
import struct
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from cmlib import CM, roster_has, char_info

TAMPER = "--tamper" in sys.argv     # negative control: the CM_NO_MART image stands in for the shipping one -> FAIL

STATE = "tools/emu_states/ck9.state"
BASE = "rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
WEAVILE, GLISCOR = 235, 209
RAZOR_CLAW, RAZOR_FANG = 0xE4, 0xE5
HOOK = 0x45 * 0x4000 + 0x6E8A - 0x4000


def mart0(rom):
    o = 0x45 * 0x4000 + 0x7DE0 - 0x4000
    a = struct.unpack_from("<H", rom, o)[0]
    p = 0x45 * 0x4000 + a - 0x4000
    return a, list(rom[p + 1:p + 1 + rom[p]])


def run(img, cid, addr):
    cm = CM(img + ".gbc", img + ".sym")
    cm.load(STATE)
    cm.set_char(cid)
    cm.wb(0xD03F, 0x45)                  # wMartPointerBank / wMartPointer, as LoadMartPointer leaves them
    cm.wb(0xD040, addr & 0xFF)
    cm.wb(0xD041, addr >> 8)
    cm.call((0x45, 0x6E78))
    n = cm.rb(0xD0F0)
    items = list(cm.rd(0xD0F1, n))
    term = cm.rb(0xD0F1 + n)
    prices = [cm.rd(0xD002 + 3 * k, 3).hex() for k in range(n)]
    cm.pb.stop(save=False)
    return items, term, prices


def live_buy(img, cid):
    cm = CM(img + ".gbc", img + ".sym")
    cm.load(STATE)
    cm.set_char(cid)
    seen = {}

    def probe(f):
        if f == 330:                     # Buy list open, cursor at the bottom
            seen["list"] = list(cm.rd(0xD0F1, cm.rb(0xD0F0)))
            cm.pb.screen.image.save("build/test_mart_buy.png")
    presses = [(100, "a", 6)] + [(200 + 12 * k, "down", 4) for k in range(7)] + [(400 + 30 * k, "b", 6) for k in range(12)]
    cm.call((0x45, 0x6A5B), frames=900, script=presses, probe=probe, c=0, e=0, b=0x45, d=0)
    cm.pb.stop(save=False)
    return seen.get("list")


def main():
    rom = open("build/prism_cm.gbc", "rb").read()
    base = open(BASE, "rb").read()
    fails = 0
    ok = base[HOOK:HOOK + 6] == bytes.fromhex("2102d011f1d0") and rom[HOOK] == 0xCF and rom[HOOK + 4:HOOK + 6] == b"\0\0"
    print(("PASS" if ok else "FAIL") + " hook 45:6E8A: base ld hl,$D002 / ld de,$D0F1 -> rst $08 farcall + 2 nops")
    fails += not ok

    info = char_info()
    offered = [c for c in sorted(info) if info[c]["selectable"]]
    claw_only = next(c for c in offered if roster_has(c, WEAVILE) and not roster_has(c, GLISCOR))
    both = next(c for c in offered if roster_has(c, WEAVILE) and roster_has(c, GLISCOR))
    neither = next(c for c in offered if not roster_has(c, WEAVILE) and not roster_has(c, GLISCOR))
    addr, stock = mart0(base)
    img = "build/prism_cm_test_nomart" if TAMPER else "build/prism_cm_test"
    cases = [
        ("%s (Weavile, no Gliscor)" % info[claw_only]["name"], img, claw_only, stock + [RAZOR_CLAW]),
        ("%s (Weavile + Gliscor)" % info[both]["name"], img, both, stock + [RAZOR_FANG, RAZOR_CLAW]),
        ("%s (neither)" % info[neither]["name"], img, neither, stock),
        ("Character Mode off", img, None, stock),
        ("control CM_NO_MART, %s" % info[claw_only]["name"], "build/prism_cm_test_nomart", claw_only, stock),
    ]
    for name, im, cid, want in cases:
        items, term, prices = run(im, cid, addr)
        added_prices = prices[len(stock):]
        ok = items == want and term == 0xFF and all(p == "002100" for p in added_prices)
        print(("PASS" if ok else "FAIL") + " %s: mart $%04X list %s (want %s), added priced %s"
              % (name, addr, [hex(x) for x in items], [hex(x) for x in want], added_prices))
        fails += not ok
    got = live_buy(img, both)
    ok = got == stock + [RAZOR_FANG, RAZOR_CLAW]
    print(("PASS" if ok else "FAIL") + " live: real Mart dialog, Buy list open for %s: %s" % (info[both]["name"], got and [hex(x) for x in got]))
    fails += not ok
    print("RESULT: %s (%d failed, want 0 of 7)" % ("PASS" if not fails else "FAIL", fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
