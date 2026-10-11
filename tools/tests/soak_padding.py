#!/usr/bin/env python3
"""Soak: random play from every committed savestate must never touch the padding
bytes $DC87-$DC9C (the block the character byte lives in). Evidence, not proof:
see docs/SELECTION_MECHANISM.md for the static scan it complements."""
import glob, random, sys
sys.path.insert(0, "tools")
from cmlib import CM

random.seed(1)
cm = CM(rom="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc")   # UNPATCHED ROM: vanilla behaviour
btn = ["a", "b", "up", "down", "left", "right", "start"]
bad = 0
total = 0
for st in sorted(glob.glob("tools/emu_states/*.state")):
    cm.load(st)
    pad0 = cm.rd(0xDC87, 22)
    changed = set()
    for i in range(1500):
        if i % 6 == 0:
            for b in btn:
                cm.pb.button_release(b)
            cm.pb.button_press(random.choice(btn))
        cm.pb.tick()
        if i % 25 == 0:
            now = cm.rd(0xDC87, 22)
            changed |= {0xDC87 + k for k in range(22) if now[k] != pad0[k]}
    total += 1500
    print(f"{st.split('/')[-1]:28s} {'CHANGED ' + str([hex(x) for x in sorted(changed)]) if changed else 'padding untouched'}")
    bad += bool(changed)
print("frames", total, "RESULT:", "FAIL" if bad else "ALL UNTOUCHED")
sys.exit(1 if bad else 0)
