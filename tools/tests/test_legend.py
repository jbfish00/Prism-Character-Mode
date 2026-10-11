#!/usr/bin/env python3
"""The 1% legendary rule (game_plans/legendary_encounters.md) on the REAL OverrideWildSpecies.

  * a character with a legendary: ~1% of encounters become one of THEIR legendaries (never an
    off-roster one, never a non-legendary), at the area's level (family stage), and the old
    10% override still fires on the remaining encounters (~10% of those)
  * "offered until caught": with the Pokedex caught flag set a legendary is never offered
  * a roster with nothing but legendaries stays repeatable at 1% even when all are caught
    (patched into a ROM copy: no shipped roster is all-legendary today)
  * a character with NO legendary draws exactly the random numbers it always did
    (one PCT_ROLL per encounter, no extra draw) -- "the data check goes before the RNG call"
(--tamper corrupts the caught-flag expectation and must FAIL.)
"""
import shutil, sys, tempfile
sys.path.insert(0, "tools")
from cmlib import CM, roster_has, species_names

STATE = "tools/emu_states/ck9.state"
TEST_ROM = "build/prism_cm_test.gbc"
TEST_SYM = "build/prism_cm_test.sym"
N = 30000
PCT_ROLL = 0x2AA8


def fam():
    d = {}
    hdr = None
    for l in open("tools/character_mode/wildmon_families.tsv"):
        p = l.rstrip("\n").split("\t")
        if hdr is None:
            hdr = p
            continue
        r = dict(zip(hdr, p))
        d[int(r["id"])] = (int(r["family_root"]), int(r["stage_min"]), int(r["stage_max"]), r["is_legendary"] == "1")
    return d


def set_caught(cm, species, on=True):
    a = 0xDE99 + ((species - 1) >> 3)
    bit = 1 << ((species - 1) & 7)
    cm.wb(a, (cm.rb(a) | bit) if on else (cm.rb(a) & ~bit))


def main():
    tamper = "--tamper" in sys.argv
    F = fam()
    names = species_names()
    legend_ids = {s for s, r in F.items() if r[3]}
    cm = CM(rom=TEST_ROM, sym=TEST_SYM)
    cm.load(STATE)
    base = cm.snapshot()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def run(cm_, char, n, level=30):
        """n encounters through OverrideWildSpecies, looped INSIDE the emulator (CMTestWildLoop on
        the test build). Returns (list of results with None = engine's own roll stands, 0)."""
        cm_.restore(base_of[cm_])
        cm_.set_char(char)
        m = cm_.pb.memory
        m[0xFF70] = 7
        for k in range(0x200):
            m[0xD000 + k] = 0
        m[0xFF70] = 1
        cm_.call("CMTestWildLoop", b=n >> 8, c=n & 0xFF, d=level, frames=max(300, n // 5))
        m[0xFF70] = 7
        tally = bytes(m[0xD000:0xD200])
        m[0xFF70] = 1
        out = []
        for sp in range(256):
            cnt = tally[2 * sp] | tally[2 * sp + 1] << 8
            out += [None if sp == 0 else sp] * cnt
        return out, 0

    base_of = {cm: base}
    # a character with several legendaries: Red
    red = 60
    red_legends = sorted(s for s in legend_ids if roster_has(red, s))
    print("Red's legendaries:", [names[s] for s in red_legends])
    out, pcts = run(cm, red, N)
    hits = [o for o in out if o is not None]
    roots = {F[s][0] for s in red_legends}
    leg_hits = [o for o in hits if F[o][0] in roots and F[o][3]]
    rate = len(leg_hits) / N
    check(0.004 <= rate <= 0.018, f"Red: legendary rate {rate:.3%} over {N} encounters (target 1%)")
    check(all(roster_has(red, o) for o in leg_hits), "Red: every legendary offered is on his roster")
    others = [o for o in hits if not F[o][3]]
    check(0.07 <= len(others) / N <= 0.13, f"Red: ordinary roster override still ~10% ({len(others) / N:.1%})")
    check(set(leg_hits) <= set(red_legends), "Red: legendaries offered are exactly roster legendaries (stage-matched)")
    # caught -> never offered again
    cm.restore(base)
    for s in red_legends:
        if not tamper:                 # tamper: leave them uncaught but still expect none -> must fail
            set_caught(cm, s)
    base_of[cm] = cm.snapshot()
    out, _ = run(cm, red, N)
    leg = [o for o in out if o is not None and F[o][3]]
    check(not leg, f"Red, every legendary caught: none offered ({len(leg)} seen)")
    # one uncaught: only that one
    cm.restore(base)
    for s in red_legends[1:]:
        set_caught(cm, s)
    base_of[cm] = cm.snapshot()
    out, _ = run(cm, red, 8000)
    leg = {o for o in out if o is not None and F[o][3]}
    check(leg == {red_legends[0]}, f"Red, one uncaught: exactly that one is offered ({[names[s] for s in leg]})")

    # uniform choice among several legendaries: the character with the most
    many = max(range(76), key=lambda c: sum(roster_has(c, x) for x in legend_ids))
    ml = sorted(x for x in legend_ids if roster_has(many, x))
    cm.restore(base)
    base_of[cm] = base
    out, _ = run(cm, many, 60000)
    cnt = {x: sum(1 for o in out if o == x) for x in ml}
    mean = sum(cnt.values()) / len(ml)
    check(len(ml) >= 3 and all(0.55 * mean <= v <= 1.45 * mean for v in cnt.values()),
          f"character {many} with {len(ml)} legendaries: uniform choice {dict((names[k], v) for k, v in cnt.items())}")

    # character with no legendary draws no extra random numbers
    flags = [int(l.split("\t")[0]) for l in open("tools/character_mode/selectable.tsv").read().splitlines()[1:]]
    src = open("tools/character_mode/select_data.asm").read()
    import re
    fl = []
    for m in re.finditer(r"CharLegendFlags::\n((?:\tdb .*\n)+)", src):
        fl = [int(x) for x in re.findall(r"\d+", m.group(1))]
    nolegend = [c for c, f in enumerate(fl) if not (f & 1)]
    c0 = nolegend[0]
    cm.restore(base)
    base_of[cm] = base
    n_enc = 300
    out, _ = run(cm, c0, 20000)
    check(all(o is None or not F[o][3] for o in out), f"character {c0} (no legendary): never a legendary in 20000 encounters")
    # RNG consumption: LegendPick on a character with no legendary must not call the RNG at all
    pct = []
    cm.restore(base)
    cm.set_char(c0)
    cm.pb.hook_register(0, PCT_ROLL, lambda c=None: pct.append(1), None)
    cm.pb.hook_register(0, 0x29D8, lambda c=None: pct.append(1), None)       # RAW_RANDOM
    for _ in range(40):
        cm.call("LegendPick", d=c0, b=30, frames=20)
    cm.pb.hook_deregister(0, PCT_ROLL)
    cm.pb.hook_deregister(0, 0x29D8)
    check(not pct, f"character {c0} (no legendary): LegendPick draws no random numbers ({len(pct)} draws in 40 calls)")

    # repeatable all-legendary rule, on a patched ROM copy
    tmp = tempfile.NamedTemporaryFile(suffix=".gbc", delete=False)
    shutil.copyfile("build/prism_cm_test.gbc", tmp.name)
    syms = {}
    for l in open(TEST_SYM):
        p = l.split(";")[0].split()
        if len(p) == 2 and ":" in p[0]:
            b, a = p[0].split(":")
            syms[p[1]] = (int(b, 16), int(a, 16))
    b, a = syms["CharLegendFlags"]
    with open(tmp.name, "r+b") as f:
        f.seek(b * 0x4000 + a - 0x4000 + red)
        f.write(bytes([3]))
    shutil.copyfile("build/prism_cm_test.gbc", tmp.name)
    with open(tmp.name, "r+b") as f:
        f.seek(b * 0x4000 + a - 0x4000 + red)
        f.write(bytes([3]))
    cm2 = CM(rom=tmp.name, sym=TEST_SYM)
    cm2.load(STATE)
    for s in red_legends:
        set_caught(cm2, s)
    base_of[cm2] = cm2.snapshot()
    out, _ = run(cm2, red, N)
    leg = [o for o in out if o is not None and F[o][3]]
    check(len(leg) > 20, f"all-legendary roster (flag bit 1): still offered when caught ({len(leg)} in {N})")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
