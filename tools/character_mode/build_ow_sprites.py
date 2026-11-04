#!/usr/bin/env python3
"""Player overworld sprite per character for Prism (2026-11-04): the player walks as the chosen character.

Every sheet is native Game Boy Color art (16x96, 4 shades, Crystal's walking-sprite layout: down / up / side
standing, then down / up / side walking). Sources, in order (credits: CREDITS.md):
  1. the character's own sprite in Polished Crystal (~/src-donors/gbc-art/polishedcrystal/gfx/sprites),
  2. ... in Crystal Inheritance's tree (~/src-donors/ci-cm-build/gfx/sprites),
  3. ... in pokecrystal (tools/pokecrystal_donor/gfx/sprites),
  4. otherwise a STAND-IN: the nearest native GBC sprite (a trainer class or a look-alike) in a palette that
     matches the character (STAND_IN below). A 32x32 DS/GBA sheet shrunk to 16x16 was tried first and
     rejected: at 4 shades it is an unreadable blob (2026-11-04, scratch comparisons).
A standing-only sheet (16x48) gets its standing frames repeated as walking frames.

Palettes are Prism's OBJ palettes 1-7 (blue, green, brown, red, silver, yellow, purple; OBJ palette 0 is the
player's own, set by Prism's outfit code). The donors' palette names are mapped onto those.

Writes art/overworld/<id>.2bpp (24 tiles, uncompressed, what the game decompresses to), manifest.json
{id: {name, sprite, source, palette, kind}}, contact.png, and tools/character_mode/ow_sprites.asm:
  * OWArtTable (bank 118 $7400): per character id db bank (0 = none), dw LZ address, db palette (1..7)
  * the LZ sheets (pokecrystal LZ, tools/gblz.py; every one round-trips) deduplicated, packed into bank $7F
    and then the free tail of bank $78.
"""
import json
import re
import struct
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "tools"))
import gblz  # noqa: E402

OUT = REPO / "art/overworld"
ASM = HERE / "ow_sprites.asm"
NUM_CHARS = 152
TABLE_ADDR = 0x7400
PACK = [(0x7F, 0x4000, 0x8000), (0x78, 0x5800, 0x8000)]     # (bank, first free, end)
DONORS = [
    ("polishedcrystal", Path.home() / "src-donors/gbc-art/polishedcrystal"),
    ("crystal-inheritance", Path.home() / "src-donors/ci-cm-build"),
    ("pokecrystal", REPO / "tools/pokecrystal_donor"),
]
# donor palette name -> Prism OBJ palette
PAL = {"RED": 4, "PINK": 4, "ORANGE": 4, "BLUE": 1, "TEAL": 1, "AZURE": 1, "GREEN": 2, "BROWN": 3, "TAN": 3,
       "BLACK": 3, "GRAY": 5, "SILVER": 5, "WHITE": 5, "EMOTE": 5, "YELLOW": 6, "PURPLE": 7}
PNAME = {1: "blue", 2: "green", 3: "brown", 4: "red", 5: "silver", 6: "yellow", 7: "purple"}
P = {v: k for k, v in PNAME.items()}

# the character's own sprite under another file name
ALIAS = {"Ethan": "chris", "Lt. Surge": "surge", "Silver": "rival"}
# stand-ins: character -> (donor sprite, palette). Chosen by look (outfit, hair, role).
STAND_IN = {
    "Ash": ("red", "blue"), "Gary": ("blue", "purple"), "Birch": ("elm", "brown"), "Ritchie": ("chris", "green"),
    "Samson Oak": ("oak", "red"), "Sycamore": ("elm", "blue"),
    "Acerola": ("twin", "purple"), "Adaman": ("ace_trainer_m", "blue"), "Archie": ("sailor", "blue"),
    "Bede": ("psychic", "purple"), "Beni": ("ninja", "blue"), "Bertha": ("granny", "brown"),
    "Brandon": ("hiker", "brown"), "Brawly": ("cool_dude", "blue"), "Brendan": ("youngster", "red"),
    "Byron": ("hiker", "brown"), "Calem": ("ace_trainer_m", "red"), "Candice": ("skier", "green"),
    "Chloe": ("schoolgirl", "brown"), "Crasher Wake": ("black_belt", "blue"), "Cyrus": ("gentleman", "blue"),
    "Dahlia": ("beauty", "red"), "Dawn": ("lass", "red"), "Elio": ("chris", "blue"), "Fantina": ("beauty", "purple"),
    "Flint": ("firebreather", "red"), "Gardenia": ("picnicker", "green"), "Gladion": ("rocker", "brown"),
    "Goh": ("youngster", "blue"), "Greta": ("battle_girl", "red"), "Hau": ("camper", "green"),
    "Hilbert": ("schoolboy", "blue"), "Hilda": ("ace_trainer_f", "blue"), "Hop": ("youngster", "purple"),
    "Ingo": ("gentleman", "silver"), "Iono": ("cute_girl", "purple"), "Irida": ("skier", "red"),
    "Juan": ("gentleman", "purple"), "Jupiter": ("rocket_girl", "purple"), "Kabu": ("veteran_m", "red"),
    "Kiawe": ("beach_guy", "red"), "Korrina": ("battle_girl", "blue"), "Lana": ("lass", "blue"),
    "Liza": ("twin", "red"), "Lucas": ("schoolboy", "red"), "Lucian": ("gentleman", "red"),
    "Lucy": ("ace_trainer_f", "purple"), "Lusamine": ("lady", "yellow"), "Marnie": ("cute_girl", "red"),
    "Mars": ("rocket_girl", "red"), "Maxie": ("gentleman", "brown"), "May": ("picnicker", "red"),
    "N": ("ace_trainer_m", "green"), "Noland": ("cool_dude", "brown"), "Paul": ("rocker", "purple"),
    "Penny": ("schoolgirl", "yellow"), "Phoebe": ("picnicker", "purple"), "Roark": ("hiker", "red"),
    "Roxanne": ("schoolgirl", "blue"), "Saturn": ("rocket", "blue"), "Selene": ("lass", "green"),
    "Serena": ("ace_trainer_f", "red"), "Shauna": ("picnicker", "yellow"), "Shauntal": ("teacher", "purple"),
    "Spenser": ("gramps", "green"), "Tate": ("youngster", "brown"), "Volkner": ("cool_dude", "yellow"),
    "Volo": ("sage", "yellow"), "Wallace": ("gentleman", "blue"), "Wally": ("youngster", "green"),
    "Wattson": ("pokefan_m", "yellow"), "Winona": ("bird_keeper", "blue"), "Zisu": ("battle_girl", "yellow"),
    "Zoey": ("cute_girl", "brown"), "Archer": None, "Karen": None,
}


def key(n):
    return n.lower().replace(" ", "_").replace(".", "").replace("'", "")


def donor_index():
    """donor -> {file stem: (png path, palette name or None)}."""
    out = {}
    for dn, root in DONORS:
        pal_of = {}
        spr = root / "data/sprites/sprites.asm"
        gfx = root / "gfx/sprites.asm"
        if spr.is_file() and gfx.is_file():
            lab_pal = dict(re.findall(r"overworld_sprite (\w+)SpriteGFX, (?:\d+, )?\w+, PAL_OW_(\w+)", spr.read_text()))
            for lab, stem in re.findall(r"(\w+)SpriteGFX::\s*INCBIN \"gfx/sprites/(\w+)\.2bpp", gfx.read_text()):
                if lab in lab_pal:
                    pal_of[stem] = lab_pal[lab]
        if dn == "pokecrystal":
            s = (root / "data/sprites/sprites.asm").read_text()
            for lab, pal in re.findall(r"overworld_sprite (\w+)SpriteGFX, \d+, \w+, PAL_OW_(\w+)", s):
                stem = re.sub(r"(?<!^)(?=[A-Z])", "_", lab).lower()
                pal_of.setdefault(stem, pal)
        out[dn] = {p.stem: (p, pal_of.get(p.stem)) for p in sorted((root / "gfx/sprites").glob("*.png"))}
    return out


def sheet_2bpp(png):
    im = Image.open(png).convert("L")
    w, h = im.size
    assert w == 16 and h in (48, 96), (png, im.size)
    shades = sorted(set(im.getdata()), reverse=True)
    assert len(shades) <= 4, (png, shades)
    lut = {255: 0, 170: 1, 85: 2, 0: 3}
    px = [lut[min(lut, key=lambda s: abs(s - v))] for v in im.getdata()]
    if h == 48:
        px = px + px                                   # standing only: walking frames = standing frames
    out = bytearray()
    for ty in range(12):
        for tx in range(2):
            for y in range(8):
                lo = hi = 0
                for x in range(8):
                    v = px[(ty * 8 + y) * 16 + tx * 8 + x]
                    lo |= (v & 1) << (7 - x)
                    hi |= (v >> 1) << (7 - x)
                out += bytes((lo, hi))
    return bytes(out), h == 48


def find(idx, stem, prefer=None):
    order = [d for d, _ in DONORS]
    if prefer:
        order.remove(prefer); order.insert(0, prefer)
    for dn in order:
        if stem in idx[dn]:
            return dn, *idx[dn][stem]
    return None


def bank78_free_from():
    """Bank $78 holds the roster bitmaps from $4000 (rosters.asm, $1300 bytes in 2026-11). The sheets start at a
    FIXED $5800 so a rebuild never moves them; refuse to build if the rosters ever grow past that."""
    data = (HERE / "rosters.asm").read_text()
    n = sum(len(re.findall(r"\$[0-9A-Fa-f]{2}", l)) for l in data.splitlines() if l.strip().startswith("db"))
    assert 0x4000 + n <= 0x5800, ("rosters reach", hex(0x4000 + n))
    return 0x5800


def main():
    rows = [l.split("\t") for l in (HERE / "selectable.tsv").read_text().splitlines()]
    h = rows[0]
    allrows = [(int(r[0]), r[1]) for r in rows[1:]]
    assert len(allrows) == NUM_CHARS, len(allrows)
    sel = [(int(r[0]), r[1]) for r in rows[1:] if r[h.index("selectable")] == "1"]
    idx = donor_index()
    OUT.mkdir(parents=True, exist_ok=True)
    man, missing = {}, []
    for cid, name in sel:
        st = STAND_IN.get(name)
        own = ALIAS.get(name, key(name))
        hit = None if (name in STAND_IN and st is not None) else find(idx, own)
        if hit:
            dn, png, palname = hit
            kind = "own"
            pal = PAL.get(palname or "", 4)
        elif st:
            dn, png, _ = find(idx, st[0]) or (None, None, None)
            assert png, (name, st)
            kind, pal = "stand-in", P[st[1]]
        else:
            missing.append(name)
            continue
        raw, standing = sheet_2bpp(png)
        if standing:
            kind += " (standing frames only)"
        (OUT / f"{cid}.2bpp").write_bytes(raw)
        man[cid] = {"name": name, "sprite": png.stem, "source": dn, "palette": PNAME[pal], "kind": kind}
    # pack: dedupe identical sheets, LZ each, fill bank $7F then bank $78's tail
    PACK[1] = (0x78, bank78_free_from(), 0x8000)
    blobs, where, place = {}, {}, []
    for cid in sorted(man):
        raw = (OUT / f"{cid}.2bpp").read_bytes()
        if raw not in blobs:
            lz = gblz.compress(raw)
            assert gblz.decompress(lz, 0)[0] == raw, cid
            blobs[raw] = (lz, cid)
    cursor = [list(p) for p in PACK]
    for raw, (lz, first) in blobs.items():
        for c in cursor:
            if c[1] + len(lz) <= c[2]:
                place.append((c[0], c[1], first, lz)); where[raw] = (c[0], c[1]); c[1] += len(lz)
                break
        else:
            raise SystemExit("out of room for overworld sheets")
    L = ["; generated by tools/character_mode/build_ow_sprites.py -- do not edit",
         "; Player overworld sprite per character id: db bank (0 = none), dw LZ sheet, db OBJ palette (1..7).",
         'SECTION "OWArtTable", ROMX[$%04X], BANK[118]' % TABLE_ADDR, "OWArtTable::"]
    for cid in range(NUM_CHARS):
        if cid in man:
            b, a = where[(OUT / f"{cid}.2bpp").read_bytes()]
            L.append("\tdb $%02X\n\tdw $%04X\n\tdb %d ; %s" % (b, a, P[man[cid]["palette"]], man[cid]["name"]))
        else:
            L.append("\tdb 0, 0, 0, 0")
    for n, (b, a, first, lz) in enumerate(place):
        (OUT / f"sheet_{first}.lz").write_bytes(lz)
        L.append('SECTION "OWSheet%d", ROMX[$%04X], BANK[$%02X]' % (n, a, b))
        L.append('\tINCBIN "art/overworld/sheet_%d.lz" ; %s' % (first, man[first]["sprite"]))
    ASM.write_text("\n".join(L) + "\n")
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1))
    # contact sheet: each character's 6 frames in its Prism palette (morning colours)
    cols = {1: (10, 9, 31), 2: (7, 23, 3), 3: (15, 10, 3), 4: (31, 7, 0), 5: (14, 14, 10), 6: (31, 28, 0), 7: (26, 0, 26)}
    sheet = Image.new("RGB", (8 + 6 * 18, 18 * len(man)), (60, 60, 60))
    for r, cid in enumerate(sorted(man)):
        raw = (OUT / f"{cid}.2bpp").read_bytes()
        c2 = cols[P[man[cid]["palette"]]]
        pal = [(232, 248, 232), (248, 152, 80), tuple(v * 8 for v in c2), (0, 0, 0)]
        for f in range(6):
            im = Image.new("RGB", (16, 16))
            for t in range(4):
                tile = raw[(f * 4 + t) * 16:(f * 4 + t + 1) * 16]
                for y in range(8):
                    for x in range(8):
                        v = ((tile[y * 2] >> (7 - x)) & 1) | (((tile[y * 2 + 1] >> (7 - x)) & 1) << 1)
                        im.putpixel(((t & 1) * 8 + x, (t >> 1) * 8 + y), pal[v])
            sheet.paste(im, (8 + f * 18, r * 18))
    sheet.save(OUT / "contact.png")
    used = {b: sum(len(lz) for bb, _, _, lz in place if bb == b) for b, _, _ in PACK}
    print("overworld %d / %d selectable (own %d, stand-in %d); %d unique sheets, bytes per bank %s; missing %s" % (
        len(man), len(sel), sum(v["kind"].startswith("own") for v in man.values()),
        sum(v["kind"].startswith("stand") for v in man.values()), len(blobs),
        {hex(b): n for b, n in used.items()}, missing))


if __name__ == "__main__":
    main()
