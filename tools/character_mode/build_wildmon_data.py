#!/usr/bin/env python3
"""Build Character Mode wild-encounter override data (Phase 5).

Produces, for every Prism internal species id (1-255):
  - family_root: the Prism species id of that family's base stage
    (stable key used to find "siblings" when picking a stage to fit a level)
  - stage_min / stage_max: the [min,max] level band this stage occupies
    within its family (bands partition 1-100 contiguously per family so
    every rolled level maps to exactly one stage)
  - is_legendary: 1 for legendary/mythical species (excluded from wild
    overrides entirely per spec)

Two data sources, clearly separated so provenance is auditable:

1. Gen 1/2 evolution levels: parsed directly from
   tools/pokecrystal_donor/data/pokemon/evos_attacks.asm (pret/pokecrystal,
   authoritative, byte-exact donor already used elsewhere in this project).
   Only EVOLVE_LEVEL entries carry a real level; EVOLVE_ITEM/EVOLVE_TRADE/
   EVOLVE_HAPPINESS entries have no in-game level requirement.

2. Species Prism added beyond the Gen 1/2 dex (61 of them appear in at
   least one character's scraped roster - see CLAUDE.md session on this
   feature). pokecrystal has no data for these at all (they're Gen 3/4).
   EXTRA_CHAINS below hand-encodes their evolution chains from standard,
   well-documented Pokemon game mechanics (the same facts Bulbapedia
   itself would show - this project's existing roster scrapers already
   treat Bulbapedia as authoritative, this is the same class of fact,
   just not fetched over HTTP because it's franchise-constant, not
   Prism-specific or roster-specific).

   Entries with method != LEVEL (ITEM/TRADE/HAPPINESS/SPECIAL) have NO
   canonical minimum level in the actual games. For band-partitioning
   purposes only (so "nearest stage fit" has something to compare against)
   these are given a PLACEHOLDER level of (previous stage's evolution
   level + 1) - flagged is_placeholder=True in the comments below and in
   the emitted .asm, and called out in CLAUDE.md. This is an ordering
   convenience, not an asserted canon level.

Species with no known evolution data at all (Prism-original fakemon not
on Bulbapedia: Varaneous, Fambaco, Raiwato, Phancero, Libabeel, plus the
Egg/Debug placeholders) are emitted as standalone single-stage families
(band = whole 1-100 range) rather than guessed at.

Output: wildmon_families.tsv (id, family_root, stage_min, stage_max,
is_legendary, is_placeholder_band) and wildmon_families.asm (packed
4-byte-per-species table: family_root, stage_min, stage_max, flags).
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DONOR_EVOS = os.path.join(HERE, "..", "pokecrystal_donor", "data", "pokemon", "evos_attacks.asm")
SPECIES_TABLE = os.path.join(HERE, "prism_species_table.tsv")

EVOLVE_LEVEL = "EVOLVE_LEVEL"

# Legendary/mythical species actually present in Prism's 255-entry species
# table (checked 2026-07-17: Raikou/Entei/Suicune/Celebi and every Gen 3+
# legendary/mythical beyond this list are simply ABSENT from Prism's table,
# not guessed as present).
LEGENDARY_NAMES = {
    "Articuno", "Zapdos", "Moltres", "Mewtwo", "Mew",
    "Groudon", "Kyogre", "Rayquaza", "Lugia", "Ho-Oh",
}

# Prism-original fakemon / engine placeholders with no Bulbapedia page and
# therefore no known evolution data - explicitly flagged, not guessed.
NO_DATA_NAMES = {"Varaneous", "Fambaco", "Raiwato", "Phancero", "Libabeel",
                  "Egg", "Debug"}

# (from_name, to_name, level_or_None) - level is None for ITEM/TRADE/
# HAPPINESS/SPECIAL methods (no canonical level; see module docstring).
# Covers every Prism-added (non-Gen1/2) species that appears in any
# character roster, PLUS the intermediate/base family members needed to
# complete those chains even if not independently roster-referenced.
EXTRA_CHAINS = [
    ("Aron", "Lairon", 32), ("Lairon", "Aggron", 42),
    ("Swablu", "Altaria", 35),
    ("Anorith", "Armaldo", 40),
    ("Shuppet", "Banette", 37),
    ("Bronzor", "Bronzong", 33),
    ("Buneary", "Lopunny", None),  # happiness
    ("Cacnea", "Cacturne", 32),
    ("Chingling", "Chimecho", None),  # happiness, night
    ("Lileep", "Cradily", 40),
    ("Skorupi", "Drapion", 40),
    ("Drifloon", "Drifblim", 28),
    ("Duskull", "Dusclops", 37), ("Dusclops", "Dusknoir", None),  # trade
    ("Elekid", "Electabuzz", 30), ("Electabuzz", "Electivire", None),  # trade
    ("Whismur", "Loudred", 20), ("Loudred", "Exploud", 40),
    ("Trapinch", "Vibrava", 35), ("Vibrava", "Flygon", 45),
    ("Snorunt", "Glalie", 42), ("Snorunt", "Froslass", None),  # item, female
    ("Ralts", "Kirlia", 20), ("Kirlia", "Gardevoir", 30),
    ("Kirlia", "Gallade", None),  # item, male
    ("Gible", "Gabite", 24), ("Gabite", "Garchomp", 48),
    ("Eevee", "Glaceon", None), ("Eevee", "Leafeon", None),  # item exposure
    ("Gligar", "Gliscor", None),  # item, night
    ("Makuhita", "Hariyama", 24),
    ("Lotad", "Lombre", 14), ("Lombre", "Ludicolo", None),  # item
    ("Riolu", "Lucario", None),  # happiness, day
    ("Magnemite", "Magneton", 30), ("Magneton", "Magnezone", 30),  # location, lvl30 min (Bulbapedia)
    ("Swinub", "Piloswine", 33), ("Piloswine", "Mamoswine", 34),  # move+level, placeholder
    ("Electrike", "Manectric", 26),
    ("Beldum", "Metang", 20), ("Metang", "Metagross", 45),
    ("Misdreavus", "Mismagius", None),  # item
    ("Feebas", "Milotic", None),  # beauty/trade
    ("Cranidos", "Rampardos", 30),
    ("Rhyhorn", "Rhydon", 42), ("Rhydon", "Rhyperior", 43),  # trade, placeholder
    ("Bagon", "Shelgon", 30), ("Shelgon", "Salamence", 50),
    ("Shieldon", "Bastiodon", 30),
    ("Taillow", "Swellow", 22),
    ("Tangela", "Tangrowth", 33),  # move+level, placeholder
    ("Togepi", "Togetic", None), ("Togetic", "Togekiss", None),  # happiness, item
    ("Wailmer", "Wailord", 40),
    ("Sneasel", "Weavile", None),  # item, night
    ("Yanma", "Yanmega", 34),  # move+level, placeholder
    ("Onix", "Steelix", None),  # trade (already in donor for Onix itself,
                                  # kept here too so Steelix's OWN band has
                                  # a defined predecessor even though this
                                  # duplicates donor data harmlessly)
    # Forward/branched evolutions whose PRE-evo is present in Prism's table
    # but which were previously orphaned as their own single-stage family.
    # Required so full-evolution-line roster expansion (emit_rosters.py)
    # links these into the correct family_root; also correct for the wild
    # band feature. Same class of franchise-constant fact as the rest of
    # EXTRA_CHAINS (see module docstring).
    ("Shinx", "Luxio", 15), ("Luxio", "Luxray", 30),
    ("Numel", "Camerupt", 33),
    ("Surskit", "Masquerain", 22),
    ("Shroomish", "Breloom", 23),
    ("Magmar", "Magmortar", None),  # item (Magmarizer, trade)
    ("Porygon2", "Porygon-Z", None),  # item (Dubious Disc, trade)
    ("Eevee", "Sylveon", None),  # affection + Fairy-type move
]

# Standalone species with no evolution relationship at all (both directions)
# among Prism-added species. Listed for documentation; anything not
# mentioned anywhere gets this treatment by default anyway.
STANDALONE_EXTRA = {
    "Absol", "Mawile", "Lunatone", "Solrock", "Torkoal", "Relicanth",
    "Sableye", "Spiritomb", "Volbeat", "Illumise", "Chansey",
}


def parse_donor_chains():
    """Parse pokecrystal's evos_attacks.asm into {from_name: [(to_name, level_or_None)]}."""
    text = open(DONOR_EVOS).read()
    chains = {}
    # e.g. "BulbasaurEvosAttacks:\n\tdb EVOLVE_LEVEL, 16, IVYSAUR\n\tdb 0 ..."
    for m in re.finditer(r"^(\w+)EvosAttacks:\n((?:\tdb [^\n]*\n)*)", text, re.M):
        label = m.group(1)
        body = m.group(2)
        evos = []
        for line in body.splitlines():
            line = line.strip()
            if not line.startswith("db ") or line.startswith("db 0"):
                continue
            parts = [p.strip() for p in line[3:].split(",")]
            if not parts or not parts[0].startswith("EVOLVE_"):
                continue
            method = parts[0]
            if method == EVOLVE_LEVEL:
                level = int(parts[1])
                to_name = parts[2]
            elif method == "EVOLVE_STAT":
                # db EVOLVE_STAT, level, ATK_*_DEF constant, species
                level = int(parts[1])
                to_name = parts[3]
            else:
                level = None
                to_name = parts[2]
            evos.append((to_name, level))
        if evos:
            chains[label] = evos
    return chains


def load_species_table():
    """Return {name_lower: id} and {id: name} for Prism's real species table."""
    name_to_id = {}
    id_to_name = {}
    for line in open(SPECIES_TABLE):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        sid, name = int(parts[0]), parts[1]
        name_to_id[name.lower()] = sid
        id_to_name[sid] = name
    return name_to_id, id_to_name


def donor_label_to_const_name(label):
    """'Bulbasaur' donor label already matches CONST-style species names in
    most cases via evos_attacks_pointers ordering; but the evolution TARGET
    names inside db lines are RGBDS constant names (e.g. IVYSAUR, MR_MIME).
    Normalize both label and constant forms to a bare lowercase compare
    key so they match prism_species_table.tsv's display names."""
    return re.sub(r"[^a-z0-9]", "", label.lower())


def main():
    name_to_id, id_to_name = load_species_table()
    donor_chains = parse_donor_chains()

    # normalized-name -> Prism id, for fuzzy matching donor CONST names
    # (IVYSAUR, MR_MIME, NIDORAN_F, ...) against the Prism table's display
    # names (Ivysaur, MrMime-ish, Nidoranf, ...).
    norm_to_id = {donor_label_to_const_name(n): sid for sid, n in id_to_name.items()}

    def resolve(name):
        key = donor_label_to_const_name(name)
        return norm_to_id.get(key)

    # edges[from_id] = [(to_id, level_or_None)]
    edges = {}
    unresolved = []

    def add_edge(from_name, to_name, level):
        fid = resolve(from_name)
        tid = resolve(to_name)
        if fid is None or tid is None:
            unresolved.append((from_name, to_name, level, fid, tid))
            return
        edges.setdefault(fid, []).append((tid, level))

    for label, evos in donor_chains.items():
        for to_name, level in evos:
            add_edge(label, to_name, level)

    for from_name, to_name, level in EXTRA_CHAINS:
        add_edge(from_name, to_name, level)

    # Build reverse edges to find each species' predecessor (for band
    # boundaries) and roots (species with no predecessor = base stage).
    has_predecessor = set()
    for fid, lst in edges.items():
        for tid, _level in lst:
            has_predecessor.add(tid)

    all_ids = sorted(id_to_name)
    roots = [sid for sid in all_ids if sid not in has_predecessor]

    # Pass 1 (top-down): assign stage_min. Real EVOLVE_LEVEL/EVOLVE_STAT
    # edges give the child a real minimum level. Non-level edges (ITEM/
    # TRADE/HAPPINESS - no canonical level exists) make the child INHERIT
    # its parent's stage_min unchanged rather than fabricating one; this
    # is the honest "we don't have a level fact" representation, not a
    # placeholder guess. `placeholder[sid]` marks species whose min came
    # from inheritance rather than a real evolution level.
    family_root = {}
    stage_min = {}
    placeholder = {}

    def walk(root):
        family_root[root] = root
        stage_min[root] = 1
        placeholder[root] = False
        stack = [root]
        seen = {root}
        while stack:
            cur = stack.pop()
            for tid, level in edges.get(cur, []):
                if tid in seen:
                    continue
                seen.add(tid)
                family_root[tid] = root
                if level is not None:
                    stage_min[tid] = level
                    placeholder[tid] = False
                else:
                    stage_min[tid] = stage_min[cur]
                    placeholder[tid] = True
                stack.append(tid)

    for r in roots:
        walk(r)

    # Any id never touched (no edges either direction, e.g. fakemon or a
    # donor species genuinely absent from Prism, or a species not reached
    # because both its family root computation was skipped) -> standalone.
    for sid in all_ids:
        if sid not in family_root:
            family_root[sid] = sid
            stage_min[sid] = 1
            placeholder[sid] = False

    # Pass 2 (bottom-up per node, using only REAL-level direct children):
    # stage_max[node] = min(level_child.stage_min for real-level children)
    # - 1, or 100 if there are none. Non-level children never constrain a
    # parent's band (there's no level fact to constrain it with) - they
    # simply inherit the same band as their parent, and ties between
    # siblings/parent-child sharing a band are broken at RANDOM at runtime,
    # not by arbitrary tie-break here.
    stage_max = {}

    def compute_max(sid):
        if sid in stage_max:
            return stage_max[sid]
        real_children_mins = [stage_min[tid]
                               for tid, lvl in edges.get(sid, []) if lvl is not None]
        stage_max[sid] = (max(stage_min[sid], min(real_children_mins) - 1)
                           if real_children_mins else 100)
        return stage_max[sid]

    for sid in all_ids:
        compute_max(sid)

    # Legendary flag by name.
    is_legendary = {sid: (id_to_name[sid] in LEGENDARY_NAMES) for sid in all_ids}
    no_data = {sid: (id_to_name[sid] in NO_DATA_NAMES) for sid in all_ids}

    # Emit TSV.
    tsv_path = os.path.join(HERE, "wildmon_families.tsv")
    with open(tsv_path, "w") as f:
        f.write("id\tname\tfamily_root\tstage_min\tstage_max\tis_legendary\tis_placeholder_band\tno_data\n")
        for sid in all_ids:
            f.write(f"{sid}\t{id_to_name[sid]}\t{family_root[sid]}\t{stage_min[sid]}\t"
                    f"{stage_max[sid]}\t{int(is_legendary[sid])}\t{int(placeholder[sid])}\t"
                    f"{int(no_data[sid])}\n")

    # Emit packed ASM table: 4 bytes/species (family_root, stage_min,
    # stage_max, flags[bit0=legendary]), indexed directly by Prism species
    # id (index 0 unused/padding so table[species_id] works with no -1).
    asm_path = os.path.join(HERE, "wildmon_families.asm")
    with open(asm_path, "w") as f:
        f.write("; AUTO-GENERATED by build_wildmon_data.py - do not hand-edit.\n")
        f.write("; 4 bytes per Prism species id (index 0 = unused padding):\n")
        f.write(";   byte0 = family_root id, byte1 = stage_min level,\n")
        f.write(";   byte2 = stage_max level, byte3 = flags (bit0 = legendary).\n")
        f.write("; See wildmon_families.tsv for the human-readable version and\n")
        f.write("; CLAUDE.md for data provenance / placeholder-band caveats.\n")
        f.write("WildmonFamilies::\n")
        f.write("\tdb $00, $00, $00, $00 ; id 0 padding\n")
        for sid in all_ids:
            flags = 1 if is_legendary[sid] else 0
            f.write(f"\tdb ${family_root[sid]:02X}, ${stage_min[sid]:02X}, "
                    f"${stage_max[sid]:02X}, ${flags:02X} ; {sid}: {id_to_name[sid]}\n")
        f.write("WildmonFamiliesEnd::\n")

    print(f"resolved {len(all_ids)} species, {len(roots)} family roots, "
          f"{sum(is_legendary.values())} legendary, {sum(no_data.values())} no-data, "
          f"{sum(placeholder.values())} placeholder-band stages")
    if unresolved:
        print(f"{len(unresolved)} unresolved edges (name didn't match Prism species table):")
        for u in unresolved:
            print("  ", u)


if __name__ == "__main__":
    main()
