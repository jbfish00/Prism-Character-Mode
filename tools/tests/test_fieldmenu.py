#!/usr/bin/env python3
"""LIVE party-menu test: the real START menu (the script the overworld's START check runs), the
real party screen and the real mon submenu, with the screen text read back from the tilemap.

  CM on , mon knows no field move : the submenu lists Flash and Fly
  CM on , mon knows Fly           : Fly appears exactly once (no duplicate row)
  CM off, mon knows no field move : neither row (the engine as shipped)
  CM off, mon knows Fly+Flash     : both rows, once each
Then, CM on with the badges set, Flash is chosen for a mon that does not know it and must light
the cave ("A blinding Flash lights the area!" is what the engine prints).
--tamper expects the CM-off case to show the rows and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM
from live_battle import give_mon, open_start_menu, shot

STATE = "tools/emu_states/ck9.state"
CH = {0x7F: " ", 0xE8: ".", 0xE7: "!", 0xE6: "?", 0xE3: "-", 0xE0: "'", 0xF4: ","}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CH[0x80 + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CH[0xA0 + i] = c
for i, c in enumerate("0123456789"):
    CH[0xF6 + i] = c


def screen(cm):
    rows = []
    for r in range(18):
        raw = bytes(cm.pb.memory[0xC4A0 + r * 20:0xC4A0 + r * 20 + 20])
        rows.append("".join(CH.get(b, "") for b in raw).strip())
    return "\n".join(x for x in rows if x)


def submenu(cm, char, moves, badges=0xFF, shots=None):
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    for i in range(4):
        cm.wb(0xDCDF + 2 + i, moves[i] if i < len(moves) else 0)
        cm.wb(0xDCDF + 23 + i, 15)
    cm.wb(0xDED9, badges)
    cm.set_char(char)
    open_start_menu(cm)
    cm.tap("a", 4, 60)            # Pokemon
    cm.tap("a", 4, 40)            # the mon
    if shots:
        shot(cm, shots)
    return screen(cm)


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    CHAR = 9
    FLY, FLASH = 0x13, 0x94
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    s = submenu(cm, CHAR, [], shots="fm_on.png")
    check("Flash" in s and "Fly" in s and s.count("Fly") == 1, f"CM on, no moves: Flash and Fly rows ({s.splitlines()[-8:]})")
    s = submenu(cm, CHAR, [FLY])
    check(s.count("Fly") == 1 and "Flash" in s, "CM on, mon knows Fly: exactly one Fly row")
    s = submenu(cm, None, [])
    check(("Flash" in s or "Fly" in s) == tamper, "CM off, no moves: neither row")
    s = submenu(cm, None, [FLY, FLASH])
    check(s.count("Fly") == 1 and s.count("Flash") == 1, "CM off, mon knows both: both rows once each")

    # The row's action must behave exactly as it does for a mon that knows the move.
    def act(char, moves, row, shot_name=None):
        submenu(cm, char, moves)
        for _ in range(row):
            cm.tap("down", 4, 20)
        cm.tap("a", 4, 120)
        if shot_name:
            shot(cm, shot_name)
        txt = screen(cm).splitlines()
        # the mon's own HP differs between the two builds of the party; compare the message/screen below the header
        return "\n".join(l for l in txt if not l.startswith("Pikachu")), None

    # CM on: rows are [Fly, Flash]; CM off with both moves known, the list is in move-slot order
    on_flash = act(CHAR, [], 1, "fm_flash.png")
    off_flash = act(None, [FLASH, FLY], 0)
    check(on_flash == off_flash and on_flash[0], f"Flash: CM-on no-learner == CM-off learner ({on_flash[0].replace(chr(10), ' / ')[:60]})")
    on_fly = act(CHAR, [], 0, "fm_fly.png")
    off_fly = act(None, [FLY], 0)
    check(on_fly == off_fly and on_fly[0], f"Fly: CM-on no-learner == CM-off learner ({on_fly[0].replace(chr(10), ' / ')[:60]})")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
