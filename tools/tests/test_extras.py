#!/usr/bin/env python3
"""START > Extras (QoL round 2 item 3, 2026-11-12): LIVE, the real START menu (script 25:5537) in PyBoy.

The last START row (the shipped EXIT) is "Extras" whenever Character Mode is on or the party is not empty; its chooser is
Roster (Character Mode only) / Heal party / PC / Cancel. Heal = the game's own HealParty (no limit), PC = the game's own
PokemonCenterPC (71:5E6A). Every case reads the real screen and the party's HP:
  heal (CM on) / heal (CM off) / PC (text "Bill's PC", HP untouched) / roster / cancel / no Pokemon (roster at once; CM
  off: the row stays Exit) / after each action the map answers a move key (not stuck in a menu)
Control ROM (CM_NO_EXTRAS): the row reads "Roster" and no heal happens.
--tamper runs the heal checks against the control ROM, which has no Extras row: must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM
from live_battle import give_mon, open_start_menu
from test_fieldmenu import screen

STATE = "tools/emu_states/ck9.state"
PARTY = 0xDCDF
HP, STATUS = PARTY + 34, PARTY + 32     # current HP (big-endian word), status byte
fails = 0


def check(ok, msg):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    fails += (not ok)


def hp(cm):
    return (cm.rb(HP) << 8) | cm.rb(HP + 1), (cm.rb(HP + 2) << 8) | cm.rb(HP + 3), cm.rb(STATUS)


def setup(cm, char, party=True):
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    if party:
        give_mon(cm, 25, 30)
        cm.wb(HP, 0); cm.wb(HP + 1, 1); cm.wb(STATUS, 8)       # 1 HP, poisoned
    cm.set_char(char)
    open_start_menu(cm)


def last_row(cm):
    return screen(cm)


def pick(cm, item):
    """START: Up to the last row, A (the chooser), `item` Downs, A."""
    cm.tap("up", 4, 20)
    cm.tap("a", 4, 60)
    for _ in range(item):
        cm.tap("down", 4, 20)
    cm.tap("a", 4, 150)


def moves(cm):
    """The map answers a direction key: the screen changes after a few steps (we are not stuck in a menu)."""
    a = bytes(cm.pb.screen.image.convert("L").tobytes())
    for _ in range(4):
        cm.tap("down", 8, 8)
    b = bytes(cm.pb.screen.image.convert("L").tobytes())
    return a != b


def leave(cm):
    for _ in range(8):
        cm.tap("b", 4, 40)


def main():
    tamper = "--tamper" in sys.argv
    cm = CM("build/prism_cm.gbc", "build/prism_cm.sym")
    ctl = CM("build/prism_cm_noextras.gbc", "build/prism_cm_noextras.sym")
    sub = ctl if tamper else cm         # --tamper: the heal checks below run on the control ROM

    # the row and the chooser
    setup(cm, 9)
    s = screen(cm)
    check("Extras" in s and "Roster" not in s.split("Extras")[0][-12:], "CM on + party: the last START row reads Extras")
    cm.tap("up", 4, 20); cm.tap("a", 4, 60)
    s = screen(cm)
    check(all(w in s for w in ("Roster", "Heal party", "PC", "Cancel")), "the chooser lists Roster / Heal party / PC / Cancel")
    cm.pb.screen.image.save("/tmp/prism_extras_chooser.png")
    setup(cm, None)
    cm.tap("up", 4, 20); cm.tap("a", 4, 60)
    s = screen(cm)
    check("Heal party" in s and "PC" in s and "Cancel" in s and "Roster" not in s, "CM off + party: the chooser lists Heal party / PC / Cancel (no Roster)")

    # heal, CM on and off
    setup(sub, 9); pick(sub, 1)
    sub.pb.screen.image.save("/tmp/prism_extras_heal.png")
    s = screen(sub)
    check("fully healed" in s, "heal (CM on): the message 'Your party was fully healed!' is on the screen")
    sub.tap("a", 4, 60); leave(sub)
    h, m, st = hp(sub)
    check(h == m and m > 1 and st == 0, f"heal (CM on): HP {h}/{m}, status {st} (want full HP, cured)")
    check(moves(sub), "heal (CM on): the map answers a move key afterwards")
    setup(sub, None); pick(sub, 0)          # CM off: the chooser has no Roster, so item 0 is Heal
    s = screen(sub)
    sub.tap("a", 4, 60); leave(sub)
    h, m, st = hp(sub)
    check("fully healed" in s and h == m and m > 1 and st == 0, f"heal (CM off): HP {h}/{m}, status {st} (want full HP, cured)")
    if tamper:
        print("RESULT: FAIL" if fails else "RESULT: ALL PASS", f"({fails} failed)")
        sys.exit(1 if fails else 0)

    # PC
    setup(cm, 9); pick(cm, 2)
    cm.tick(200)
    s = screen(cm)
    check("turned on" in s or "Bill" in s, f"PC (CM on): the PC's own text is up ({s.splitlines()[-2:]})")
    cm.tap("a", 4, 120)
    s = screen(cm)
    check("Bill" in s and "Turn" in s, "PC: its menu lists Bill's PC / the player's PC / Turn off")
    cm.pb.screen.image.save("/tmp/prism_extras_pc.png")
    leave(cm)
    h, m, st = hp(cm)
    check(h == 1 and moves(cm), f"PC: backed out to the map (HP still {h}: no heal), and the map answers a move key")
    setup(cm, None); pick(cm, 1)
    cm.tick(200)
    check("turned on" in screen(cm) or "Bill" in screen(cm), "PC (CM off): the PC's own text is up")
    leave(cm)
    check(moves(cm), "PC (CM off): backed out, the map answers a move key")

    # roster, cancel, no Pokemon
    setup(cm, 9); pick(cm, 0)
    check("roster" in screen(cm), "roster: the roster screen opens from the chooser")
    leave(cm)
    check(moves(cm), "roster: backed out, the map answers a move key")
    setup(cm, 9); cm.tap("up", 4, 20); cm.tap("a", 4, 60); cm.tap("b", 4, 60)
    h, m, st = hp(cm)
    check(h == 1 and "Extras" in screen(cm), "cancel (B on the chooser): nothing done, the START menu is still up")
    leave(cm)
    setup(cm, 9, party=False); cm.tap("up", 4, 20); cm.tap("a", 4, 120)
    check("roster" in screen(cm), "CM on, no Pokemon: the row opens the roster at once (no chooser)")
    setup(cm, None, party=False)
    s = screen(cm)
    check("Exit" in s and "Extras" not in s, "CM off, no Pokemon: the last row stays Exit")

    # control: the old Roster-only row, nothing healed
    setup(ctl, 9)
    s = screen(ctl)
    check("Roster" in s and "Extras" not in s, "control (CM_NO_EXTRAS): the last row reads Roster")
    ctl.tap("up", 4, 20); ctl.tap("a", 4, 120)
    check("roster" in screen(ctl) and hp(ctl)[0] == 1, "control: A opens the roster, no heal")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
