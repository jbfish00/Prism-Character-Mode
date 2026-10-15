#!/usr/bin/env python3
"""LIVE overworld obstacles: Cut tree, Waterfall, Whirlpool on real maps (map teleport, see
docs/SELECTION_MECHANISM.md section 7). The A button goes through the overworld's own
TryTileCollisionEvent (25:5686), so the prompt, the yes/no and the tree falling are the shipped engine.

Map 30:6 has a real Cut tree at step (12,14) and a real waterfall (collision $33) at (4..7,2) with
water below it. Collision is read the way GetCoordTileCollision (00:1DBF) reads it: block from
$C800 (stride width+6, 3-block border), quadrant byte from WRAM bank 5 at $D300 + 4*block.

  Cut, CM on , no learner, badge  : "Want to use Cut?" -> "used Cut" -> the tree's collision is gone
  Cut, CM off, no learner, badge  : no prompt, tree stays (the engine as shipped)
  Cut, CM off, learner,    badge  : the tree falls (control: the harness reaches the real path)
  Cut, CM on , no learner, no badge: no prompt, tree stays (the badge check is kept)
  Waterfall, surfing, facing $33, A: no Waterfall branch exists. The dispatcher goes straight to
      TrySurfOW (2C:540E), which returns while surfing, and the player does not move, for CM on
      without a learner AND CM off with a mon that knows Waterfall (move $7F, its battle-menu name)
      alike. Prism 0.95 has no way to climb a waterfall; there is nothing for CM to unlock.
  Whirlpool: the dispatcher compares only $12 (Cut tree) and $15 (Headbutt tree), and
      MonMenuOptions (09:45EE) has no Whirlpool (5) or Waterfall (7) row. Both are pinned on ROM bytes.
--tamper expects the CM-off/no-learner Cut to fell the tree and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM
from live_battle import give_mon
from test_fieldmenu import screen

STATE = "tools/emu_states/ck9.state"
MAP = (30, 6)
TREE = (12, 14)
CUT, WATERFALL = 0x0F, 0x7F
CHAR = 9


def warp(cm, g, n, x, y):
    """What the `warp` script command leaves behind: map, coords, no spawn point, MAPSETUP_WARP, ENTER."""
    cm.wb(0xDCB5, g); cm.wb(0xDCB6, n); cm.wb(0xDCB8, x); cm.wb(0xDCB7, y)
    cm.wb(0xD001, 0xFF); cm.wb(0xFF9F, 0xF1); cm.wb(0xD432, 1)
    cm.tick(200)


def coll(cm, x, y):
    m = cm.pb.memory
    w = cm.rb(0xD19F)
    b = m[0xC800 + (w + 6) * (y // 2 + 3) + x // 2 + 3]
    return m[5, 0xD300 + 4 * b + (x & 1) + 2 * (y & 1)]


def setup(cm, char, moves, badges, x, y):
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    for i in range(4):
        cm.wb(0xDCDF + 2 + i, moves[i] if i < len(moves) else 0)
        cm.wb(0xDCDF + 23 + i, 15)
    cm.set_char(char)
    cm.wb(0xDED9, badges)
    warp(cm, *MAP, x, y)


def cut(cm, char, moves, badges=0xFF):
    setup(cm, char, moves, badges, TREE[0] + 2, TREE[1])
    cm.pb.button_press("left"); cm.tick(20); cm.pb.button_release("left"); cm.tick(40)   # one step, faces the tree
    assert cm.rb(0xC2FC) == 0x12 and coll(cm, *TREE) == 0x12, "not facing the Cut tree"
    texts = []
    for _ in range(8):
        cm.tap("a", 4, 60)
        texts.append(screen(cm))
    cm.tick(200)
    return " / ".join(texts), coll(cm, *TREE)


def waterfall(cm, char, moves):
    setup(cm, char, moves, 0xFF, 4, 3)
    cm.pb.button_press("right"); cm.tick(20); cm.pb.button_release("right"); cm.tick(30)
    cm.tap("up", 2, 30)
    y0, tile = cm.rb(0xD4E7), cm.rb(0xC2FB)
    hits = []
    for b, a in ((0x25, 0x5686), (0x2C, 0x540E)):
        cm.pb.hook_register(b, a, lambda c: hits.append(c), f"{b:02X}:{a:04X}")
    for _ in range(4):
        cm.tap("a", 4, 60)
    for b, a in ((0x25, 0x5686), (0x2C, 0x540E)):
        cm.pb.hook_deregister(b, a)
    cm.pb.button_press("up"); cm.tick(60); cm.pb.button_release("up"); cm.tick(60)
    return dict(surfing=cm.rb(0xD9A0) == 4, facing=tile, moved=cm.rb(0xD4E7) != y0, hits=sorted(set(hits)),
                text="Waterfall" in screen(cm) or "Yes" in screen(cm))


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    t, c = cut(cm, CHAR, [])
    check("Want to use Cut?" in t and "used" in t and c != 0x12, f"Cut, CM on, no learner: prompt, used Cut, tree gone (collision {c:#04x})")
    t, c = cut(cm, None, [])
    check(("Want to use Cut?" not in t and c == 0x12) != tamper, f"Cut, CM off, no learner: no prompt, tree stays (collision {c:#04x})")
    t, c = cut(cm, None, [CUT])
    check("Want to use Cut?" in t and c != 0x12, f"Cut, CM off, knows Cut: the tree falls (control) (collision {c:#04x})")
    t, c = cut(cm, CHAR, [], badges=0)
    check("Want to use Cut?" not in t and c == 0x12, f"Cut, CM on, no badge: no prompt, tree stays (collision {c:#04x})")

    on = waterfall(cm, CHAR, [])
    off = waterfall(cm, None, [WATERFALL])
    for tag, r in (("CM on, no learner", on), ("CM off, knows Waterfall", off)):
        check(r["surfing"] and r["facing"] == 0x33, f"Waterfall {tag}: surfing, facing a real waterfall tile ($33)")
        check(r["hits"] == ["25:5686", "2C:540E"] and not r["moved"] and not r["text"],
              f"Waterfall {tag}: A goes dispatcher -> TrySurfOW only, no prompt, no climb ({r['hits']}, moved={r['moved']})")

    rom = open("build/prism_cm.gbc", "rb").read()
    disp = rom[0x25 * 0x4000 + 0x1686: 0x25 * 0x4000 + 0x16B6]
    check(disp.count(b"\xfe") == 2 and b"\xfe\x12" in disp and b"\xfe\x15" in disp,
          "TryTileCollisionEvent (25:5686) compares only $12 (Cut tree) and $15 (Headbutt): no Whirlpool/Waterfall branch")
    mmo = rom[0x09 * 0x4000 + 0x05EE: 0x09 * 0x4000 + 0x05EE + 3 * 22]
    ids = [mmo[i + 1] for i in range(0, len(mmo), 3) if mmo[i] == 0]
    check(5 not in ids and 7 not in ids and 1 in ids and 6 in ids,
          f"MonMenuOptions (09:45EE) has no Whirlpool (5) / Waterfall (7) row (field ids {ids})")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
