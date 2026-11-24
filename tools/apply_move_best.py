#!/usr/bin/env python3
"""Move "best version" (user 2026-11-23: raise every move to its best value), cheap tier, on linked Prism ROMs.

usage: python3 -I tools/apply_move_best.py ROM.gbc [ROM2.gbc ...]       (tools/build.sh runs it on every variant)
       python3 -I tools/apply_move_best.py --check build/prism_cm.gbc build/prism_cm_nomovebest.gbc
Moves at 0x41263 (7-byte records from move 1: anim, effect, power, type|category<<6, acc %, pp, chance %; the table the
step-2 extractor read). Power, type (low 6 bits; the category bits stay), accuracy, pp, chance via movepatch layout
"gbc7". Never-miss and priority are effects in pokecrystal: deferred. Each edit asserts the value it replaces
(tools/character_mode/move_changes.json). --check: every applied row reads its new value against the unpatched control,
and nothing else in the table changed; the control must fail it (run_tests.sh checks both)."""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import movepatch

TABLE = 0x41263 - 7
EXPECT = (185, 3)        # (applied, deferred), pinned 2026-11-23
SL = json.loads((ROOT / "tools/character_mode/move_changes.json").read_text())

if sys.argv[1] == "--check":
    built, base = (Path(p).read_bytes() for p in sys.argv[2:4])
    todo, deferred, _, _ = movepatch.plan(SL, "gbc7")
    bad = movepatch.verify(base, built, SL, TABLE, "gbc7", 255)
    if (len(todo), len(deferred)) != EXPECT:
        bad.append("counts %d/%d (want %s)" % (len(todo), len(deferred), EXPECT))
    for b in bad[:20]:
        print("FAIL", b)
    print("move best-version check: %d applied, %d deferred, %d failures (want 0)" % (len(todo), len(deferred), len(bad)))
    sys.exit(1 if bad else 0)
for p in map(Path, sys.argv[1:]):
    rom = bytearray(p.read_bytes())
    rep = movepatch.apply(rom, SL, TABLE, "gbc7")
    p.write_bytes(rom)
    print("move best-version %s: %d applied, %d deferred" % (p.name, rep["applied"], rep["deferred"]))
