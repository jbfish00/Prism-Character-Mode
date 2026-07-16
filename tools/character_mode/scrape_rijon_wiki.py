#!/usr/bin/env python3
"""Scrape each Prism-original character's documented Pokemon from the Rijon Wiki.

New script (not a port) — Bulbapedia has no page for Prism's own cast, only
the fan-run Rijon Wiki (rijon.fandom.com, MediaWiki/Fandom) does. Shares the
MediaWiki-API-plus-cache core with scrape_bulbapedia.py, but the page
structure is different, and NOT uniform across pages (confirmed empirically
2026-07-12 by dry-running against several real pages before trusting this):

- Pages covering ONLY Prism content (e.g. "Rinji", "Josiah" — Naljo-original
  gym leaders with no other game appearance) have no game-disambiguating
  heading at all; the whole page is Prism content.
- Pages covering MULTIPLE games on one page (e.g. "Karpman", who's a gym
  leader in Pokemon Brown, Prism, AND the unrelated "Rijon Adventures" hack
  that shares this wiki) use level-2 headings like `==Pokémon Prism==` to
  separate sections, and do NOT reliably use a `Party/HeaderPrism`-named
  template inside that section (Karpman's page uses the game-agnostic
  `Party/Header` and relies entirely on the heading for disambiguation).

So this scraper slices by the `==Pokémon Prism==` heading when present, and
falls back to treating the whole page as Prism content when no game headings
exist at all. A page that clearly covers multiple games (has a `Pokémon
Brown`/`Rijon Adventures` heading) but has NO `Pokémon Prism` heading is
flagged as a problem rather than guessed at. Within whichever slice is chosen,
species come from `Pokemon N Name = X` fields inside `{{Party/Pokemon...}}`-
family templates, regardless of which `Party/Header*` variant opened them.

Species names are validated against the SAME Bulbapedia national-dex name
dictionary scrape_bulbapedia.py uses (via load_valid_names below) — Prism's
own trainers use real Pokemon (confirmed Gen 4 species on the Elite Four,
e.g. Mamoswine/Weavile/Froslass), not restricted to Gen 1/2, so the full
all-generation dictionary is the right validator, not a Gen 1/2-only list.

Reads characters.txt (source=rijon entries only), writes/merges into the same
rosters_raw.json scrape_bulbapedia.py writes.

Usage: python3 tools/character_mode/scrape_rijon_wiki.py [--only "Name"]
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
RIJON_API = "https://rijon.fandom.com/api.php"
BULBA_API = "https://bulbapedia.bulbagarden.net/w/api.php"
UA = "Prism-character-mode-research/1.0 (personal ROM hack project; low volume)"

# Matches ONLY exactly-2-equals headings: [^=\n] in the title excludes any
# stray "=" so a 3-equals subheading (`===8 Badges===`) can't be mistaken for
# one (a real bug found 2026-07-12 - a naive `^==.+?==$` matches the first two
# and last two "=" of a 3-equals heading too, collapsing the sliced section).
LEVEL2_HEADING_RE = re.compile(r"^==([^=\n].*?)==$", re.M)
PRISM_HEADING_RE = re.compile(r"pok[eé]mon\s+prism", re.I)
MULTI_GAME_HINT_RE = re.compile(r"pok[eé]mon\s+brown|rijon\s+adventures", re.I)
# Two field-naming conventions coexist on the wiki (confirmed 2026-07-12:
# "Rinji"/"Karpman"/"Elite Four" use `Pokemon N Name = X`; "Ayaka" uses the
# older `NameN = X` form). `Name\d+` (no space before the digit) can't
# collide with the trainer's own `|Name=X` header field, which has no digit.
POKEMON_NAME_RE = re.compile(r"(?:Pokemon\s+\d+\s+Name|Name\d+)\s*=\s*([^\n|}]+)")
PARTY_BLOCK_RE = re.compile(r"\{\{Party/Pokemon\d*\b")
ANY_HEADER_RE = re.compile(r"\{\{Party/Header\w*\b")
NAME_FIELD_RE = re.compile(r"\|\s*Name\s*=\s*([^\n|]+)")


def api_get(api, params, cache_key):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, re.sub(r"[^\w.-]", "_", cache_key) + ".json")
    if os.path.isfile(path):
        with open(path) as f:
            return json.load(f)
    params = dict(params, format="json", redirects="1")
    url = api + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    with open(path, "w") as f:
        json.dump(data, f)
    time.sleep(1.0)  # be polite
    return data


def get_wikitext(page):
    data = api_get(RIJON_API, {"action": "parse", "page": page, "prop": "wikitext"},
                    "rijon_wt_" + page)
    if "error" in data:
        return None
    return data["parse"]["wikitext"]["*"]


def load_valid_names():
    """Reuse Bulbapedia's all-generation national-dex name list as the
    validator — Prism trainers use real, any-gen Pokemon (see module docstring),
    so this is the correct dictionary even though the page itself is scraped
    from a different wiki."""
    data = api_get(BULBA_API, {"action": "parse", "page": "List of Pokémon by National Pokédex number",
                                "prop": "wikitext"}, "natdex_list")
    wt = data["parse"]["wikitext"]["*"]
    names = set()
    for m in re.finditer(r"\{\{rdex\|[^|]*\|[^|]*\|([^|}]+)", wt):
        names.add(m.group(1).strip())
    for m in re.finditer(r"\{\{ndex\|[^|]*\|([^|}]+)", wt):
        names.add(m.group(1).strip())
    if len(names) < 800:
        raise SystemExit("species name list came back too small (%d)" % len(names))
    return names


def slice_prism_section(wikitext):
    """Return (section_text, ambiguous) where ambiguous=True means the page
    clearly covers multiple games but has no `==Pokémon Prism==`-style
    heading to disambiguate (caller should flag this as a problem, not guess)."""
    headings = list(LEVEL2_HEADING_RE.finditer(wikitext))
    prism_heading = None
    is_multigame = False
    for h in headings:
        title = h.group(1)
        if PRISM_HEADING_RE.search(title):
            prism_heading = h
        if MULTI_GAME_HINT_RE.search(title):
            is_multigame = True
    if prism_heading:
        start = prism_heading.end()
        end = len(wikitext)
        for h in headings:
            if h.start() > prism_heading.start():
                end = h.start()
                break
        return wikitext[start:end], False
    if is_multigame:
        return "", True
    # No game-disambiguating headings at all -> single-game (Prism-only) page.
    return wikitext, False


def normalize_wikilink(s):
    """`[[Rinji]]` / `[[Rinji|display]]` -> `Rinji`; plain text passes through."""
    s = s.strip()
    m = re.match(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]$", s)
    return m.group(1).strip() if m else s


def extract_prism_species(wikitext, valid_names, character_name=None):
    """Species names from `Pokemon N Name = X` fields inside any
    `{{Party/Pokemon...}}`-family template within the Prism-relevant slice
    of the page (see slice_prism_section).

    Some pages host MULTIPLE trainers' battle boxes on one page (e.g. "Elite
    Four" documents Yuki/Sora/Daichi/Mura together, and none of those four
    have their own standalone page - confirmed 2026-07-12; note a standalone
    "Mura" page DOES exist but is a same-named, unrelated Pokemon Brown rival,
    a real name collision, not this Mura). When character_name is given and
    the section's `{{Party/Header*}}` blocks carry a `|Name=` field, scope
    extraction to only the blocks whose Name matches. If no blocks carry a
    Name field at all, there's nothing to scope by - fall back to the whole
    section (matches single-trainer pages like "Rinji")."""
    section, ambiguous = slice_prism_section(wikitext)
    header_starts = [m.start() for m in ANY_HEADER_RE.finditer(section)]
    chunks = [section[s:(header_starts[i + 1] if i + 1 < len(header_starts) else len(section))]
              for i, s in enumerate(header_starts)] or [section]

    any_name_field = any(NAME_FIELD_RE.search(c) for c in chunks)
    found = set()
    blocks = 0
    for chunk in chunks:
        if character_name is not None and any_name_field:
            m = NAME_FIELD_RE.search(chunk)
            if not m or normalize_wikilink(m.group(1)) != character_name:
                continue
        blocks += len(PARTY_BLOCK_RE.findall(chunk))
        for m in POKEMON_NAME_RE.finditer(chunk):
            name = m.group(1).strip()
            name = re.sub(r"<[^>]*>", "", name)
            if name in valid_names:
                found.add(name)
    return found, blocks, ambiguous


def load_characters(only_source):
    chars = []
    with open(os.path.join(HERE, "characters.txt")) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            disp, pages, cat = parts[0], parts[1], parts[2]
            gen = int(parts[3]) if len(parts) > 3 else 0
            source = parts[4] if len(parts) > 4 else "bulbapedia"
            if source != only_source:
                continue
            chars.append((disp, [p.strip() for p in pages.split("+")], cat, gen))
    return chars


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]

    valid_names = load_valid_names()
    print("species name dictionary: %d names" % len(valid_names))

    chars = load_characters("rijon")

    out_path = os.path.join(HERE, "rosters_raw.json")
    out = {}
    if os.path.isfile(out_path):
        with open(out_path) as f:
            out = json.load(f)

    problems = []
    for disp, pages, cat, gen in chars:
        if only and disp != only:
            continue
        species = set()
        total_blocks = 0
        any_ambiguous = False
        found_any_page = False
        for page in pages:
            wt = get_wikitext(page)
            if wt is None:
                problems.append("PAGE MISSING: %s (%s)" % (page, disp))
                continue
            found_any_page = True
            page_species, blocks, ambiguous = extract_prism_species(wt, valid_names, disp)
            total_blocks += blocks
            any_ambiguous = any_ambiguous or ambiguous
            species |= page_species
        if not found_any_page:
            continue
        if any_ambiguous:
            problems.append("AMBIGUOUS: %s - page covers multiple games but has no "
                             "'Pokémon Prism' heading to disambiguate — check manually"
                             % disp)
        elif total_blocks == 0:
            problems.append("NO BATTLE DATA: %s (no Party/Pokemon-family template found "
                             "in the Prism-relevant section — check page manually)" % disp)
        elif not species:
            problems.append("EMPTY: %s - %d battle block(s) found but no species names "
                             "validated" % (disp, total_blocks))
        out[disp] = {"page": " + ".join(pages), "category": cat, "gen": gen,
                     "source": "rijon", "species": sorted(species)}
        print("%-14s %3d species (%d battle blocks)"
              % (disp, len(species), total_blocks))
        with open(out_path, "w") as f:
            json.dump(out, f, indent=1, sort_keys=True)

    if problems:
        print("\n--- problems ---")
        print("\n".join(problems))
    print("\nwrote %s (%d characters total, rijon pass)" % (out_path, len(out)))


if __name__ == "__main__":
    main()
