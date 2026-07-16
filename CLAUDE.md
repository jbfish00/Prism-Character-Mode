# CLAUDE.md — Pokemon Prism "Character Mode"

Guidance for Claude Code when working in this repo. Keep this file current at
every pause — it's the handoff doc for a fresh instance picking this up cold.

## What this project is

Porting the "Character Mode" feature from the Pokemon ROWE project
(`/home/jbfish00/Documents/Pokemon Rowe Alteration`) to **Pokemon Prism**, a
Game Boy Color hack built on the Pokemon Crystal (Gen 2) engine (Rijon/Naljo
region, by Adam "Koolboyman" Vierra): an opt-in choice to play as an iconic
character, restricted to that character's documented roster (evolution
families included, per the ROWE precedent — though family-normalization isn't
implemented yet here, see Phase 2 status below).

**Roster scope for THIS subproject (user-confirmed 2026-07-12): classic Gen 1/2
cast + Prism's own original cast.** This differs from the GBA siblings
(Unbound-Character-Mode, RadicalRed-Character-Mode), which span Gen 1-8/Alain.
Prism-original characters have no Bulbapedia page — the fan-run Rijon Wiki
(rijon.fandom.com) is the only source for those.

## Critical differences from the other subprojects in this workspace

- **No public Prism source, despite appearances.** A GitHub repo named
  "Pokemon Prism source code" (`kanzure/pokemon-prism`, forked as
  `monhacks/prism`) exists but is an abandoned 2013 stub (2 commits, both
  predate Prism's actual Dec 2016 release; `constants.asm`/`wram.asm` are 0
  bytes). Treat Prism as closed-binary, same posture as Unbound/RadicalRed —
  reverse-engineer the compiled ROM, inject into free space, patch-only
  distribution (see workspace-root `CLAUDE.md`'s distribution policy).
- **Different CPU/engine generation entirely.** GBC (SM83/"GBZ80"), not GBA
  (ARM7TDMI). No C layer anywhere in this lineage — pure RGBDS assembly, like
  pokecrystal. The GBA toolchain (`arm-none-eabi-gcc`, `armips`) doesn't apply;
  needs RGBDS + a GBZ80 Ghidra loader instead. See `docs/TOOLCHAIN.md`.
- **A real RE shortcut the GBA siblings didn't have**: Prism is a direct
  Crystal derivative, and `pret/pokecrystal` is a mature, buildable disassembly
  of vanilla Crystal. Bindiffing a self-built vanilla-Crystal ROM against the
  real Prism ROM, anchored on pokecrystal's labeled routines, should localize
  Prism's catch/gift/trade/PC-deposit logic much faster than blind search.
  Not yet executed — blocked on ROM files. Full plan in `docs/TOOLCHAIN.md`.
- **Prism's species table is a confirmed custom expansion beyond vanilla
  Crystal's Gen 1/2 cap** (Naljo Elite Four member Yuki's team includes
  Mamoswine/Weavile/Froslass/Glaceon — all Gen 4). No donor for that expansion
  is known yet. `map_species.py` only resolves the Gen 1/2 subset against
  `pret/pokecrystal`; everything else is explicitly flagged unresolved, not
  guessed. See `docs/TOOLCHAIN.md`.

## Standing rules (carried over from ROWE/Unbound, user-confirmed pattern)

- **Checkpoint rule**: at every pause, update this file for seamless handoff.
- **Ask questions until 95% confident** before making consequential decisions.
- Distribution: patch only (UPS/BPS via `tools/bin/flips`), never a
  prebuilt/redistributed ROM.
- Every located ROM address will be pinned to the exact SHA1 in `rom.sha1`
  once the ROM lands. Re-verify before trusting notes against a different copy.
- **Flag, don't fabricate.** When a mapping/lookup can't be confirmed (species
  ids beyond Gen 1/2, characters the Rijon Wiki scraper can't cleanly parse),
  write it to an explicit unresolved/problems list rather than guessing or
  silently dropping it. Matches the `unmatched_names.txt`/`PAGE MISSING`/
  `EMPTY` reporting pattern already used in ROWE/Unbound/RadicalRed.

## Repo layout

- `rom/` — gitignored; contains the real Prism ROM as of 2026-07-12 session 2
  (`Pokemon Prism (v0.95 build 254 Hotfix 5).gbc`, see `rom/README.md` for
  the expected contents). A vanilla Crystal ROM was never separately
  supplied/needed — the byte-verified `pokecrystal_donor` build stands in.
- `rom.sha1` — populated (2026-07-12 session 2), see the file for the sha1
  and version-choice note.
- `tools/bindiff_venv/` — gitignored venv for `bsdiff4` (alignment-tolerant
  binary diffing), added session 2. Regenerate with `python3 -m venv
  tools/bindiff_venv && tools/bindiff_venv/bin/pip install bsdiff4`.
- `tools/search_gametext.py` — Gen 2 charmap text search tool, added session 2.
  **Superseded for Prism by `tools/prism_text.py`** (session 4): Prism text is
  Huffman-compressed; `prism_text.py` decodes and searches it (see session 4
  status section).
- `tools/match_code.py` / `tools/sweep_anchors.py` / `tools/prism_anchor_map.tsv`
  — operand-masked SM83 skeleton matcher (donor routine → Prism location) and
  the full-ROM anchor sweep it feeds (session 4).
- `tools/gbdis.py`, `tools/drive.py`, `tools/autoplay.py`, `tools/emu_states/`
  (gitignored), `tools/emu_venv/` (gitignored) — session 3 dynamic-analysis
  rig (PyBoy); see session 4 status section for caveats (gbdis desyncs after
  Prism's inline-operand rst opcodes).
- `tools/character_mode/prism_species_table.tsv` — Prism's real internal
  species-id → name table (255 entries), extracted directly from the ROM,
  added session 2. Committed, not gitignored — see `docs/TOOLCHAIN.md`.
- `docs/ROM_INFO.md` — stub, to fill in once ROM lands.
- `tools/rgbds/`, `tools/ghidra_11.4.2/`, `tools/ghidraboy_src/` — gitignored,
  installed/built this session (see Toolchain status below).
- `docs/TOOLCHAIN.md` — the Phase 1 RE plan (RGBDS, GhidraBoy/GameBoy_GhidraSleigh,
  pokecrystal-bindiff technique, open RGBDS-injection question, species-table
  gap). Written this session, not yet executed.
- `tools/bin/flips` — vendored from the sibling repos (format-agnostic UPS/BPS
  patcher), confirmed working here (`flips --version` → `Flips v1.31`).
- `tools/pokecrystal_donor/` — read-only shallow clone of `pret/pokecrystal`
  (gitignored), the Gen 1/2 species-id + routine-label donor.
- `tools/character_mode/`:
  - `characters.txt` — seed list, classic Gen 1/2 (reused verbatim from ROWE)
    + Prism-original (verified against the live Rijon Wiki API 2026-07-12, not
    guessed from search snippets — see the file's own header comment for what
    was confirmed vs. intentionally excluded, e.g. Silver/Lance's Prism
    reappearances aren't duplicated as separate entries yet).
  - `scrape_bulbapedia.py` — ported verbatim (algorithm unchanged) from
    ROWE/Unbound/RadicalRed's `scrape_rosters.py`; filters to
    `source=bulbapedia` entries.
  - `scrape_rijon_wiki.py` — new script. Keys off the `{{Party/HeaderPrism`
    template (confirmed present on Rijon Wiki trainer pages, isolates
    Prism-specific battle data even on pages that also cover Pokemon Brown or
    the unrelated "Rijon Adventures" hack) to extract species names, validated
    against Bulbapedia's all-generation national-dex name list.
  - `map_species.py` — resolves scraped names against `pokecrystal_donor`'s
    Gen 1/2 national-dex order (`data/pokemon/names.asm`, entries 1-251).
    Does NOT do evolution-family base-stage normalization yet (ROWE's version
    does; this one doesn't — deferred, needs Prism's actual catch-restriction
    semantics from Phase 1 first).
  - `cache/` — committed (not gitignored), same as the sibling repos, so a
    fresh clone doesn't need to re-scrape from scratch.

## Toolchain status (de-risked 2026-07-12, everything ROM-independent confirmed)

- `flips` v1.31 — vendored, confirmed working.
- RGBDS v1.0.1 — installed (`tools/bin/rgbasm`/`rgblink`/`rgbfix`/`rgbgfx`,
  also under `tools/rgbds/`, gitignored).
- `pokecrystal_donor` — **built successfully**, output SHA1
  (`f4cd194bdee0d04ca4eac29e09b8e4e9d818c133`) is an exact match to
  pokecrystal's own published Crystal (UE) (V1.0) checksum. The bindiff
  donor for Phase 1 is verified byte-identical, not just assumed to work.
- GhidraBoy (GBZ80/SM83 Ghidra loader) — installed into a **separate** Ghidra
  11.4.2 instance (`tools/ghidra_11.4.2/`, gitignored, ~764 MB), because it
  doesn't build against the GBA siblings' shared 12.0.2 install (confirmed
  real API break in `AbstractProgramLoader`/`HashUtilities`, not just an
  unverified version-support claim — full detail in `docs/TOOLCHAIN.md`).
  Verified via a successful headless import of the built `pokecrystal.gbc`
  (`Using Loader: Game Boy`, `SM83:LE:16:default:default`, import succeeded).
- Still open: only the RGBDS-targeted-injection question (RGBDS normally
  links a whole ROM from source rather than patching bytes into an existing
  binary — candidate `rgblink --overlay`, unverified). The bindiff/anchor
  work is done — see the session 4 status section.

## Status (2026-07-15, session 4 — Phase 1 substantially closed: catch handler + text decompression FOUND)

**Headline: both remaining Phase 1 unknowns are solved, statically, with
cross-confirming evidence.** All addresses below are file offsets / bank:addr
in the v0.95 build 254 Hotfix 5 ROM (sha1 in `rom.sha1`).

**1. The catch handler: `PokeBallEffect` ≡ Prism 03:7853 (file 0xF853).**
Found via Prism's ItemEffects dispatch chain, all statically confirmed:
- `_DoItemEffect` ≡ 03:66DC — instruction-for-instruction identical to
  vanilla's (03:6722 in the donor), **including identical WRAM addresses**
  (`$d106` wCurItem, `$d265` wNamedObjectIndex, `$d0ec`).
- `ItemEffects` jumptable ≡ 03:66F2, 254 word entries indexed by item-id − 1
  (inline after `rst $28` — see rst conventions below). Common values:
  `$7665` = no-effect (147 items), `$7853` = ball handler (**14 ball items:
  ids 1, 2, 4, 5, 148, 160, 161, 164, 177, 217, 246, 247, 248, 249**).
- The Prism 03:7853 routine head matches vanilla `PokeBallEffect` (donor
  03:68A2) line-for-line with same WRAM/SRAM: `$d22d` wBattleMode, `$dcd7`
  wPartyCount (cp 6), `$ad10` sBoxCount (cp $14 = box size 20), `$c64e`.
- Cross-confirmation: the four shake/miss text pointers loaded inside it
  (`$7b72/$7b87/$7b9d/$7bad`) decode (see item 2) to "Oh no! The POKémon
  broke free!" / "Aww! It appeared to be caught!" / "Aargh! Almost had it!" /
  "Shoot! It was so close too!", and 03:7BC1 = "Gotcha! [mon] was caught!".

**2. Text compression: Huffman, decoder at 35:4E14 (file 0xD4E14).** Prism
text strings are text-command scripts (dispatch loop `DoTextUntilTerminator`
≡ 00:3266; `PrintText` ≡ 00:2F57). Command byte `$03` = Huffman-compressed
text, bitstream inline right after the `$03`. Decoder walks a 256-byte
node-transition table at 35:4E9A (index = index*2 + bit, MSB-first; value
< $70 → next node, ≥ $70 → leaf), leaf post-processing at 35:4F8C with two
escape codes ($7D → 4 raw bits into a 16-entry literal table 35:4F74;
$7C → 6 raw bits range-decoded via delta table 35:4F83). **A working Python
re-implementation is `tools/prism_text.py`** (`--at`/`--script` to decode,
`--search --icase` to find strings ROM-wide) — this replaces
`tools/search_gametext.py` for Prism (which correctly found nothing because
everything is compressed; that mystery is now fully explained).

**3. Prism's repurposed rst vectors (needed to read ANY Prism disassembly
correctly — linear disassembly desyncs after every rst otherwise):**
- `rst $08` (→ $02F5): farcall, **3 inline bytes**: `db bank, dw addr`
  (bank bit7 = tail-call/jump variant).
- `rst $10` (→ $05D3): bank service, **1 inline byte** (e.g. replaces
  vanilla `ld a,BANK / call OpenSRAM/CloseSRAM` pairs).
- `rst $18` (→ $22F7): AddNTimes (hl += bc * a), no inline operand.
- `rst $20` (→ $02A0): farcall-to-hl, **1 inline byte**: `db bank`.
- `rst $28` (→ $14C0): jumptable dispatch on `a`; **2 inline bytes**: either
  the table follows inline (next word's bit7 clear) or `dw table|$8000`
  points elsewhere in the same bank.
- `rst $30` (→ $0BD3): CopyBytes. Vanilla text-command bytes differ too:
  Prism text cmds are $00 (print-from-RAM, dw), $01 (call), $02 (BCD),
  $03 (Huffman text, see above); chars $04-$43 in a text script are far
  fragment refs `[addr_hi−$3C][addr_lo][bank]`.

**4. The operand-masked skeleton matcher works** (`tools/match_code.py`,
new: wildcard 16-bit immediates / `ld a,d8` / relocatable `ldh`, chunked
regex search with delta clustering; `tools/sweep_anchors.py` sweeps every
donor routine and emits `tools/prism_anchor_map.tsv`). Validation: 100%
self-match against the donor; against Prism, 67 of 208 swept bank-0 vanilla
routines survive at ≥50% chunk match (many at 100% — serial, menus, map
objects). Misses are real rewrites, usually because vanilla
`farcall`/SRAM-open sequences became Prism's shorter rst forms (which is
exactly why `PokeBallEffect` itself only matched 6/199 chunks — the routine
is vanilla-shaped but rst-ified throughout). Use the anchor map for
orientation, then eyeball with `tools/gbdis.py` (mind the rst inline
operands).

**Session 3 (2026-07-12/13, was never checkpointed — reconstructed and
salvaged this session):** a PyBoy 2.7.0 dynamic-analysis rig exists and
works. `tools/emu_venv/` (gitignored, regenerable), `tools/drive.py`
(scripted input driver), `tools/autoplay.py` (reads textboxes from the
shadow tilemap at 0xC4A0), `tools/gbdis.py` (linear SM83 disassembler —
predates the rst discovery, output desyncs after rst opcodes with inline
operands; fine between them). Savestates salvaged from that session's
scratchpad into `tools/emu_states/` (gitignored): `ap2.state` is furthest
progress (through the intro, in the intro cave). A GhidraBoy project for the
Prism ROM was also salvaged to `tools/ghidra_prism_proj/` (gitignored).
`.gitignore` updated for all three.

**Remaining Phase 1 item (the only one): the RGBDS targeted-injection
question** — how to assemble/link hook code at chosen free-space offsets and
splice it into the existing ROM (candidate: `rgbasm` + `rgblink --overlay`,
unverified; worst case, assemble with rgbasm and splice bytes with a small
Python patcher, which the rst conventions make easy to hand-author).
After that: Phase 4 design — the Character Mode catch gate hooks into
03:7853's head (species is in WRAM at battle time; vanilla-compatible WRAM
addresses make ROWE's design portable), plus text for the rejection message
(either plaintext via literal chars, or reuse an existing string).

Nothing committed to git yet (still pending user direction). The anchor-map
sweep (`tools/sweep_anchors.py` → `tools/prism_anchor_map.tsv`) takes ~30
min; re-run after any matcher change. Final sweep results (2026-07-15):
12,574 donor routines swept, **1,624 anchors** (654 at 100% chunk match).
Caveats: low-frac/low-chunk rows can be false positives — verify with
`gbdis.py` before trusting; farcall/SRAM-heavy routines (Random,
GetBaseData, TryAddMonToParty, LoadEnemyMon, GivePoke...) are absent
because Prism rst-ified them — find those the way `PokeBallEffect` was
found: preserved dispatch tables, preserved WRAM addresses, and
`prism_text.py --search` text anchors.

**Suggested next session (Phase 4 start): the catch-gate hook.** Hook site
chosen: 03:7896 `ld a,[$d206]; ld [$c64e],a` (wEnemyMonSpecies → wWildMon,
6 bytes — replace with `rst $08; db bank; dw addr` + 2 nops; stub in bank
118 re-executes the displaced pair, checks the active character's roster
bitmap, and either continues or aborts the ball with a rejection message).
Prerequisites to build first: roster binary emitter targeting Prism ids
(Phase 2 pipeline emits none yet), character-selection UI + persistence
(needs a free save-file byte), rejection text (either literal-char string —
chars ≥ $44 print uncompressed — or reuse an existing string).

## Status (2026-07-12, session 2 — ROM acquired, Phase 1 started)

**The blocker from session 1 is cleared.** User had both Prism ROM zips
(`Pokemon Prism v0.95 build 254 (Hotfix 5).zip` and `(v0.94).zip`) sitting in
the workspace root already. Extracted v0.95 Hotfix 5 (newer) into `rom/`,
sha1 `752076692ae3387cf426ce5f51a98c6b60e8df6a`, recorded in `rom.sha1`.
v0.94 is available but unused unless a version-specific offset needs
cross-checking later.

**Phase 1 (reverse engineering) — genuinely started, several concrete
results, not yet gate-closed.** Full detail in `docs/TOOLCHAIN.md`; headline
findings:
- Naive positional `cmp` between Prism and the built vanilla-Crystal donor is
  the wrong tool (98.6% "differ" even in the normally-stable home bank,
  because Prism was recompiled, not binary-patched, so bank alignment
  shifts). Switched to `bsdiff4` (alignment-tolerant), installed in a new
  gitignored venv `tools/bindiff_venv/`. Found real (non-padding-coincidence)
  high-match engine-code bank clusters at banks 70-80 and 50-65 — best
  starting points for Ghidra analysis of shared Crystal-engine routines.
- Ghidra 11.4.2 + GhidraBoy confirmed importing the **real** Prism ROM
  (previously only tested against the vanilla build).
- Built `tools/search_gametext.py` (Gen 2 charmap text search, fresh port —
  different charmap than the GBA siblings' Gen 3 version). Validated against
  the donor. Found the real Prism ROM's dialogue/script text returns **zero**
  hits for common words ("you", "your", "nickname", "Gotcha!") that have
  hundreds+ of hits in vanilla Crystal — strong evidence Prism's script text
  is compressed (common in large-scope Gen 2 hacks), blocking text-based
  location of catch/gift/nickname strings until the decompression routine is
  found.
- The vanilla `PokeBallEffect` catch handler's exact byte signature (down to
  8 bytes) doesn't appear anywhere in Prism — confirmed relocated/rewritten,
  needs real disassembly-based RE, not a byte-match shortcut.

**MAJOR, unplanned win: Prism's species-table expansion donor gap (flagged
unresolved at the end of session 1) is now resolved.** While probing
plain-charmap text regions, found and fully extracted Prism's own internal
species-id → name table directly from the ROM (255 entries, fixed 10-byte
records, file offset 0x0155E5 — see `docs/TOOLCHAIN.md` for the extraction
method and validation). Saved as
`tools/character_mode/prism_species_table.tsv` (committed).

This forced a real correction: Prism's species order is a **fully custom
re-ordering**, not vanilla Crystal's Gen 1/2 order kept in place as
session-1 assumed (e.g. Prism inserts Chingling/Chimecho at ids 13/14 where
Crystal has Weedle/Kakuna/Beedrill). `map_species.py` originally used
pokecrystal's National-Dex ids as a stand-in for Prism ids — **that was
wrong even for shared Gen 1/2 species**, not just incomplete for Gen 3+.
Rewrote it to resolve against `prism_species_table.tsv`
(`id_source: "prism_rom"`); any species ids recorded before this fix are
stale. Re-ran the full pipeline: 65 characters mapped (unchanged), 0
unmatched names, 792/1366 roster species-rows resolved to a real Prism id
(58%), 232 unique species names genuinely absent from Prism's curated
255-species roster (not a donor gap anymore — a real, correctly-flagged
absence; up from the old, silently-wrong 195, since the pokecrystal donor
had been spuriously "resolving" some names Prism doesn't actually contain).
Same 12 empty rosters as before (Rijon Wiki source-data gap, unrelated).

NEXT (real Phase 1 work, not blocked on anything now): (1) find Prism's text
decompression routine via Ghidra, starting from the high-match banks 70-80/
50-65; (2) locate the relocated catch-handler routine via disassembly now
that byte-signature search has ruled out a shortcut; (3) the
RGBDS-targeted-injection question is still open. Nothing has been committed
to git yet — `.gitignore` re-verified with a dry-run `git add -A` this
session (confirms ROM, `tools/bindiff_venv/`, `tools/pokecrystal_donor/`,
`tools/ghidra_11.4.2/` all correctly excluded; new files
`tools/search_gametext.py`, `tools/character_mode/prism_species_table.tsv`,
and the corrected `map_species.py`/`rosters_mapped.json`/`roster_review.csv`
would be staged correctly) — still pending user direction on when to make
the first commit.

## Status (2026-07-12, session 1 — scaffolding, blocked on ROM)

**Phase 0 (scaffolding) — done.** Repo initialized (git, own repo, matches
sibling layout), `.gitignore` adapted for GBC, `rom/`+`rom.sha1` placeholders,
`docs/ROM_INFO.md` stub, `docs/TOOLCHAIN.md` written, `flips` vendored.

**Phase 1 (reverse engineering) — blocked on the Prism ROM, but toolchain
de-risked ahead of time (2026-07-12).** Everything that didn't need the ROM
is now installed and verified: RGBDS, a byte-verified `pokecrystal.gbc`
build (exact SHA1 match to retail Crystal), and a working Ghidra GBZ80
loader (a real Ghidra-12.0.2-vs-GhidraBoy incompatibility was found and
worked around with a separate 11.4.2 install — see Toolchain status above
and `docs/TOOLCHAIN.md`). The actual bindiff and RGBDS-injection questions
remain open until a real Prism ROM is available — nothing to run either
technique against yet.

**Phase 2 (roster data pipeline) — done and tested, independent of Phase 1**
(same pattern as Unbound: this phase needs no ROM). `characters.txt`: 38
classic Gen 1/2 (reused verbatim from ROWE) + 27 Prism-original characters
(verified against the live Rijon Wiki API 2026-07-12, not guessed).

Pipeline run results (2026-07-12):
- `scrape_bulbapedia.py`: all 38 classic characters, **0 problems** (no
  missing pages, no empty rosters, no section failures). Sped up by copying
  `Unbound-Character-Mode`'s existing 25 MB Bulbapedia cache over first
  (same characters, same cache-key scheme, since `scrape_bulbapedia.py` is a
  verbatim port) — the scraper hit cache for nearly everything instead of
  making ~2000 live requests at 1 req/sec.
- `scrape_rijon_wiki.py`: 20 of 27 Prism-original characters got real battle
  data; **7 came back empty, all confirmed as genuine gaps in the Rijon
  Wiki's own documentation, not scraper bugs** (verified by hand-inspecting
  each page's raw wikitext): Bronze (76-char stub, no battle data at all),
  all 6 Palette Patrollers (no individual pages exist; the shared "Palette
  Patrollers" page is pure prose with zero battle templates — their data, if
  documented at all, is scattered across location pages like Route 74/
  Firelight Caverns/Eagulou Gym/Algernon Laboratories, not chased down this
  session), and 5 of the 8 Rijon-region gym leaders (Lois, Sparky, Koji,
  Sheryl, Joe — all short infobox-only stubs; Rijon is less thoroughly
  documented than Naljo on this wiki. Karpman and Lily, the other 2 Rijon
  leaders, DID have full battle data). TODO if this matters later: track
  down the Palette Patrollers' per-location battle boxes; Bronze/the 5 empty
  Rijon leaders may just have no documented data anywhere.
- Building this scraper required two real bug fixes, both because Rijon Wiki
  page structure turned out to be inconsistent across pages (verified by
  dry-running against real pages before trusting any of it, not assumed):
  (1) a naive `^==.+?==$` heading regex matched the first two and last two
  `=` of *3*-equals subheadings too, collapsing the sliced Prism section to
  nearly nothing on pages like "Elite Four" — fixed with an anchored regex.
  (2) two incompatible Pokemon-name field conventions coexist on the wiki
  (`Pokemon N Name = X` on newer pages vs. `NameN = X` on older ones, e.g.
  "Ayaka") — fixed by matching both.
- `map_species.py`: 65 characters mapped, **0 unmatched (non-Pokemon)
  names** (confirms both scrapers' Bulbapedia-name validation held up), 195
  real species with no pokecrystal id (expected — classic characters' anime
  appearances span Gen 3+ Pokemon Bulbapedia documents but pokecrystal's
  Gen 1/2 table can't resolve; correctly flagged unresolved, not guessed),
  12 empty rosters (exactly the 7 Rijon-wiki gaps above, all 6 Palette
  Patrollers counted individually + Bronze + Lois/Sparky/Koji/Sheryl/Joe).
- `.gitignore` verified with `git check-ignore` + a dry-run `git add -A`:
  ROM files, `tools/bin/`, `tools/pokecrystal_donor/`, and `__pycache__/`
  are correctly excluded; `tools/character_mode/cache/` is correctly
  included (matches the sibling repos' convention of committing the cache).

**Phases 3-6 not started** — sprites, injection, and packaging all gated on
Phase 1 (needs the ROM) and, for species-table-dependent work, on finding a
donor for Prism's species-table expansion (open gap, see `docs/TOOLCHAIN.md`).

NEXT: this subproject is now blocked on the user supplying a Prism ROM in
`rom/` before Phase 1 (reverse engineering) can actually start — see
`rom/README.md` (a vanilla Crystal ROM is no longer required, just still
useful as a cross-check). The ROM-independent toolchain de-risking pass is
done: RGBDS installed, pokecrystal builds byte-verified, GhidraBoy 11.4.2
installed and confirmed importing. Until the ROM lands, optional/non-blocking
follow-ups: chase down the Palette Patrollers' scattered per-location battle
data if their roster matters; double-check whether Bronze/the 5 empty Rijon
leaders truly have no documented roster anywhere else (this wiki is the only
source found so far). Nothing has been committed to git yet (matches the
RadicalRed precedent — repo initialized, all files untracked) pending user
direction.
