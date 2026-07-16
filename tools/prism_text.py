#!/usr/bin/env python3
"""Decode Pokemon Prism's Huffman-compressed game text.

Reverse-engineered from the ROM (v0.95 build 254 Hotfix 5, sha1 in rom.sha1):

- Text strings are text-command scripts (dispatch loop at 00:3266). Command
  byte $03 = "Huffman text": the compressed bitstream directly follows the
  $03 byte, decoded by the routine at 35:4E14 (file 0xD4E14).
- Decoding walks a 256-byte node-transition table at 35:4E9A (file 0xD4E9A):
  index = index*2 + bit (MSB-first bits); table value < $70 -> next index,
  >= $70 -> leaf.
- Leaf post-processing (35:4F8C): $78-$7B -> value-$20; $BC-$CF -> value-$78;
  $7D -> 4 raw bits index a 16-entry literal table (35:4F74);
  $7C -> 6 raw bits range-decoded through a delta table (35:4F83).
- Decoded chars use the standard Gen 2 charmap; $50 '@' terminates.

Usage:
  prism_text.py ROM --at 0xF602            # decode one string at file offset
  prism_text.py ROM --at 0xF601 --script   # decode a text-command script
                                           # (handles the leading $03)
  prism_text.py ROM --search "used the"    # brute-scan: try decoding at every
                                           # offset after a $03 byte, report hits
"""
import argparse
import re
import sys

NODE_TABLE = 0xD4E9A
RAW16_TABLE = 0xD4F74
DELTA_TABLE = 0xD4F83

# standard pokecrystal charmap subset
CH = {0x4E: '\n', 0x4F: '\n', 0x51: '\n\n', 0x55: '\n', 0x56: '…',
      0x57: '', 0x58: '', 0x5F: '',
      0x52: '<PLAYER>', 0x53: '<RIVAL>', 0x54: 'POKé', 0x5D: '<TRAINER>',
      0x59: '<TARGET>', 0x5A: '<USER>', 0x5B: 'PC', 0x5C: 'TM', 0x5E: 'ROCKET',
      0x4A: 'PKMN', 0x49: '#', 0x7F: ' ',
      0x9A: '(', 0x9B: ')', 0x9C: ':', 0x9D: ';', 0x9E: '[', 0x9F: ']',
      0xD0: "'d", 0xD1: "'l", 0xD2: "'m", 0xD3: "'r", 0xD4: "'s",
      0xD5: "'t", 0xD6: "'v",
      0xE0: "'", 0xE1: 'PK', 0xE2: 'MN', 0xE3: '-', 0xE6: '?', 0xE7: '!',
      0xE8: '.', 0xE9: '&', 0xEA: 'é', 0xEF: '♂', 0xF5: '♀',
      0xF0: '¥', 0xF1: '×', 0xF2: '.', 0xF3: '/', 0xF4: ','}
for _i in range(26):
    CH[0x80 + _i] = chr(ord('A') + _i)
    CH[0xA0 + _i] = chr(ord('a') + _i)
for _i in range(10):
    CH[0xF6 + _i] = chr(ord('0') + _i)


class Bits:
    def __init__(self, rom, off):
        self.rom, self.off, self.n, self.cur = rom, off, 0, 0

    def bit(self):
        if self.n == 0:
            self.cur = self.rom[self.off]
            self.off += 1
            self.n = 8
        self.n -= 1
        b = (self.cur >> 7) & 1
        self.cur = (self.cur << 1) & 0xFF
        return b

    def bits(self, n):
        v = 0
        for _ in range(n):
            v = (v << 1) | self.bit()
        return v


def leaf_char(rom, a, bits):
    """Port of the leaf handler at 35:4F8C."""
    if a < 0x78:
        return a
    if a < 0x7C:
        return a - 0x20
    if a == 0x7D:
        return rom[RAW16_TABLE + bits.bits(4)]
    if a == 0x7C:
        v = bits.bits(6)
        hl = DELTA_TABLE
        while True:
            hl += 1
            v -= rom[hl]
            hl += 1
            if v < 0:
                break
        return (v + rom[hl]) & 0xFF
    if a < 0xBC:
        return a
    if a < 0xD0:
        return a - 0x78
    return a


def decode_string(rom, off, maxchars=1000):
    """Huffman-decode one string starting at file offset `off` (the byte
    after the $03 command). Returns (text, chars, end_off)."""
    bits = Bits(rom, off)
    out, raw = [], []
    for _ in range(maxchars):
        idx = 0
        while True:
            idx = (idx * 2 + bits.bit()) & 0xFF
            a = rom[NODE_TABLE + idx]
            if a >= 0x70:
                break
            idx = a
        ch = leaf_char(rom, a, bits)
        raw.append(ch)
        if ch == 0x50:
            break
        out.append(CH.get(ch, f'[{ch:02X}]'))
    return "".join(out), raw, bits.off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rom")
    ap.add_argument("--at", help="file offset (hex ok) of bitstream start")
    ap.add_argument("--script", action="store_true",
                    help="offset points at a text script; expect leading $03")
    ap.add_argument("--search", help="brute-scan ROM for a decoded substring")
    ap.add_argument("--icase", action="store_true")
    args = ap.parse_args()
    rom = open(args.rom, "rb").read()

    if args.at:
        off = int(args.at, 0)
        if args.script:
            if rom[off] != 0x03:
                sys.exit(f"no $03 text command at 0x{off:06X} "
                         f"(found ${rom[off]:02X})")
            off += 1
        text, raw, end = decode_string(rom, off)
        print(f"0x{off:06X}..0x{end:06X}:")
        print(text)
        return

    if args.search:
        needle = args.search.lower() if args.icase else args.search
        hits = 0
        for m in re.finditer(b"\x03", rom):
            off = m.start() + 1
            try:
                text, raw, end = decode_string(rom, off, maxchars=250)
            except IndexError:
                continue
            if raw and raw[-1] != 0x50:
                continue        # never hit a terminator: not a real string
            hay = text.lower() if args.icase else text
            if needle in hay:
                bank = m.start() // 0x4000
                inbank = m.start() % 0x4000 + (0x4000 if bank else 0)
                one = text.replace("\n", " / ")
                print(f"0x{m.start():06X} ({bank:02X}:{inbank:04X}): {one}")
                hits += 1
                if hits >= 200:
                    print("(...capped at 200 hits)")
                    break
        print(f"{hits} hits")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
