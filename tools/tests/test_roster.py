#!/usr/bin/env python3
"""Roster screen (START menu 'Roster' row, Character Mode only).

  * RosterScreen draws '<Name>'s roster', one two-line row per family ROOT in alphabetical order (6 per page, the
    name at col 4; checked against the generated lists), scrolls with Up/Down/Left/Right and leaves on A/B/Start
  * icons (2026-11-04): each visible row shows the root's own party icon: VRAM bank 0 $8000 + k*$80 holds frame 0 of
    the ROM's icon (IconPointers 1C:77CE, LZ), shadow OAM entries 4k..4k+3 draw it at cols 1-2 of the row in OBJ
    palette k, and OBJ palette k is white / the species' two PokemonPalettes colours (02:4C84) / black; rows past
    the end are hidden; leaving the screen hides every icon entry
  * the START menu: with Character Mode on, menu item 7 (EXIT) resolves to the Roster entry
    (function CMExtrasFunc, label 'Extras' since 2026-11-12; Roster is its first item); with it off and no Pokemon, to the shipped EXIT entry. Every other
    item resolves exactly as shipped (04:60E0 vs. the donor arithmetic)
  * the Roster function runs the screen between FadeToMenu/CloseSubmenu and returns 0 (reopen menu)
(--tamper expects a wrong name and the NEXT row's icon, and must FAIL.)
"""
import sys, re
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, species_names
import gblz

ROWS = 6
ROM = open("build/prism_cm.gbc", "rb").read()


def icon_frame0(sp):
    o = 0x1C * 0x4000 + 0x37CE + (sp - 1) * 3
    b, a = ROM[o], ROM[o + 1] | ROM[o + 2] << 8
    return gblz.decompress(ROM, b * 0x4000 + a - 0x4000)[0][:64]


def mon_pal(sp):
    o = 2 * 0x4000 + 0x0C84 + sp * 8
    return [0x7FFF, ROM[o] | ROM[o + 1] << 8, ROM[o + 2] | ROM[o + 3] << 8, 0]


def obj_pal(m, k):
    out = []
    for c in range(4):
        m[0xFF6A] = k * 8 + c * 2
        lo = m[0xFF6B]
        m[0xFF6A] = k * 8 + c * 2 + 1
        out.append(lo | m[0xFF6B] << 8)
    return out


def icons_ok(cm, snap, exp, top, tamper):
    """snap: shadow OAM + VRAM bank 0 + OBJ palettes captured on screen."""
    ok = True
    for k in range(ROWS):
        ent = snap["oam"][k * 16:k * 16 + 16]
        if top + k >= len(exp):
            ok &= all(ent[i] == 0 for i in (0, 4, 8, 12))
            continue
        sp = exp[top + k + (1 if tamper and top + k + 1 < len(exp) else 0)]
        y = (3 + 2 * k) * 8 + 16
        want = bytes([y, 16, 8 * k, k, y, 24, 8 * k + 1, k, y + 8, 16, 8 * k + 2, k, y + 8, 24, 8 * k + 3, k])
        ok &= ent == want
        ok &= snap["vram"][k * 0x80:k * 0x80 + 64] == icon_frame0(sp)
        ok &= snap["pals"][k] == mon_pal(sp)
        if not ok:
            print("   icon mismatch at row", k, "species", sp)
            return False
    return ok


def capture(cm):
    m = cm.pb.memory
    return {"rows": rows(cm), "oam": bytes(m[0xC400 + i] for i in range(ROWS * 16)),
            "vram": bytes(m[0, 0x8000 + i] for i in range(ROWS * 0x80)), "pals": [obj_pal(m, k) for k in range(ROWS)]}

STATE = "tools/emu_states/ck9.state"
TILEMAP = 0xC4A0


def enc(s):
    out = []
    for c in s:
        if c.isupper(): out.append(0x80 + ord(c) - 65)
        elif c.islower(): out.append(0xA0 + ord(c) - 97)
        elif c == " ": out.append(0x7F)
        elif c == "'": out.append(0xE0)
        elif c == ".": out.append(0xE8)
        elif c == "-": out.append(0xE3)
        else: raise ValueError(c)
    return bytes(out)


def rows(cm):
    return [bytes(cm.pb.memory[TILEMAP + r * 20: TILEMAP + r * 20 + 20]) for r in range(18)]


def expected_roots(cid):
    fam = {}
    for l in open("tools/character_mode/wildmon_families.tsv").read().splitlines()[1:]:
        p = l.split("\t")
        fam[int(p[0])] = int(p[2])
    names = species_names()
    roots = {fam[x] for x in range(1, 256) if roster_has(cid, x) and x in fam}
    return sorted(roots, key=lambda r: names.get(r, "~").lower())


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    names = species_names()
    info = {}
    for l in open("tools/character_mode/roster_index.tsv").read().splitlines()[1:]:
        p = l.split("\t")
        info[int(p[0])] = p[1]
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    for cid in (9, 60, 45):         # Brock, Red, Lorelei
        exp = expected_roots(cid)
        cm.restore(base)
        cm.set_char(cid)
        snap = {}

        def probe(f, snap=snap):
            if f == 100:
                snap.update(capture(cm))
        cm.call("RosterScreen", frames=300, script=[(160, "b", 6)], probe=probe)
        rws = snap["rows"]
        title = enc(info[cid] + ("x" if tamper else "") + "'s roster")
        check(title in rws[1], f"{info[cid]}: title '<Name>'s roster' on row 1")
        shown = []
        for r in range(3, 14):
            for k, nm in enumerate(exp):
                pass
        want = [names[x] for x in exp[:ROWS]]
        got_ok = all(rws[3 + 2 * i][4:4 + len(enc(nm[:10]))] == enc(nm[:10]) for i, nm in enumerate(want))
        check(got_ok, f"{info[cid]}: first {len(want)} roots alphabetical at col 4 of lines 3,5,.. ({want[:3]}...)")
        check(icons_ok(cm, snap, exp, 0, tamper), f"{info[cid]}: each row's own party icon (tiles, OAM, palette)")
        check(enc("Evolutions count") in rws[15], f"{info[cid]}: hint line present")

    # scrolling: pick the character with the longest list, press Down 3 times then Page down
    longest = max(range(76), key=lambda c: len(expected_roots(c)))
    exp = expected_roots(longest)
    cm.restore(base)
    cm.set_char(longest)
    snap = {}

    def probe2(f):
        if f == 260:
            snap.update(capture(cm))
    cm.call("RosterScreen", frames=500, script=[(80, "down", 4), (130, "down", 4), (180, "down", 4),
                                                  (320, "b", 6)], probe=probe2)
    want = [names[x] for x in exp[3:3 + ROWS]]
    check(all(enc(nm[:10]) in snap["rows"][3 + 2 * i] for i, nm in enumerate(want)),
          f"{info[longest]} ({len(exp)} roots): three Downs scroll the list by three")
    check(icons_ok(cm, snap, exp, 3, tamper), f"{info[longest]}: the icons follow the scroll")
    cm.restore(base)
    cm.set_char(longest)
    snap = {}

    def probe3(f):
        if f == 260:
            snap.update(capture(cm))
    cm.call("RosterScreen", frames=500, script=[(80, "right", 4), (160, "right", 4), (320, "b", 6)], probe=probe3)
    top = min(2 * ROWS, max(0, len(exp) - ROWS))
    want = [names[x] for x in exp[top:top + ROWS]]
    check(all(enc(nm[:10]) in snap["rows"][3 + 2 * i] for i, nm in enumerate(want)),
          f"{info[longest]}: paging right twice stops at the end (top={top})")
    check(icons_ok(cm, snap, exp, top, tamper), f"{info[longest]}: icons after paging")

    # START menu entry resolution: call the table-lookup routine (04:60E0) for every item
    def entry(char, item, party=0):
        cm.restore(base)
        cm.wb(0xDCD7, party)
        cm.wb(0xCF97, 0x6F)
        cm.wb(0xCF98, 0x60)
        cm.set_char(char)
        r = cm.call((4, 0x60E0), frames=60, d=0, e=item)
        return r["HL"]

    cm.restore(base)
    cm.set_char(9)
    shown = {}

    def probe4(f):
        if f == 150:
            shown["rows"] = rows(cm)
            shown["img"] = cm.pb.screen.image.copy()
    r = cm.call("CMRosterFunc", frames=600, script=[(250, "b", 6)], probe=probe4)
    check(r["A"] == 0 and enc("Brock's roster") in shown["rows"][1],
          f"CMRosterFunc (the START-menu item body): fades to the screen, shows it, returns a={r['A']} (reopen the menu)")
    # 2026-10-28: the tilemap alone passed while the GBC showed a blank white screen (palettes never restored after
    # FadeToMenu). Photograph it: the frame must show dark text pixels, not one flat colour.
    img = shown["img"].convert("RGB")
    img.save("/tmp/prism_roster_screen.png")
    px = list(img.getdata())
    dark = sum(1 for (r_, g_, b_) in px if r_ + g_ + b_ < 300)
    check(len(set(px)) >= 2 and dark > len(px) // 50,
          f"roster screen photographed: {len(set(px))} colours, {dark} dark pixels of {len(px)} (text visible, not blank)")
    # LIVE (2026-10-28): the real START menu (script 25:5537), Up to the last row, A, photograph, B. The right columns
    # used to keep the START menu cells' attributes (overworld tiles showed through) and the palettes stayed white.
    from live_battle import give_mon, open_start_menu
    cm.load(STATE)
    give_mon(cm, 25, 30)
    cm.set_char(9)
    open_start_menu(cm)
    cm.tap("up", 4, 10)
    cm.tap("a", 4, 30)             # the last row is Extras (a party exists): its first item is Roster
    cm.tap("a", 4, 10)
    cm.tick(120)
    live = cm.pb.screen.image.convert("RGB")
    live.save("/tmp/prism_roster_live.png")
    from collections import Counter
    bg = lambda x0, x1: Counter(live.getpixel((x, y)) for x in range(x0, x1) for y in range(24, 112)).most_common(1)[0][0]
    left, right = bg(16, 64), bg(120, 152)
    check(enc("Brock's roster") in rows(cm)[1] and left == right and sum(left) > 600,
          f"live START > Roster: title on row 1, one light text-box background across the screen (left {left}, right {right})")
    shadow_on = bytes(cm.pb.memory[0xC400 + i] for i in range(ROWS * 16))
    cm.tap("b", 4, 10)
    cm.tick(150)
    shadow_off = bytes(cm.pb.memory[0xC400 + i] for i in range(ROWS * 16))
    icon_entries = {shadow_on[i:i + 4] for i in range(0, ROWS * 16, 4) if shadow_on[i]}
    check(shadow_on[:4] == bytes([40, 16, 0, 0]) and
          not any(shadow_off[i:i + 4] in icon_entries for i in range(0, 160, 4)) and shadow_off[3] & 8,
          "live: icons on the screen; after B no icon entry is left and the map's sprites (VRAM bank 1) are back")
    check(any(enc("Extras") in r for r in rows(cm)), "live: B goes back to the START menu (its Extras row redrawn)")
    rom = open("build/prism_cm.gbc", "rb").read()
    base_rom = open("rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc", "rb").read()
    ok = True
    for item in range(9):
        want = 0x606F + 4 * item
        for ch in (None, 9):
            for party in (0, 1):
                got = entry(ch, item, party)
                exp_hl = want
                if item == 7 and (ch is not None or party):
                    exp_hl = cm.sym["CMExtrasEntry"][1]     # Extras: Character Mode on, or a Pokemon in the party
                if got != exp_hl:
                    ok = False
                    print("   mismatch", item, ch, party, hex(got), hex(exp_hl))
    check(ok, "item table: every item as shipped, except item 7 (EXIT) -> Extras entry when Character Mode is on or the party is not empty")
    lab = cm.sym["CMExtrasLabel"][1]
    check(bytes(rom[lab:lab + 7]) == enc("Extras") + b"\x50", "Extras label is 'Extras@' in the home bank")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
