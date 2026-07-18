#!/usr/bin/env python3
"""SM83 linear disassembler, rst-aware for Prism's repurposed rst vectors.

Usage: python3 gbdis_rst.py <rom.gbc> <file_offset_hex> [count]
"""
import sys

R8 = ["b", "c", "d", "e", "h", "l", "[hl]", "a"]
R16 = ["bc", "de", "hl", "sp"]
CC = ["nz", "z", "nc", "c"]
ALU = ["add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp"]
CBOPS = ["rlc", "rrc", "rl", "rr", "sla", "sra", "swap", "srl"]


def _s8(v):
    return v - 256 if v >= 128 else v


def decode(rom, off):
    op = rom[off]
    d8 = rom[off + 1] if off + 1 < len(rom) else 0
    d16 = d8 | (rom[off + 2] << 8) if off + 2 < len(rom) else 0

    if op == 0x00: return 1, "nop"
    if op == 0x10: return 2, "stop"
    if op == 0x76: return 1, "halt"
    if op == 0xF3: return 1, "di"
    if op == 0xFB: return 1, "ei"
    if op == 0x07: return 1, "rlca"
    if op == 0x0F: return 1, "rrca"
    if op == 0x17: return 1, "rla"
    if op == 0x1F: return 1, "rra"
    if op == 0x27: return 1, "daa"
    if op == 0x2F: return 1, "cpl"
    if op == 0x37: return 1, "scf"
    if op == 0x3F: return 1, "ccf"

    hi2 = op >> 6
    if op < 0x40:
        lo3 = op & 7
        mid = (op >> 3) & 7
        if lo3 == 0:
            if op == 0x08: return 3, f"ld [${d16:04x}], sp"
            if op == 0x18: return 2, f"jr ${(off + 2 + _s8(d8)) & 0xFFFF:04x}"
            if op in (0x20, 0x28, 0x30, 0x38):
                return 2, f"jr {CC[(op >> 3) & 3]}, ${(off + 2 + _s8(d8)) & 0xFFFF:04x}"
        if lo3 == 1:
            if mid & 1: return 1, f"add hl, {R16[mid >> 1]}"
            return 3, f"ld {R16[mid >> 1]}, ${d16:04x}"
        if lo3 == 2:
            tgt = ["[bc]", "[de]", "[hl+]", "[hl-]"][mid >> 1]
            if mid & 1: return 1, f"ld a, {tgt}"
            return 1, f"ld {tgt}, a"
        if lo3 == 3:
            return 1, (f"dec {R16[mid >> 1]}" if mid & 1 else f"inc {R16[mid >> 1]}")
        if lo3 == 4: return 1, f"inc {R8[mid]}"
        if lo3 == 5: return 1, f"dec {R8[mid]}"
        if lo3 == 6: return 2, f"ld {R8[mid]}, ${d8:02x}"
    if hi2 == 1:
        return 1, f"ld {R8[(op >> 3) & 7]}, {R8[op & 7]}"
    if hi2 == 2:
        return 1, f"{ALU[(op >> 3) & 7]} {R8[op & 7]}"

    if op == 0xCB:
        cb = d8
        r = R8[cb & 7]
        if cb < 0x40: return 2, f"{CBOPS[cb >> 3]} {r}"
        n = (cb >> 3) & 7
        return 2, [f"bit {n}, {r}", f"res {n}, {r}", f"set {n}, {r}"][(cb >> 6) - 1]
    tbl = {
        0xC0: (1, "ret nz"), 0xC8: (1, "ret z"), 0xD0: (1, "ret nc"), 0xD8: (1, "ret c"),
        0xC9: (1, "ret"), 0xD9: (1, "reti"),
        0xC3: (3, f"jp ${d16:04x}"), 0xE9: (1, "jp hl"),
        0xC2: (3, f"jp nz, ${d16:04x}"), 0xCA: (3, f"jp z, ${d16:04x}"),
        0xD2: (3, f"jp nc, ${d16:04x}"), 0xDA: (3, f"jp c, ${d16:04x}"),
        0xCD: (3, f"call ${d16:04x}"),
        0xC4: (3, f"call nz, ${d16:04x}"), 0xCC: (3, f"call z, ${d16:04x}"),
        0xD4: (3, f"call nc, ${d16:04x}"), 0xDC: (3, f"call c, ${d16:04x}"),
        0xE0: (2, f"ldh [$ff{d8:02x}], a"), 0xF0: (2, f"ldh a, [$ff{d8:02x}]"),
        0xE2: (1, "ldh [c], a"), 0xF2: (1, "ldh a, [c]"),
        0xEA: (3, f"ld [${d16:04x}], a"), 0xFA: (3, f"ld a, [${d16:04x}]"),
        0xE8: (2, f"add sp, {_s8(d8)}"), 0xF8: (2, f"ld hl, sp{_s8(d8):+d}"),
        0xF9: (1, "ld sp, hl"),
        0xC6: (2, f"add a, ${d8:02x}"), 0xCE: (2, f"adc a, ${d8:02x}"),
        0xD6: (2, f"sub ${d8:02x}"), 0xDE: (2, f"sbc a, ${d8:02x}"),
        0xE6: (2, f"and ${d8:02x}"), 0xEE: (2, f"xor ${d8:02x}"),
        0xF6: (2, f"or ${d8:02x}"), 0xFE: (2, f"cp ${d8:02x}"),
        0xC1: (1, "pop bc"), 0xD1: (1, "pop de"), 0xE1: (1, "pop hl"), 0xF1: (1, "pop af"),
        0xC5: (1, "push bc"), 0xD5: (1, "push de"), 0xE5: (1, "push hl"), 0xF5: (1, "push af"),
    }
    if op in tbl:
        return tbl[op]
    if (op & 0xC7) == 0xC7:
        rst_n = op & 0x38
        # Prism-specific inline operands after certain rst vectors
        if rst_n == 0x08:
            bank = rom[off + 1]
            addr = rom[off + 2] | (rom[off + 3] << 8)
            return 4, f"rst $08 ; farcall {bank:02x}:{addr:04x}"
        if rst_n == 0x10:
            bank = rom[off + 1]
            return 2, f"rst $10 ; bank {bank:02x}"
        if rst_n == 0x18:
            return 1, "rst $18 ; AddNTimes"
        if rst_n == 0x20:
            bank = rom[off + 1]
            return 2, f"rst $20 ; farcall-to-hl {bank:02x}:xxxx"
        if rst_n == 0x28:
            b1 = rom[off + 1]
            b2 = rom[off + 2]
            return 3, f"rst $28 ; jumptable on a (operand {b1:02x}{b2:02x})"
        if rst_n == 0x30:
            return 1, "rst $30 ; CopyBytes"
        if rst_n == 0x00:
            return 1, "rst $00"
        return 1, f"rst ${rst_n:02x}"
    return 1, f"db ${op:02x} ; invalid"


def main():
    rom = open(sys.argv[1], "rb").read()
    off = int(sys.argv[2], 16)
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    for _ in range(count):
        bank = off // 0x4000
        addr = off if bank == 0 else 0x4000 + (off % 0x4000)
        n, text = decode(rom, off)
        raw = rom[off:off + n].hex()
        print(f"{off:06X}  {bank:02X}:{addr:04X}  {raw:<10}  {text}")
        off += n


if __name__ == "__main__":
    main()
