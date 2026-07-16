#!/usr/bin/env python3
"""
Search a Gen 2 (Crystal-engine) GBC ROM for ASCII text encoded with the
pokecrystal charmap (constants/charmap.asm). Ported from the GBA siblings'
search_gametext.py — the encoding table is different (Gen2 charmap, not the
Gen3 charmap ROWE/Unbound/RadicalRed share), so this is a fresh port, not a
copy-paste.

Usage:
  python3 search_gametext.py <rom.gbc> "search text" [--icase]
"""
import argparse
import sys

CHARMAP = {
    " ": 0x7F,
    "'": 0xE0,
    "-": 0xE3,
    "?": 0xE6,
    "!": 0xE7,
    ".": 0xE8,
    ",": 0xF4,
    ":": 0x9C,
    ";": 0x9D,
    "(": 0x9A,
    ")": 0x9B,
    "&": 0xE9,
    "/": 0xF3,
}
for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    CHARMAP[c] = 0x80 + i
for i, c in enumerate("abcdefghijklmnopqrstuvwxyz"):
    CHARMAP[c] = 0xA0 + i
for i, c in enumerate("0123456789"):
    CHARMAP[c] = 0xF6 + i


def encode(text, icase=False):
    if not icase:
        return bytes(CHARMAP[c] for c in text)
    # icase: build a regex-free multi-candidate search by encoding upper form;
    # caller handles case variants explicitly since GBC text is single-case
    # per glyph (no case-folding at the byte level).
    return bytes(CHARMAP[c] for c in text)


def find_all(hay, needle):
    hits = []
    start = 0
    while True:
        idx = hay.find(needle, start)
        if idx < 0:
            break
        hits.append(idx)
        start = idx + 1
    return hits


def bank_addr(file_off):
    BANK = 0x4000
    bank = file_off // BANK
    if bank == 0:
        return 0, file_off
    addr = 0x4000 + (file_off % BANK)
    return bank, addr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("text")
    ap.add_argument("--icase", action="store_true",
                     help="also try Titlecase and UPPERCASE variants")
    ap.add_argument("--context", type=int, default=16,
                     help="bytes of context to show around each hit")
    args = ap.parse_args()

    rom = open(args.rom, "rb").read()

    variants = {args.text}
    if args.icase:
        variants.add(args.text.upper())
        variants.add(args.text.lower())
        variants.add(args.text.capitalize())

    seen_offsets = set()
    for variant in variants:
        try:
            needle = encode(variant)
        except KeyError as e:
            print(f"skip variant {variant!r}: no charmap entry for {e}", file=sys.stderr)
            continue
        hits = find_all(rom, needle)
        for off in hits:
            if off in seen_offsets:
                continue
            seen_offsets.add(off)
            bank, addr = bank_addr(off)
            ctx = rom[max(0, off - args.context):off + len(needle) + args.context]
            print(f"variant={variant!r} file_off=0x{off:06X} bank={bank:02X} addr=0x{addr:04X} "
                  f"raw_ctx={ctx.hex()}")

    if not seen_offsets:
        print("No matches found.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
