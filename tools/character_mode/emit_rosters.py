#!/usr/bin/env python3
"""Emit Prism Character Mode roster bitmap tables (with evolution-family
expansion).

Reads rosters_mapped.json (species already resolved to Prism internal ids by
map_species.py against prism_species_table.tsv) and writes:

  - rosters.asm       RGBDS include: one 32-byte bitmap per character
                       (256 bits, bit N = Prism species id N allowed;
                        LSB-first within each byte: bit = id & 7 of byte
                        id >> 3 — must match the catch-gate stub's check)
  - roster_index.tsv  character index -> name/category/source + species counts
                       (the character id byte the gate reads is an index into
                        this order)

Characters are emitted in sorted(name) order, same as rosters_mapped.json's
key order. Empty rosters (Rijon Wiki documentation gaps, see CLAUDE.md) are
emitted as all-zero bitmaps and flagged in roster_index.tsv.

EVOLUTION-FAMILY EXPANSION (implemented 2026-07-17):
Per the ROWE/Unbound/Lazarus precedent, every character is allowed their
canon roster mon's ENTIRE evolution family — the base stage, every forward
evolution, AND every branched evolution (e.g. Eevee's whole family: all
eeveelutions incl. Sylveon) — even mon the character never personally owned.
A character who canonically used only a mid- or final-stage mon still gets
that mon's full family allowed.

The family topology is the single source of truth built by
build_wildmon_data.py: wildmon_families.tsv maps every Prism species id to
its family_root (base stage), and all members of one family share that root.
Expansion is therefore: for each resolved roster id, normalize to its
family_root, then add every species whose family_root equals that root.

Prism-original fakemon / engine placeholders with no evolution data
(Varaneous, Fambaco, Raiwato, Phancero, Libabeel, Egg, Debug) are their own
family_root with no members, so expansion leaves them standalone — flagged,
never guessed (matches build_wildmon_data.py's NO_DATA handling).
"""
import collections
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILIES_TSV = os.path.join(HERE, "wildmon_families.tsv")


def load_family_topology():
    """Return (id_to_root, root_to_members, no_data_ids) from
    wildmon_families.tsv (built by build_wildmon_data.py)."""
    id_to_root = {}
    root_to_members = collections.defaultdict(list)
    no_data_ids = set()
    with open(FAMILIES_TSV) as f:
        header = f.readline().rstrip("\n").split("\t")
        col = {name: i for i, name in enumerate(header)}
        for line in f:
            p = line.rstrip("\n").split("\t")
            if len(p) < len(header):
                continue
            sid = int(p[col["id"]])
            root = int(p[col["family_root"]])
            id_to_root[sid] = root
            root_to_members[root].append(sid)
            if int(p[col["no_data"]]):
                no_data_ids.add(sid)
    if len(id_to_root) < 250:
        raise SystemExit(
            "wildmon_families.tsv parsed too few species (%d) — run "
            "build_wildmon_data.py first" % len(id_to_root))
    return id_to_root, root_to_members, no_data_ids


def expand_family(ids, id_to_root, root_to_members):
    """Given an iterable of resolved Prism species ids, return the full
    allowed set: for each id, its family_root plus every member of that
    family (base + all forward + all branched evolutions)."""
    out = set()
    for sid in ids:
        root = id_to_root.get(sid, sid)
        out.update(root_to_members.get(root, [sid]))
    return out


def set_bit(bm, sid):
    if not 1 <= sid <= 255:
        raise SystemExit(f"species id {sid} out of range")
    bm[sid >> 3] |= 1 << (sid & 7)



# ---------------------------------------------------------------------------
# The empty-roster INVENTORY.
#
# rowe_parity.md §10 measured 35 characters across three ports whose rosters
# emit nothing and asked the Iscan/Cogita question of each: is the species
# absent from this game, or is the mapped data simply older than the game's own
# tables?
#
# ⭐ For Prism the answer is NEITHER, and that makes it a different shape from
# its siblings. Lazarus's 17 and Seaglass's 3 are genuine dex absences -- the
# species exist in the roster data and this ROM has no id for them. Prism's 12
# are empty in rosters_raw.json itself: the scrape returned no Pokemon at all
# for these pages. They are all Prism/Rijon originals (`source: rijon`) -- six
# gym leaders, a rival, and the six Palette Patrollers -- so their teams are
# documented on the Rijon wiki rather than Bulbapedia, and nothing here ever
# populated them.
#
# ⚠️ So this inventory is pinning a KNOWN GAP, not a clean bill of health. If
# the Rijon rosters are ever scraped, every character here will "gain a first
# roster" and this guard will fire with the index-shift warning -- which is
# exactly the moment someone needs to read it, because saves store the
# character INDEX.
#
# ✅ MEASURED 2026-09-01: re-running map_species.py reproduces
# rosters_mapped.json byte-for-byte, so the data is not stale either.
EMPTY_ROSTER_EXPECTED = {
    "Bronze":          "no source data: the rijon-wiki scrape of page 'Bronze' "
                        "returned no Pokemon at all",
    "Joe":             "no source data: the rijon-wiki scrape of page 'Joe' "
                        "returned no Pokemon at all",
    "Koji":            "no source data: the rijon-wiki scrape of page 'Koji' "
                        "returned no Pokemon at all",
    "Lois":            "no source data: the rijon-wiki scrape of page 'Lois' "
                        "returned no Pokemon at all",
    "Palette Black":   "no source data: the rijon-wiki scrape of page 'Palette Patrollers' "
                        "returned no Pokemon at all",
    "Palette Blue":    "no source data: the rijon-wiki scrape of page 'Palette Patrollers' "
                        "returned no Pokemon at all",
    "Palette Green":   "no source data: the rijon-wiki scrape of page 'Palette Patrollers' "
                        "returned no Pokemon at all",
    "Palette Pink":    "no source data: the rijon-wiki scrape of page 'Palette Patrollers' "
                        "returned no Pokemon at all",
    "Palette Red":     "no source data: the rijon-wiki scrape of page 'Palette Patrollers' "
                        "returned no Pokemon at all",
    "Palette Yellow":  "no source data: the rijon-wiki scrape of page 'Palette Patrollers' "
                        "returned no Pokemon at all",
    "Sheryl":          "no source data: the rijon-wiki scrape of page 'Sheryl' "
                        "returned no Pokemon at all",
    "Sparky":          "no source data: the rijon-wiki scrape of page 'Sparky' "
                        "returned no Pokemon at all",
}


def assert_empty_inventory(empty):
    """Fail the emit unless the empty rosters are exactly the ones above."""
    seen, want = set(empty), set(EMPTY_ROSTER_EXPECTED)
    added, gone = sorted(seen - want), sorted(want - seen)
    if not added and not gone:
        return
    msg = ["empty-roster inventory mismatch -- see EMPTY_ROSTER_EXPECTED"]
    for c in added:
        msg.append("  NEW empty roster: %s. Something stopped resolving; find "
                   "out why before adding it to the inventory." % c)
    for c in gone:
        msg.append("  %s is NO LONGER empty -- it gained a roster. Saves store "
                   "the character INDEX, so a character who gains a first "
                   "roster must move to the END of the emit order, or every "
                   "later index shifts." % c)
    raise SystemExit("\n".join(msg))


def main():
    with open(os.path.join(HERE, "rosters_mapped.json")) as f:
        mapped = json.load(f)

    id_to_root, root_to_members, no_data_ids = load_family_topology()

    names = sorted(mapped)
    bitmaps = []
    index_rows = []
    total_added = 0
    fakemon_seen = set()
    for idx, name in enumerate(names):
        info = mapped[name]
        base_ids = sorted({e["species_id"] for e in info["species"]
                           if e["species_id"] is not None})
        expanded = expand_family(base_ids, id_to_root, root_to_members)
        total_added += len(expanded) - len(base_ids)
        fakemon_seen |= (set(base_ids) & no_data_ids)
        bm = bytearray(32)
        for sid in sorted(expanded):
            set_bit(bm, sid)
        bitmaps.append(bytes(bm))
        flag = "EMPTY" if not base_ids else ""
        index_rows.append((idx, name, info["category"], info["source"],
                           len(base_ids), len(expanded), flag))

    with open(os.path.join(HERE, "rosters.asm"), "w") as f:
        f.write("; AUTO-GENERATED by emit_rosters.py - do not hand-edit.\n")
        f.write("; One 32-byte bitmap per character, bit N (LSB-first) = Prism\n")
        f.write("; species id N catchable. Character index order matches\n")
        f.write("; roster_index.tsv. Full evolution families included (base +\n")
        f.write("; forward + branched). See tools/character_mode/emit_rosters.py.\n")
        f.write(f"DEF NUM_CM_CHARACTERS EQU {len(names)}\n\n")
        f.write("CharacterModeRosters::\n")
        for (idx, name, cat, src, nbase, nexp, flag) in index_rows:
            f.write(f"; {idx:3d}: {name} ({cat}, {src}, {nbase} canon -> "
                    f"{nexp} w/ evo families{', EMPTY' if flag else ''})\n")
            bm = bitmaps[idx]
            for row in range(0, 32, 16):
                chunk = ", ".join(f"${b:02X}" for b in bm[row:row+16])
                f.write(f"\tdb {chunk}\n")
        f.write("CharacterModeRostersEnd::\n")

    with open(os.path.join(HERE, "roster_index.tsv"), "w") as f:
        f.write("index\tname\tcategory\tsource\tcanon_count\texpanded_count\tflag\n")
        for row in index_rows:
            f.write("\t".join(str(x) for x in row) + "\n")

    assert_empty_inventory([r[1] for r in index_rows if r[6]])
    n_empty = sum(1 for r in index_rows if r[6])
    print(f"emitted {len(names)} characters ({n_empty} empty rosters), "
          f"{len(names)*32} bytes of bitmap data; evolution-family expansion "
          f"added {total_added} allowed species-slots across all rosters")
    if fakemon_seen:
        print(f"note: {len(fakemon_seen)} no-evo-data fakemon appear in rosters "
              f"and stay standalone (not guessed): "
              + ", ".join(sorted(str(s) for s in fakemon_seen)))

    _self_checks(names, bitmaps, id_to_root, root_to_members)


def _bit(bm, sid):
    return (bm[sid >> 3] >> (sid & 7)) & 1


def _self_checks(names, bitmaps, id_to_root, root_to_members):
    """Prove expansion works: a known character's full evolution line is
    allowed (incl. base stages never owned and branched evolutions), and an
    off-roster family is NOT allowed."""
    # (1) legacy check: Yuki still includes Mamoswine (230).
    if "Yuki" in names:
        bm = bitmaps[names.index("Yuki")]
        assert _bit(bm, 230), "Yuki should include Mamoswine (230)"
        print("self-check Yuki has Mamoswine(230): OK")

    # (2) full-line + branch: Blaine's canon roster contains only Flareon
    #     (136) from the Eevee family, yet expansion must allow the ENTIRE
    #     Eevee family — Eevee(133, base, never owned) and Sylveon(241, a
    #     branched evolution linked via build_wildmon_data.py) included.
    if "Blaine" in names:
        bm = bitmaps[names.index("Blaine")]
        eevee_family = root_to_members[id_to_root[133]]  # root 133 = Eevee
        for sid in eevee_family:
            assert _bit(bm, sid), \
                f"Blaine must allow Eevee-family id {sid} (from owning Flareon)"
        assert _bit(bm, 133), "Blaine must allow Eevee(133) base stage"
        assert _bit(bm, 241), "Blaine must allow Sylveon(241) branched evo"
        # (3) negative: the Bulbasaur family (1,2,3) is off-roster for Blaine
        #     and must remain disallowed.
        for sid in (1, 2, 3):
            assert not _bit(bm, sid), \
                f"Blaine must NOT allow off-roster Bulbasaur-family id {sid}"
        print(f"self-check Blaine full Eevee line allowed ({len(eevee_family)} "
              f"members incl. base Eevee + branch Sylveon), Bulbasaur family "
              f"disallowed: OK")


if __name__ == "__main__":
    main()
