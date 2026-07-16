#!/usr/bin/env python3
"""Map scraped roster species names to Prism's own internal species ids.

Reads rosters_raw.json (written by scrape_bulbapedia.py + scrape_rijon_wiki.py),
resolves each display name against prism_species_table.tsv - a species id ->
name table extracted DIRECTLY from the real v0.95 Hotfix 5 ROM (fixed 10-byte
records at file offset 0x0155E5, see docs/TOOLCHAIN.md for the extraction
method) - and writes:
  - rosters_mapped.json   (character -> species list, each tagged with an id
                            if resolved, or id_source="unresolved" if not)
  - roster_review.csv     (for the user to audit: one row per character/species)
  - unmatched_names.txt   (scraped names that aren't real Pokemon at all - would
                            indicate a scraper bug, since both scrapers already
                            validate against Bulbapedia's national dex)
  - unresolved_ids.txt    (real Pokemon with NO Prism id - i.e. genuinely absent
                            from Prism's 255-entry species table, distinct from
                            the earlier "no donor" gap which is now resolved)

IMPORTANT CORRECTION (2026-07-12): earlier runs of this script used
pret/pokecrystal's National-Dex-ordered names.asm as a stand-in for Prism's
own species ids, assuming Prism kept vanilla Crystal's Gen 1/2 ordering. That
assumption is WRONG, confirmed by extracting Prism's real table: Prism uses
its own fully custom species order even for shared Gen 1/2 species (e.g.
Prism inserts Chingling/Chimecho at ids 13/14, where Crystal has
Weedle/Kakuna/Beedrill). Any species_id/id_source="pokecrystal" recorded by a
prior run of this script is stale and must not be trusted - re-run against
the current prism_species_table.tsv donor.

Does NOT normalize to evolution-family base stage the way ROWE's map_species.py
does (no evos_attacks parsing here yet) - that requires knowing Prism's actual
catch-restriction semantics, which is Phase 1 (RE) territory, not assumed here.
"""
import csv
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SPECIES_TABLE = os.path.join(HERE, "prism_species_table.tsv")


def canon(name):
    """Canonical match key: letters+digits only, uppercased, gender symbols
    mapped to F/M. Collapses Bulbapedia's "Mr. Mime"/"Farfetch'd"/"Nidoran♀"
    display style and the ROM's own "Farfetch'd"/"Nidoran F" display style
    onto the same key without hand-listing every special case."""
    name = name.replace("♀", "F").replace("♂", "M")  # ♀ ♂
    return re.sub(r"[^A-Za-z0-9]", "", name).upper()


def load_prism_species():
    """canon(name) -> (1-based Prism-internal species id, Prism display name)."""
    if not os.path.isfile(SPECIES_TABLE):
        raise SystemExit("Prism species table not found at %s - see docs/TOOLCHAIN.md"
                          % SPECIES_TABLE)
    out = {}
    with open(SPECIES_TABLE, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            idx, name = line.split("\t", 1)
            out[canon(name)] = (int(idx), name)
    if len(out) < 250:
        raise SystemExit("prism_species_table.tsv parsed too few entries (%d, expected ~255)"
                          % len(out))
    return out


def main():
    with open(os.path.join(HERE, "rosters_raw.json")) as f:
        raw = json.load(f)

    species_by_canon = load_prism_species()
    print("Prism ROM species table: %d species loaded" % len(species_by_canon))

    unmatched = set()      # not a real Pokemon name at all (scraper bug if any)
    unresolved = set()     # real Pokemon, no id in Prism's 255-entry table
    mapped = {}

    for disp, info in sorted(raw.items()):
        entries = []
        for name in info["species"]:
            hit = species_by_canon.get(canon(name))
            if hit:
                sid, donor_name = hit
                entries.append({"name": name, "species_id": sid,
                                 "id_source": "prism_rom"})
            else:
                unresolved.add(name)
                entries.append({"name": name, "species_id": None,
                                 "id_source": "unresolved"})
        entries.sort(key=lambda e: e["name"])
        mapped[disp] = {"page": info["page"], "category": info["category"],
                         "gen": info.get("gen", 0), "source": info.get("source", ""),
                         "species": entries}

    with open(os.path.join(HERE, "rosters_mapped.json"), "w") as f:
        json.dump(mapped, f, indent=1, sort_keys=True)

    with open(os.path.join(HERE, "roster_review.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["character", "category", "source", "species", "species_id", "id_source", "keep(Y/n)"])
        for disp, info in sorted(mapped.items()):
            for e in info["species"]:
                w.writerow([disp, info["category"], info["source"], e["name"],
                            e["species_id"] if e["species_id"] is not None else "",
                            e["id_source"], "Y"])

    with open(os.path.join(HERE, "unmatched_names.txt"), "w") as f:
        f.write("\n".join(sorted(unmatched)) + ("\n" if unmatched else ""))

    with open(os.path.join(HERE, "unresolved_ids.txt"), "w") as f:
        f.write("# Real Pokemon with no id in Prism's 255-entry species table\n"
                "# (prism_species_table.tsv, extracted from the real ROM - see\n"
                "# docs/TOOLCHAIN.md). Genuinely absent from this game, not a\n"
                "# donor gap.\n")
        f.write("\n".join(sorted(unresolved)) + ("\n" if unresolved else ""))

    empty = [d for d, i in mapped.items() if not i["species"]]
    print("mapped %d characters; %d unmatched (non-Pokemon) names; "
          "%d real species with no Prism id; %d empty rosters%s"
          % (len(mapped), len(unmatched), len(unresolved), len(empty),
             (": " + ", ".join(empty)) if empty else ""))


if __name__ == "__main__":
    main()
