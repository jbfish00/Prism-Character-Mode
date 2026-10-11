#!/usr/bin/env python3
"""Fold the 2026-07-25 adversarial roster audit into Prism's pipeline inputs.

  python3 tools/character_mode/apply_audit.py

Scope (user, 2026-10-10): the rosters of the characters the OTHER Character Mode games implement,
audited; Prism's own Rijon/Naljo originals are out (they stay in the table so ids never move, but
are never offered). So:

  * every existing non-Rijon character's raw roster is REPLACED by the audit's final roster
    (the audit found ~45% of the scraped rows belonged to someone else);
  * every audited character Prism lacks is APPENDED after the existing 76 (append-only: a save
    stores the character id), carrying the metadata ROWE's characters.txt holds for it;
  * Rijon characters keep their rows untouched and are marked hidden by emit_select.py.
Which of the new characters are actually appended is decided by --keep (a file of names the
playability threshold lets through; see derive_new.py). Idempotent: re-running rebuilds from the
backups (*.pre-audit.json) written on the first run.
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
AUDIT = os.path.join(ROOT, "audit_2026-07-25")
ROWE_CHARS = os.path.join(os.path.dirname(ROOT), "Pokemon Rowe Alteration", "tools", "character_mode", "characters.txt")
RAW = os.path.join(HERE, "rosters_raw.json")
ORDER = os.path.join(HERE, "roster_order.txt")


def rowe_meta():
    meta = {}
    for line in open(ROWE_CHARS, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = [x.strip() for x in line.split("|")]
        if len(p) >= 4:
            meta[p[0]] = (p[1], p[2], int(p[3]))
    return meta


def main():
    keep_file = sys.argv[1] if len(sys.argv) > 1 else None
    backup = RAW.replace(".json", ".pre-audit.json")
    if not os.path.exists(backup):
        shutil.copy(RAW, backup)
    raw = json.load(open(backup, encoding="utf-8"))
    final = json.load(open(os.path.join(AUDIT, "final_rosters.json"), encoding="utf-8"))["rosters"]
    meta = rowe_meta()
    # existing order = the current roster_index (alphabetical at the time Prism's ids were pinned)
    existing = sorted(raw)
    replaced = 0
    for c in existing:
        if raw[c].get("source") == "rijon":
            continue
        if c in final and final[c]:
            raw[c]["species"] = sorted(final[c])
            raw[c]["source"] = "audit"
            replaced += 1
    new = [c for c in sorted(final) if c not in raw and final[c]]
    keep = None
    if keep_file and os.path.exists(keep_file):
        keep = set(open(keep_file).read().split("\n")) - {""}
        new = [c for c in new if c in keep]
    for c in new:
        page, cat, gen = meta.get(c, (c, "anime", 8))
        raw[c] = {"category": cat, "gen": gen, "page": page, "source": "audit",
                  "species": sorted(final[c])}
    json.dump(raw, open(RAW, "w", encoding="utf-8"), indent=1, ensure_ascii=False, sort_keys=True)
    with open(ORDER, "w") as f:
        f.write("# character id order (id = line number). The first block is Prism's original 76 (ids pinned);\n"
                "# everything after is appended by apply_audit.py. Never reorder, only append.\n")
        for c in existing + new:
            f.write(c + "\n")
    print(f"existing audited: {replaced} replaced; Rijon left alone: "
          f"{sum(1 for c in existing if raw[c].get('source') == 'rijon')}; new appended: {len(new)}")


main()
