#!/usr/bin/env python3
"""Live test of the new-game character picker (tools/build.sh first).

Boots the built ROM cold, mashes through the real intro to the hook (so the
picker is reached ORGANICALLY, through the real New Game flow), snapshots the
state at CharSelect's entry, then drives the real joypad:

  * every entry (all CHARSEL_COUNT of them) is reached with Down presses, A is
    pressed, and wCharMode ($DC96) must equal the selectable list's id + 1
    (0 for 'Normal game'); this includes character #57-class deep entries
  * Up from the top wraps to the last entry; Right pages by 12 and clamps
  * B / Start / Select do nothing (the picker can't be dismissed)
  * the intro screen is restored after confirm (tilemap identical to before)
  * NEGATIVE CONTROL: --tamper builds expectations from a shifted list and
    must FAIL (proves the checks can fail)
"""
import io, re, sys
from pyboy import PyBoy

ROM = "build/prism_cm.gbc"
WCHAR = 0xDC96
TILEMAP = 0xC4A0


def sym(name):
    for l in open("build/prism_cm.sym"):
        p = l.split(";")[0].split()
        if len(p) == 2 and p[1] == name:
            b, a = p[0].split(":")
            return int(b, 16), int(a, 16)
    raise SystemExit(f"{name} not in build/prism_cm.sym")


def selectable():
    ids = []
    for l in open("tools/character_mode/selectable.tsv").read().splitlines()[1:]:
        p = l.split("\t")
        if p[5] == "1":
            ids.append((int(p[0]), p[1]))
    return ids


def main():
    tamper = "--tamper" in sys.argv
    sel = selectable()
    n = len(sel) + 1
    pb = PyBoy(ROM, window="null", cgb=True)
    pb.set_emulation_speed(0)
    snap = {}
    bank, addr = sym("CharSelect")

    def at_entry(ctx=None):
        buf = io.BytesIO()
        pb.save_state(buf)
        snap["state"] = buf.getvalue()
        snap["tilemap"] = bytes(pb.memory[TILEMAP:TILEMAP + 360])
    pb.hook_register(bank, addr, at_entry, None)
    for f in range(8000):
        if "state" in snap:
            break
        if f % 20 == 5: pb.button_press("a")
        if f % 20 == 9: pb.button_release("a")
        if f % 200 == 150: pb.button_press("start")
        if f % 200 == 154: pb.button_release("start")
        pb.tick()
    assert "state" in snap, "never reached CharSelect through the real intro"
    print(f"reached picker organically at frame {pb.frame_count}")

    def fresh():
        pb.load_state(io.BytesIO(snap["state"]))
        for _ in range(40): pb.tick()

    def tap(b, hold=4, wait=8):
        pb.button_press(b)
        for _ in range(hold): pb.tick()
        pb.button_release(b)
        for _ in range(wait): pb.tick()

    fails = 0
    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    # every entry
    bad = []
    for k in range(n):
        fresh()
        for _ in range(k): tap("down")
        tap("a")
        for _ in range(60): pb.tick()
        want = 0 if k == 0 else sel[k - 1][0] + 1
        if tamper and k == 5: want += 1
        got = pb.memory[WCHAR]
        if got != want:
            bad.append((k, want, got))
    check(not bad, f"all {n} entries pick the right id (bad: {bad[:5]})")

    # wrap up
    fresh(); tap("up"); tap("a")
    for _ in range(60): pb.tick()
    check(pb.memory[WCHAR] == sel[-1][0] + 1, "Up from the top wraps to the last entry")
    # paging
    fresh(); tap("right"); tap("a")
    for _ in range(60): pb.tick()
    check(pb.memory[WCHAR] == sel[12 - 1][0] + 1, "Right pages by 12")
    fresh()
    for _ in range(len(sel) // 12 + 2): tap("right")
    tap("a")
    for _ in range(60): pb.tick()
    check(pb.memory[WCHAR] == sel[-1][0] + 1, "Right clamps at the last entry")
    # cannot be dismissed
    fresh()
    for b in ("b", "start", "select"): tap(b)
    for _ in range(30): pb.tick()
    check(pb.memory[WCHAR] == 0 and bytes(pb.memory[TILEMAP:TILEMAP + 360]) != snap["tilemap"],
          "B/Start/Select do not dismiss the picker")
    # restore
    fresh(); tap("down"); tap("a")
    for _ in range(90): pb.tick()
    # the intro prints text after the picker; compare only the portrait rows (0-10)
    after = bytes(pb.memory[TILEMAP:TILEMAP + 11 * 20])
    check(after == snap["tilemap"][:11 * 20], "intro screen restored after confirm (rows 0-10)")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
