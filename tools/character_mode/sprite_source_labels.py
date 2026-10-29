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
    return _DEX.get(_norm(_REGION.sub("", (name or "").strip())))


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
