#!/usr/bin/env python3
"""Roster screen (START menu 'Roster' row, Character Mode only).

  * RosterScreen draws '<Name>'s roster', one row per family ROOT in alphabetical order
    (checked against the generated lists), scrolls with Up/Down/Left/Right and leaves on A/B/Start
  * the START menu: with Character Mode on, menu item 7 (EXIT) resolves to the Roster entry
    (function CMRosterFunc, label 'Roster'); with it off, to the shipped EXIT entry. Every other
    item resolves exactly as shipped (04:60E0 vs. the donor arithmetic)
  * the Roster function runs the screen between FadeToMenu/CloseSubmenu and returns 0 (reopen menu)
(--tamper expects a wrong name and must FAIL.)
"""
import sys, re
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, species_names

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
            if f == 60:
                snap["rows"] = rows(cm)
        cm.call("RosterScreen", frames=200, script=[(120, "b", 6)], probe=probe)
        rws = snap["rows"]
        title = enc(info[cid] + ("x" if tamper else "") + "'s roster")
        check(title in rws[1], f"{info[cid]}: title '<Name>'s roster' on row 1")
        shown = []
        for r in range(3, 14):
            for k, nm in enumerate(exp):
                pass
        want = [names[x] for x in exp[:11]]
        got_ok = all(enc(nm[:10]) in rws[3 + i] for i, nm in enumerate(want))
        check(got_ok, f"{info[cid]}: first {len(want)} roots alphabetical ({want[:3]}...)")
        check(enc("Evolutions count") in rws[15], f"{info[cid]}: hint line present")

    # scrolling: pick the character with the longest list, press Down 3 times then Page down
    longest = max(range(76), key=lambda c: len(expected_roots(c)))
    exp = expected_roots(longest)
    cm.restore(base)
    cm.set_char(longest)
    snap = {}

    def probe2(f):
        if f == 140:
            snap["rows"] = rows(cm)
    cm.call("RosterScreen", frames=400, script=[(40, "down", 4), (60, "down", 4), (80, "down", 4),
                                                  (150, "b", 6)], probe=probe2)
    want = [names[x] for x in exp[3:14]]
    check(all(enc(nm[:10]) in snap["rows"][3 + i] for i, nm in enumerate(want)),
          f"{info[longest]} ({len(exp)} roots): three Downs scroll the list by three")
    cm.restore(base)
    cm.set_char(longest)
    snap = {}

    def probe3(f):
        if f == 130:
            snap["rows"] = rows(cm)
    cm.call("RosterScreen", frames=400, script=[(40, "right", 4), (80, "right", 4), (150, "b", 6)], probe=probe3)
    top = min(22, max(0, len(exp) - 11))
    want = [names[x] for x in exp[top:top + 11]]
    check(all(enc(nm[:10]) in snap["rows"][3 + i] for i, nm in enumerate(want)),
          f"{info[longest]}: paging right twice stops at the end (top={top})")

    # START menu entry resolution: call the table-lookup routine (04:60E0) for every item
    def entry(char, item):
        cm.restore(base)
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
    cm.tap("a", 4, 10)
    cm.tick(120)
    live = cm.pb.screen.image.convert("RGB")
    live.save("/tmp/prism_roster_live.png")
    from collections import Counter
    bg = lambda x0, x1: Counter(live.getpixel((x, y)) for x in range(x0, x1) for y in range(24, 112)).most_common(1)[0][0]
    left, right = bg(16, 64), bg(120, 152)
    check(enc("Brock's roster") in rows(cm)[1] and left == right and sum(left) > 600,
          f"live START > Roster: title on row 1, one light text-box background across the screen (left {left}, right {right})")
    cm.tap("b", 4, 10)
    cm.tick(150)
    check(any(enc("Roster") in r for r in rows(cm)), "live: B goes back to the START menu (its Roster row redrawn)")
    rom = open("build/prism_cm.gbc", "rb").read()
    base_rom = open("rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc", "rb").read()
    ok = True
    for item in range(9):
        want = 0x606F + 4 * item
        for ch in (None, 9):
            got = entry(ch, item)
            exp_hl = want
            if ch is not None and item == 7:
                exp_hl = cm.sym["CMRosterEntry"][1]
            if got != exp_hl:
                ok = False
                print("   mismatch", item, ch, hex(got), hex(exp_hl))
    check(ok, "item table: every item as shipped, except item 7 (EXIT) -> Roster entry when Character Mode is on")
    lab = cm.sym["CMRosterLabel"][1]
    check(bytes(rom[lab:lab + 7]) == enc("Roster") + b"\x50", "Roster label is 'Roster@' in the home bank")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
