"""Source labels for the sprite rosters. Shared by every hack's sprite-roster emitter (copied beside it
with sprite_sources_master.json). A final evolution F shown for character C is labelled with where C's
canon has a member of F's evolution family: "Emerald" when C had F itself, "as Slowbro — Stadium" when the
source names another family member (the roster rule: a family is canon if any member is)."""
import json, os, re, unicodedata
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
_M = json.load(open(os.path.join(HERE, "sprite_sources_master.json"), encoding="utf-8"))
_DEX = _M.pop("_dex")
_EVOS = [tuple(e) for e in _M.pop("_evos")]   # complete national-dex evolution edges (hack tables miss some Eeveelutions)
_REGION = re.compile(r"^(alolan|galarian|hisuian|paldean|mega|primal|gigantamax)\s+", re.I)
NONE = "Source not recorded"


def _norm(s):
    s = unicodedata.normalize("NFD", s or "")
    return re.sub(r"[^a-z0-9]", "", "".join(c for c in s if unicodedata.category(c) != "Mn").lower())


def dex_of(name):
    # The dex table keys the Nidoran pair as "nidoranu2640" / "nidoranu2642"; _norm drops the symbols, so map them first
    # (2026-11-21: without this both resolved to Nidoran♀, 29).
    name = (name or "").strip().replace("\u2640", "u2640").replace("\u2642", "u2642")
    return _DEX.get(_norm(_REGION.sub("", name)))


def families(edges):
    """edges: iterable of (dex_a, dex_b) evolution links -> dex -> frozenset(family)."""
    adj = defaultdict(set)
    for a, b in list(edges) + _EVOS:
        adj[a].add(b); adj[b].add(a)
    fam, seen = {}, set()
    for d in list(adj):
        if d in seen:
            continue
        comp, todo = set(), [d]
        while todo:
            x = todo.pop()
            if x in comp:
                continue
            comp.add(x); todo.extend(adj[x] - comp)
        seen |= comp
        f = frozenset(comp)
        for x in comp:
            fam[x] = f
    return fam


def label(character, final_dex, final_name, fam):
    """fam: dex -> frozenset of that family's dex ids (from families())."""
    rows = _M.get(re.sub(r" \(anime\)$", "", character)) or _M.get(character) or {}
    members = fam.get(final_dex, frozenset([final_dex]))
    best = None
    for sp, (owned, src) in rows.items():
        d = dex_of(sp)
        if d not in members:
            continue
        od = dex_of(owned)
        rank = (0 if (od == final_dex or d == final_dex) else 1, sp)
        if best is None or rank < best[0]:
            best = (rank, owned, src)
    if not best:
        return NONE
    _, owned, src = best
    if dex_of(owned) != final_dex and owned and owned.lower() not in ("normal", "base", "none", "-"):
        return "as %s — %s" % (owned, src)
    return src


# Documentation rosters list Eevee's evolutions as ONE row (user 2026-11-20: "We can keep those in-game, but let's
# take them off the documentation rosters, so as not to clog it up"). In-game rosters are unchanged; only the docs fold.
EEVEE_DEX = 133
EEVEELUTIONS = frozenset({134, 135, 136, 196, 197, 470, 471, 700})
EEVEE_ROW = "Eevee (any evolution)"


def doc_finals(dexes):
    """National-dex finals -> the list a doc shows: every Eeveelution becomes EEVEE_DEX once, order kept."""
    out, seen = [], set()
    for d in dexes:
        d = EEVEE_DEX if d in EEVEELUTIONS else d
        if d not in seen:
            seen.add(d); out.append(d)
    return out


def doc_name(dex, name):
    return EEVEE_ROW if dex == EEVEE_DEX else name
