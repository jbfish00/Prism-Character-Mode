# Toolchain & Phase 1 plan (write-up only — not executed yet, blocked on ROM files)

This captures the research done before any ROM was in hand, so it doesn't need
to be re-derived once `rom/` is populated. Pokemon Prism is a closed-binary
Game Boy Color hack built on the Pokemon Crystal (Gen 2) engine — same overall
situation as `Unbound-Character-Mode`/`RadicalRed-Character-Mode` (reverse-engineer
a compiled ROM, inject into free space, output a patch), but the concrete
toolchain is entirely different because the target CPU/engine generation differs
(SM83/"GBZ80", not ARM7TDMI; pure RGBDS assembly, not C).

## Is there real Prism source? No.

A GitHub repo named "Pokemon Prism source code" exists (`kanzure/pokemon-prism`,
forked as `monhacks/prism`) but is **not a real disassembly of the shipped game**:
2 commits, both dated Jan 2013 — three years before Prism's actual Dec 2016
release/leak. `constants.asm` and `wram.asm` are 0 bytes. `main.asm` is 17 KB
(a genuine Crystal-scale disassembly, cf. pokecrystal, is many MB across hundreds
of files). Treat this as an abandoned early stub, not usable source. Proceed as
closed-binary RE, same posture as the two GBA siblings.

## The Prism-specific shortcut: bindiff against a self-built vanilla Crystal

Unlike Unbound/RadicalRed (whose closest "donor" was an *engine* fork — CFRU/DPE
— with no relation to the actual base game's shipped binary), Prism is a direct
derivative of retail Pokemon Crystal, and `pret/pokecrystal`
(https://github.com/pret/pokecrystal) is a mature, actively-maintained,
byte-matching disassembly that builds a ROM identical (or near-identical,
modulo revision) to a real Crystal cartridge dump.

**Step 1 done and verified (2026-07-12), ahead of having any ROM at all:**
cloned `pret/pokecrystal` into `tools/pokecrystal_donor/`, installed RGBDS
v1.0.1 (prebuilt Linux release, `tools/bin/rgbasm`/`rgblink`/`rgbfix`/`rgbgfx`,
also kept under `tools/rgbds/`), and ran `make RGBDS=../rgbds/`. Output
`pokecrystal.gbc` SHA1 is `f4cd194bdee0d04ca4eac29e09b8e4e9d818c133` — an
**exact match** to the Crystal (UE) (V1.0) checksum pokecrystal's own README
publishes. This is a real, confirmed, byte-identical vanilla Crystal ROM,
not just "should work in theory" — the donor is validated and ready for
step 2 the moment a real Prism ROM is available. (This doesn't need the
user's own Crystal ROM dump at all, since pokecrystal's disassembly already
reproduces the retail ROM from source — the vanilla Crystal ROM asked for in
`rom/README.md` remains useful as a second, independent cross-check, but
isn't load-bearing anymore now that the source build is verified byte-exact.)

Plan for once the Prism ROM is available:
2. Bindiff the built vanilla-Crystal ROM against the real Prism ROM (simple
   byte-level diff first; the two should share large identical regions since
   Prism reuses most of Crystal's engine code, with insertions/relocations for
   new maps/story/content). Large diverging regions of otherwise-similar code
   are the signal for "this is where Prism's own logic lives."
3. Use pokecrystal's labeled routines as anchors — it has readable symbol names
   for exactly the functions Character Mode needs to hook: catch handling
   (`TryCatchingWildMon` and friends), gift Pokemon, in-game trades, PC deposit/
   box-full handling, and the intro/new-game menu. Even where Prism has shifted
   or modified these routines, matching surrounding byte patterns from the
   labeled vanilla routine should localize the Prism equivalent much faster than
   blind search.
4. Cross-check with the text/pointer-search techniques that worked well for
   Unbound/RadicalRed (`search_gametext.py`/`find_pointer_refs.py`-equivalents),
   ported to Gen 2's charmap — pokecrystal's `charmap.asm`-equivalent encoding
   is different from the Gen 3 charmap the GBA siblings reused from ROWE, so
   these scripts need a real charmap swap, not a copy-paste.

## Static analysis: Ghidra GBZ80 support — installed and confirmed (2026-07-12)

No official GBA-style Ghidra loader applies (different CPU). Two community
GBZ80/SM83 loaders/processor modules were evaluated:
- `Gekkio/GhidraBoy` — https://github.com/Gekkio/GhidraBoy — **chosen**:
  actively maintained (last pushed Aug 2025), has prebuilt release zips.
- `CTurt/GameBoy_GhidraSleigh` — https://github.com/CTurt/GameBoy_GhidraSleigh
  — ruled out: no releases, last commit 2020, clearly unmaintained.

**Real incompatibility found**: GhidraBoy officially supports only up to
Ghidra 11.4.2, while `Unbound-Character-Mode`/`RadicalRed-Character-Mode`'s
shared Ghidra install (`tools/ghidra/`, reused across those two subprojects)
is 12.0.2. Confirmed this is a genuine API break, not just an unverified
version-support list: building GhidraBoy from source against the 12.0.2 SDK
fails to compile — `AbstractProgramLoader.getDefaultOptions`/`createProgram`/
`loadProgramInto` signatures changed, and `ghidra.util.HashUtilities` no
longer exists at that path. Not a quick patch; porting GhidraBoy to Ghidra
12.x's loader API is out of scope for this session.

**Resolution**: installed a second, separate Ghidra 11.4.2 instance at
`tools/ghidra_11.4.2/` (gitignored, ~764 MB, does not touch or replace the
GBA siblings' 12.0.2 install) and the prebuilt GhidraBoy 11.4.2 release into
`tools/ghidra_11.4.2/Ghidra/Extensions/GhidraBoy/` (the correct install path
is `<ghidra>/Ghidra/Extensions/`, confirmed by checking where the GBA
siblings' working `gba-ghidra-loader` actually lives — NOT
`<ghidra>/Extensions/Ghidra/`, which is where prepackaged-but-not-yet-installed
extension zips sit, a mistake made and caught this session).

**Verified working end-to-end**: `tools/ghidra_11.4.2/support/analyzeHeadless`
successfully imported the `pokecrystal.gbc` built above —
`Using Loader: Game Boy`, `Using Language/Compiler: SM83:LE:16:default:default`,
`REPORT: Import succeeded`. Static analysis tooling is ready for the real
Prism ROM the moment it's available.

## Injection: RGBDS, not armips — RESOLVED (2026-07-15, session 4)

The GBA siblings use `armips` (Kingcom/armips), which is purpose-built for
"assemble this snippet targeting a specific address inside an existing binary"
— exactly the closed-binary-patching workflow this project needs. RGBDS turns
out to support this natively: **`rgblink -O <existing.gbc>` (overlay mode)**
patches fixed-address sections into a copy of an existing ROM, leaving every
other byte untouched. Proof of concept run and byte-verified this session:

```asm
SECTION "CharacterModePOC", ROMX[$4000], BANK[118]   ; bank 118 = $FF padding
CharacterModePOC::
	ld a, $42
	ld [$D000], a
	ret
```

```bash
tools/bin/rgbasm -o cm.o cm.asm
tools/bin/rgblink -O original.gbc -o patched.gbc cm.o
```

Result: exactly 6 bytes changed (file 0x1D8000-0x1D8005), size unchanged,
patched ROM boots normally in PyBoy. Overlay mode requires every section to
have a fixed BANK/address — fine, that's the whole point. The same mechanism
overwrites *existing code* for hooks (e.g. a section at `ROMX[$7853],
BANK[3]` to splice a hook into the catch handler head). Free space: banks
118-127 are $FF padding (~160 KB). Note Prism's repurposed rst conventions
(see CLAUDE.md session-4 status) when hand-writing hook stubs — `rst $08`
farcall takes 3 inline operand bytes, etc.

`tools/bin/flips` (vendored from the sibling repos, format-agnostic UPS/BPS
patcher) is already confirmed working here and needs no rework for the final
patch-output step.

## Species-id / charmap donor — correction from initial assumption

Originally assumed Prism's roster would stay within vanilla Crystal's Gen 1/2
species cap (IDs 1-251, from `pret/pokecrystal`'s `constants/pokemon_constants.asm`).
**That assumption is wrong.** Confirmed directly from the Rijon Wiki's actual
trainer data (Naljo Elite Four member "Yuki", scraped 2026-07-12): her battle
roster includes Mamoswine, Weavile, Glalie, Froslass, Glaceon — all Gen 4.
Prism's species table is a custom expansion far beyond vanilla Crystal's 251,
analogous to how Dynamic-Pokemon-Expansion expanded FireRed's table for Unbound
— but **no donor for Prism's specific expansion has been identified yet**. This
is an open Phase 1 research gap, not solved by this session's work.

Until a real donor is found (community documentation, Skeetendo/ROM-hacking
forum threads about Prism's engine, or direct RE against the ROM once it's in
hand), `map_species.py` only resolves species names to `pret/pokecrystal`
SPECIES_* constants where the species is actually Gen 1/2 (a real subset, not
the whole roster) and explicitly marks every Gen 3+ species as
`id_source: unresolved` rather than fabricating a numeric id. Do not assume
these are Gen 1/2-only games when they clearly are not.

## Status

**Toolchain de-risking pass done (2026-07-12), everything ROM-independent
confirmed working:**
- RGBDS v1.0.1 installed, verified (`tools/bin/rgbasm`/`rgblink`/`rgbfix`/`rgbgfx`).
- `pret/pokecrystal` builds a byte-identical vanilla Crystal ROM from source
  (SHA1-confirmed against the published checksum) — the bindiff donor for
  step 2 above is validated, not just assumed to work.
- Ghidra 11.4.2 + GhidraBoy GBZ80/SM83 loader installed and confirmed via a
  successful headless import of the built `pokecrystal.gbc`.
- `flips` (vendored) confirmed working since Phase 0.

**ROM acquired and Phase 1 actually started (2026-07-12, later session).**
The user had both `Pokemon Prism v0.95 build 254 (Hotfix 5).zip` and
`Pokemon Prism (v0.94).zip` sitting in the workspace root. Extracted v0.95
Hotfix 5 (newer, 2023-08-25) as the primary target into `rom/`, sha1
`752076692ae3387cf426ce5f51a98c6b60e8df6a`, recorded in `rom.sha1`. v0.94
was not extracted/used but is available if a v0.95-specific offset ever
needs cross-checking. A vanilla Crystal dump was still not supplied/needed —
the byte-verified `pokecrystal_donor` build stands in for it, as already
noted above.

**Real finding: naive positional byte-diff is the wrong tool here.** A raw
`cmp -l` between the Prism ROM and the built vanilla-Crystal donor showed
98.6% of bytes differing — including bank 0, the fixed home bank that's
usually the most stable region across ROM hack variants. This is NOT because
Prism shares little with Crystal; it's because Prism was rebuilt/recompiled
(not binary-patched in place), so even lightly-touched banks are shifted out
of positional alignment. Switched to `bsdiff4` (installed into a dedicated
venv, `tools/bindiff_venv/`, gitignored — `python3 -m venv tools/bindiff_venv
&& tools/bindiff_venv/bin/pip install bsdiff4`), which does suffix-array-based
alignment tolerant of insertions/relocations. The resulting patch is 68.4% of
the raw ROM size (`bsdiff4.diff(crystal, prism)`), and decoding its control
stream (diff/extra/seek triples) gives a real per-bank match percentage:
- Banks 118-127 (the last 160KB) are 100% byte-identical — but confirmed via
  a uniqueness check to be **pure `$FF` padding in both ROMs**, coincidental,
  not a meaningful engine match. Always check `len(set(bank_bytes))` before
  trusting a "100% match" bank.
- Real (non-padding) high-match banks: 70-80 (65-86% match, contiguous run,
  file offset 0x118000-0x140000) and 50-65 (44-71%, scattered) — genuine
  shared engine code, dense byte variety confirmed. These are the best
  starting points for locating stable Crystal-engine routines in Prism.
- `PokeBallEffect` (the actual catch-rate/catch-handling routine, in
  `engine/items/item_effects.asm`, pokecrystal bank 3 / file offset 0xE8A2)
  sits in a LOW-match bank (11.7%) — confirming Prism relocated and/or
  modified this routine specifically, not a surprise given Character Mode
  needs to hook exactly here anyway. An exact byte-signature search (down to
  8 bytes) for `PokeBallEffect`'s opening instructions found **zero** matches
  anywhere in the Prism ROM — real RE (disassembly-based), not a
  byte-matching shortcut, will be needed to relocate this routine.
- Ghidra 11.4.2 + GhidraBoy confirmed importing the **real** Prism ROM
  (`Using Loader: Game Boy`, `SM83:LE:16:default:default`, import succeeded)
  — previously only verified against the vanilla-Crystal test build.

**Text/pointer search (item 4 of the plan above) — built and validated, but
revealed dialogue text is NOT stored in plain charmap bytes.** Wrote
`tools/search_gametext.py`, a Gen 2 charmap encoder/searcher (ported fresh
from the GBA siblings' Gen 3-charmap tool — the encoding tables are
unrelated, not a copy-paste). Validated against the vanilla-Crystal donor:
correctly finds `Text_BallCaught`'s "Gotcha!" string at the exact bank/addr
the donor's own `.sym` file reports (bank 0x71, matching), and finds
thousands of instances of "you"/"your" as expected for ordinary game
dialogue. Against the real Prism ROM: **zero hits** for "Gotcha!", "was
caught", "nickname", "you", "your", "sent to", "BOX is full" — despite these
being common enough that vanilla Crystal has hundreds to thousands of hits
each. This is a real, structural finding, not a tool bug: Prism's
script/dialogue text is very likely stored compressed (a known technique in
other large-scope Gen 2 hacks that need far more script text than vanilla
Crystal's budget allows in the same 2MB), and the decompression routine
hasn't been located yet. **This blocks locating the catch/gift/nickname
dialogue strings via text search until that decompression routine is found**
(real Phase 1 work, likely needs Ghidra analysis of one of the high-match
engine banks above, or of the PrintText-equivalent call path).

**Not all ROM text is compressed, though** — some regions remain plain
Gen2-charmap and were directly readable with the same tool, which is what
led to the species-table breakthrough below:
- A disclaimer/credits blurb ("...based on the Pokémon franchise... Please
  support the official products...") around file offset 0x0061AF/0x015825.
- **The full species name table itself.**

**MAJOR: Prism's species-table expansion donor gap (flagged as unresolved
research 2026-07-12) is now resolved.** Found and fully extracted the ROM's
own internal species-id → name table: a fixed 10-byte-per-record array at
file offset 0x0155E5 (name padded with the `$50` text terminator to 10
bytes; names that are exactly 10 letters, e.g. "Charmander"/"Feraligatr"/
"Typhlosion", have no terminator byte at all — a benign edge case, not a
gap). 255 entries (ids 1-255, consistent with a single-byte species-id
field), ending at the same `Egg`(253)/`Debug`(255) placeholder pattern
vanilla Crystal itself uses at its table's tail — strong independent
confirmation this is the real table, not a coincidental byte run. All 255
decoded cleanly (spot-checked apostrophes/hyphens/gender symbols too).
Saved as `tools/character_mode/prism_species_table.tsv` (committed, not
gitignored — it's essential extracted data, same treatment as the scraper
cache).

**Critical correction this forced**: Prism's species order is a **fully
custom re-ordering**, not vanilla Crystal's Gen 1/2 ordering preserved
in-place as previously assumed. E.g. Prism inserts Chingling/Chimecho at ids
13/14, where Crystal has Weedle/Kakuna/Beedrill; Taillow/Swellow at 19/20
where Crystal has Rattata/Raticate. This means `map_species.py`'s original
approach — using `pret/pokecrystal`'s National-Dex ids as a stand-in for
Prism ids for the "Gen 1/2 subset" — was **wrong even for shared Gen 1/2
species**, not just silently incomplete for Gen 3+. Rewrote `map_species.py`
to resolve against `prism_species_table.tsv` instead (`id_source:
"prism_rom"` replaces the old, now-known-incorrect `id_source: "pokecrystal"`
values — any previously-saved `rosters_mapped.json`/`roster_review.csv` from
before this fix must be treated as stale and re-generated, which has now
been done). Confirms specific rosters flagged earlier as unresolved-gap
cases: Naljo Elite Four member Yuki's Gen 4 additions (Mamoswine id 230,
Weavile id 235, Froslass id 34, Glaceon id 198 — verified directly against
`prism_species_table.tsv`) are now real, resolvable ids, not unresolved gaps.

Re-ran the full pipeline with the corrected donor: 255 Prism species loaded,
65 characters mapped (same character list, unchanged), 0 unmatched
(non-Pokemon) names, 792/1366 total roster species-rows resolved to a real
Prism id (58%), 232 unique species names with no id in Prism's 255-entry
table (up from the old, incorrect 195 — this is an improvement, not a
regression: many of the old "195 unresolved" were undercounts because the
pokecrystal donor spuriously "resolved" some Gen 1/2 names that Prism's real,
smaller, hand-curated 255-species roster doesn't actually contain — those are
now correctly flagged unresolved instead of silently wrong). Same 12 empty
rosters as before (Bronze, 6 Palette Patrollers, 5 of 8 Rijon gym leaders) —
unchanged, this is a scraper-source-data gap (Rijon Wiki has no page/battle
data for them), not a species-mapping issue.

**Update 2026-07-15 (session 4): the first three items below are SOLVED —
text decompression (Huffman, decoder 35:4E14, Python port
`tools/prism_text.py`), catch handler (`PokeBallEffect` ≡ 03:7853, via the
ItemEffects jumptable 03:66F2 and `_DoItemEffect` 03:66DC), and RGBDS
injection (rgblink overlay, see the resolved section above). Full findings
with cross-confirmations live in CLAUDE.md's session-4 status section.
Original list kept for history:**

**Still open, real Phase 1 work:**
- Locate Prism's text-decompression routine (needed before catch/gift/
  nickname dialogue can be found via text search) — real RE work, use the
  high-match banks (70-80, 50-65) as a starting point in Ghidra. **SOLVED.**
- Locate the relocated `PokeBallEffect`-equivalent catch handler — byte
  signature search failed, needs disassembly-based tracing. **SOLVED.**
- The RGBDS-targeted-injection question (see above) — **SOLVED.**
- The 232 species genuinely absent from Prism's roster (`unresolved_ids.txt`)
  — real, not a donor gap; only matters if any roster character's real
  Prism-catchable set turns out to need one of them (unlikely, since these
  are Bulbapedia/anime appearances Prism's curated 255-species world simply
  doesn't include).
