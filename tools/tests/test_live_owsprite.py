#!/usr/bin/env python3
"""Player overworld sprite follows the character (2026-11-04), live: a real map load (warp) runs the shipped
SpawnPlayer / GetPlayerSprite / GetSprite / sprite loader.

  * CM on, a character with a sheet (one 'own' sheet, one stand-in, one standing-only): all 24 tiles of the
    character's sheet (art/overworld/<id>.2bpp) are in VRAM bank 1 ($8000: 12 tiles, $8800: 12 tiles), the
    player's OAM entries use the manifest's OBJ palette, the player's sprite id is 1
  * CM on with a Prism outfit set (wOutfit $DFD7 = 1): still sprite 1 and the character's tiles
  * CM on, on the bike (wPlayerState 1): Prism's own bike sprite (outfit 1 -> $61), not the character
  * CM off (outfit 1): Prism's outfit sprite $60, OBJ palette 0, none of the sheets in VRAM
  * walking up, the player's OAM shows a walking frame (tiles $80-$8B, the sheet's second half)
--tamper compares each character against the NEXT character's sheet and must FAIL.
"""
import json
import sys
sys.path.insert(0, "tools")
sys.path.insert(0, "tools/tests")
from cmlib import CM
from test_live_obstacles import warp

PALS = {"blue": 1, "green": 2, "brown": 3, "red": 4, "silver": 5, "yellow": 6, "purple": 7}
MAP = (30, 6, 10, 10)


def vram_sheet(m):
    return bytes(m[1, 0x8000 + i] for i in range(0xC0)) + bytes(m[1, 0x8800 + i] for i in range(0xC0))


def setup(cm, cid, outfit=0, state=0):
    cm.load("tools/emu_states/ck9.state")
    cm.wb(0xDFD7, outfit)
    cm.wb(0xD9A0, state)
    cm.set_char(cid)
    warp(cm, *MAP)
    m = cm.pb.memory
    return m, [m[0xFE00 + i] for i in range(16)]


def main():
    tamper = "--tamper" in sys.argv
    man = {int(k): v for k, v in json.load(open("art/overworld/manifest.json")).items()}
    ids = sorted(man)
    own = next(c for c in ids if man[c]["kind"] == "own")
    stand = next(c for c in ids if man[c]["kind"] == "stand-in")
    standing = next(c for c in ids if "standing" in man[c]["kind"])
    cm = CM()
    fails = []

    def check(ok, what):
        print(("ok   " if ok else "FAIL ") + what)
        if not ok:
            fails.append(what)

    sheets = {c: open(f"art/overworld/{c}.2bpp", "rb").read() for c in ids}
    for cid in (own, stand, standing, ids[-1]):
        want = cid if not tamper else ids[(ids.index(cid) + 1) % len(ids)]
        if sheets[want] == sheets[cid] and tamper:
            want = next(c for c in ids if sheets[c] != sheets[cid])
        m, oam = setup(cm, cid)
        pal = PALS[man[want]["palette"]]
        check(vram_sheet(m) == sheets[want], f"{man[cid]['name']} ({man[cid]['kind']}): 24 tiles in VRAM = sheet")
        check(all(oam[i + 3] & 7 == pal and oam[i + 3] & 8 for i in (0, 4)) or (tamper and False),
              f"{man[cid]['name']}: player OAM uses OBJ palette {pal} ({man[want]['palette']}), VRAM bank 1")
        check(cm.rb(0xD4D6) == 1, f"{man[cid]['name']}: player sprite id 1")
        walk = set()
        cm.pb.button_press("up")
        for _ in range(24):
            cm.tick(1)
            walk |= {m[0xFE00 + i * 4 + 2] for i in range(4)}
        cm.pb.button_release("up"); cm.tick(20)
        check(vram_sheet(m) == sheets[want] and any(0x80 <= t < 0x8C for t in walk),
              f"{man[cid]['name']}: walking up draws a walking frame from the sheet's $8800 half")

    m, oam = setup(cm, own, outfit=1)
    check(cm.rb(0xD4D6) == 1 and vram_sheet(m) == sheets[own], "outfit 1 + CM on: sprite 1, the character's sheet")
    m, oam = setup(cm, own, outfit=1, state=1)
    check(cm.rb(0xD4D6) == 0x61, "bike + CM on: Prism's outfit bike sprite $61 (got $%02X)" % cm.rb(0xD4D6))
    m, oam = setup(cm, None, outfit=1)
    v = vram_sheet(m)
    check(cm.rb(0xD4D6) == 0x60 and oam[3] & 7 == 0 and all(v != s for s in sheets.values()),
          "CM off: Prism's outfit sprite $60, OBJ palette 0, no character sheet in VRAM")
    cm.stop()
    print("FAILED: %d" % len(fails) if fails else "ALL PASS")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
