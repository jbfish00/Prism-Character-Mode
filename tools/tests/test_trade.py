#!/usr/bin/env python3
"""Live test of the NPC-trade gate (hook at 63:4092, gate in bank 118).

Runs Prism's REAL NPCTrade (63:4082) from a real in-game state for EVERY trade the game
defines (trade NPC index = the routine's `e` argument), for several characters:
  the NPC's GET species on the character's roster -> the offer is made (intro dialog,
      then the engine's Yes/No box)
  off the roster -> refused before the offer: no Yes/No box, CANCEL dialog, returns
  mode off -> offer always made
Offer vs refusal is read from the screen: the engine's Yes/No box is drawn only for an offer.
(--tamper expects the opposite and must FAIL.)
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, char_info, species_names

STATE = "tools/emu_states/ck9.state"
TILEMAP = 0xC4A0


def trade_table(rom):
    """GetTradeAttr's table at 63:42FF, 32 bytes/entry (index*16 added twice):
    attr 0 = dialog set, attr 1 = give species, attr 2 = get species"""
    b = 63 * 0x4000 + 0x42FF - 0x4000
    out = []
    for i in range(16):
        e = rom[b + 32 * i: b + 32 * i + 32]
        out.append((e[0], e[1], e[2]))
    return out


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    rom = open("build/prism_cm.gbc", "rb").read()
    cm.load(STATE)
    base = cm.snapshot()
    info, names = char_info(), species_names()
    tbl = trade_table(rom)
    print("trade table (dialog, give, get):", [(a, names.get(b, b), names.get(c, c)) for a, b, c in tbl[:8]])
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def run(char, idx):
        cm.restore(base)
        cm.set_char(char)
        cm.wb(0xDCD7, 1); cm.wb(0xDCD8, 95); cm.wb(0xDCD9, 0xFF)
        for a in range(0xD9A3, 0xD9A3 + 4):      # wTradeFlags: no trade done yet
            cm.wb(a, 0)
        offered = []
        # the engine's Yes/No box call site: 63:4097 `call YesNoBox`
        cm.pb.hook_register(0x3F, 0x4097, lambda c=None: offered.append(1), None)
        done = False
        try:
            cm.call((0x3F, 0x4082), frames=6000, e=idx, buttons=("b",))
            done = True
        except TimeoutError:
            pass
        cm.pb.hook_deregister(0x3F, 0x4097)
        return bool(offered), done

    # which trades exist: those with plausible species
    # real trades have a dialog set 0-3 (later 'entries' are unrelated data after the table's end)
    trades = [i for i, (d, g, r) in enumerate(tbl) if d <= 3 and 1 <= g < 252 and 1 <= r < 252]
    print("usable trade indices:", trades)
    for i in trades:
        get = tbl[i][2]
        yes = [c for c in range(76) if roster_has(c, get)][:2]
        no = [c for c in range(76) if not roster_has(c, get)][:2]
        for cid in yes + no:
            offered, done = run(cid, i)
            want = roster_has(cid, get)
            if tamper:
                want = not want
            check(offered == want, f"{info[cid]['name']:9s} trade {i} gets {names.get(get, get):10s} on-roster={roster_has(cid, get)} -> offered={offered}")
    for i in trades[:3]:
        offered, done = run(None, i)
        check(offered, f"mode off: trade {i} always offered")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
