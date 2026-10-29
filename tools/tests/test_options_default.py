#!/usr/bin/env python3
"""QoL A3 (2026-10-28): a new game starts with battle animations off.

Cold boot with no save (PyBoy starts with blank SRAM), the real intro reaches CharSelect, then wOptions ($CFCC) is
read: bit 7 (BATTLE_SCENE) must be set, and the rest must equal Prism's own default ($21: text delay 1 + stereo).
Then the in-battle reader is checked against the same byte: Prism's CheckBattleScene (00:0893 reads wOptions,
and $80) returns carry = animations off.
CONTROL: the same ROM with DefaultOptions' byte put back to the base $21 must show bit 7 clear.
--tamper expects bit 7 CLEAR on the shipped ROM and must FAIL.
"""
import io
import os
import sys
import tempfile
from pyboy import PyBoy

ROM = "build/prism_cm.gbc"
WOPTIONS = 0xCFCC
DEFAULT_OPTS = 5 * 0x4000 + (0x5093 - 0x4000)


def sym(name):
    for l in open("build/prism_cm.sym"):
        p = l.split(";")[0].split()
        if len(p) == 2 and p[1] == name:
            b, a = p[0].split(":")
            return int(b, 16), int(a, 16)
    raise SystemExit(f"{name} not in build/prism_cm.sym")


def options_at_picker(rom):
    pb = PyBoy(rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    got = {}
    bank, addr = sym("CharSelect")

    def at_entry(ctx=None):
        got.setdefault("opt", pb.memory[WOPTIONS])
    pb.hook_register(bank, addr, at_entry, None)
    for f in range(8000):
        if "opt" in got:
            break
        if f % 20 == 5: pb.button_press("a")
        if f % 20 == 9: pb.button_release("a")
        if f % 200 == 150: pb.button_press("start")
        if f % 200 == 154: pb.button_release("start")
        pb.tick()
    pb.stop(save=False)
    return got.get("opt")


def main():
    tamper = "--tamper" in sys.argv
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    data = bytearray(open(ROM, "rb").read())
    check(data[DEFAULT_OPTS] == 0xA1, f"DefaultOptions byte 0 (05:5093) is $A1 (got ${data[DEFAULT_OPTS]:02X})")
    check(data[0x0893:0x089A] == bytes.fromhex("facccfe680c837"),
          "00:0893 is CheckBattleScene: ld a,[wOptions] / and $80 / ret z / scf (bit 7 = animations off)")
    opt = options_at_picker(ROM)
    check(opt is not None, "the real intro reached CharSelect")
    want = 0 if tamper else 1
    check(opt is not None and (opt >> 7) & 1 == want and opt & 0x7F == 0x21,
          f"new game: wOptions = ${opt or 0:02X} (battle scene off bit = {want}, the rest = Prism's $21)")
    with tempfile.TemporaryDirectory() as td:
        ctl = os.path.join(td, "control.gbc")
        data[DEFAULT_OPTS] = 0x21
        open(ctl, "wb").write(data)
        copt = options_at_picker(ctl)
    check(copt == 0x21, f"CONTROL (base byte $21 restored): wOptions = ${copt or 0:02X}, animations on")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
