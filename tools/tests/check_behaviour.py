#!/usr/bin/env python3
"""Static check of the move best-version behaviour cards, batch 1 (2026-11-25, src/behaviour.asm), on the COMPILED ROM.

usage: python3 -I tools/tests/check_behaviour.py [build/prism_cm.gbc] [--control build/prism_cm_nobeh.gbc]
Every site is pinned twice: the control build (-DCM_NO_BEHAVIOUR, = the previous release byte for byte) must hold the
release bytes, and the cards build the new ones. Call operands are resolved from the build's .sym, and the 4 routines in
bank $0D's tail are pinned instruction by instruction. EXPECT_CHECKS checks; one tamper per check must fail exactly it;
the control must fail every check (EXPECT_CHECKS). Design: ../game_plans/move_ability_best_2026-11-22/behaviour_all/PRISM.md
verify_hooks.py imports SITES + TAIL from here (the bytes it allows)."""
import re, sys
from pathlib import Path

R = Path(__file__).resolve().parents[2]


def off(bank, addr):
    return addr if bank == 0 else bank * 0x4000 + addr - 0x4000


def call(a):
    return "cd%02x%02x" % (a & 0xFF, a >> 8)


# (name, bank, addr, release hex, new hex or a function of the sym table)
SITES = [
    ("never_miss", 0x0D, 0x7534, "cd2d76", lambda S: call(S["CM_NeverMiss"])),
    ("disable", 0x0D, 0x6AAD, "3e050c", lambda S: call(S["CM_DisableTurns"])),
    ("encore", 0x0D, 0x6B17, "cdce29e603c604", lambda S: call(S["CM_EncoreTurns"]) + "00" * 4),
    ("protect", 0x0D, 0x6F01, "46cdce29", lambda S: call(S["CM_ProtectCap"]) + "00"),
    ("trap_turns", 0x0D, 0x5A79, "e603c603", lambda S: "e601c605"),
    ("roar_level", 0x0D, 0x4C9B, "cdcf4c", lambda S: "a70000"),
    ("flail_mult", 0x0D, 0x61E7, "3e30", lambda S: "3e40"),
    ("flail_table", 0x0D, 0x6221, "01c8049609641050202830 14".replace(" ", ""),
     lambda S: bytes([1, 200, 5, 150, 12, 100, 21, 80, 42, 40, 64, 20]).hex()),
]
# routines: (sym, hex) -- CM_NeverMiss: call PerfectAcc / ret z / ld a,$0E / call GetBattleVar / cp 49 / ret z / cp 198 / ret
ROUTINES = [
    ("CM_NeverMiss", "cd2d76c8" "3e0ecd3307" "fe31c8" "fec6c9"),
    ("CM_DisableTurns", "cdce29e603c6050cc9"),
    ("CM_EncoreTurns", "cdce29e607fe0530f7c605c9"),
    ("CM_ProtectCap", "7efe0438023e0447c3ce29"),
]
TAIL = (0x0D, 0x7F80, 0x80)          # bank $0D $7F80-$7FFF: $FF in the base ROM, the routines live here
EXPECT_CHECKS = len(SITES) + len(ROUTINES) + 1


def sym(p):
    out = {}
    for l in Path(p).read_text().splitlines():
        m = re.match(r"([0-9a-f]{2}):([0-9a-f]{4}) (\S+)$", l)
        if m:
            out[m.group(3)] = int(m.group(2), 16)
    return out


def checks(rom, S):
    """name -> (ok, offset of a byte whose change must break it)"""
    out = {}
    for name, b, a, old, new in SITES:
        o = off(b, a)
        try:
            want = bytes.fromhex(new(S))
        except KeyError:
            out[name] = (False, o); continue
        out[name] = (bytes(rom[o:o + len(want)]) == want, o + len(want) - 1)
    for name, hx in ROUTINES:
        a = S.get(name)
        if a is None:
            out[name] = (False, off(*TAIL[:2])); continue
        o = off(0x0D, a)
        want = bytes.fromhex(hx)
        out[name] = (bytes(rom[o:o + len(want)]) == want, o + len(want) // 2)
    t = off(*TAIL[:2])
    used = max((off(0x0D, S[n]) + len(bytes.fromhex(h)) for n, h in ROUTINES if n in S), default=t)
    out["tail_rest_ff"] = (set(rom[used:t + TAIL[2]]) == {0xFF} and used > t, t + TAIL[2] - 1)
    return out


def release_ok(rom):
    """the control: every site holds the release bytes and the tail is $FF"""
    bad = [n for n, b, a, old, _ in SITES if bytes(rom[off(b, a):off(b, a) + len(old) // 2]) != bytes.fromhex(old)]
    t = off(*TAIL[:2])
    if set(rom[t:t + TAIL[2]]) != {0xFF}:
        bad.append("tail")
    return bad


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    ctl = None
    if "--control" in sys.argv:
        ctl = Path(sys.argv[sys.argv.index("--control") + 1]); a = [x for x in a if Path(x) != ctl]
    rom_p = Path(a[0]) if a else R / "build/prism_cm.gbc"
    rom, S = bytearray(rom_p.read_bytes()), sym(rom_p.with_suffix(".sym"))
    res = checks(rom, S)
    for n, (ok, _) in res.items():
        print("%-5s %s" % ("ok" if ok else "FAIL", n))
    nbad = sum(not ok for ok, _ in res.values())
    print("behaviour cards: %d checks, %d failures (want %d checks, 0 failures)" % (len(res), nbad, EXPECT_CHECKS))
    rc = 1 if nbad or len(res) != EXPECT_CHECKS else 0
    caught = 0
    for n, (ok, at) in res.items():
        t = bytearray(rom); t[at] ^= 0x01
        hit = not checks(t, S)[n][0]
        print("caught" if hit else "MISSED", "tamper", n, hex(at)); caught += hit
    print("tampers: %d/%d caught (want %d)" % (caught, len(res), EXPECT_CHECKS))
    rc |= caught != EXPECT_CHECKS
    if ctl:
        c = bytearray(ctl.read_bytes())
        nf = sum(not ok for ok, _ in checks(c, sym(ctl.with_suffix(".sym"))).values())
        rb = release_ok(c)
        print("control %s fails %d checks (want %d); release bytes at every site: %s" % (ctl.name, nf, EXPECT_CHECKS, rb or "yes"))
        rc |= nf != EXPECT_CHECKS or bool(rb)
        rb2 = release_ok(rom)
        print("cards build differs from the release at %d of %d sites + tail (want all)" % (len(rb2), len(SITES) + 1))
        rc |= len(rb2) != len(SITES) + 1
    sys.exit(rc)


if __name__ == "__main__":
    main()
