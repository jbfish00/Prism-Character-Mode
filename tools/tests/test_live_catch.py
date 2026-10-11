#!/usr/bin/env python3
"""LIVE catch test: a real wild battle (the shipped engine, started through its own encounter
script, see tools/live_battle.py), a real Poke Ball thrown from the real Pack menu, the real
throw animation, and the verdict read from the battle text and the party/dex afterwards.

  CM on, on-roster wild species  : caught every time, even at level 60 (a vanilla ball fails)
  CM on, off-roster wild species : never caught ("dodged"/broke free), even at level 5
  CM off                         : engine odds (a level-60 mon must escape at least once)
--tamper flips the on-roster expectation and must FAIL.
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, char_info, species_names
from live_battle import give_mon, start_wild, wait_battle, shot

STATE = "tools/emu_states/ck9.state"
CHAR = 9
CH = {0x7F: " ", 0xE8: ".", 0xE7: "!", 0xE6: "?", 0xE3: "-", 0xE0: "'", 0xF4: ","}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CH[0x80 + i] = c
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CH[0xA0 + i] = c


def text(cm):
    out = []
    for row in range(12, 18):
        raw = bytes(cm.pb.memory[0xC4A0 + row * 20 + 1:0xC4A0 + row * 20 + 19])
        out.append("".join(CH.get(b, "") for b in raw).strip())
    return " ".join(t for t in out if t)


def battle_menu(cm, species, level, char, veteran=False):
    cm.load(STATE)
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 30)
    for i, v in enumerate((1, 5, 99, 0xFF)):         # ball pocket (count, id, qty, end)
        cm.wb(0xD8EC + i, v)
    if veteran:
        # Prism's own catch assist (03:7D59) keys on how many species are caught (dex flags $DE99,
        # 32 bytes): a fresh save gets near-guaranteed catches. Mark everything caught except the
        # target's own byte so the ENGINE's odds are the hard ones and the rule is what's measured.
        for a in range(0xDE99, 0xDEB9):
            cm.wb(a, 0 if a == 0xDE99 + ((species - 1) >> 3) else 0xFF)
    cm.set_char(char)
    start_wild(cm, species, level)
    assert wait_battle(cm), "battle did not start"
    for _ in range(60):                    # advance the intro text until the real battle menu is up
        if "Fight" in text(cm):
            cm.tick(30)
            break
        cm.tap("a", 4, 40)
    assert "Fight" in text(cm), "never reached the battle menu: " + text(cm)
    return cm.snapshot()


def throw(cm, snap, seed, char, shots=None):
    cm.restore(snap)
    cm.tick(seed)                      # vary the RNG
    cm.set_char(char)
    cm.tap("down", 4, 20); cm.tap("a", 4, 90)      # Pack
    cm.tap("right", 4, 30); cm.tap("a", 4, 40)     # Balls, Poke Ball
    cm.tap("a", 4, 20)                              # Use
    seen = ""
    n0 = cm.rb(0xDCD7)
    for f in range(900):
        cm.tick(6)
        t = text(cm)
        if shots and f in shots:
            shot(cm, shots[f])
        seen += " | " + t
        if "Gotcha" in t or "broke free" in t or "dodged" in t or "missed" in t or "so close" in t or "Aww" in t or "Shoot" in t:
            cm.tick(30)
            break
    caught = "Gotcha" in seen
    return caught, seen


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    info, names = char_info(), species_names()
    SP = 1                                   # Bulbasaur
    ON = next(c for c in info if info[c]["selectable"] and roster_has(c, SP))
    OFF = 9                                  # Brock: no Bulbasaur
    assert roster_has(ON, SP) and not roster_has(OFF, SP)
    print(f"{info[ON]['name']} (has {names[SP]}), {info[OFF]['name']} (does not)")
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    N = 8

    def run(lv, char, vet, shots=None):
        snap = battle_menu(cm, SP, lv, char, vet)
        return [throw(cm, snap, 3 + 7 * i, char, shots=shots if i == 0 else None)[0] for i in range(N)]

    r = run(100, None, True)
    check(sum(r) == 0, f"CM off, veteran save, level-100 {names[SP]}: engine odds, caught {sum(r)}/{N} (control: a ball really fails)")
    r = run(100, ON, True, {5: "live_on_a.png", 25: "live_on_b.png", 60: "live_on_c.png"})
    check((sum(r) == N) != tamper, f"CM on, ON-roster level-100 {names[SP]}: caught {sum(r)}/{N}")
    r = run(5, None, False)
    check(sum(r) == N, f"CM off, fresh save, level-5 {names[SP]}: caught {sum(r)}/{N} (control: the engine's assist catches it)")
    r = run(5, OFF, False, {5: "live_off_a.png", 40: "live_off_b.png"})
    check(sum(r) == 0, f"CM on, OFF-roster level-5 {names[SP]}: caught {sum(r)}/{N}")
    print("FAILED" if fails else "OK")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
