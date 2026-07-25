#!/usr/bin/env python3
"""Generate ROSTERS.md / ROSTERS_SPRITES.md / sprites/gen_*.md from the data
the ROM actually enforces.

Why this exists: these docs used to be hand-maintained, and in the ROWE
reference project that produced a shipped doc promising 194 family bases the
catch gate refused. Here they are derived from `rosters.asm` - the very
32-byte allow-bitmaps the catch-gate stub bit-tests - so a doc entry cannot
claim anything the ROM does not honour.

Inputs:
  rosters.asm            the injected per-character allow-bitmaps
  roster_index.tsv       character index -> name, category, source
  characters.txt         generation per character
  wildmon_families.tsv   id -> name, family_root, level band, legendary flag
  natdex_by_name.json    National Dex number per species, for sprite URLs

"Final evolutions" = allowed species that nothing else in their family
evolves into. Prism has no evolution-edge table of its own; what
build_wildmon_data.py recovered is per-species LEVEL BANDS within a family
(Bulbasaur 1-15, Ivysaur 16-31, Venusaur 32-100), so the final stages are the
members whose band runs to the top. Branch families (Eevee) work naturally:
every eeveelution's band ends at 100.

Prism-original fakemon have no National Dex number and render without a
sprite - by design, PokeAPI has no art for them.

Run after emit_rosters.py:
    python3 tools/character_mode/emit_roster_docs.py
"""
import csv
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TARGET = os.path.abspath(os.path.join(HERE, "..", ".."))

GAME_TITLE = "Pokémon Prism (GBC)"
WIP_NOTE = ("> ⚠️ **Work in progress** — availability in this specific game "
            "may differ.")
TOP_BAND = 100          # a family's last stage runs to level 100
BITMAP_BYTES = 32       # 256 species ids, LSB-first within each byte

CATEGORY_LABEL = {
    "protagonist": "Protagonist", "rival": "Rival", "gymleader": "Gym Leader",
    "elite4": "Elite Four", "champion": "Champion", "villain": "Villain",
    "anime": "Anime", "professor": "Professor",
}

SPRITE_URL = ("https://cdn.jsdelivr.net/gh/PokeAPI/sprites@master"
              "/sprites/pokemon/%d.png")
SPRITES_PER_ROW = 8


def load_bitmaps():
    """[bytes] per character, in rosters.asm order (= roster_index.tsv order)."""
    text = open(os.path.join(HERE, "rosters.asm"), encoding="utf-8").read()
    body = text.split("CharacterModeRosters::", 1)[1]
    out, cur = [], []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith(";"):
            continue
        m = re.match(r"db\s+(.*)$", line)
        if not m:
            continue
        cur.extend(int(b.strip().lstrip("$"), 16) for b in m.group(1).split(","))
        if len(cur) >= BITMAP_BYTES:
            out.append(bytes(cur[:BITMAP_BYTES]))
            cur = cur[BITMAP_BYTES:]
    return out


def load_families():
    """id -> {name, root, stage_max}."""
    species = {}
    with open(os.path.join(HERE, "wildmon_families.tsv")) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            species[int(row["id"])] = {
                "name": row["name"],
                "root": int(row["family_root"]),
                "stage_max": int(row["stage_max"]),
            }
    return species


def load_characters():
    """[(name, category, generation)] in roster_index.tsv order."""
    gens = {}
    with open(os.path.join(HERE, "characters.txt"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) > 3 and parts[3].isdigit():
                gens[parts[0]] = int(parts[3])
    out = []
    with open(os.path.join(HERE, "roster_index.tsv")) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out.append((row["name"], row["category"], gens.get(row["name"], 0)))
    return out


def main():
    bitmaps = load_bitmaps()
    species = load_families()
    characters = load_characters()
    with open(os.path.join(HERE, "natdex_by_name.json"), encoding="utf-8") as f:
        dex = json.load(f)["numbers"]

    if len(bitmaps) != len(characters):
        raise SystemExit("rosters.asm has %d bitmaps but roster_index.tsv has "
                         "%d characters - re-run emit_rosters.py"
                         % (len(bitmaps), len(characters)))

    chars = []
    for (name, category, gen), bits in zip(characters, bitmaps):
        finals = []
        for sid, info in sorted(species.items()):
            if sid >= BITMAP_BYTES * 8 or not (bits[sid >> 3] & (1 << (sid & 7))):
                continue
            if info["stage_max"] < TOP_BAND:
                continue                      # a lower stage of its family
            finals.append((info["name"], dex.get(info["name"], 0)))
        finals.sort(key=lambda e: (e[1] or 9999, e[0]))
        chars.append({
            "name": name,
            "gen": gen,
            "label": CATEGORY_LABEL.get(category, category.title()),
            "finals": finals,
        })

    by_gen = defaultdict(list)
    for c in chars:
        by_gen[c["gen"]].append(c)
    for g in by_gen:
        by_gen[g].sort(key=lambda c: c["name"])
    gens = sorted(by_gen)

    generated_note = ("GENERATED by `tools/character_mode/emit_roster_docs.py` "
                      "from `rosters.asm`, the same allow-bitmaps the catch-gate "
                      "stub bit-tests — do not hand-edit, regenerate.")

    out = ["# Character Mode — Final-Evolution Rosters (%s)" % GAME_TITLE, "",
           "Every playable character and the **final evolutions** their complete "
           "roster resolves to, in **National Pokédex order**. Rosters were "
           "researched from Bulbapedia and the Rijon Wiki and cross-checked where "
           "possible. Off-roster Pokémon are routed to your PC.", "",
           "Only species this ROM actually contains are listed — Prism's dex is "
           "Gen 1-2 plus its own additions, so canon roster members the binary "
           "does not have are omitted rather than promised. Prism-original "
           "species have no National Dex number and appear without a sprite.",
           "", WIP_NOTE, "",
           "**%d characters.** Sprite version: `ROSTERS_SPRITES.md`." % len(chars),
           "", generated_note, "", "## Contents"]
    for g in gens:
        out.append("- [Generation %d](#generation-%d)" % (g, g))
    out.append("")
    for g in gens:
        out += ["", "## Generation %d" % g, ""]
        for c in by_gen[g]:
            out.append("### %s — %s" % (c["name"], c["label"]))
            out.append("**Final evolutions (%d):**" % len(c["finals"]))
            out.append(", ".join(n for n, _ in c["finals"]) or "_(none in this ROM)_")
            out.append("")
    with open(os.path.join(TARGET, "ROSTERS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out).rstrip() + "\n")

    idx = ["# Character Mode — Roster Sprites (%s)" % GAME_TITLE, "",
           "Each character's **final-evolution** roster, in **National Pokédex "
           "order**, with sprites and names. Split by generation to keep pages "
           "fast. Sprites via [PokéAPI](https://github.com/PokeAPI/sprites); "
           "Prism-original species have none. Text: `ROSTERS.md`.",
           "", "**%d characters.**" % len(chars), "", generated_note,
           "", "## Generations", ""]
    for g in gens:
        idx.append("- [Generation %d](sprites/gen_%d.md) — %d characters"
                   % (g, g, len(by_gen[g])))
    with open(os.path.join(TARGET, "ROSTERS_SPRITES.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(idx).rstrip() + "\n")

    os.makedirs(os.path.join(TARGET, "sprites"), exist_ok=True)
    for g in gens:
        page = ["# %s — Roster Sprites (Generation %d)" % (GAME_TITLE, g), "",
                "Final-evolution rosters in National Pokédex order, sprites with "
                "names. [← back to index](../ROSTERS_SPRITES.md)", ""]
        for c in by_gen[g]:
            page.append("### %s — %s" % (c["name"], c["label"]))
            page.append("<table>")
            row = []
            for name, num in c["finals"]:
                art = ('<img width="56" src="%s"><br>' % (SPRITE_URL % num)) if num else ""
                row.append('<td align="center" width="80">%s<sub>%s</sub></td>'
                           % (art, name))
                if len(row) == SPRITES_PER_ROW:
                    page.append("<tr>" + "".join(row) + "</tr>")
                    row = []
            if row:
                page.append("<tr>" + "".join(row) + "</tr>")
            page += ["</table>", ""]
        with open(os.path.join(TARGET, "sprites/gen_%d.md" % g), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(page).rstrip() + "\n")

    print("wrote ROSTERS.md, ROSTERS_SPRITES.md and %d sprites/gen_*.md: "
          "%d characters, %d final-evolution entries"
          % (len(gens), len(chars), sum(len(c["finals"]) for c in chars)))


if __name__ == "__main__":
    main()
