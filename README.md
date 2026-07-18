# Character Mode — Pokémon Prism (work in progress)

A port of the "Character Mode" feature to [Pokémon Prism](https://www.pokecommunity.com/threads/pok%C3%A9mon-prism.365538/)
(by Adam "Koolboyman" Vierra) — an opt-in mode where you play as an iconic
character and are restricted to that character's documented Pokémon roster.

**Prism is the odd one out among the Character Mode ports:** it's a Game Boy
Color hack built on the Pokémon Crystal (Gen 2) engine, not a GBA game. That
means a completely different CPU (SM83, not ARM), a pure RGBDS-assembly codebase
(no C layer anywhere), and a different toolchain from the GBA siblings.

> ⚠️ **This project is in progress and not yet playable.** The core catch gate
> is injected and boot-verified, but there is no in-game character-selection
> mechanism yet, rosters are incomplete, and trades aren't handled. See
> `CLAUDE.md`/`docs/` in the working tree for the current status. Don't expect
> a finished patch here yet.

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
