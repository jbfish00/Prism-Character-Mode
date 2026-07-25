# Sprite/asset coverage — Prism Character Mode

## 2026-07-24 — CORRECTION: overworld coverage was undercounted (engine-native sprites)

Every previous coverage number in this file came from cross-referencing ROWE's
`sprite_report.txt`, which records only art ROWE had **staged for injection**.
That silently undercounts overworld sprites, because most of these characters are
NPCs in the games themselves — **this engine already ships their overworld
graphics**. Prof. Oak is the clearest case: the old survey listed him with no
overworld art at all, while both engine families define him
(`OBJ_EVENT_GFX_PROF_OAK` / `EVENT_OBJ_GFX_OAK`). Referencing an existing
graphics id is not an injection job.

Re-surveyed against pokecrystal (`tools/pokecrystal_donor/constants/sprite_constants.asm`, `SPRITE_*`):

**28 of this repo's 76 characters already have an overworld sprite in the
ROM** and need no art sourced:

Red, Blue, Lance, Bruno, Koga, Brock, Misty, Lt. Surge, Erika, Sabrina,
Blaine, Gary, Ethan, Kris, Will, Karen, Janine, Falkner, Bugsy, Whitney,
Morty, Chuck, Jasmine, Pryce, Clair, Silver, Oak, Elm

Cross-repo, counting the engine tables adds **12 characters the old survey called
empty** — Lyra, Oak, Elm, Birch and eight Frontier Brains (Anabel, Tucker, Greta,
Spenser, Noland, Lucy, Brandon, Palmer) — and reclassifies **54 more** from "needs
injecting" to "already there".

Regenerate with `python3 RadicalRed-Character-Mode/tools/survey_engine_ow.py`
(canonical copy lives in the RR repo; it reads every sibling repo's live
`characters.txt`). Visual summary: the "Character Mode — Sprite Coverage by
Character" artifact.

### Three name collisions deliberately NOT counted

CFRU defines `MARLON`, `PENNY` and `MELONY`, but CFRU is Unbound's engine: its
Marlon is Unbound's own protagonist (`MARLON_PLAYER`, `YOUNG_MARLON`,
`MARLON_ARM`), and the engine has no Gen 9 content at all, so its `PENNY` cannot
be the Paldea character. Matching on name alone would have claimed art that does
not depict our character.

### Still open after this correction

1. **Prism's own 27 original characters** (Bronze, the Palette villains, the
   Rijon/Naljo gym leaders and Elite Four) are NPCs in Prism, so their overworld
   art is in this ROM by definition — but Prism's sprite table has never been
   dumped, so none of it is confirmed. They are correctly marked "in-ROM,
   unsurveyed", not "missing".
2. **The GBA sibling repos' Ash Gray donor art does not apply here.** Those blobs
   are GBA 4bpp + BGR555 LZ77; Prism is a Game Boy Color hack (2bpp, GBC
   palettes). Anything sourced for the anime cast here would have to come from a
   GBC-era donor, and none has been surveyed.
3. Prism's roster is the classic Gen 1/2 cast plus Prism originals, so the
   Gen 6-9 "no GBA-style art exists" problem that dominates the other repos does
   not arise — pokecrystal already covers 28 of the 49 non-original characters.


## 2026-07-25 — CORRECTION 2: "no GBA-style art exists for 3D-era characters" is FALSE

> **Prism-specific caveat, read first.** Prism is a Game Boy Color hack (2bpp, GBC palettes).
> Everything below is GBA 4bpp/BGR555 art, so **none of it is directly usable here** — it is
> recorded because the finding is workspace-wide and because it is reference material if anyone
> ever downconverts. Prism's roster is also the classic Gen 1/2 cast plus Prism originals, so the
> Gen 6-9 gap that drove this search barely applies: only 2 of its characters gain anything.
> pokecrystal already covers 28 of Prism's 49 non-original characters natively (see Correction 1).

The claim stated above (and in every sibling repo's copy of this file) that GBA-style pixel art
"genuinely doesn't exist anywhere (official or fan-made) for 3D-model-era characters" is **wrong**.
A five-agent search of fan-games and ROM hacks found it, and the format was verified by measuring
pixels rather than trusting page descriptions.

### Primary source: Pokémon Emerald Rogue (open source, drop-in format)

`https://github.com/Pokabbie/pokeemerald-rogue` (branch `vanilla`) — a pret/pokeemerald decomp fork.
Its `graphics/trainers/front_pics/` is split into `kalos/` (13), `alola/` (14), `galar/` (11),
`paldea/` (12) and `rival/` (Gen 6-9 subset), plus Gen 1-5 casts. **Format verified locally: every
sampled front pic is 64x64, 4-bit colormap, exactly 16 palette entries** — stock pokeemerald format,
zero conversion. Back pics are 64x320 5-frame sheets; overworld sets are 144x32 (9 x 16x32 frames).

Cross-matched against this repo's live `characters.txt`: **2 of its characters gain a
trainer front pic they did not have**:

Lyra, Silver

Workspace-wide the search takes trainer-pic coverage from 76 to 165 of 236 characters, and the
"nothing at all" group from 92 down to 31.

**Cost: attribution.** The repo has no LICENSE and no CREDITS.md. The only credit trail is its
in-game credits roll (`src/data/credits.h`), which lists ~46 artists under "Additional Sprites"
without saying who drew what — so we can credit the project and that roll, but not per sprite.
Several of those names (Beliot419, princess-phoenix, Zender1752, SageDeoxys) are the same DeviantArt
spriters other searches found independently: the repo is best understood as a pre-converted
aggregation of those galleries.

### Secondary sources worth knowing

- **SwSh Ultimate Plus** (PCL.G -> Jeanstars -> Phantonomy; FireRed + CFRU, BPS-distributed) — the
  "Sword and Shield GBA hack". Real, and our Ash Gray rip recipe would apply unchanged. **Rejected as
  primary**: its own README says *"As a non-original dev, I'm not certain where all of the assets
  came from"*, with exactly one Gen 8 sprite attributed. Correct format, unattributable provenance.
- **darklight177 + RHcks Paldea sheet** (DeviantArt) — 8 Paldea leaders + Geeta, trainer pics AND
  overworld strips, measured GBA-native. Free to use, credit RHcks. Adds overworld art Rogue lacks.
- **RichardPT** (DeviantArt) — the only Alain art anywhere: a complete Gen 3 engine set (front, back,
  walking, running, surfing, fishing, town map, VS Seeker). Free with credit.
- **Kalarie's anime overworlds**, PokéCommunity thread 407124 — includes **Paul**, one of the six
  anime characters previously believed to have no art anywhere. Free with credit; needs a dynamic
  overworld palette patch. NOT yet retrieved or verified.
- **Droid779** (Eevee Expo 284) — Gen III-style overworlds for Mallow, Kiawe, Gladion; author takes
  requests.
- **Beliot419 / mid117 / Zender1752** — broad Gen 7-9 coverage including Sada, Turo, Penny and Arven,
  but DS/Gen 5 style at 80x80. Reference for a redraw, not a drop-in.

### Rejected on measurement (do not re-chase)

- mid117's Scarlet/Violet set: DS/Gen 5 style, not GBA.
- xDracolich's Nemona overworld: genuine Gen 3 art but Essentials scale (30x40 per frame vs GBA's
  16x32).
- PokéCommunity 339994: the Gen 6 block is a to-do list with zero image links.
- PokéCommunity 316888 "Kalos Sprites for GBA": Pokémon species only, and every image is a TinyPic
  link — that domain no longer resolves.
- spherical-ice's "Accurate FireRed Overworld Sprite Resource", referenced in our docs for a year:
  Gen 3 trainer *classes* only, nothing past Gen 3.
- Upstream `rh-hideout/pokeemerald-expansion`: ships no Gen 6-9 human character art at all. Adding
  Gen 9 *species* is not the same as adding Gen 9 *humans* — this distinction is the easiest way to
  get a wrong answer here.

### Still unresolved

1. **35 of this repo's characters still have no art of any kind.** Workspace-wide the 31 are
   the anime cast (Drew, Zoey, Nando, Trip, Alain, Sawyer, Tobias, Goh, Chloe, the Alola anime
   four), the professors (Rowan, Juniper, Sycamore, Burnet, Samson Oak, Magnolia, Sonia, Laventon,
   Cerise, Sada, Turo), and Guzma, Plumeria, Lusamine, Rose, Dahlia, Darach.
2. **The anime-arc search never finished** — that agent hit a usage limit having just surfaced a
   Pokesho 64x64 GBA trainer gallery described as free material. Unverified lead, not a finding.
   The "is there an Ash Gray equivalent for the Hoenn/Sinnoh/Unova arcs" question is still open.
3. **The Ash Gray overworld dump is still unlabelled**: 152 sprites, 15 identified. Ritchie and
   Tracey are both in that game so their overworld art is very likely already ripped —
   `ow014`/`ow015` are the candidates. Confirmed so far: `ow050` Jessie, `ow051`/`ow052` James,
   `ow064` Nurse Joy.
4. **Nothing has been staged or injected.** This is a sourcing finding only; `sprite_asset_id` is
   still `0xFFFF` everywhere.
