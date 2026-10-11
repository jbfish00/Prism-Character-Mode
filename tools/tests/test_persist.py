#!/usr/bin/env python3
"""Persistence of the active character through Prism's REAL save/load routines.

The character is stored in saved WRAM ($DC96 id+1, $DC97 check). This runs the
game's own copy/checksum routines (bank 5) from a real in-game state:

  * WRAM -> primary SRAM (05:4E8A, 05:4EA3, 05:4EB2) then checksum (05:4ECB);
    clear WRAM; SRAM -> WRAM (05:50DF, 05:5105, 05:5114): the byte must come back
  * the same for the BACKUP copy (05:4F0C/4F25/4F34/4F47 save, 05:516B/5184/5193 load)
  * COVERAGE: after the save + checksum, 05:512D (verify) must succeed, and flipping
    the SRAM byte that holds $DC96 must make it FAIL -- i.e. the checksum really covers it
  * CM_GetChar validity: bad pair, out-of-range and junk all read as 'off'
(--tamper flips the check byte before the save: the roundtrip must FAIL.)
"""
import sys
sys.path.insert(0, "tools")
from cmlib import CM

STATE = "tools/emu_states/ck9.state"
SRAM_OFF = 0xA009 + (0xDC96 - 0xD47B)      # where $DC96 lands in the primary SRAM image


def main():
    tamper = "--tamper" in sys.argv
    cm = CM()
    cm.load(STATE)
    base = cm.snapshot()
    fails = 0

    def check(ok, msg):
        nonlocal fails
        print(("[PASS] " if ok else "[FAIL] ") + msg)
        fails += (not ok)

    def save_primary():
        for a in (0x4E8A, 0x4EA3, 0x4EB2, 0x4ECB):
            cm.call((5, a), frames=60)

    def load_primary():
        for a in (0x50DF, 0x5105, 0x5114):
            cm.call((5, a), frames=60)

    def save_backup():
        for a in (0x4F0C, 0x4F25, 0x4F34, 0x4F47):
            cm.call((5, a), frames=60)

    def load_backup():
        for a in (0x516B, 0x5184, 0x5193):
            cm.call((5, a), frames=60)

    for cid in (0, 9, 29, 75):
        cm.restore(base)
        cm.set_char(cid)
        if tamper:
            cm.wb(0xDC97, 0)
        save_primary()
        cm.wb(0xDC96, 0); cm.wb(0xDC97, 0)
        load_primary()
        check(cm.rb(0xDC96) == cid + 1 and cm.rb(0xDC97) == (cid + 1) ^ 0xA5,
              f"primary save/load keeps character {cid} ($DC96={cm.rb(0xDC96)}, $DC97={cm.rb(0xDC97):02X})")
        cm.restore(base)
        cm.set_char(cid)
        save_backup()
        cm.wb(0xDC96, 0); cm.wb(0xDC97, 0)
        load_backup()
        check(cm.rb(0xDC96) == cid + 1, f"backup save/load keeps character {cid}")

    cm.restore(base)
    cm.set_char(20)
    save_primary()
    r = cm.call((5, 0x512D), frames=60)
    check(bool(r["F"] & 0x80), "verify (05:512D) accepts the freshly saved block")
    s = bytearray(cm.sram(1))      # rst $10 $81 = primary SRAM bank 1
    check(s[SRAM_OFF - 0xA000] == 21, f"SRAM image holds id+1 at ${SRAM_OFF:04X}")
    # corrupt that one SRAM byte, as a real save would after a bit flip
    m = cm.pb.memory
    m[0x0000] = 0x0A; m[0x4000] = 1
    m[SRAM_OFF] = 0x55
    m[0x0000] = 0x00
    r = cm.call((5, 0x512D), frames=60)
    check(not (r["F"] & 0x80), "...and verify REJECTS the block once that byte differs (checksum covers $DC96)")

    # CM_GetChar validity
    NUM = sum(1 for _ in open('tools/character_mode/roster_index.tsv')) - 1
    cm.restore(base)
    for v, chk, want, why in ((21, 21 ^ 0xA5, 21, "valid pair"),
                              (21, 0, 0, "wrong check byte"),
                              (NUM + 1, (NUM + 1) ^ 0xA5, 0, f"out of range (id {NUM})"),
                              (0, 0xA5, 0, "off"),
                              (0xFF, 0xFF ^ 0xA5, 0, "junk 0xFF")):
        cm.wb(0xDC96, v); cm.wb(0xDC97, chk)
        r = cm.call("CM_GetChar", frames=30)
        check(r["A"] == want and bool(r["F"] & 0x80) == (want == 0),
              f"CM_GetChar: {why} -> a={r['A']} (want {want}), Z={bool(r['F'] & 0x80)}")
    print("RESULT:", "FAIL" if fails else "ALL PASS", f"({fails} failed)")
    sys.exit(1 if fails else 0)


main()
