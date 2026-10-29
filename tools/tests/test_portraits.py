#!/usr/bin/env python3
"""Picker portraits (2026-10-28), live: the real intro reaches CharSelect, the real joypad moves the cursor.

  * for characters with art (first, middle and last selectable ones that have a portrait), the 56x56 area at
    cols 12-18 / rows 8-14 of the photographed screen shows exactly that character's pic: every pixel's colour
    class matches the committed art/portraits/<id>.2bpp (4 classes; compared as a partition, so the check does
    not depend on the emulator's RGB555 -> RGB conversion), and the area uses 2..4 colours
  * a character without art leaves the area one flat colour, and Normal game (entry 0) too
  * after A the intro comes back: rows 0-10 (its picture) identical in tilemap AND attribute map
--tamper compares each portrait against the NEXT character's art and must FAIL.
"""
import io
import json
import sys
from pyboy import PyBoy

ROM = "build/prism_cm.gbc"
TILEMAP, ATTRMAP = 0xC4A0, 0xCDD9
X0, Y0 = 12 * 8, 8 * 8


def sym(name):
    for l in open("build/prism_cm.sym"):
        p = l.split(";")[0].split()
        if len(p) == 2 and p[1] == name:
            b, a = p[0].split(":")
            return int(b, 16), int(a, 16)
    raise SystemExit(f"{name} not in build/prism_cm.sym")


def art_idx(cid):
    raw = open(f"art/portraits/{cid}.2bpp", "rb").read()
    idx = [0] * (56 * 56)
    for t in range(49):
        ty, tx = divmod(t, 7)
        for y in range(8):
            lo, hi = raw[t * 16 + y * 2], raw[t * 16 + y * 2 + 1]
            for x in range(8):
                idx[(ty * 8 + y) * 56 + tx * 8 + x] = ((lo >> (7 - x)) & 1) | (((hi >> (7 - x)) & 1) << 1)
    return idx


def same_partition(a, b):
    fwd, back = {}, {}
    for x, y in zip(a, b):
        if fwd.setdefault(x, y) != y or back.setdefault(y, x) != x:
            return False
    return True


def main():
    tamper = "--tamper" in sys.argv
    rows = [l.split("\t") for l in open("tools/character_mode/selectable.tsv").read().splitlines()[1:]]
    sel = [(int(r[0]), r[1]) for r in rows if r[5] == "1"]          # picker entry k + 1 = sel[k]
    man = {int(k): v for k, v in json.load(open("art/portraits/manifest.json")).items()}
    with_art = [k for k, (cid, _) in enumerate(sel) if cid in man]
    without = [k for k, (cid, _) in enumerate(sel) if cid not in man]
    pick = [with_art[0], with_art[len(with_art) // 2], with_art[-1]]

    pb = PyBoy(ROM, window="null", cgb=True)
    pb.set_emulation_speed(0)
    snap = {}
    bank, addr = sym("CharSelect")

    def at_entry(ctx=None):
        buf = io.BytesIO()
        pb.save_state(buf)
        snap["s"] = buf.getvalue()
        snap["tm"] = bytes(pb.memory[TILEMAP:TILEMAP + 360])
        snap["am"] = bytes(pb.memory[ATTRMAP:ATTRMAP + 360])
    pb.hook_register(bank, addr, at_entry, None)
    for f in range(8000):
        if "s" in snap:
            break
        if f % 20 == 5: pb.button_press("a")
        if f % 20 == 9: pb.button_release("a")
        if f % 200 == 150: pb.button_press("start")
        if f % 200 == 154: pb.button_release("start")
        pb.tick()
    assert "s" in snap, "never reached CharSelect through the real intro"
    pb.hook_deregister(bank, addr)

    def tap(b):
        pb.button_press(b)
        for _ in range(4): pb.tick()
        pb.button_release(b)
        for _ in range(12): pb.tick()

    def area_at(entry):
        pb.load_state(io.BytesIO(snap["s"]))
        for _ in range(60): pb.tick()
        for _ in range(entry): tap("down")
        for _ in range(60): pb.tick()        # DMA + WaitBGMap2 (attributes go over in thirds)
        im = pb.screen.image.convert("RGB")
        return [im.getpixel((X0 + x, Y0 + y)) for y in range(56) for x in range(56)]

    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    for k in pick:
        cid, name = sel[k]
        want_cid = sel[with_art[(with_art.index(k) + 1) % len(with_art)]][0] if tamper else cid
        px = area_at(k + 1)
        ok = same_partition(px, art_idx(want_cid)) and 2 <= len(set(px)) <= 4
        check(ok, f"entry {k + 1} {name} (id {cid}): the portrait area is its pic ({len(set(px))} colours, "
                  f"source {man[cid]['source']})")
    for k in (without[0] if without else None,):
        if k is None:
            continue
        px = area_at(k + 1)
        check(len(set(px)) == 1, f"entry {k + 1} {sel[k][1]} (no art): the portrait area is blank")
    px = area_at(0)
    check(len(set(px)) == 1, "entry 0 Normal game: the portrait area is blank")
    # confirm a character with art: the intro comes back exactly (tilemap + attributes)
    pb.load_state(io.BytesIO(snap["s"]))
    for _ in range(60): pb.tick()
    for _ in range(pick[1] + 1): tap("down")
    tap("a")
    for _ in range(90): pb.tick()
    # the intro prints text after the picker (rows 12+): compare the picture rows 0-10, tiles and attributes
    check(bytes(pb.memory[TILEMAP:TILEMAP + 220]) == snap["tm"][:220] and bytes(pb.memory[ATTRMAP:ATTRMAP + 220]) == snap["am"][:220],
          "after A the intro's rows 0-10 are restored exactly (tilemap and attribute map)")
    print(f"portraits in the manifest: {len(man)} of {len(sel)} selectable")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
