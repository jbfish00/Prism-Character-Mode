#!/usr/bin/env python3
"""Operand-masked SM83 code matcher: find pokecrystal routines inside Prism.

Prism was recompiled/relinked, so exact byte search fails on any routine that
contains an address operand (16-bit immediates and BANK() constants all
shifted). But the opcode *skeleton* of an unmodified routine survives a
relink. This tool:

 1. pulls a labeled routine's bytes out of the built pokecrystal donor ROM
    (label -> next top-level label, via pokecrystal.sym),
 2. linear-decodes it (SM83 opcode lengths) and builds a byte-regex where
    - 16-bit immediate operands (jp/call/ld rr,d16/ld [a16],a/...) -> wildcard
    - `ld a, d8` operands -> wildcard (usually BANK(...) constants)
    - everything else (opcodes, jr offsets, cp/and/or constants, ldh hw regs,
      CB-prefixed ops) stays literal,
 3. scans the target ROM with overlapping N-instruction chunks and reports
    clusters of in-order chunk hits (so a partially modified routine still
    localizes even when no single full-routine match exists).

Usage:
  match_code.py --donor pokecrystal.gbc --sym pokecrystal.sym \
      --target prism.gbc LabelName [LabelName ...] [--chunk 12] [--stride 4]
"""
import argparse
import bisect
import re
import sys

# opcodes with a 16-bit immediate operand (wildcard both operand bytes)
IMM16 = {0x01, 0x08, 0x11, 0x21, 0x31,
         0xC2, 0xC3, 0xC4, 0xCA, 0xCC, 0xCD,
         0xD2, 0xD4, 0xDA, 0xDC, 0xEA, 0xFA}
# opcodes with an 8-bit immediate operand
IMM8 = {0x06, 0x0E, 0x16, 0x1E, 0x26, 0x2E, 0x36, 0x3E,
        0x18, 0x20, 0x28, 0x30, 0x38,
        0xC6, 0xCE, 0xD6, 0xDE, 0xE6, 0xEE, 0xF6, 0xFE,
        0xE0, 0xF0, 0xE8, 0xF8}
# 8-bit-immediate opcodes whose operand is masked anyway:
#   0x3E ld a,d8 — overwhelmingly BANK(...) constants in farcall/rombank code,
#   and banks moved in Prism's relink.
IMM8_MASKED = {0x3E}
MASK_JR = False


def ilen(rom, off):
    op = rom[off]
    if op == 0xCB:
        return 2
    if op in IMM16:
        return 3
    if op in IMM8:
        return 2
    return 1


def load_sym(path):
    """Return sorted list of (fileoff, name) for top-level ROM labels."""
    syms = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        m = re.match(r"([0-9a-fA-F]{2,3}):([0-9a-fA-F]{4})\s+(\S+)", line)
        if not m:
            continue
        bank, addr, name = int(m.group(1), 16), int(m.group(2), 16), m.group(3)
        if addr >= 0x8000:      # RAM symbol, not ROM
            continue
        fileoff = addr if bank == 0 else bank * 0x4000 + (addr - 0x4000)
        syms.append((fileoff, name))
    syms.sort(key=lambda t: t[0])
    return syms


def routine_bytes(rom, syms, label):
    """Bytes from `label` to the next *top-level* (non-.local) symbol."""
    offs = [s[0] for s in syms]
    idx = next((i for i, (_, n) in enumerate(syms) if n == label), None)
    if idx is None:
        raise SystemExit(f"label {label!r} not in sym file")
    start = syms[idx][0]
    end = None
    for off, name in syms[idx + 1:]:
        if off > start and "." not in name:
            end = off
            break
    if end is None:
        end = start + 0x400
    return start, rom[start:end]


def skeleton_regex(code, i0, i1, insn_offs):
    """Regex for instructions [i0:i1) of decoded routine; returns (regex, nlit)."""
    pat = []
    nlit = 0
    for i in range(i0, i1):
        off = insn_offs[i]
        op = code[off]
        pat.append(re.escape(bytes([op])))
        nlit += 1
        if op == 0xCB:
            pat.append(re.escape(bytes([code[off + 1]])))
            nlit += 1
        elif op in IMM16:
            pat.append(b"..")
        elif op in IMM8:
            operand = code[off + 1]
            masked = op in IMM8_MASKED
            # ldh with operand >= $80 is an HRAM *variable* (relocatable in a
            # relink), not a fixed hardware register — mask it
            if op in (0xE0, 0xF0) and operand >= 0x80:
                masked = True
            if MASK_JR and op in (0x18, 0x20, 0x28, 0x30, 0x38):
                masked = True
            if masked:
                pat.append(b".")
            else:
                pat.append(re.escape(bytes([operand])))
                nlit += 1
    return b"".join(pat), nlit


def match_routine(donor, target, syms, label, chunk, stride, min_lit):
    start, code = routine_bytes(donor, syms, label)
    # linear decode
    insn_offs = []
    off = 0
    while off < len(code) and off + ilen(code, off) <= len(code):
        insn_offs.append(off)
        off += ilen(code, off)
    print(f"\n=== {label}: donor file off 0x{start:06X}, "
          f"{len(code)} bytes, {len(insn_offs)} insns ===")

    hits = []   # (donor_chunk_byteoff, target_off)
    nchunks = 0
    for i0 in range(0, max(1, len(insn_offs) - chunk + 1), stride):
        i1 = min(i0 + chunk, len(insn_offs))
        pat, nlit = skeleton_regex(code, i0, i1, insn_offs)
        if nlit < min_lit:
            continue
        nchunks += 1
        for m in re.finditer(pat, target, re.DOTALL):
            hits.append((insn_offs[i0], m.start()))

    if not hits:
        print(f"  no chunk hits ({nchunks} chunks tried)")
        return

    # cluster: group hits by (target_off - donor_chunk_off) delta, tolerant
    # of small drift from inserted/removed code
    deltas = {}
    for doff, toff in hits:
        base = toff - doff
        key = next((k for k in deltas if abs(k - base) <= 64), None)
        if key is None:
            deltas[base] = []
            key = base
        deltas[key].append((doff, toff))
    ranked = sorted(deltas.items(), key=lambda kv: -len(kv[1]))
    for base, group in ranked[:6]:
        cover = len({d for d, _ in group})
        first = min(t for _, t in group)
        bank = first // 0x4000
        inbank = first % 0x4000 + (0x4000 if bank else 0)
        print(f"  candidate 0x{first:06X} (bank {bank:02X}:{inbank:04X}): "
              f"{cover}/{nchunks} chunks in-order (delta 0x{base:X})")
    stray = len(hits) - sum(len(g) for _, g in ranked[:6])
    if stray:
        print(f"  (+{stray} stray hits outside top clusters)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donor", required=True)
    ap.add_argument("--sym", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--chunk", type=int, default=12)
    ap.add_argument("--stride", type=int, default=4)
    ap.add_argument("--min-lit", type=int, default=10)
    ap.add_argument("--mask-jr", action="store_true")
    ap.add_argument("labels", nargs="+")
    args = ap.parse_args()
    global MASK_JR
    MASK_JR = args.mask_jr

    donor = open(args.donor, "rb").read()
    target = open(args.target, "rb").read()
    syms = load_sym(args.sym)
    for label in args.labels:
        match_routine(donor, target, syms, label,
                      args.chunk, args.stride, args.min_lit)


if __name__ == "__main__":
    main()
