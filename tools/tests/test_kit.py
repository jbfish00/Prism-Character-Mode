#!/usr/bin/env python3
"""QoL starter kit (round 2 item 1, 2026-11-13): the Bicycle key item at New Game. LIVE, through the real intro.

Boots the built ROM cold, mashes through the intro to the picker (organically), confirms an entry with the real joypad,
then keeps mashing A until the intro is over and reads the bag: wNumKeyItems ($D8B8) = 1 and wKeyItems[0] ($D8B9) = $07
(BICYCLE), for 'Normal game' (Character Mode off) AND a real character. Control image (CM_NO_KIT, build/prism_cm_nokit.gbc):
the key pocket stays empty. --tamper runs the positive checks against the control image: must FAIL.
Run: tools/emu_venv/bin/python3 tools/tests/test_kit.py [--tamper]
"""
import io, sys
from pyboy import PyBoy

TAMPER = "--tamper" in sys.argv
SHIP = "build/prism_cm_nokit.gbc" if TAMPER else "build/prism_cm.gbc"
CONTROL = "build/prism_cm_nokit.gbc"
NUM_KEY, KEYS, WCHAR = 0xD8B8, 0xD8B9, 0xDC96   # Prism: wNumKeyItems $D8B8 (not Crystal's $D8BC), wNumItems $D866
BICYCLE = 0x07
fails = 0


def check(ok, msg):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    fails += (not ok)


def sym(path, name):
    for l in open(path[:-4] + ".sym"):
        p = l.split(";")[0].split()
        if len(p) == 2 and p[1] == name:
            b, a = p[0].split(":")
            return int(b, 16), int(a, 16)
    raise KeyError(name)


def run(rom, entry):
    pb = PyBoy(rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    snap = {}
    bank, addr = sym(rom, "CharSelect")

    def at_entry(ctx=None):
        b = io.BytesIO(); pb.save_state(b); snap["s"] = b.getvalue()
    pb.hook_register(bank, addr, at_entry, None)
    for f in range(8000):
        if "s" in snap:
            break
        if f % 20 == 5: pb.button_press("a")
        if f % 20 == 9: pb.button_release("a")
        if f % 200 == 150: pb.button_press("start")
        if f % 200 == 154: pb.button_release("start")
        pb.tick()
    assert "s" in snap, "never reached the picker"
    pb.load_state(io.BytesIO(snap["s"]))
    for _ in range(40): pb.tick()
    for _ in range(entry):
        pb.button_press("down")
        for _ in range(4): pb.tick()
        pb.button_release("down")
        for _ in range(8): pb.tick()
    pb.button_press("a")
    for _ in range(4): pb.tick()
    pb.button_release("a")
    char = pb.memory[WCHAR]
    for f in range(6000):                       # the rest of the intro, then the first overworld frames
        if f % 20 == 5: pb.button_press("a")
        if f % 20 == 9: pb.button_release("a")
        pb.tick()
    out = (pb.memory[NUM_KEY], pb.memory[KEYS], pb.memory[KEYS + 1], char)
    pb.stop(save=False)
    return out


for label, entry in (("Normal game (CM off)", 0), ("a real character (entry 3)", 3)):
    n, k0, k1, ch = run(SHIP, entry)
    check(n == 1 and k0 == BICYCLE, f"{label}: key pocket = [{n} item(s), first {k0:#04x}] (want 1, BICYCLE $07), wCharMode {ch}")
    check(k1 in (0, 0xFF), f"{label}: terminator after the Bicycle ({k1:#04x})")
n, k0, _, ch = run(CONTROL, 3)
check(n == 0, f"CONTROL CM_NO_KIT: key pocket empty ({n} items)")
print("RESULT:", "PASS" if not fails else "FAIL", f"({fails} failed)")
sys.exit(1 if fails else 0)
