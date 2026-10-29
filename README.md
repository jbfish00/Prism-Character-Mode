# Character Mode — Pokémon Prism (work in progress)

A port of the "Character Mode" feature to [Pokémon Prism](https://www.pokecommunity.com/threads/pok%C3%A9mon-prism.365538/)
(by Adam "Koolboyman" Vierra) — an opt-in mode where you play as an iconic
character and are restricted to that character's documented Pokémon roster.

**Prism is the odd one out among the Character Mode ports:** it's a Game Boy
Color hack built on the Pokémon Crystal (Gen 2) engine, not a GBA game. That
means a completely different CPU (SM83, not ARM), a pure RGBDS-assembly codebase
(no C layer anywhere), and a different toolchain from the GBA siblings.

> ⚠️ **Work in progress, but playable from a new game.** A new file now asks which
> character to play; the gates below enforce the choice. It has been tested against the
> real routines in an emulator (see `docs/SELECTION_MECHANISM.md`), **not yet played through by
> a person**, and several features the GBA ports have (character art) are not built.

## ▶️ How to turn Character Mode on

1. Apply `build/prism_cm.bps` (made by `tools/make_patch.sh`) to your own copy of
   *Pokemon Prism v0.95 build 254 Hotfix 5* (sha1 in `rom.sha1`). Do not share the patched ROM.
2. Start a **New Game**. After you pick your look and name, a list appears:
   *Normal game* plus the offered characters (117 of 152 slots; the 07-25 audit rosters, no Rijon; see `ROSTERS.md`). Up/Down move, Left/Right page, **A** confirms.
   The highlighted character's portrait shows on the right (105 of the 117 have one; 2026-10-28, sources in `CREDITS.md`).
3. Pick *Normal game* and the hack is invisible. Pick a character and:
   * you can only catch that character's roster (and every on-roster wild Pokemon is caught
     100%); off-roster Pokemon cannot be caught, withdrawn from the PC, or received by an NPC trade;
   * an off-roster gift becomes your character's own starter if you have no Pokemon yet, otherwise it
     is sent to the box;
   * 10% of wild encounters turn into a roster Pokemon, and 1% into one of the character's legendaries
     until you catch it;
   * Surf, Strength, Headbutt, Rock Smash and Cut need no Pokemon that knows them, and Fly and Flash get party-menu rows for any Pokemon;
   * the whole party shares experience (Exp. Share without the item); since 2026-10-21 this also applies
     with Character Mode off;
   * TMs are reusable (Prism already does this);
   * the Moraga Town relearner offers every level-up move, not only up to the Pokemon's level (with Character Mode
     on or off; 2026-10-24);
   * every Mart also sells a Razor Claw or Razor Fang (2100) when your roster has Weavile or Gliscor: no Mart in
     Prism stocks them, so those families could not finish evolving (2026-10-24; every stone is already sold);
   * a new game (no save yet) starts with battle animations off; Options turns them back on (with Character Mode
     on or off; 2026-10-28);
   * START has a **Roster** row (it replaces Exit) listing the character's Pokemon (it showed a blank white screen
     on Game Boy Color until 2026-10-28: fixed).
4. The choice is saved with the game. It cannot be changed afterwards.

**Not built:** the player's overworld sprite and Pokemon icons on the roster screen. Portraits are
missing for 12 characters with no art found yet (Ash, Samson Oak, Adaman, Beni, Chloe, Goh, Ingo, Irida,
Paul, Volo, Zisu, Zoey); the picker leaves the area blank for them. An off-roster **egg** is not refused (same ruling as the other
ports); link trades are vetoed in decision code only (PyBoy has no cable).

The features are tested in a **live harness** (`tools/live_battle.py`: real wild battles, Pack/throw animation and START/party menus in PyBoy); see `docs/SELECTION_MECHANISM.md` section 7.

## Roster scope

Classic Gen 1/2 cast plus Prism's own original cast (Rijon/Naljo region
characters, sourced from the fan-run Rijon Wiki since they have no Bulbapedia
pages). This differs from the GBA ports, which span Gen 1–8.

## Distribution

Patch only (never a redistributed ROM), matching the other Character Mode ports
and standard ROM-hacking norms. Prism is treated as a closed binary and
reverse-engineered directly; the ROM itself is never committed.

## Related projects

Part of a family of Character Mode ports across several Pokémon ROM hacks —
see the Unbound, Lazarus, Radical Red, Seaglass, and ROWE repositories.
