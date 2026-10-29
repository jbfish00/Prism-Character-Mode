#!/usr/bin/env python3
"""Picker portraits for Prism (2026-10-28): one 56x56, 4-colour GBC pic per selectable character.

Sources, in order (credits: CREDITS.md):
  1. Polished Crystal's own trainer pic (~/src-donors/gbc-art/polishedcrystal/gfx/trainers/<name>.png + .pal):
     native GBC art, used as is (4 shades -> white / pal light / pal dark / black).
  2. ROWE's front pic for the character (src/data/characters.h .trainerFrontPic -> front_pic_tables.h ->
     graphics/trainers.h -> the PNG): a 64x64 GBA pic, background (index 0) -> white, cropped to the figure,
     scaled to fit 56x56 (only when larger), and reduced to white + black + two fitted mid-tones.

Writes art/portraits/<id>.2bpp (49 tiles, row-major), <id>.pal (4 x RGB555), contact.png and manifest.json
{id: {name, source}}, plus tools/character_mode/portraits.asm (the per-character table in bank 119 at $46A0
and the pics in banks $79-$7F, 20 per bank). Characters without a source get none: the picker leaves the
portrait area blank for them.
"""
import json
import os
import re
import struct
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = REPO / "art/portraits"
ASM = HERE / "portraits.asm"
FIRST_BANK, PER_BANK, NUM_CHARS = 0x79, 20, 152
PC = Path.home() / "src-donors/gbc-art/polishedcrystal/gfx/trainers"
ROWE = Path("/home/jbfish00/Documents/Pokemon Rowe Alteration")
SIZE = 56
PC_ALIAS = {"Lt. Surge": "lt_surge"}


def key(n):
    return PC_ALIAS.get(n, n.lower().replace(" ", "_").replace(".", "").replace("'", ""))


def rowe_pngs():
    """character name -> ROWE front pic PNG."""
    ch = (ROWE / "src/data/characters.h").read_text()
    names = dict(re.findall(r'static const u8 (sName_\w+)\[\] = _\("([^"]*)"\);', ch))
    pic_of = {}
    for m in re.finditer(r"\.name = (sName_\w+),.*?\.trainerFrontPic = (\w+),", ch, re.S):
        pic_of[names.get(m.group(1))] = m.group(2)
    tables = (ROWE / "src/data/trainer_graphics/front_pic_tables.h").read_text()
    sym = dict(re.findall(r"TRAINER_SPRITE\((\w+), (gTrainerFrontPic_\w+),", tables))
    gfx = (ROWE / "src/data/graphics/trainers.h").read_text()
    path = dict(re.findall(r'const u32 (gTrainerFrontPic_\w+)\[\] = INCBIN_U32\("([^"]+)"\);', gfx))
    out = {}
    for name, pic in pic_of.items():
        s = sym.get(pic.replace("TRAINER_PIC_", ""))
        p = path.get(s) if s else None
        if p:
            png = ROWE / re.sub(r"\.4bpp(\.lz)?$", ".png", p)
            if png.is_file():
                out[name] = png
    return out


def rgb555(c):
    r, g, b = c
    return (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)


def from_pc(name):
    png, pal = PC / (key(name) + ".png"), PC / (key(name) + ".pal")
    im = Image.open(png).convert("L")
    assert im.size == (SIZE, SIZE), (name, im.size)
    cols = [tuple(int(x) for x in re.findall(r"\d+", l)[:3]) for l in pal.read_text().splitlines() if "RGB" in l]
    assert len(cols) == 2, (name, cols)
    shades = sorted(set(im.getdata()), reverse=True)        # light -> dark
    assert len(shades) <= 4, (name, shades)
    lut = {v: i for i, v in enumerate([255, 170, 85, 0])}
    idx = [lut[min(lut, key=lambda s: abs(s - v))] for v in im.getdata()]
    pal4 = [(31, 31, 31)] + cols + [(0, 0, 0)]               # Polished Crystal .pal is 0-31 per channel
    return idx, [r | (g << 5) | (b << 10) for r, g, b in pal4]


def from_gba(png):
    im = Image.open(png)
    assert im.mode == "P", png
    pal = im.getpalette()[:48]
    w, h = im.size
    px = list(im.getdata())
    rgb = Image.new("RGB", (w, h), (255, 255, 255))
    for i, v in enumerate(px):
        if v:
            rgb.putpixel((i % w, i // w), tuple(pal[v * 3:v * 3 + 3]))
    mask = Image.new("L", (w, h), 0)
    mask.putdata([255 if v else 0 for v in px])
    box = mask.getbbox()
    rgb, mask = rgb.crop(box), mask.crop(box)
    bw, bh = rgb.size
    if bw > SIZE or bh > SIZE:
        f = min(SIZE / bw, SIZE / bh)
        nw, nh = max(1, round(bw * f)), max(1, round(bh * f))
        rgb, mask = rgb.resize((nw, nh), Image.LANCZOS), mask.resize((nw, nh), Image.LANCZOS)
        bw, bh = nw, nh
    canvas = Image.new("RGB", (SIZE, SIZE), (255, 255, 255))
    cm = Image.new("L", (SIZE, SIZE), 0)
    x0, y0 = (SIZE - bw) // 2, SIZE - bh                     # centred, standing on the bottom edge
    canvas.paste(rgb, (x0, y0))
    cm.paste(mask, (x0, y0))
    fig = [(c, m) for c, m in zip(canvas.getdata(), cm.getdata())]
    lum = lambda c: 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    body = [c for c, m in fig if m >= 128 and 40 < lum(c) < 235]
    # two mid-tones: k-means (k=2) on the figure's non-outline colours, seeded light / dark
    body.sort(key=lum)
    cents = [body[len(body) * 3 // 4], body[len(body) // 4]] if body else [(200, 160, 120), (90, 70, 60)]
    for _ in range(12):
        grp = [[], []]
        for c in body:
            grp[min((0, 1), key=lambda k: sum((a - b) ** 2 for a, b in zip(c, cents[k])))].append(c)
        cents = [tuple(sum(ch) // len(g) for ch in zip(*g)) if g else cents[k] for k, g in enumerate(grp)]
    if lum(cents[0]) < lum(cents[1]):
        cents.reverse()
    pal4 = [(248, 248, 248), cents[0], cents[1], (16, 16, 16)]
    idx = []
    for c, m in fig:
        if m < 128:
            idx.append(0)
        else:
            idx.append(min(range(1, 4), key=lambda k: sum((a - b) ** 2 for a, b in zip(c, pal4[k]))))
    return idx, [rgb555(c) for c in pal4]


def to_2bpp(idx):
    out = bytearray()
    for ty in range(7):
        for tx in range(7):
            for y in range(8):
                lo = hi = 0
                for x in range(8):
                    v = idx[(ty * 8 + y) * SIZE + tx * 8 + x]
                    lo |= (v & 1) << (7 - x)
                    hi |= (v >> 1) << (7 - x)
                out += bytes((lo, hi))
    return bytes(out)


def emit_asm(man):
    ids = sorted(man)
    nrows = len([l for l in (HERE / "selectable.tsv").read_text().splitlines()[1:] if l.strip()])
    assert nrows == NUM_CHARS, nrows
    where = {cid: (FIRST_BANK + n // PER_BANK, 0x4000 + (n % PER_BANK) * 784) for n, cid in enumerate(ids)}
    assert max(b for b, _ in where.values()) <= 0x7F, "out of free banks"
    L = ["; generated by tools/character_mode/build_portraits.py -- do not edit",
         "; Picker portraits: per character id (0..%d) db bank (0 = none), dw pic, db 0; then 4 x RGB555 each." % (NUM_CHARS - 1),
         'SECTION "PortraitTable", ROMX[$46A0], BANK[119]', "PortraitPtrs::"]
    for cid in range(NUM_CHARS):
        b, a = where.get(cid, (0, 0))
        L.append("\tdb $%02X\n\tdw $%04X\n\tdb 0" % (b, a))
    L.append("PortraitPals::")
    for cid in range(NUM_CHARS):
        pal = struct.unpack("<4H", (OUT / ("%d.pal" % cid)).read_bytes()) if cid in man else (0x7FFF, 0, 0, 0)
        L.append("\tdw " + ", ".join("$%04X" % v for v in pal))
    for n in range(0, len(ids), PER_BANK):
        L.append('SECTION "PortraitPics%d", ROMX[$4000], BANK[$%02X]' % (n // PER_BANK, FIRST_BANK + n // PER_BANK))
        for cid in ids[n:n + PER_BANK]:
            L.append('\tINCBIN "art/portraits/%d.2bpp" ; %s' % (cid, man[cid]["name"]))
    ASM.write_text("\n".join(L) + "\n")


def main():
    rows = [l.split("\t") for l in (HERE / "selectable.tsv").read_text().splitlines()]
    h = rows[0]
    sel = [(int(r[0]), r[1]) for r in rows[1:] if r[h.index("selectable")] == "1"]
    rowe = rowe_pngs()
    OUT.mkdir(parents=True, exist_ok=True)
    man, sheet = {}, Image.new("RGB", (SIZE * 12, SIZE * ((len(sel) + 11) // 12)), (90, 90, 90))
    for n, (cid, name) in enumerate(sel):
        if (PC / (key(name) + ".png")).is_file():
            idx, pal, src = *from_pc(name), "polishedcrystal:" + key(name)
        elif name in rowe:
            idx, pal, src = *from_gba(rowe[name]), "rowe:" + rowe[name].name
        else:
            continue
        (OUT / ("%d.2bpp" % cid)).write_bytes(to_2bpp(idx))
        (OUT / ("%d.pal" % cid)).write_bytes(struct.pack("<4H", *pal))
        man[cid] = {"name": name, "source": src}
        cols = [((p & 31) << 3, ((p >> 5) & 31) << 3, ((p >> 10) & 31) << 3) for p in pal]
        im = Image.new("RGB", (SIZE, SIZE))
        im.putdata([cols[v] for v in idx])
        sheet.paste(im, ((n % 12) * SIZE, (n // 12) * SIZE))
    sheet.save(OUT / "contact.png")
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1))
    emit_asm(man)
    missing = [name for cid, name in sel if cid not in man]
    print("portraits %d / %d selectable (polishedcrystal %d, rowe %d); missing: %s" % (
        len(man), len(sel), sum(v["source"].startswith("polished") for v in man.values()),
        sum(v["source"].startswith("rowe") for v in man.values()), missing))


if __name__ == "__main__":
    main()
