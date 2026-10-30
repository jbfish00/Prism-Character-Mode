#!/usr/bin/env python3
"""LIVE Exp. Rate option (2026-10-29; src/exp_rate.asm): a real wild battle, the lead KOs a 1-HP wild mon with Tackle
from the real Fight menu (the bench mon shares, party-wide Exp. Share), with wExpRate ($DC98) set first. Both exact
gains are pinned: measured at 1x, the others follow from x*N/2 (1 = 1.5x, 2 = 2x, 3 = 3x, 4 = 0.5x).

  shipped : each rate gives its pinned gains
  CONTROL : the same ROM with the 5 hook bytes at 0F:6894 put back ($F0 $B6 $EA $87 $D0) gives the 1x gains at 2x
  OPTIONS : the real Options menu (18:44BA): DOWN to Page, RIGHT to page 2, UP to row 5 (Exp. Rate), RIGHT x2, B
            -> wExpRate 2; LEFT once -> 4; no arrow -> 0. The label and value are photographed.
--tamper expects 2x to give the 1x gains and must FAIL.
"""
import os
import sys
import tempfile
sys.path.insert(0, "tools"); sys.path.insert(0, "tools/tests")
from cmlib import CM, ROM, SYM
from live_battle import give_mon, start_wild, wait_battle
from test_live_catch import text, STATE

PARTY = 0xDCDF
W_EXP_RATE = 0xDC98
SITE = 0x0F * 0x4000 + (0x6894 - 0x4000)
ORIG = bytes.fromhex("f0b6ea87d0")
GAIN_1X = (84, 84)   # (lead, bench), measured at 1x (the bench shares the full award: Prism's Exp. Share split)
WANT = {0: GAIN_1X, 2: (168, 168), 4: (42, 42), 3: (252, 252)}


def exp(cm, slot):
    o = PARTY + slot * 0x30 + 8
    return cm.rb(o) << 16 | cm.rb(o + 1) << 8 | cm.rb(o + 2)


def fight(rom, rate):
    cm = CM(rom, SYM)
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    give_mon(cm, 1, 30)
    for i, mv in enumerate((33, 0, 0, 0)):                  # lead knows Tackle
        cm.wb(PARTY + 2 + i, mv); cm.wb(PARTY + 23 + i, 25)
    cm.set_char(None)
    cm.wb(W_EXP_RATE, rate)
    start_wild(cm, 19, 10)
    assert wait_battle(cm)
    for _ in range(60):
        if "Fight" in text(cm):
            break
        cm.tap("a", 4, 40)
    cm.tick(30)
    cm.wb(0xD216, 0); cm.wb(0xD217, 1)                        # enemy at 1 HP
    before = (exp(cm, 0), exp(cm, 1))
    cm.tap("a", 4, 60)                                        # Fight
    cm.tap("a", 4, 60)                                        # move 1
    for _ in range(40):
        cm.tap("a", 4, 40)
    cm.tick(120)
    gain = (exp(cm, 0) - before[0], exp(cm, 1) - before[1])
    cm.stop()
    return gain


CHARS = {0x7F: " ", 0xE8: ".", 0x9C: ":"}
CHARS.update({0x80 + i: chr(65 + i) for i in range(26)}); CHARS.update({0xA0 + i: chr(97 + i) for i in range(26)})
CHARS.update({0xF6 + i: str(i) for i in range(10)})


def tile_row(cm, row):
    return "".join(CHARS.get(cm.rb(0xC4A0 + 20 * row + c), "?") for c in range(20))


def options(keys, shot=None):
    cm = CM()
    cm.load("tools/emu_states/ck9.state")
    cm.wb(W_EXP_RATE, 0)
    sc, f = [], 150
    for k in ["down"] * 6 + ["right", "up"] + keys:          # rows 0..5, Page; page 2; up from Page = row 5
        sc.append((f, k, 4)); f += 40
    end = f + 60
    sc.append((end, "b", 6))

    rows = {}

    def probe(fr):
        if fr == end - 10:
            rows["label"], rows["value"] = tile_row(cm, 10), tile_row(cm, 11)   # page 2, 5th row (tile rows 10/11)
            if shot:
                cm.pb.screen.image.save(shot)
    cm.call((0x18, 0x44BA), frames=end + 200, script=sc, probe=probe)
    v = cm.rb(W_EXP_RATE)
    cm.stop()
    options.rows = rows
    return v


def main():
    tamper = "--tamper" in sys.argv
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    data = bytearray(open(ROM, "rb").read())
    check(data[SITE] == 0xCF, "0F:6894 is rst $08 (ExpRateApply hook)")
    ctl = bytearray(data); ctl[SITE:SITE + 5] = ORIG
    tmp = tempfile.NamedTemporaryFile(suffix=".gbc", delete=False); tmp.write(ctl); tmp.close()
    for rate, name in ((0, "1x"), (2, "2x"), (4, "0.5x"), (3, "3x")):
        g = fight(tmp.name if tamper else ROM, rate)
        check(g == WANT[rate], f"wExpRate {rate} ({name}): exp gained lead,bench {g} (want {WANT[rate]})")
    g = fight(tmp.name, 2)
    check(g == GAIN_1X, f"CONTROL (hook bytes restored), wExpRate 2: gained {g} (want the 1x {GAIN_1X})")
    os.unlink(tmp.name)
    v = options(["right", "right"], "/tmp/prism_exprate_options.png")
    check(v == 2, f"Options > page 2 > Exp. Rate, RIGHT x2 -> wExpRate {v} (want 2)")
    r = options.rows
    check("Exp. Rate" in r.get("label", "") and "2x" in r.get("value", ""),
          f"the row reads {r.get('label', '').strip()!r} / {r.get('value', '').strip()!r} (want 'Exp. Rate' / '2x')")
    v = options(["left"])
    check(v == 4, f"Options > page 2 > Exp. Rate, LEFT -> wExpRate {v} (want 4, 0.5x)")
    v = options([])
    check(v == 0, f"Options CONTROL, no arrow -> wExpRate {v} (want 0)")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
