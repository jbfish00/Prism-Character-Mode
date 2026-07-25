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
