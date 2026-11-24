#!/usr/bin/env python3
"""Move "best version" (user 2026-11-23: raise every move to its best value), cheap tier, on linked Prism ROMs.

usage: python3 -I tools/apply_move_best.py ROM.gbc [ROM2.gbc ...]       (tools/build.sh runs it on every variant)
       python3 -I tools/apply_move_best.py --check build/prism_cm.gbc build/prism_cm_nomovebest.gbc
Moves at 0x41263 (7-byte records from move 1: anim, effect, power, type|category<<6, acc %, pp, chance %; the table the
step-2 extractor read). Power, type (low 6 bits; the category bits stay), accuracy, pp, chance via movepatch layout
"gbc7". Never-miss and priority are effects in pokecrystal: deferred. Each edit asserts the value it replaces
(tools/character_mode/move_changes.json). --check: every applied row reads its new value against the unpatched control,
and nothing else in the table changed; the control must fail it (run_tests.sh checks both).
Crit +2 (2026-11-24, RULES.md): BattleCommand_Critical (09:795F) adds 1 stage for a move in CriticalHitMoves (09:7990),
which already lists exactly the 9 of the 25 moves any generation gave a high crit ratio that Prism has (152 is Night
Slash here). The 8 bytes `push bc / call IsInArray / pop bc / jr nc,+1 / inc c` become `nop / call IsInArray /
jr nc,+2 / inc c / inc c` (+2): IsInArray (00:039F) keeps c and clobbers only b/d/e, and b is reloaded (ld b,0) before
the next read. --check pins both the patch and the list; the control keeps the release bytes."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import movepatch

TABLE = 0x41263 - 7
EXPECT = (185, 3)        # (applied, deferred), pinned 2026-11-23
CRIT_AT = 0x2795F                     # bank 9 $795F
CRIT_OLD = bytes.fromhex("c5cd9f03c130010c")
CRIT_NEW = bytes.fromhex("00cd9f0330020c0c")
CRIT_LIST = 0x27990                   # CriticalHitMoves (ld hl, $7990 right before the patch)
CRIT_IDS = [2, 75, 143, 152, 163, 177, 217, 238, 244]   # Karate Chop, Razor Leaf, Sky Attack, Night Slash, Slash,
                                                       # Aeroblast, Psycho Cut, Cross Chop, Shadow Claw (pinned)


def crit_list(rom):
    out = []
    for b in rom[CRIT_LIST:CRIT_LIST + 32]:
        if b == 0xFF:
            return out
        out.append(b)
    return None


def crit_bad(rom):
    bad = []
    if rom[CRIT_AT:CRIT_AT + 8] != CRIT_NEW:
        bad.append("crit +2 patch at %#x reads %s, want %s" % (CRIT_AT, rom[CRIT_AT:CRIT_AT + 8].hex(), CRIT_NEW.hex()))
    if rom[CRIT_AT - 3:CRIT_AT] != bytes.fromhex("219079"):
        bad.append("the patch no longer follows ld hl, CriticalHitMoves")
    if sorted(crit_list(rom) or []) != CRIT_IDS:
        bad.append("CriticalHitMoves %s, want %s" % (crit_list(rom), CRIT_IDS))
    return bad
SL = json.loads((ROOT / "tools/character_mode/move_changes.json").read_text())

if sys.argv[1] == "--check":
    built, base = (Path(p).read_bytes() for p in sys.argv[2:4])
    todo, deferred, _, _ = movepatch.plan(SL, "gbc7")
    bad = movepatch.verify(base, built, SL, TABLE, "gbc7", 255) + crit_bad(built)
    if base[CRIT_AT:CRIT_AT + 8] != CRIT_OLD:
        bad.append("control ROM's crit bytes are not the release's")
    if (len(todo), len(deferred)) != EXPECT:
        bad.append("counts %d/%d (want %s)" % (len(todo), len(deferred), EXPECT))
    for b in bad[:20]:
        print("FAIL", b)
    print("move best-version check: %d applied, %d deferred, %d failures (want 0)" % (len(todo), len(deferred), len(bad)))
    sys.exit(1 if bad else 0)
for p in map(Path, sys.argv[1:]):
    rom = bytearray(p.read_bytes())
    rep = movepatch.apply(rom, SL, TABLE, "gbc7")
    assert rom[CRIT_AT:CRIT_AT + 8] == CRIT_OLD, "crit site %#x is not the release bytes" % CRIT_AT
    rom[CRIT_AT:CRIT_AT + 8] = CRIT_NEW
    p.write_bytes(rom)
    print("move best-version %s: %d applied, %d deferred, crit +2 patched" % (p.name, rep["applied"], rep["deferred"]))
