# Prism Character Mode: selection mechanism and gates

Everything here targets `Pokemon Prism (v0.95 build 254 Hotfix 5).gbc` (sha1 in `rom.sha1`).
The overlay is assembled by `tools/build.sh` (`rgbasm` + `rgblink -O`, every section at a
fixed address) and shipped as a BPS patch (`tools/make_patch.sh`). The base ROM is never
modified. `tools/run_tests.sh` builds and runs every test below, plus a `--tamper`
negative control for each.

## 1. Storage (front 1): one byte pair in the SAVED player data

| address | meaning |
|---|---|
| `$DC96` `wCharMode` | `0` = Character Mode off, otherwise **character id + 1** (id order = `tools/character_mode/roster_index.tsv`) |
| `$DC97` `wCharModeCheck` | `wCharMode xor $A5` (validity pair) |

**Why this byte.** Prism's save routine (bank 5) copies WRAM `$D47B` (`$82A` bytes) to SRAM
`$A009`, `$DCA5` (`$32`) to `$A833`, `$DCD7` (`$311`) to `$A865` (and bank-2 WRAM `$D735`,
400 bytes, to `$AB76`); the backup copy is made from WRAM the same way. `$DC87-$DC9C` is
Crystal's `ds 22` padding after `wPhoneList`, inside that block, so the byte is saved,
loaded, checksummed (`05:52BE` over `$A009-$AB75` and `$AB76-$AD05`) and backed up with no
save code touched. No real instruction I disassembled references `$DC93/$DC94/$DC96-$DC9B` (static scan: the
real hits were the phone-list code at `$DC7C-$DC7E` and the new-game list init; the rest sit in
compressed text/data), and random play for 1,500 frames from each of the 16 post-intro savestates
(`tools/tests/soak_padding.py`) never changed the block. The other 4 savestates are intro states,
where the intro's own init rewrites it (next paragraph). This is evidence, not proof.

**What the intro does to it.** The New Game intro saves WRAM, clears it, and restores it
several times (map `127,128` is a scratch world), so the pair dips to `00 FF` transiently and
comes back; `tools/tests/test_intro_persist.py` plays the real intro after the picker and
requires the choice to be intact at the end.

`CM_GetChar` (bank 118, `src/gates.asm`) is the only reader: it returns `a = 0` (off) unless
`$DC96` is `1..76` **and** `$DC97 == $DC96 xor $A5`, so a vanilla Prism save (or any junk in
those bytes) can never switch the mode on.

⚠️ **Ids are positions.** A save stores the id, not the name. Do not insert a character in
the middle of `roster_index.tsv`; append new ones (the Seaglass/Lazarus manifests pin
slots for the same reason). Hidden characters keep their slot.

Verified by `tools/tests/test_persist.py`: the game's own save/load copy routines
(`05:4E8A…4ECB`, `05:50DF…5114`, backup `05:4F0C…4F47`, `05:516B…5193`) round-trip the byte
for four characters; the checksum verify routine (`05:512D`) accepts the saved block and
**rejects it when the SRAM byte holding `$DC96` is flipped**, which proves the checksum covers it.

## 2. New-game hook (front 2)

The New Game intro (`01:5B60..5B89`, "Why not tell me a little about yourself") ends with
`call $5E15` (gender + name) then `ld hl,$5D8D / jp $2F57` (print). The six bytes at `01:5B86`
become `jp CharSelectHook`; `CharSelectHook` (home bank `$3CC7`, 825 bytes of `$FF` filler)
farcalls `CharSelect` (bank 119 `$5000`) and then replays the displaced `ld hl,$5D8D / jp $2F57`.
The intro is reached only from New Game, so the picker always runs for a new file and never for
Continue. `tools/tests/test_select.py` reaches it organically (cold boot, mash the real intro).

## 3. Selection UI (front 3)

A full-screen box over the intro scene: title, 12 visible rows, `>` cursor, A confirms, Up/Down
move (wrapping), Left/Right page by 12, B/Start/Select do nothing. Row 0 is "Normal game".
Names are data (`CharSelectNames`, 14 bytes each, bank 119) written by
`tools/character_mode/emit_select.py`; the tilemap is parked in WRAM bank 7 (`$D000`) and
restored afterwards. Home-bank primitives used (found with `tools/home_vote.py`, which votes
donor symbols onto Prism addresses from the anchored routines; map in `tools/home_map.tsv`):
`ByteFill $0BE1`, `WaitBGMap $0F22`, `DelayFrame $0F45`, `GetJoypad $1386`, `Textbox $2EB2`,
`PlaceString $2FC5` (**hl** = destination here, not bc).

**Playability threshold** (user ruling): a character is offered only with at least six
fully-evolved, non-legendary species on the roster or a legendary on it. **Roster scope
(user, 2026-10-10):** the rosters of the characters the OTHER Character Mode games implement,
as audited (`audit_2026-07-25/final_rosters.json`), not Prism's own Rijon/Naljo originals. So
`tools/character_mode/apply_audit.py` (a) replaced the 49 classic characters' scraped rosters with
the audit's (about 45% of the scrape belonged to someone else), (b) appended every audited
character Prism lacks that clears the threshold in Prism's Gen 1-4 dex (76 of 189; the other 113
are simply not added, so ids stay append-only), and (c) left the 27 Rijon originals in the table
(ids never move) but forced hidden. **152 table slots, 117 offered.** Regional forms resolve to
their ordinary species, a later evolution of a species Prism carries resolves to its family
(`map_species.py` `LATER_EVO_OF`), everything else is dropped as absent from the dex. Professors
Juniper, Magnolia and Sonia end up with empty rosters (their audited teams are all Gen 5+).
**Layout:** the bitmaps are 32 bytes per character, so the table moved to its own bank
(`CharacterModeRosters`, bank 120 `$4000`); every reader goes through `CM_OnRoster`, which reads
the byte with the home bank's far-byte helper (`$004B`). `CharStarters`/`LegendData` moved to bank
118 `$4200`/`$4300`, `CharSelectIds` to bank 119 `$4E00`; the roster screen's name table covers all
ids and its lists only the offered ones (the rest share one empty list).

## 4. Gates (all in bank 118, `src/gates.asm`)

| rule | hook | what it does |
|---|---|---|
| catch gate (shipped earlier) | `03:78CA` | an off-roster species cannot end caught |
| 100% on-roster catch | `03:788C` `CatchBoost` | sets the capture value X >= 256 (the engine's own guaranteed branch, the one a Master Ball uses) so the animation agrees; off-roster X = 0 |
| scripted gifts | `3C:48D7` `GiveGate` | off-roster gift: party empty -> the character's starter instead; party not empty -> the engine's own "party full" path boxes it |
| NPC trades | `3F:4092` `TradeGate` | the species you would RECEIVE is fixed per NPC; off-roster -> offer refused with the CANCEL dialog |
| PC withdraw | `38:6DA7` `WithdrawGate` | off-roster box mon cannot be withdrawn ("Not on the roster!") |
| Exp. Share | `0F:6C3A` `ExpShareHolders` | every alive party mon is a holder (no item needed), **with Character Mode on OR off** (user, 2026-10-21; the catch rules stay CM-only). `test_vanilla_equiv` now checks off == on == alive mask, and that the shipped item rule differs |
| HMs with no learner | `2C:5924` `CheckPartyMoveCM` | Surf, Strength, Headbutt, Rock Smash, Cut answer "found" |
| 1% legendary | `OverrideWildSpecies` | see below |
| roster screen | `04:60E0` `GetMenuItemCM` | with Character Mode on, the START menu's EXIT row is the ROSTER row (section 5b) |
| Fly / Flash with no learner | `09:4707` `MonSubmenuCM` | the party submenu (`GetMonSubmenuItems`, 09:46DA) lists the mon's own field moves, then Stats/Switch/Item. With Character Mode on the two moves that have no overworld interaction, Fly and Flash, are offered to every mon (deduped if it knows one); the row's action keeps its own badge check |
| scripted eggs | `25:658B` `GiveEggGate` | `giveegg` (25:657B) calls `GiveEgg` (3C:4632), which adds the egg unconditionally; an off-roster egg becomes an egg of the character's starter. Day-Care eggs come from on-roster parents and rosters are family-closed, so they pass |
| link-cable trades | `0A:4AA5` `LinkTradeGate` | `LinkTrade`'s confirm (0A:4A96..4AA9): with Character Mode on, an off-roster mon offered to us makes the confirm read as Cancel (the engine's own "trade canceled" text; the partner sees the cancel). Eggs exempt. **Not seen over a real cable**: PyBoy has none, so the real decision code is run with the offered species planted |
| wild 10% override | three hooks (shipped earlier) | unchanged |
| relearner any level (QoL A2, 2026-10-24) | `02:769F` (in-place) | the list builder's `ld a,MON_LEVEL / call GetPartyParam` (wCurPartyLevel $D143) is `ld a,100` + 3 nops, so every learnset move of the mon and its pre-evolutions is listed (deduped; room to $D073). Always on. `test_relearner.py` compares with the `CM_NO_ANYLEVEL` image (Raichu Lv30 +7, Charizard Lv40 +5 moves, each above the level) |
| Mart evolution items (QoL A1, 2026-10-24) | `45:6E8A` `MartEvoAppend` | `ReadMart` (45:6E78) copies the Mart to `wCurMart` ($D0F0: count, items, $FF); its `ld hl,$D002 / ld de,$D0F1` becomes a farcall that, with Character Mode on, appends each `MartEvoPairs` item whose evolved species is on the roster (unless listed; cap 14) and then sets hl/de. Pairs are generated from the ROM by `emit_mart_evo.py` (evolution table bank $10 $5DEF; standard Marts table 45:7DE0): only Razor Fang (Gliscor) and Razor Claw (Weavile) are sold by no Mart (the points shop, mart type 5, has them). Priced shops (types 5-7) have other readers and are untouched. `test_mart.py`: the real ReadMart for 4 discriminating cases + `CM_NO_MART` control, and the real Mart dialog's Buy list |

Mechanics worth knowing (each cost an hour once):
* `rst $08` = farcall (`db bank, dw addr`); **bank bit 7 = jump variant** (tail call: the callee's
  `ret` returns to the caller of the hooked routine). Gates that must abort or resume the
  hooked routine use it (`WithdrawGate`, `TradeGate`, `ExpShareHolders`, `CheckPartyMoveCM`).
* `rst $20 db N` = **predef** N (table `43:4C23`, 3 bytes per entry), not "farcall to hl".
  `rst $20 db $1E` in the catch routine is `PlayBattleAnim`.
* A routine in bank 118 cannot read a table that lives in another bank after a farcall
  returns (bank 118 is mapped again); use `ROM_GetFarByte $004B` (a = bank, hl = address).
* The farcall trampoline preserves a/hl/flags across the call but the callee may clobber
  b/c/d/e (GetTradeAttr clobbers d and e).
* Prism's VBlank ISR requires SP in `$C0xx` and `[$C000..$C001] = 00 FE`; an emulator test
  that calls a routine on a fake stack gets a crash screen ("err 003"). `tools/cmlib.py`
  pushes the park address on the real stack and enters through `CMTestEnter`
  (`ei ; jp hl`, home filler) because PyBoy leaves IME cleared after a PC rewrite.
* Text scripts in bank 56: a plain string needs a SECOND `$50` (the engine skips the
  string's terminator, then expects the script terminator).

**Reusable TMs:** native. `TeachTMHM` (`0B:47BB`) never calls a consume routine (after
`LearnMove`/`IsHM` it only calls `ChangeHappiness` and returns), and TM/HM ownership is a bit
array at `$D859`, not counts. `tools/tests/test_qol.py` pins the bytes.

**Field moves.** Cut, Surf, Strength, Headbutt and Rock Smash go through `CheckPartyMove` (hooked,
above). **Seen live 2026-10-14** (`tools/tests/test_live_obstacles.py`, map 30:6): facing a real Cut
tree, CM on with no learner gets "Want to use Cut?" / "Pikachu used Cut!" and the tree's collision goes
$12 -> $00; CM off with no learner gets no prompt; CM off with a learner cuts (control); no badge, no prompt.
**Waterfall and Whirlpool do not exist as usable obstacles in Prism 0.95**, so there is nothing to
unlock. The A-button dispatcher `TryTileCollisionEvent` (25:5686) compares only $12 (Cut tree) and $15
(Headbutt tree), then goes to `TrySurfOW` (2C:540E), which returns at once while surfing; Crystal's
whirlpool and waterfall branches are gone, and `MonMenuOptions` (09:45EE) has no Whirlpool (5) or
Waterfall (7) row. Live: surfing below a real waterfall ($33, map 30:6 at (4..7,2)), A reaches only
those two routines and up does not move the player, with CM on and no learner AND with CM off and a
mon that knows Waterfall (move $7F, named "Waterfall" in the battle FIGHT menu). A warp scan of groups
1-44 x maps 1-89 found no tile with Crystal's whirlpool collision ($24/$2C). The earlier note that
"2C:5485 / 2C:56CA are the Waterfall/Whirlpool overworld code" was wrong: the party-menu Fly row runs
2C:546C -> 2C:5485 (seen with a PC hook), i.e. 5485 is Fly; 56CA is the first entry of the jumptable
the 04:66A2 party-menu farcall uses, not obstacle code. The hooks do not require the HM item in the bag
(the other ports do); Prism's TM/HM numbering is its own and its move table was not located.

## 5. 1% legendary

`OverrideWildSpecies` asks `LegendPick` first. The per-character flag byte (`CharLegendFlags`,
bit 0 = a legendary is on the roster, bit 1 = the roster is all legendary) is read BEFORE any
random number, so a character with no legendary draws exactly the numbers it always did.
Otherwise one `PCT_ROLL` < 1 picks uniformly among roster legendaries not yet caught (the
Pokedex caught flag at `$DE99`, via `CheckCaughtMon $28E7`); a bit-1 roster stays repeatable.
The level is matched with the same family-stage routine as the 10% override. No shipped Prism
roster is all-legendary, so that branch is tested on a patched ROM copy.

## 5b. Roster screen (START menu)

The START menu (bank 4) resolves an item through one lookup (`04:60E0`: `hl = [$CF97] + 4*de`, a
9-entry table at `04:606F`, entry = function, label; item 7 is EXIT). With Character Mode on
`GetMenuItemCM` returns `CMRosterEntry` (home bank) for item 7: label "Roster", function
`CMRosterFunc` = `FadeToMenu ($1E8E)` / `RosterScreen` (bank 119) / `CloseSubmenu ($1E9F)` / `ld a,0`
(the shape of `StartMenu_Pokegear`). Off, every item resolves as shipped (`test_roster.py` checks
all nine). `RosterScreen` shows "<Name>'s roster", one row per **family root** on the roster in
alphabetical order (a roster is a set, the list is not), the hint "Evolutions count too" in two
lines, scrolls with Up/Down and pages with Left/Right, and leaves on A/B/Start. No icons yet.
⚠️ **Found 2026-10-21: on a real CGB run the roster screen is ALL WHITE** (PyBoy screenshot: one colour). `RosterScreen`
never restores palettes after `FadeToMenu` faded them out; `test_roster.py` reads only the tilemap, so it passes. Fix: call
`SetPalettes` (`00:28A9`) after the first draw, and add a screenshot assertion. Not fixed yet.

## 6. Tests and what they do not show

`tools/run_tests.sh`: gate (255-species sweep), wild override stubs, picker (every entry,
paging, wrap, restore), persistence (real save/load + checksum coverage), intro persistence,
gifts (every selectable character), withdraw, trades (every real NPC trade, both ways),
catch odds (every species), QoL (Exp. Share, HMs, TMs), roster screen (+ the START-menu table),
legendary (rate, uniformity, caught flag, no-RNG for legend-free rosters, all-legendary repeat).
Each has a `--tamper` control that must fail. `build/prism_cm_test.gbc` (`-DCM_TEST`, never
shipped) adds `CMTestWildLoop`, because PyBoy drops to ~30 ms/frame once any PC hook exists and a
30,000-encounter tally has to run inside the emulator.

## 7. The live harness (2026-10-10): real battles and real menus in PyBoy

`tools/live_battle.py` runs the shipped engine, not a routine on a fake stack. The overworld's own
encounter code ends in `jp CallScript` with the script at `25:56DC` (`randomwildmon / startbattle /
reloadmapafterbattle / end`); `run_script()` writes exactly what `CallScript` + `StartScript` leave
behind (`$D438=$FF`, bank/pos at `$D439-$D43B`, script mode `$D437=1`) and the main loop runs it, so
the battle transition, `StartBattle` and `DoBattle` are all the real thing. The wild species/level are
`$D22E`/`$D143` (the two bytes the three wild-roll hooks write). START is the script at `25:5537`
(`open_start_menu`; the intro map disables the START key itself: `$D150` is recomputed every frame).
`give_mon()` adds a mon with the real `TryAddMonToParty` on a throwaway snapshot and copies the party
bytes back (a `cm.call()` leaves the CPU in its park loop, so it can never be the live state).
Map teleport: the recorded recipe (write `$DCB5/$DCB6`, `$D4E6/$D4E7`, `$D432 = 0`) does NOT reload the map (measured
2026-10-14: the intro map stays). What works is the state the `warp` script command leaves: `$DCB5/$DCB6` = group/map,
`$DCB8/$DCB7` = x/y, `$D001 = $FF`, `hMapEntryMethod ($FF9F) = $F1` (MAPSETUP_WARP), `$D432 = 1`, then ~200 frames.
The ball pocket is `$D8EC` (count, then id/qty pairs, `$FF`); the items pocket is `$D866`.

Live tests (all in `run_tests.sh`, each with a `--tamper` control except the species sweep, whose
control is species 0): `test_live_catch.py` (real Pack, real throw animation, verdict from the battle
text), `test_fieldmenu.py` (real START > Pokemon > mon submenu), `test_live_species.py` (all 255
species start a real battle and reach the menu), `test_live_expshare.py` (real KO, bench mon's EXP read
from the party struct), `test_egg.py`, `test_linktrade.py`, `test_live_obstacles.py` (real Cut tree and waterfall on map 30:6, reached
by map teleport: `warp` state = `$DCB5/$DCB6` map, `$DCB8/$DCB7` x/y, `$D001=$FF`, `hMapEntryMethod $FF9F=$F1`,
`$D432=1`; the older recipe `$D4E6/$D4E7` + `$D432=0` does not reload the map).

⚠️ **Prism has its own catch assist.** `03:7D59` counts the caught flags at `$DE99` (32 bytes) and, on a
fresh save, near-guarantees every ball. A catch test on a fresh savestate cannot tell Character Mode's
100% from the engine's own; `test_live_catch.py` marks the dex caught (except the target's byte) for the
cases that measure the rule, and uses the fresh save for the off-roster refusal (where the engine would
have caught it 8/8).

**Still not seen:** a human playing it; a real
cable; the PC and NPC-trade UIs by walking to a Pokemon Center (the routines are called directly).
