#!/usr/bin/env python3
"""Organic end-to-end: cold boot -> real New Game intro -> picker (choose a character)
-> keep playing the intro with the joypad until the game world (map 1,1).

The intro itself saves WRAM to SRAM, clears WRAM and restores it a few times (map
127,128 is its scratch world), so $DC96/$DC97 DIP transiently; the requirement is that
they hold the choice when the intro is over (i.e. the save/restore round trip is
faithful), and that the player reached the real world with it.
"""
import io, sys
sys.path.insert(0, "tools")
from cmlib import CM

cm = CM()
pb = cm.pb
CHAR = 9            # Brock
bank, addr = cm.sym["CharSelect"]
seen = {}
pb.hook_register(bank, addr, lambda c=None: seen.setdefault("entry", pb.frame_count), None)
for f in range(8000):
    if "entry" in seen:
        break
    if f % 20 == 5: pb.button_press("a")
    if f % 20 == 9: pb.button_release("a")
    if f % 200 == 150: pb.button_press("start")
    if f % 200 == 154: pb.button_release("start")
    pb.tick()
assert "entry" in seen
sel = [int(l.split("\t")[0]) for l in open("tools/character_mode/selectable.tsv").read().splitlines()[1:]
       if l.split("\t")[5] == "1"]
k = 1 + sel.index(CHAR)
cm.tick(40)
for _ in range(k):
    cm.tap("down")
cm.tap("a")
cm.tick(30)
print("picked entry", k, "-> $DC96/97 =", cm.rb(0xDC96), hex(cm.rb(0xDC97)))
ok = cm.rb(0xDC96) == CHAR + 1
changes = []
last = (cm.rb(0xDC96), cm.rb(0xDC97))
maps = set()
for f in range(30000):
    if f % 20 == 3: pb.button_press("a")
    if f % 20 == 7: pb.button_release("a")
    pb.tick()
    cur = (cm.rb(0xDC96), cm.rb(0xDC97))
    if cur != last:
        changes.append((f, cur, (cm.rb(0xDCB5), cm.rb(0xDCB6)), hex(pb.register_file.PC)))
        last = cur
    maps.add((cm.rb(0xDCB5), cm.rb(0xDCB6)))
print("maps visited after the picker:", sorted(maps))
print("changes:", changes[:5])
print("party", cm.party())
final = (cm.rb(0xDC96), cm.rb(0xDC97))
print("final $DC96/97:", final, "| transient dips during the intro's own save/clear/restore:", len(changes))
ok = ok and final == (CHAR + 1, (CHAR + 1) ^ 0xA5) and (1, 1) in maps
print("RESULT:", "ALL PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
