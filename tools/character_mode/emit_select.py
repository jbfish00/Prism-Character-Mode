#!/usr/bin/env python3
"""Emit the character-select data tables (select_data.asm) and the selectable list.

Reads rosters.asm (the bitmaps the gates use), roster_index.tsv (names) and
wildmon_families.tsv (final stage = stage_max 100, legendary flag).

Playability threshold (user ruling, workspace CLAUDE.md): a character with
fewer than 6 fully-evolved species obtainable is NOT offered (their roster slot
and id are kept, so ids never shift) unless a legendary is on the roster.
EMPTY rosters therefore drop out too.

Outputs, in bank 119 (all sections fixed; overlay mode needs that):
  CharSelectNames   (N+1) x 14 bytes, Prism charmap, $50-terminated, padded
                    entry 0 is "Normal game"
  CharSelectIds     N bytes: character id (roster_index order) per entry 1..N
  CHARSEL_COUNT     N + 1 (entries incl. the Normal-game row)
Also writes tools/character_mode/selectable.tsv for tests.
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_MIN = 6


def enc(s):
    out = []
    for ch in s:
        if "A" <= ch <= "Z": out.append(0x80 + ord(ch) - 65)
        elif "a" <= ch <= "z": out.append(0xA0 + ord(ch) - 97)
        elif "0" <= ch <= "9": out.append(0xF6 + ord(ch) - 48)
        elif ch == " ": out.append(0x7F)
        elif ch == ".": out.append(0xE8)
        elif ch == "-": out.append(0xE3)
        elif ch == "'": out.append(0xE0)
        else: raise SystemExit(f"no charmap for {ch!r} in {s!r}")
    return out


def clean_name(n):
    """Display name for the picker/roster screen (the charmap has no parentheses)."""
    return n.replace(" (anime)", "").strip()


def load_rosters():
    rows = []
    cur = None
    for line in open(os.path.join(HERE, "rosters.asm")):
        if line.startswith("\tdb "):
            vals = [int(v.strip().lstrip("$"), 16) for v in line[4:].split(",")]
            cur.extend(vals)
        elif line.startswith(";") and re.match(r";\s*\d+:", line):
            cur = []
            rows.append(cur)
    assert all(len(r) == 32 for r in rows), [len(r) for r in rows]
    return rows


def load_families():
    fam = {}
    with open(os.path.join(HERE, "wildmon_families.tsv")) as f:
        hdr = f.readline().rstrip("\n").split("\t")
        for line in f:
            p = line.rstrip("\n").split("\t")
            d = dict(zip(hdr, p))
            fam[int(d["id"])] = d
    return fam


def norm(n):
    return re.sub(r"[^a-z0-9]", "", n.lower())[:10]


def load_signatures():
    """Per-character ace (the starter) from the sibling ports' audited data.

    Prism's own rosters_mapped.json carries no 'signature'. Seaglass's does (84
    characters, from the Bulbapedia scrape); names are the shared key. The ace's
    NAME is what we keep, never its Seaglass species id (ids differ per ROM).
    """
    import json
    path = os.path.join(HERE, "..", "..", "..", "Seaglass-Character-Mode",
                        "tools", "character_mode", "rosters_mapped.json")
    sig = {}
    if os.path.isfile(path):
        for n, v in json.load(open(path)).items():
            if v.get("signature"):
                sig[n] = v["signature"]["const"].replace("SPECIES_", "")
    return sig


# Aces for characters whose first-on-roster fallback would be a poor starter.
# Honoured only when that ace's family is on the character's roster.
ACE_OVERRIDES = {"Lance": "Dratini", "Falkner": "Pidgey", "Chuck": "Poliwag",
                 "Clair": "Dratini", "Misty": "Staryu", "Whitney": "Miltank",
                 "Lorelei": "Jynx", "Jessie": "Ekans", "Erika": "Oddish",
                 "Oak": "Bulbasaur", "Elm": "Chikorita",
                 "Sycamore": "Gible"}       # user, 2026-10-18 (game_plans/TODO_sycamore_gible.md)


def pick_starters(names, fam):
    """starter species id per character (0 = none). Order of preference:
    the sibling port's signature ace's family root when that family is on the
    roster; else the first non-legendary roster species' family root."""
    import json
    mapped = json.load(open(os.path.join(HERE, "rosters_mapped.json")))
    sig = load_signatures()
    out, how = [], []
    for n in names:
        sp = [(x["name"], x["species_id"]) for x in mapped[n]["species"] if x["species_id"]]
        roots = {fam[i]["family_root"] for _, i in sp if i in fam}
        chosen, src = 0, "none"
        want = ACE_OVERRIDES.get(n) or sig.get(n)
        if want:
            for nm, i in sp:
                if norm(nm) == norm(want) and i in fam:
                    r = int(fam[i]["family_root"])
                    if fam.get(r, {}).get("is_legendary") == "0":
                        chosen, src = r, "signature"
                    break
            if not chosen:
                for nm, i in sp:       # ace listed only as a family member
                    if i in fam and fam[i]["is_legendary"] == "0" and \
                            fam[int(fam[i]["family_root"])]["name"] and \
                            norm(fam[int(fam[i]["family_root"])]["name"]) == norm(want):
                        chosen, src = int(fam[i]["family_root"]), "signature-root"
                        break
        if not chosen:
            for nm, i in sp:
                if i in fam and fam[i]["is_legendary"] == "0":
                    chosen, src = int(fam[i]["family_root"]), "first-on-roster"
                    break
        out.append(chosen)
        how.append(src)
    return out, how


def main():
    rosters = load_rosters()
    fam = load_families()
    names, sources, rawnames = [], [], []
    with open(os.path.join(HERE, "roster_index.tsv")) as f:
        f.readline()
        for line in f:
            p = line.rstrip("\n").split("\t")
            rawnames.append(p[1])
            names.append(clean_name(p[1]))
            sources.append(p[3])
    assert len(names) == len(rosters)
    sel = []
    report = []
    for cid, bm in enumerate(rosters):
        have = [s for s in range(1, 256) if bm[s >> 3] >> (s & 7) & 1]
        finals = [s for s in have if s in fam and fam[s]["stage_max"] == "100"
                  and fam[s]["is_legendary"] == "0"]
        legend = [s for s in have if s in fam and fam[s]["is_legendary"] == "1"]
        ok = len(finals) >= FINAL_MIN or bool(legend)
        if sources[cid] == "rijon":
            ok = False          # user, 2026-10-10: Prism's own Rijon/Naljo originals are out of scope
        report.append((cid, names[cid], len(have), len(finals), len(legend), ok))
        if ok:
            sel.append(cid)
    out = ["; AUTO-GENERATED by emit_select.py - do not hand-edit.",
           f"DEF CHARSEL_COUNT EQU {len(sel) + 1}",
           "",
           'SECTION "CharSelectData", ROMX[$4000], BANK[119]',
           "CharSelectNames::"]
    entries = ["Normal game"] + [names[c] for c in sel]
    for e in entries:
        b = enc(e)
        assert len(b) <= 13, e
        b = b + [0x50] + [0x50] * (13 - len(b))
        out.append("\tdb " + ", ".join(f"${x:02X}" for x in b) + f"  ; {e}")
    for lab, txt in (("CharSelectTitle", "Pick a character"),
                     ("CharSelectHint", "A:OK  L/R:page")):
        b = enc(txt.replace(":", " ").replace("/", " ")) + [0x50]
        out.append(f"{lab}::")
        out.append("\tdb " + ", ".join(f"${x:02X}" for x in b) + f"  ; {txt}")
    starters, how = pick_starters(rawnames, fam)
    out.append("")
    out.append("; starter species id per character id (0 = none); family root of the ace.")
    out.append("; Bank 118 so the gates (also bank 118) can read it without a bank switch.")
    out.append('SECTION "CharStarters", ROMX[$4200], BANK[118]')
    out.append("CharStarters::")
    for i in range(0, len(starters), 16):
        out.append("\tdb " + ", ".join(str(x) for x in starters[i:i+16]))
    # 1% legendary rule data (game_plans/legendary_encounters.md), bank 118
    legend_bm = [0] * 32
    for sid, rec in fam.items():
        if rec["is_legendary"] == "1" and 1 <= sid < 256:
            legend_bm[sid >> 3] |= 1 << (sid & 7)
    flags = []
    for cid, bm in enumerate(rosters):
        have = [x for x in range(1, 256) if bm[x >> 3] >> (x & 7) & 1]
        legends = [x for x in have if legend_bm[x >> 3] >> (x & 7) & 1]
        flags.append((1 if legends else 0) | (2 if legends and len(legends) == len(have) else 0))
    out.append("")
    out.append("; Legendary species bitmap and per-character flags (bit0 = a legendary is on the roster,")
    out.append("; bit1 = EVERY species on the roster is legendary, so the legendary stays repeatable).")
    out.append('SECTION "LegendData", ROMX[$4300], BANK[118]')
    out.append("LegendaryBitmap::")
    out.append("\tdb " + ", ".join(f"${x:02X}" for x in legend_bm[:16]))
    out.append("\tdb " + ", ".join(f"${x:02X}" for x in legend_bm[16:]))
    out.append("CharLegendFlags::")
    for i in range(0, len(flags), 16):
        out.append("\tdb " + ", ".join(str(x) for x in flags[i:i+16]))
    # Roster screen data (bank 119): every character's name, and per character the family ROOTS
    # on the roster (alphabetical), id-terminated by 0. Offsets are 2-byte bank-119 pointers.
    spnames = {}
    for line in open(os.path.join(HERE, "prism_species_table.tsv")):
        if line.startswith("#") or not line.strip():
            continue
        p = line.rstrip("\n").split("\t")
        spnames[int(p[0])] = p[1]
    lists = []
    for cid, bm in enumerate(rosters):
        roots = {int(fam[x]["family_root"]) for x in range(1, 256)
                 if bm[x >> 3] >> (x & 7) & 1 and x in fam}
        lists.append(sorted(roots, key=lambda r: spnames.get(r, "~").lower()))
    out.append("")
    out.append('SECTION "CharRosterData", ROMX[$6000], BANK[119]')
    out.append("CharAllNames::   ; 14 bytes per character id, same encoding as CharSelectNames")
    for cid, n in enumerate(names):
        b = enc(n)[:13]          # 'Palette Yellow' is 14: hidden characters can never be active
        b = b + [0x50] + [0x50] * (13 - len(b))
        assert len(b) == 14
        out.append("\tdb " + ", ".join(f"${x:02X}" for x in b) + f"  ; {cid} {n}")
    out.append("CharRosterOffsets::")
    selset = set(sel)
    for cid in range(len(lists)):
        # a character that is never offered can never be active: they share one empty list
        out.append(f"\tdw CharRosterList{cid}" if cid in selset else "\tdw CharRosterListNone")
    out.append("CharRosterListNone:")
    out.append("\tdb 0")
    for cid, lst in enumerate(lists):
        if cid not in selset:
            continue
        out.append(f"CharRosterList{cid}:")
        if lst:
            out.append("\tdb " + ", ".join(str(x) for x in lst) + ", 0")
        else:
            out.append("\tdb 0")
    out.append("")
    out.append('SECTION "CharSelectIdsSect", ROMX[$4E00], BANK[119]')
    out.append("CharSelectIds::")
    for i in range(0, len(sel), 16):
        out.append("\tdb " + ", ".join(str(x) for x in sel[i:i+16]))
    open(os.path.join(HERE, "select_data.asm"), "w").write("\n".join(out) + "\n")
    print("legend flags:", {i: f for i, f in enumerate(flags) if f})
    with open(os.path.join(HERE, "selectable.tsv"), "w") as f:
        f.write("id\tname\tspecies\tfinals\tlegendaries\tselectable\tstarter\tstarter_name\tstarter_src\n")
        for r, st, hw in zip(report, starters, how):
            f.write("\t".join(map(str, r[:5])) + f"\t{int(r[5])}\t{st}\t" +
                    (fam[st]["name"] if st in fam else "-") + f"\t{hw}\n")
    print(f"selectable {len(sel)} of {len(rosters)}; hidden: " +
          ", ".join(r[1] for r in report if not r[5]))


main()
