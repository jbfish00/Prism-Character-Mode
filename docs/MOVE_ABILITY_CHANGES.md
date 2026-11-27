# Pokémon Prism: move, ability and stat changes

> **Generated 2026-11-26** from the repo manifests by `make_change_docs.py`. Sections 1-3 are in the shipped release; section 4 (Planned) is **not in any release**.
>
> Status: batch 1 + GBC never-miss pushed (Prism e676684).

The change sets here apply with Character Mode on or off (they change the game's move data). Source manifest: `Prism-Character-Mode/tools/character_mode/move_changes.json`.

## 1. Move values

Every move the hack changed is raised to the best value any generation gave it (accuracy, PP, power, effect chance, priority, type). **141 moves changed**: 23 power, 112 pp, 13 accuracy, 27 effect %, 13 type edits. Cells read old → new.

| Move | Power | PP | Accuracy | Effect % | Type |
|---|---|---|---|---|---|
| Double Slap |  |  |  |  | Fairy → Normal |
| Zen Headbutt |  | 15 → 16 |  |  |  |
| Fire Punch |  | 15 → 16 |  | 10 → 30 |  |
| Ice Punch |  | 15 → 16 |  | 10 → 30 |  |
| Thunder Punch |  | 15 → 16 |  | 10 → 30 |  |
| Draining Kiss |  | 10 → 15 |  |  |  |
| Iron Defense |  | 15 → 20 |  |  |  |
| Swords Dance |  | 20 → 30 |  |  | Fighting → Normal |
| Fly |  | 15 → 16 |  |  |  |
| Bug Buzz |  | 10 → 12 |  | 10 → 20 |  |
| Flare Blitz |  | 15 → 16 |  | 10 → 20 |  |
| Brave Bird |  | 15 → 16 |  |  |  |
| Tackle | 40 → 50 |  |  |  |  |
| Body Slam |  | 15 → 16 |  |  |  |
| Double-Edge |  | 15 → 16 |  |  |  |
| Poison Sting | 15 → 30 |  |  | 30 → 50 |  |
| Aura Sphere | 80 → 90 |  |  |  |  |
| Pin Missile |  |  | 95 → 100 |  |  |
| Leer |  |  |  |  | Dark → Normal |
| Sing |  | 15 → 16 |  |  |  |
| Dragon Pulse | 85 → 90 | 10 → 12 | 100 → 101 |  |  |
| Disable |  |  |  |  | Dark → Normal |
| Acid |  |  |  | 10 → 33 |  |
| Ember |  |  |  | 10 → 30 |  |
| Flamethrower | 90 → 95 | 15 → 16 |  | 10 → 20 |  |
| Hydro Pump | 110 → 120 | 5 → 8 | 80 → 85 |  |  |
| Surf | 90 → 95 | 15 → 16 |  |  |  |
| Ice Beam | 90 → 95 | 10 → 12 |  | 10 → 20 |  |
| Blizzard | 110 → 120 | 5 → 8 | 70 → 90 | 10 → 30 |  |
| Bubble Beam |  |  |  | 10 → 33 |  |
| Hyper Beam |  | 5 → 8 |  |  |  |
| Drain Punch |  | 10 → 12 |  |  |  |
| Absorb | 20 → 40 |  |  |  |  |
| Mega Drain | 40 → 75 |  |  |  |  |
| Leech Seed |  | 10 → 12 |  |  |  |
| Growth |  | 20 → 40 |  |  | Normal → Grass |
| Solar Beam | 120 → 200 | 10 → 12 |  |  |  |
| Poison Powder |  |  | 75 → 80 |  |  |
| Stun Spore |  |  | 75 → 80 |  |  |
| Sleep Powder |  | 15 → 20 | 75 → 80 |  |  |
| Hyper Voice |  | 10 → 12 |  |  |  |
| Fire Spin |  | 15 → 16 |  |  |  |
| Thunder Shock |  |  |  | 10 → 30 |  |
| Thunderbolt | 90 → 95 | 15 → 16 |  | 10 → 20 |  |
| Thunder Wave |  |  | 90 → 100 |  |  |
| Thunder | 110 → 120 | 10 → 12 | 70 → 75 |  |  |
| Earthquake |  | 10 → 12 |  |  |  |
| Dig | 80 → 100 | 10 → 12 |  |  |  |
| Toxic |  | 10 → 12 |  |  |  |
| Psychic |  | 10 → 12 |  | 10 → 33 |  |
| Hypnosis |  |  | 60 → 70 |  |  |
| Night Shade |  | 15 → 16 |  |  |  |
| Energy Ball |  | 10 → 12 |  | 10 → 20 |  |
| Double Team |  | 15 → 16 |  |  |  |
| Recover |  | 5 → 20 |  |  | Psychic → Normal |
| Minimize |  | 10 → 20 |  |  |  |
| Smokescreen |  |  |  |  | Poison → Normal |
| Confuse Ray |  | 10 → 12 |  |  |  |
| Head Smash |  | 5 → 8 |  |  |  |
| Barrier |  | 20 → 30 |  |  |  |
| Astonish |  | 15 → 25 |  |  |  |
| Mirror Move |  |  | 100 → 101 |  | Normal → Flying |
| Self-Destruct |  | 5 → 8 |  |  |  |
| Sludge |  |  |  | 30 → 40 |  |
| Thunder Fang |  | 15 → 16 |  | 10 → 20 |  |
| Fire Blast | 110 → 120 | 5 → 8 |  | 10 → 30 |  |
| Waterfall |  | 15 → 16 |  |  |  |
| Flash Cannon |  | 10 → 12 |  | 10 → 20 |  |
| Will-O-Wisp |  | 15 → 16 |  |  |  |
| Soft-Boiled |  | 5 → 10 |  |  |  |
| High Jump Kick |  | 10 → 20 |  |  |  |
| Seed Bomb |  | 15 → 16 |  |  |  |
| Leech Life | 20 → 80 |  |  |  |  |
| Sky Attack | 140 → 200 | 5 → 8 |  |  |  |
| Transform |  | 10 → 12 |  |  |  |
| Bubble |  |  |  | 10 → 33 |  |
| Dizzy Punch |  |  |  |  | Fairy → Normal |
| Acid Armor |  | 20 → 40 |  |  |  |
| Night Slash |  | 15 → 20 |  |  |  |
| Explosion |  | 5 → 8 |  |  |  |
| Poison Jab |  | 15 → 20 |  |  |  |
| Rest |  | 5 → 10 |  |  |  |
| Rock Slide |  | 10 → 12 |  |  |  |
| Meteor Mash | 90 → 100 | 10 → 12 |  |  |  |
| Tri Attack |  | 10 → 12 |  | 20 → 30 |  |
| Dragon Claw |  | 15 → 16 |  |  |  |
| Slash | 70 → 80 |  |  |  |  |
| Substitute |  | 10 → 12 |  |  |  |
| Struggle |  | 1 → 10 |  |  |  |
| Wild Charge |  | 15 → 16 |  |  |  |
| X-Scissor |  | 15 → 16 |  |  |  |
| Mind Reader |  |  |  |  | Psychic → Normal |
| Flame Wheel |  |  |  | 10 → 30 |  |
| Iron Head |  | 15 → 16 |  |  |  |
| Curse |  | 10 → 12 |  |  | Normal → Ghost |
| Flail |  | 15 → 16 |  |  |  |
| Reversal |  | 15 → 16 |  |  |  |
| Spite |  | 10 → 12 |  |  |  |
| Powder Snow |  |  |  | 10 → 30 |  |
| Scary Face |  | 10 → 12 |  |  |  |
| Sweet Kiss |  | 10 → 12 |  |  |  |
| Belly Drum |  | 10 → 12 |  |  |  |
| Sludge Bomb |  | 10 → 12 |  |  |  |
| Mud-Slap | 20 → 30 | 10 → 20 |  |  |  |
| Zap Cannon |  | 5 → 8 |  |  |  |
| Destiny Bond |  | 5 → 8 |  |  |  |
| Perish Song |  | 5 → 8 |  |  |  |
| Icy Wind | 55 → 60 | 15 → 20 |  |  |  |
| Air Slash |  | 15 → 20 |  |  |  |
| Dark Pulse |  | 15 → 16 | 100 → 101 |  |  |
| Earth Power |  | 10 → 12 |  | 10 → 20 |  |
| Outrage |  | 10 → 15 |  |  |  |
| Giga Drain |  | 10 → 12 |  |  |  |
| Endure |  | 10 → 12 |  |  |  |
| Rollout | 30 → 60 |  |  |  |  |
| Swagger |  | 15 → 16 | 85 → 90 |  |  |
| Mean Look |  | 5 → 8 |  |  | Dark → Normal |
| Attract |  | 15 → 16 |  |  |  |
| Sleep Talk |  | 10 → 12 |  |  |  |
| Heal Bell |  | 5 → 8 |  |  |  |
| Dynamic Punch |  | 5 → 8 |  |  |  |
| Megahorn |  | 10 → 12 |  |  |  |
| Encore |  | 5 → 8 |  |  |  |
| Sweet Scent |  |  |  |  | Grass → Normal |
| Iron Tail |  | 15 → 16 |  |  |  |
| Morning Sun |  | 5 → 8 |  |  |  |
| Synthesis |  | 5 → 8 |  |  |  |
| Moonlight |  | 5 → 8 |  |  |  |
| Cross Chop |  | 5 → 8 |  |  |  |
| Twister |  | 20 → 25 |  |  |  |
| Rain Dance |  | 5 → 8 |  |  |  |
| Sunny Day |  | 5 → 8 |  |  |  |
| Crunch |  | 15 → 16 |  |  |  |
| Shadow Claw |  | 15 → 16 |  |  |  |
| Extreme Speed |  | 5 → 8 |  |  |  |
| Ancient Power |  | 5 → 15 |  | 10 → 20 |  |
| Shadow Ball |  | 15 → 16 |  |  |  |
| Future Sight |  | 10 → 15 |  |  |  |
| Rock Smash |  | 15 → 20 |  |  |  |
| Moonblast |  | 15 → 16 |  |  |  |
| Play Rough |  | 10 → 12 |  | 10 → 20 |  |

## 2. Critical hits and move properties

**High critical-hit ratio (+2 stages):** 9 moves: Karate Chop, Razor Leaf, Sky Attack, Night Slash, Slash, Aeroblast, Psycho Cut, Cross Chop, Shadow Claw.

**Properties:**

_none_

## 3. Behaviour changes (moves and abilities)

**pinned by tools/tests/check_behaviour.py at e676684 (13 checks)**

| Card | Kind | What it does |
|---|---|---|
| Dragon Pulse / Dark Pulse never miss (Gen III-V) | move | (no plain-words text in card_histories.txt; see the engine design doc) |
| Disable (Gen IV) | move | Gen I: disables a random move for 0-7 turns. Gen II: the target's last move, 1-7 turns. Gen III: 2-5 turns. Gen IV: 4-7 turns. Gen V onward: exactly 4 turns. Longest is Gen IV. |
| Encore (Gen IV) | move | Duration: Gen II-III 3-6 turns. Gen IV 4-8 turns. Gen V-VI 3 turns. Gen VII onward 3 turns. Longest is Gen IV. |
| Protect (Gen IV) | move | Chance when used repeatedly. Gen II: halves each time. Gen III: halves for three uses, then erratic. Gen IV-V: halves each time, floor 1/8. Gen VI onward: drops to 1/3 each time. Gen II and IV-V keep the best odds. |
| Wrap (Gen VI-VII) | move | Gen I: the target cannot act at all for 2-5 turns while the user is locked into the move. Gen II-IV: 2-5 turns, target can't switch, loses 1/16 HP per turn. Gen V: 4-5 turns. Gen VI onward: 4-5 turns at 1/8 HP per turn. Gen I's full lock is far stronger but is a different mechanic. |
| Roar (Gen V-IX) | move | Same history as Whirlwind. Gen I does nothing; Gen II fails if the user moves first; Gen III-IV can fail against higher-level targets; Gen V onward always works (except Ingrain/Suction Cups). |
| Flail (Gen IV) | move | Power table by remaining HP. Gen IV uses slightly wider HP bands for each tier, so it gives the higher power at more HP values. Gen II has no damage roll and can't crit; Gen III onward can crit. |

**Not done yet in this engine:** Sweet Scent -2 evasion, Astonish / Body Slam vs Minimize, Blizzard in hail, Dream Eater through Substitute, Growth Gen V, Rapid Spin +1 Speed, and the logic cards (Conversion, Conversion 2, Future Sight, Heal Bell, Mirror Move, Roar, Sleep Talk, Teleport). (PRISM.md)

## 4. Planned (NOT in any release)

Everything below is the Pokémon Legacy balance pass (`game_plans/legacy_balance_2026-11-26/`): decisions are closed and the manifests are built, but it is not applied in this repo; nothing here ships until the apply step runs.

### Planned: Pokémon Legacy move values (61 moves)

`from` is the value in the release plus the best-version tier above; Legacy values below the hack's are not applied.

| Move | Power | PP | Accuracy | Effect % | Type |
|---|---|---|---|---|---|
| Double Slap | 15 → 20 | 10 → 35 | 85 → 100 |  | Normal → Fairy |
| Zen Headbutt | 80 → 85 |  | 90 → 95 |  |  |
| Cut | 50 → 60 |  | 95 → 100 |  | Normal → Bug |
| Fly |  |  | 95 → 100 |  |  |
| Wrap | 15 → 30 |  | 90 → 100 |  |  |
| Take Down | 90 → 95 |  | 85 → 100 |  |  |
| Poison Sting | 30 → 35 |  |  |  |  |
| Pin Missile |  | 20 → 30 |  |  |  |
| Supersonic |  |  | 55 → 70 |  |  |
| Dragon Pulse |  | 12 → 15 |  |  |  |
| Acid | 40 → 65 |  |  |  |  |
| Hydro Pump |  | 8 → 10 |  |  |  |
| Ice Beam |  | 12 → 15 |  |  |  |
| Mega Drain |  | 15 → 25 |  |  |  |
| PoisonPowder |  |  | 80 → 90 |  |  |
| Hyper Voice | 90 → 100 |  |  |  |  |
| Fire Spin |  |  | 85 → 100 |  |  |
| Thunder |  |  | 75 → 85 |  |  |
| Rock Throw |  | 15 → 25 | 90 → 95 |  |  |
| Dig |  | 12 → 20 |  |  |  |
| Psychic |  | 12 → 15 |  |  |  |
| Rage | 20 → 60 |  |  |  |  |
| Energy Ball |  | 12 → 15 |  |  |  |
| Head Smash |  |  | 80 → 85 |  |  |
| Astonish | 30 → 50 |  |  |  |  |
| Lick | 30 → 40 |  |  |  |  |
| Smog | 30 → 40 |  | 70 → 100 |  |  |
| Sludge | 65 → 90 |  |  |  |  |
| Flash Cannon | 80 → 90 | 12 → 15 |  |  |  |
| Leech Life |  | 15 → 25 |  |  |  |
| Sky Attack |  | 8 → 10 |  |  |  |
| Dizzy Punch |  | 10 → 20 |  |  |  |
| Night Slash | 70 → 75 |  |  |  |  |
| Signal Beam | 75 → 85 |  |  |  |  |
| Rock Slide | 75 → 80 | 12 → 15 | 90 → 95 |  |  |
| Meteor Mash |  |  | 90 → 95 |  |  |
| Tri Attack | 80 → 85 | 12 → 15 |  |  |  |
| Dragon Claw | 80 → 90 |  |  |  |  |
| X-Scissor | 80 → 85 |  |  |  |  |
| Flame Wheel | 60 → 65 |  |  |  |  |
| Aeroblast |  | 5 → 10 |  |  |  |
| Mach Punch | 40 → 50 |  |  |  |  |
| Feint Attack | 60 → 70 |  |  |  |  |
| Sludge Bomb | 90 → 95 | 12 → 15 |  |  |  |
| Zap Cannon |  | 8 → 10 | 50 → 70 |  |  |
| Icy Wind | 60 → 65 |  | 95 → 100 |  |  |
| Giga Drain |  | 12 → 15 |  |  |  |
| Steel Wing | 70 → 75 |  | 90 → 100 |  |  |
| Psycho Cut | 70 → 75 |  |  |  |  |
| Sacred Fire |  | 5 → 10 |  |  |  |
| DynamicPunch |  | 8 → 10 | 50 → 70 |  |  |
| DragonBreath | 60 → 70 |  |  |  |  |
| Iron Tail |  |  | 75 → 90 |  |  |
| Metal Claw | 50 → 70 |  | 95 → 100 | 10 → 20 |  |
| Cross Chop |  | 8 → 10 | 80 → 90 |  |  |
| Twister | 40 → 70 |  |  |  |  |
| Rain Dance |  | 8 → 10 |  |  |  |
| Sunny Day |  | 8 → 10 |  |  |  |
| ExtremeSpeed |  | 8 → 15 |  |  |  |
| Rock Smash | 40 → 60 |  |  |  |  |
| Play Rough |  | 12 → 15 | 90 → 100 |  |  |

**Planned move effects (9; candidates, the apply step checks each hack's current effect first):**

- Hyper Voice: status:Confusion 30% (emerald L.)
- Sky Attack: one-turn (emerald L.)
- Sky Attack: one-turn (crystal L.)
- Sky Attack: one turn (no charge), no retype, keep 200/90 and current flinch/crit (user note)
- Sky Attack: one-turn (yellow L.)
- Dizzy Punch: status:Confusion 10% (yellow L.)
- Rock Slide: flinch 10% (yellow L.)
- Power Gem: stat:Special Defense-1 20% (xy L.)
- Crunch: defence drop matches Dark's category in this game (user note)

**Skipped (1):** Night Shade (power 1 is a placeholder (fixed/variable damage); Legacy yellow power 60 not applied)

### Planned: base stat changes (80 species)

Species Legacy changed get Legacy's per-stat delta on the hack's own line; a hack-customised line keeps the higher of each stat (user ruling 2026-11-26).

<details><summary>Show the stat table</summary>

| Species | Changes |
|---|---|
| Butterfree | HP 60 → 70, Atk 45 → 35, Def 50 → 60, SpD 80 → 90 |
| Pidgeotto | SpA 50 → 55, SpD 50 → 55 |
| Pidgeot | SpA 70 → 80, SpD 70 → 80 |
| Fearow | Atk 90 → 95, Spe 100 → 105 |
| Vulpix | HP 38 → 48, Def 40 → 45, Spe 65 → 75, SpA 50 → 61, SpD 65 → 70 |
| Ninetales | HP 73 → 78, Atk 76 → 71, Def 75 → 80, SpA 81 → 91 |
| Jigglypuff | Def 20 → 30, SpA 45 → 55, SpD 25 → 30 |
| Wigglytuff | Def 45 → 60, SpA 85 → 90, SpD 50 → 60 |
| Paras | HP 35 → 55, Def 55 → 60, SpD 55 → 60 |
| Parasect | HP 60 → 85, Atk 95 → 100, Def 80 → 90, SpD 80 → 90 |
| Venomoth | Atk 65 → 75, Spe 90 → 100, SpA 90 → 95 |
| Victreebel | Atk 105 → 120, Spe 70 → 75, SpA 100 → 115, SpD 70 → 60 |
| Golem | SpD 65 → 75 |
| Ponyta | Spe 90 → 100 |
| Rapidash | Spe 105 → 115 |
| Onix | HP 35 → 45, Atk 45 → 55 |
| Exeggutor | Atk 95 → 85, SpD 75 → 95 |
| Hitmonlee | Atk 120 → 125, Spe 87 → 97 |
| Hitmonchan | Atk 105 → 115, Def 79 → 84 |
| Weezing | HP 65 → 75 |
| Rhyhorn | HP 80 → 90, SpD 30 → 40 |
| Seaking | Atk 92 → 102, Spe 68 → 78 |
| Flareon | HP 65 → 95, SpA 95 → 65 |
| Articuno | Atk 85 → 75, SpA 95 → 105 |
| Furret | Atk 76 → 86, Def 64 → 74 |
| Ariados | HP 70 → 75, Atk 90 → 100, SpA 60 → 70, SpD 70 → 80 |
| Chinchou | SpA 56 → 66 |
| Lanturn | SpA 76 → 86 |
| Igglybuff | Def 15 → 20 |
| Togetic | HP 55 → 65 |
| Natu | Spe 70 → 75 |
| Xatu | Spe 95 → 105 |
| Ursaring | Atk 130 → 140, Def 75 → 80, SpA 75 → 55, SpD 75 → 80 |
| Slugma | HP 40 → 50, Atk 40 → 70, Def 40 → 60, SpD 40 → 60 |
| Magcargo | HP 60 → 70, Atk 50 → 80, Def 120 → 130, SpA 90 → 100, SpD 80 → 90 |
| Hitmontop | Def 95 → 100, Spe 70 → 80 |
| Ludicolo | HP 80 → 90, SpA 90 → 100 |
| Swellow | SpA 75 → 100 |
| Kirlia | HP 38 → 43, Atk 35 → 40, Def 35 → 40, SpA 65 → 75, SpD 55 → 65 |
| Masquerain | Spe 80 → 100, SpA 100 → 120 |
| Loudred | SpA 71 → 76 |
| Exploud | HP 104 → 114, Def 63 → 73, SpA 91 → 101 |
| Makuhita | HP 72 → 82, Def 30 → 40, SpD 30 → 40 |
| Sableye | HP 50 → 70, Def 75 → 95, Spe 50 → 40, SpD 65 → 95 |
| Mawile | Atk 85 → 95, Def 85 → 95, SpD 55 → 65 |
| Volbeat | HP 65 → 70, Atk 73 → 78, SpA 47 → 97, SpD 85 → 75 |
| Illumise | HP 65 → 80, Def 75 → 95, SpD 85 → 100 |
| Wailmer | Spe 60 → 55, SpA 70 → 85 |
| Wailord | Def 45 → 50, Spe 60 → 45, SpA 90 → 115, SpD 45 → 50 |
| Numel | HP 60 → 70 |
| Camerupt | HP 70 → 90, Atk 100 → 105, Spe 40 → 30, SpA 105 → 110 |
| Torkoal | SpA 85 → 95 |
| Vibrava | HP 50 → 60, Atk 70 → 80, Def 50 → 60, Spe 70 → 80, SpA 50 → 70, SpD 50 → 60 |
| Flygon | SpA 80 → 90 |
| Cacnea | HP 50 → 60, Atk 85 → 70, Def 40 → 55, Spe 35 → 25, SpD 40 → 45 |
| Cacturne | HP 70 → 100, Atk 115 → 80, Def 60 → 90, Spe 55 → 35, SpD 60 → 80 |
| Swablu | HP 45 → 60 |
| Altaria | HP 75 → 85 |
| Lunatone | HP 90 → 110, SpA 95 → 105 |
| Solrock | Atk 95 → 105, Spe 70 → 90 |
| Armaldo | SpA 70 → 60, SpD 80 → 90 |
| Banette | HP 64 → 74, SpA 83 → 93 |
| Chimecho | HP 75 → 85, Def 80 → 90, SpA 95 → 100, SpD 90 → 100 |
| Absol | Spe 75 → 95 |
| Snorunt | HP 50 → 60, Atk 50 → 60, Def 50 → 60, Spe 50 → 60, SpA 50 → 60, SpD 50 → 60 |
| Glalie | HP 80 → 85, Atk 80 → 85, Def 80 → 85, Spe 80 → 85, SpA 80 → 85, SpD 80 → 85 |
| Relicanth | Atk 90 → 110 |
| Shinx | HP 45 → 50, Atk 65 → 70, SpA 40 → 30 |
| Luxio | HP 60 → 70, Atk 85 → 90, SpA 60 → 45 |
| Luxray | HP 80 → 90, Atk 120 → 130, SpA 95 → 75 |
| Rampardos | HP 97 → 107, Spe 58 → 63, SpA 65 → 60 |
| Bastiodon | HP 60 → 80, Spe 30 → 20 |
| Drifloon | Atk 50 → 40, SpA 60 → 70 |
| Drifblim | Atk 80 → 60, SpA 90 → 110 |
| Lopunny | Atk 76 → 81, Spe 105 → 130, SpA 54 → 44 |
| Mismagius | Spe 105 → 110, SpA 105 → 110, SpD 105 → 110 |
| Chingling | SpA 65 → 70 |
| Spiritomb | Atk 92 → 108, Spe 35 → 23, SpA 92 → 108 |
| Dusknoir | HP 45 → 65, Atk 100 → 110, Def 135 → 130, Spe 45 → 25, SpD 135 → 130 |
| Froslass | HP 70 → 75, Atk 80 → 85, Def 70 → 75, Spe 110 → 115, SpA 80 → 85, SpD 70 → 75 |

</details>

Not built yet: 92 Mega / form stat rows.

### Planned: species ability changes (0 slots)


### Planned: learnset changes (857 moves added, 810 moves learned earlier)

Moves this engine lacks (skipped): 1345 entries across 277 moves.
<details><summary>Show the learnset changes</summary>

| Species | Added | Earlier |
|---|---|---|
| Bulbasaur | Acid L13, Seed Bomb L30, Body Slam L34, Energy Ball L40 | Vine Whip L10→L9, Sleep Powder L29→L11, Poison Powder L13→L11, Sweet Scent L17→L16, Sludge L26→L25 |
| Ivysaur | Acid L10, Seed Bomb L30, Body Slam L34, Energy Ball L40 | Sleep Powder L33→L11, Sweet Scent L17→L16, Razor Leaf L25→L20, Sludge L29→L25, Growth L49→L27, Synthesis L41→L39, Sludge Bomb L45→L43, Solarbeam L57→L46 |
| Venusaur | Acid L10, Poison Powder L11, Seed Bomb L30, Body Slam L34, Energy Ball L40, Ancientpower L50 | Sleep Powder L34→L11, Growth L54→L27, Synthesis L44→L39, Sludge Bomb L49→L43, Solarbeam L64→L46 |
| Charmander | Leer L13, Fire Punch L19, Flame Wheel L19, Dragon Claw L38, Body Slam L42, Fire Blast L52 | Rage L17→L13, Fire Spin L20→L15 |
| Charmeleon | Fire Punch L19, Flame Wheel L19, Scary Face L25, Flamethrower L31, Dragon Claw L38, Body Slam L42, Fire Blast L52 | Rage L18→L13, Fire Spin L22→L15, Bite L26→L23, Slash L30→L29 |
| Charizard | Rage L13, Fire Punch L19, Flame Wheel L19, Scary Face L25, Flamethrower L31, Body Slam L42, Fire Blast L52 | Outrage L66→L48 |
| Squirtle | Rapid Spin L17, Body Slam L27, Waterfall L33, Ice Beam L45 | Bubble L17→L5, Bite L20→L15, Protect L23→L20, Bubblebeam L26→L21 |
| Wartortle | Body Slam L27, Waterfall L33, Ice Beam L45 | Bubble L18→L12, Bite L22→L15, Protect L26→L20, Bubblebeam L30→L21, Rain Dance L42→L33, Iron Defense L38→L33, Hydro Pump L62→L47 |
| Blastoise | Bubble L12, Rapid Spin L17, Body Slam L27, Waterfall L33, Ice Beam L45 | Dragon Pulse L49→L1, Rain Dance L44→L33, Iron Defense L39→L33, Hydro Pump L74→L47 |
| Butterfree | Leech Life L10, Supersonic L17, Whirlwind L21, Giga Drain L27, Psychic L32 | Gust L16→L15, Psybeam L26→L20, Bug Buzz L44→L40 |
| Pidgey | Mud-Slap L24, Sky Attack L42, Hyper Voice L49 | Gust L7→L6, Quick Attack L13→L10, Whirlwind L34→L13, Mirror Move L46→L39 |
| Pidgeotto | Mud-Slap L24, Sky Attack L42, Hyper Voice L49 | Whirlwind L39→L13, Wing Attack L20→L18, Air Slash L35→L31, Mirror Move L55→L39 |
| Pidgeot | Twister L16, Wing Attack L18, Mud-Slap L24, Extremespeed L36, Sky Attack L40, Hyper Voice L49 | Whirlwind L41→L13, Mirror Move L61→L39, Brave Bird L56→L53 |
| Spearow | Focus Energy L7, Swift L18, Take Down L21, Whirlwind L28, Brave Bird L43 | Leer L22→L4, Aerial Ace L19→L15, Mirror Move L34→L18, Drill Peck L43→L24 |
| Fearow | Focus Energy L1, Pursuit L12, Swift L18, Take Down L21, Whirlwind L28, Brave Bird L43 | Mirror Move L39→L18, Drill Peck L54→L24 |
| Pikachu | Headbutt L18, Light Screen L40, Iron Tail L44, Thunder L48 | Quick Attack L13→L6, Thunder Wave L34→L10, Spark L19→L13, Thunderpunch L31→L20 |
| Raichu | Headbutt L18, Thunderbolt L30, Light Screen L40, Thunder L41, Iron Tail L44 | Growl L5→L1, Thunder Wave L48→L1, Nasty Plot L68→L1, Quick Attack L20→L6, Tail Whip L15→L11, Spark L28→L13, Double Team L24→L15, Thunderpunch L44→L20, Agility L32→L30 |
| Vulpix | Flame Wheel L19, Reflect L25, Safeguard L27, Shadow Ball L36, Night Shade L37, Sunny Day L40, Fire Blast L40 | Tail Whip L4→L1, Roar L10→L4, Fire Spin L19→L11, Confuse Ray L22→L14, Will-O-Wisp L28→L22, Flamethrower L43→L30 |
| Ninetales | Flame Wheel L19, Reflect L25, Shadow Ball L36, Night Shade L37, Sunny Day L40, Fire Blast L40 | Tail Whip L4→L1, Roar L10→L1, Ember L7→L1, Fire Spin L25→L11, Confuse Ray L30→L16, Will-O-Wisp L38→L17, Feint Attack L20→L17, Flamethrower L58→L29 |
| Jigglypuff | Charm L7, Disable L10, Rest L24, Body Slam L25, Encore L33, Double-Edge L41 | Defense Curl L10→L3, Double Slap L19→L8, Rollout L13→L12, Play Rough L43→L33, Hyper Voice L40→L36, Moonblast L52→L51 |
| Wigglytuff | Charm L7, Rest L24, Body Slam L25, Encore L33, Double-Edge L39 | Rollout L13→L12, Hyper Voice L40→L36, Moonblast L52→L51 |
| Zubat | Swift L19, Acid L27, Sludge L27 | Gust L7→L4, Bite L16→L11, Wing Attack L19→L14, Confuse Ray L33→L17, Haze L47→L34 |
| Golbat | Gust L1, Supersonic L5, Swift L19, Acid L27, Sludge L27 | Confuse Ray L41→L17, Haze L57→L34 |
| Paras | Absorb L3, Swords Dance L37, Moonlight L46 | Stun Spore L13→L6, Mega Drain L16→L13, Growth L40→L15, Giga Drain L37→L26, Seed Bomb L49→L34 |
| Parasect | Absorb L1, Poisonpowder L13, Swords Dance L37, Moonlight L46 | Growth L48→L15, Giga Drain L44→L26, Seed Bomb L60→L34, X-Scissor L52→L43 |
| Venonat | Zen Headbutt L30 | Supersonic L13→L4, Confusion L10→L7, Poison Powder L16→L9, Stun Spore L28→L18, Psybeam L25→L21, Sleep Powder L28→L26 |
| Venomoth | Confusion L7, Poison Powder L9, Leech Life L12, Gust L23, Acid L25, Signal Beam L36, Air Slash L38 | Zen Headbutt L41→L30, Psychic L57→L41, Sludge Bomb L49→L42 |
| Growlithe | Growl L1, Flamethrower L35, Extreme Speed L49 | Ember L7→L1, Leer L10→L6, Flame Wheel L19→L13, Take Down L28→L16 |
| Arcanine | Growl L1, Reversal L19, Flamethrower L35, Outrage L50 | Bite L20→L1, Agility L30→L1, Ember L7→L1, Leer L10→L6, Flame Wheel L25→L13, Take Down L38→L16, Crunch L50→L42, Flare Blitz L58→L55 |
| Machop | Take Down L33, Double-Edge L54 | Focus Energy L10→L3, Foresight L13→L9, Seismic Toss L16→L15, Counter L41→L37 |
| Machoke | Focus Energy L7, Foresight L9, Karate Chop L13, Body Slam L33, Double-Edge L54 | Counter L46→L37, Dynamic Punch L50→L49 |
| Machamp | Karate Chop L1, Focus Energy L7, Foresight L9, Take Down L33, Double-Edge L54 | Counter L51→L37, Dynamic Punch L56→L49 |
| Bellsprout | Sweet Scent L1, Headbutt L27, Body Slam L30, Sludge Bomb L32 | Growth L28→L5, Wrap L10→L8, Acid L13→L12, Sleep Powder L40→L14 |
| Weepinbell | Poisonpowder L1, Sweet Scent L1, Headbutt L27, Body Slam L30, Sludge Bomb L32 | Sleep Powder L47→L14, Sludge L27→L25 |
| Victreebel | Poisonpowder L13, Vine Whip L14, Headbutt L27, Body Slam L30, Sludge Bomb L32 | Growth L34→L1, Sludge L29→L25 |
| Tentacool | Water Gun L13, Sludge L25, Sludge Bomb L34 | Poison Sting L7→L1, Bubble L13→L1, Supersonic L4→L1, Acid L19→L6, Bubble Beam L25→L19, Poison Jab L43→L29 |
| Tentacruel | Bubble L1, Water Gun L13, Wrap L15, Sludge L20, Sludge Bomb L34 | Poison Jab L52→L29, Screech L37→L36, Hydro Pump L57→L47 |
| Geodude | Rapid Spin L1, Dig L21 | Defense Curl L29→L6, Mud-Slap L7→L6, Rock Throw L10→L9, Magnitude L32→L13 |
| Graveler | Rapid Spin L1, Mud-Slap L6, Rock Throw L9, Dig L21, Harden L26, Double-Edge L52 | Magnitude L35→L13, Earthquake L51→L40, Explosion L47→L45 |
| Golem | Rapid Spin L1, Mud-Slap L6, Rock Throw L9, Dig L21, Harden L26, Double-Edge L52 | Magnitude L38→L13, Rock Slide L43→L40, Earthquake L58→L40, Explosion L53→L45 |
| Ponyta | Take Down L22, Sunny Day L25, Flamethrower L33, High Jump Kick L42, Fire Blast L45, Double-Edge L49 | Fire Spin L19→L1, Ember L7→L6, Stomp L22→L9, Double Kick L16→L14, Flame Wheel L28→L20 |
| Rapidash | Fire Spin L1, Tackle L1, Stomp L9, Double Kick L14, Take Down L22, Sunny Day L25, Flamethrower L33, Agility L34, Hi Jump Kick L40, Fire Blast L45, Double-Edge L49 |  |
| Slowpoke | Psybeam L25, Waterfall L28 | Water Gun L7→L5, Headbutt L25→L18 |
| Slowbro | Tackle L1, Growl L5, Water Gun L5, Confusion L11, Disable L15, Psybeam L25, Waterfall L28, Zen Headbutt L31, Rain Dance L48 |  |
| Magnemite | Reflect L27, Tri Attack L30, Thunder L50 | Supersonic L4→L3, Thundershock L7→L6, Thunder Wave L16→L11, Spark L19→L17, Swift L25→L24, Thunderbolt L44→L33, Light Screen L41→L40 |
| Magneton | Supersonic L11, Thunder Wave L11, Screech L19, Reflect L27, Light Screen L40, Thunder L50 | Tri Attack L48→L30, Thunderbolt L53→L33 |
| Gastly | Poison Gas L23 | Smog L7→L4 |
| Haunter | Smog L1, Dream Eater L35 | Shadow Ball L43→L42 |
| Gengar | Smog L1, Dream Eater L35 | Shadow Ball L48→L42 |
| Onix | Rage L6, Dig L18, Harden L29, Double-Edge L46 | Rock Throw L14→L4, Rock Slide L40→L30, Screech L49→L30, Earthquake L46→L40 |
| Exeggcute | Psybeam L28, Giga Drain L31, Soft-Boiled L45 | Reflect L7→L5, Leech Seed L19→L9, Sleep Powder L40→L19 |
| Exeggutor | Giga Drain L1, Leech Seed L9, Psybeam L28, Growth L30, Soft-Boiled L45 | Reflect L7→L1, Stomp L25→L13, Stun Spore L20→L17, Sleep Powder L54→L19, Psychic L46→L45 |
| Hitmonchan | Karate Chop L25, Dizzy Punch L39 | Foresight L10→L1, Agility L32→L4, Bullet Punch L20→L14, Drain Punch L40→L20, Ice Punch L48→L27, Thunder Punch L36→L27, Fire Punch L44→L27 |
| Koffing | Rapid Spin L1, Amnesia L26 | Selfdestruct L16→L15, Sludge L22→L16, Haze L40→L22, Sludge Bomb L46→L36 |
| Weezing | Smokescreen L15, Sludge L16, Self-Destruct L20, Acid L23, Amnesia L26 | Haze L42→L22, Sludge Bomb L50→L35, Destiny Bond L55→L43 |
| Rhyhorn | Rock Throw L12, Dig L24, Take Down L29, Megahorn L45, Double-Edge L56 | Stomp L16→L9, Magnitude L31→L23, Rock Slide L37→L36, Earthquake L43→L39 |
| Rhydon | Rock Throw L12, Dig L24, Take Down L29, Megahorn L45, Double-Edge L56 | Earthquake L44→L39 |
| Chansey | Take Down L17, Defense Curl L33, Light Screen L37 | Tail Whip L7→L4, Double Slap L10→L8, Softboiled L40→L10, Minimize L46→L18, Sing L28→L22 |
| Tangela | Energy Ball L43 | Absorb L14→L1, Mega Drain L22→L19, Stun Spore L31→L23, Sleep Powder L43→L25, Giga Drain L46→L31, Body Slam L65→L37 |
| Kangaskhan | Tail Whip L1, Double-Edge L48 | Focus Energy L20→L8, Bite L25→L12, Dizzy Punch L39→L25, Crunch L42→L36, Body Slam L45→L37, Endure L54→L41, Reversal L51→L44 |
| Goldeen | Bubble L1, Drill Peck L27 | Water Gun L7→L3, Supersonic L10→L6, Flail L34→L13, Waterfall L28→L15, Swords Dance L31→L30, Megahorn L43→L35 |
| Seaking | Bubble L1, Water Gun L1, Supersonic L1, Drill Peck L27, Rain Dance L32 | Flail L35→L13, Megahorn L47→L35 |
| Scyther | Cut L15, Double Team L31 | Leer L10→L1, Fury Cutter L37→L1, Agility L31→L24, Wing Attack L34→L30, X-Scissor L49→L40, Night Slash L55→L44 |
| Electabuzz | Thundershock L1, Spark L17, Thunderbolt L42 | Thunder Wave L48→L16 |
| Magmar | Smokescreen L6, Smog L10, Leer L15, Flame Wheel L17, Will-O-Wisp L22, Fire Punch L25, Sunny Day L30, Flamethrower L39, Dark Pulse L48 | Confuse Ray L36→L20 |
| Gyarados | Gust L20 | Leer L25→L1, Waterfall L34→L25, Twister L30→L26, Crunch L54→L41 |
| Eevee | Sand Attack L4, Quick Attack L6, Bite L9, Growl L11, Double Kick L14, Charm L20, Headbutt L22, Focus Energy L30, Baton Pass L30 |  |
| Vaporeon | Bubble L1, Growl L1, Icy Wind L1, Quick Attack L6, Double Kick L14, Rest L47 | Sand Attack L10→L4, Bite L30→L17, Bubblebeam L34→L26, Haze L60→L39, Acid Armor L42→L41, Hydro Pump L57→L49, Ice Beam L54→L52 |
| Jolteon | Growl L1, Quick Attack L6, Bite L17, Spark L26, Thunderbolt L36, Zap Cannon L52 | Sand Attack L10→L4, Double Kick L30→L14, Pin Missile L42→L30, Thunder L57→L49 |
| Flareon | Leer L1, Growl L1, Quick Attack L6, Double Kick L14, Flame Wheel L26, Will-O-Wisp L35, Double-Edge L36, Play Rough L48, Fire Blast L52 | Sand Attack L10→L4, Fire Spin L34→L12, Scary Face L42→L22, Flamethrower L45→L36 |
| Porygon | Signal Beam L24, Hyper Beam L50 | Psybeam L22→L4, Swift L14→L10, Recover L44→L14, Tri Attack L50→L28, Barrier L47→L40 |
| Snorlax | Rollout L25, Harden L33 | Crunch L46→L44 |
| Articuno | Drill Peck L40, Air Slash L40 | Heal Bell L80→L1, Mist L15→L5, Haze L35→L13, Mind Reader L100→L20, Ancient Power L40→L25, Agility L70→L35, Sky Attack L60→L55, Blizzard L90→L70 |
| Zapdos | Wing Attack L1, Thunderbolt L45 | Thunder Wave L35→L5, Ancient Power L40→L25, Agility L80→L35, Drill Peck L95→L42, Sky Attack L60→L55, Baton Pass L70→L61, Thunder L90→L70 |
| Moltres | Whirlwind L1, Endure L10, Growth L20, Drill Peck L40, Flamethrower L45 | Ember L7→L1, Fire Spin L25→L5, Ancient Power L40→L25, Agility L70→L35, Air Slash L95→L40, Fire Blast L90→L51, Sky Attack L60→L55, Solar Beam L100→L65 |
| Mew | Sky Attack L1, Iron Tail L1, Icy Wind L1, Hyper Voice L10, Confusion L15, Psybeam L25 | Soft-Boiled L74→L1, Zen Headbutt L50→L30 |
| Chikorita | Mega Drain L21, Giga Drain L26, Seed Bomb L39, Solarbeam L45, Sunny Day L46 | Razor Leaf L20→L4, Poison Powder L10→L6, Leech Seed L47→L9, Reflect L13→L12, Body Slam L32→L30 |
| Bayleef | Mega Drain L21, Giga Drain L26, Seed Bomb L39, Solarbeam L45, Sunny Day L46 | Leech Seed L58→L9, Light Screen L26→L23, Body Slam L38→L30 |
| Meganium | Reflect L12, Mega Drain L21, Giga Drain L26, Safeguard L34, Solarbeam L45, Sunny Day L46 | Leech Seed L65→L9, Body Slam L40→L30 |
| Cyndaquil | Rollout L31, Sunny Day L34, Double-Edge L45, Fire Blast L50 | Ember L7→L4, Quick Attack L13→L10, Defense Curl L28→L12, Flame Wheel L19→L16, Swift L25→L19 |
| Quilava | Rollout L31, Sunny Day L34, Double-Edge L45, Fire Blast L50 | Defense Curl L33→L12, Flame Wheel L21→L16, Swift L29→L19, Flamethrower L37→L31 |
| Typhlosion | Thunder Punch L1, Quick Attack L10, Rollout L31, Sunny Day L34, Fire Blast L50 | Flamethrower L38→L31 |
| Totodile | Bubble Beam L17, Screech L40 | Water Gun L7→L4, Bite L22→L11, Scary Face L16→L13 |
| Croconaw | Bubble Beam L17 | Bite L24→L11, Agility L28→L25, Crunch L48→L45 |
| Feraligatr | Dynamic Punch L1, Bubble Beam L17, Screech L37 | Crunch L53→L45, Outrage L63→L47 |
| Sentret | Thief L9, Headbutt L15, Dig L20, Extremespeed L30, Double-Edge L43 | Quick Attack L10→L6, Pursuit L19→L16 |
| Furret | Thief L1, Tackle L1, Headbutt L15, Agility L15, Dig L20, Extremespeed L30, Double-Edge L43 | Hyper Voice L33→L1, Pursuit L21→L16, Rest L36→L35 |
| Spinarak | Scary Face L1, Giga Drain L25, Psychic L30 | Leech Life L7→L5, Night Shade L26→L8, Poison Jab L47→L27, Megahorn L56→L43 |
| Ariados | Leech Life L1, Giga Drain L25, Psychic L30 | Night Shade L28→L8, Poison Jab L50→L27, Megahorn L58→L43 |
| Crobat | Gust L1, Giga Drain L1, Swift L19, Sludge L27, Toxic L50 | Confuse Ray L47→L17, Haze L67→L34, Air Slash L42→L41 |
| Chinchou | Thunder Wave L5, Take Down L15, Rain Dance L33, Thunder L42 | Supersonic L4→L1, Flail L10→L1, Bubble Beam L25→L23, Confuse Ray L34→L25, Signal Beam L40→L26, Thunderbolt L43→L33 |
| Lanturn | Flail L1, Water Gun L13, Take Down L15, Rain Dance L33, Thunder L42 | Confuse Ray L39→L25, Signal Beam L47→L26, Thunderbolt L51→L33, Hydro Pump L43→L41 |
| Togepi | Return L10, Swift L25, Ancient Power L27, Safeguard L32, Tri Attack L43 | Fairy Wind L7→L1, Sweet Kiss L16→L7, Encore L31→L15, Double-Edge L46→L38 |
| Togetic | Return L10, Wing Attack L24, Ancient Power L27, Safeguard L32, Tri Attack L39, Soft-Boiled L50 | Fairy Wind L7→L1, Encore L36→L15, Air Slash L51→L38 |
| Natu | Morning Sun L1, Night Shade L9, Baton Pass L30, Air Slash L31, Wing Attack L40 | Confusion L13→L4, Confuse Ray L32→L19, Psybeam L26→L21, Recover L47→L30, Psychic L50→L35 |
| Xatu | Teleport L7, Baton Pass L30, Air Slash L31, Wing Attack L40, Morning Sun L49 | Confuse Ray L37→L19, Psybeam L27→L21, Recover L58→L30, Psychic L62→L35 |
| Mareep | Thunderbolt L47 | Cotton Spore L13→L4, Confuse Ray L28→L24 |
| Flaaffy | Take Down L18, Signal Beam L41, Thunderbolt L47, Thunder L52 | Confuse Ray L33→L24, Power Gem L45→L33 |
| Ampharos | Cotton Spore L1, Take Down L18, Signal Beam L41, Thunderbolt L47, Thunder L52, Zap Cannon L56 | Confuse Ray L34→L24, Power Gem L49→L33 |
| Marill | Take Down L22, Rain Dance L28 | Bubblebeam L19→L18, Aqua Jet L43→L27, Hydro Pump L52→L42, Belly Drum L49→L45 |
| Azumarill | Take Down L22, Rain Dance L28 | Bubblebeam L20→L18, Aqua Jet L54→L27, Hydro Pump L66→L42, Belly Drum L62→L45, Play Rough L50→L45 |
| Yanma | Double Team L7, Twister L12 | Leech Life L7→L1, Quick Attack L15→L4, Wing Attack L27→L15, Signal Beam L30→L24, Air Slash L42→L38, Bug Buzz L45→L43 |
| Espeon | Growl L1, Quick Attack L6, Double Kick L14, Swift L26, Calm Mind L48, Reflect L52, Tri Attack L52 | Sand Attack L10→L4, Bite L30→L17, Psybeam L34→L30, Psychic L57→L36, Morning Sun L60→L47 |
| Umbreon | Growl L1, Curse L1, Quick Attack L6, Double Kick L14 | Sand Attack L10→L4, Bite L34→L17, Confuse Ray L54→L26, Dark Pulse L57→L37, Moonlight L60→L47 |
| Slowking | Psybeam L25, Swagger L36, Amnesia L40 | Growl L4→L1, Water Gun L7→L1, Headbutt L34→L18, Psychic L46→L45 |
| Misdreavus | Night Shade L4, Icy Wind L22, Screech L24, Sing L24 | Spite L7→L1, Astonish L10→L4, Confuse Ray L20→L8, Mean Look L43→L10, Psybeam L24→L14, Shadow Ball L40→L27, Pain Split L34→L29, Perish Song L52→L43 |
| Pineco | Harden L1, Mega Drain L15 | Rapid Spin L22→L4, Pin Missile L19→L7, Spikes L28→L27 |
| Forretress | Harden L1, Mega Drain L15, Double-Edge L46 | Explosion L39→L36, Iron Defense L51→L39 |
| Gligar | Fury Cutter L14 | Sand Attack L4→L1, Harden L15→L3, Quick Attack L20→L6, Wing Attack L24→L18, Screech L27→L24, Earthquake L45→L36 |
| Steelix | Rock Slide L1, Rage L6, Dig L18, Double-Edge L46 | Rock Throw L15→L4, Screech L62→L30, Iron Tail L50→L40, Earthquake L58→L45 |
| Scizor | Cut L15, Double Team L24 | Fury Cutter L37→L1, X-Scissor L49→L40, Night Slash L55→L44 |
| Sneasel | Agility L18, Blizzard L50 | Pursuit L7→L4, Quick Attack L24→L6, Icy Wind L10→L9, Slash L28→L22, Screech L31→L30, Ice Punch L40→L33, Night Slash L46→L39 |
| Teddiursa | Sweet Scent L11, Headbutt L24 | Slash L37→L33 |
| Ursaring | Sweet Scent L11, Metal Claw L15, Focus Energy L28, Scary Face L35 | Slash L43→L33 |
| Slugma | Flame Wheel L21, Body Slam L28, Power Gem L39 | Harden L4→L1, Ancient Power L31→L20, Amnesia L52→L22, Earth Power L49→L45 |
| Magcargo | Harden L1, Flame Wheel L21, Body Slam L28, Rock Slide L31, Power Gem L39, Earthquake L50 | Amnesia L57→L22, Fire Blast L49→L48 |
| Swinub | Take Down L26 | Powder Snow L10→L6, Endure L13→L12, Icy Wind L22→L16, Mist L40→L34, Earthquake L43→L39 |
| Piloswine | Mud-Slap L1, Endure L12, Take Down L26 | Mist L43→L34, Earthquake L47→L39, Blizzard L51→L50 |
| Houndour | Roar L7, Flame Wheel L22, Dark Pulse L41 | Bite L31→L12, Crunch L43→L35, Flamethrower L46→L38 |
| Houndoom | Roar L1, Flame Wheel L22, Dark Pulse L41 | Bite L37→L1, Crunch L53→L35, Flamethrower L57→L38 |
| Phanpy | Endure L19, Double-Edge L48, Curse L52 | Mud-Slap L7→L5, Rollout L22→L10, Magnitude L32→L14, Earthquake L44→L40 |
| Donphan | Mud-Slap L1, Defense Curl L1, Endure L19, Flail L23, Take Down L25, Double-Edge L48, Curse L52 | Magnitude L37→L14, Body Slam L32→L30, Rapid Spin L59→L36, Earthquake L55→L40 |
| Porygon2 | Curse L1, Signal Beam L24, Hyper Beam L50 | Psybeam L25→L4, Swift L15→L10, Recover L49→L14, Tri Attack L55→L38 |
| Hitmontop | Seismic Toss L22, Dig L29, Dynamic Punch L36, Iron Tail L51 | Focus Energy L32→L1, Pursuit L28→L1, Foresight L10→L1, Quick Attack L20→L12 |
| Elekid | Spark L17 | Thundershock L10→L1, Thunder Wave L43→L16 |
| Magby | Flame Wheel L17, Fire Punch L25, Will-O-Wisp L28, Dark Pulse L48 | Leer L13→L1, Ember L7→L1, Fire Spin L19→L9 |
| Larvitar | Screech L9, Dragon Claw L56 | Rock Throw L13→L8 |
| Pupitar | Dragon Claw L56, Hyper Beam L61 | Scary Face L41→L34, Earthquake L53→L47 |
| Tyranitar | Rock Throw L1, Scary Face L34, Dragon Claw L56, Hyper Beam L61 | Earthquake L55→L47 |
| Lugia | Ancientpower L44, Sky Attack L70 | Gust L7→L1, Recover L70→L22, Hydro Pump L40→L35, Aeroblast L50→L40, Calm Mind L80→L65 |
| Ho-Oh | Fire Spin L10, Ancientpower L44, Sky Attack L60 | Gust L10→L1, Recover L70→L22, Fire Blast L90→L25, Sacred Fire L50→L40, Calm Mind L80→L65 |
| Lotad | Rain Dance L27, Seed Bomb L30, Energy Ball L44, Hydro Pump L49 | Bubble L10→L1, Nature Power L34→L12, Bubble Beam L22→L17 |
| Lombre | Mega Drain L23, Rain Dance L27 | Bubble Beam L25→L17, Giga Drain L37→L36 |
| Ludicolo | Water Gun L1, Rain Dance L27 | Bubble Beam L28→L17, Giga Drain L43→L36, Hydro Pump L68→L49 |
| Taillow | Aerial Ace L18, Whirlwind L23, Air Slash L32, Hyper Voice L39 | Wing Attack L19→L12, Double Team L35→L15 |
| Swellow | Aerial Ace L18, Whirlwind L23, Hyper Voice L39 | Sky Attack L36→L1, Double Team L41→L15, Brave Bird L56→L48 |
| Kirlia | Fairy Wind L1, Dream Eater L49, Moonblast L58 |  |
| Gardevoir | Fairy Wind L1, Charm L16, Dream Eater L49 | Psychic L57→L36 |
| Surskit | Leech Life L5 | Bubble Beam L32→L16, Agility L41→L24, Haze L35→L29, Baton Pass L47→L33, Hydro Pump L44→L37 |
| Masquerain | Leech Life L1, Icy Wind L32, Hydro Pump L42 | Gust L22→L14, Scary Face L29→L24 |
| Shroomish | Giga Drain L26 | Stun Spore L19→L5, Leech Seed L13→L8, Mega Drain L16→L11, Headbutt L25→L15, Toxic L43→L29, Synthesis L37→L31, Seed Bomb L40→L34 |
| Breloom | Drain Punch L1, Counter L21, Dynamic Punch L49 | Headbutt L27→L15, Seed Bomb L50→L37 |
| Whismur | Flail L29 | Astonish L7→L1, Stomp L22→L18, Hyper Voice L40→L29 |
| Loudred | Supersonic L11, Hyper Beam L50 | Stomp L23→L18, Hyper Voice L47→L29, Screech L51→L30, Crunch L59→L35, Outrage L55→L49 |
| Exploud | Supersonic L11, Stomp L18, Bite L26, Roar L26, Hyper Beam L55 | Hyper Voice L49→L29, Screech L54→L30, Crunch L64→L35, Outrage L59→L49 |
| Hariyama | Bulk Up L1, Reversal L43, Endure L45 | Whirlwind L46→L14, Body Slam L41→L32 |
| Sableye | Bite L12, Crunch L27 | Foresight L3→L1, Astonish L10→L3, Shadow Claw L51→L24 |
| Mawile | Sweet Scent L1, Metal Claw L20, Faint Attack L24, Meteor Mash L45 | Bite L25→L6, Double Slap L18→L12, Iron Defense L28→L27, Baton Pass L37→L29 |
| Aron | Headbutt L7, Rock Throw L9, Roar L16, Take Down L21, Protect L27, Double-Edge L41, Earthquake L51 | Iron Defense L39→L15, Rock Slide L33→L30 |
| Lairon | Rock Throw L9, Metal Claw L10, Roar L16, Take Down L21, Protect L27, Double-Edge L41, Earthquake L51 | Iron Defense L43→L15, Rock Slide L34→L30, Iron Tail L38→L37 |
| Aggron | Rock Throw L9, Metal Claw L10, Roar L16, Take Down L21, Protect L27, Double-Edge L41, Earthquake L51 | Iron Defense L44→L15 |
| Electrike | Wild Charge L43, Rain Dance L46, Thunder L50 | Roar L28→L1, Quick Attack L13→L12, Thunder Fang L31→L26, Thunderbolt L43→L36 |
| Manectric | Thunder Shock L1, Flamethrower L1, Quick Attack L12, Rain Dance L46, Thunder L50 | Roar L29→L1, Thunder Fang L33→L26, Thunderbolt L49→L36, Crunch L41→L40 |
| Volbeat | Double Team L6, Leech Life L10, Light Screen L41, Moonblast L45 | Confuse Ray L29→L8, Quick Attack L15→L14, Signal Beam L25→L24, Baton Pass L49→L29, Zen Headbutt L37→L32, Bug Buzz L41→L40 |
| Illumise | Charm L6, Leech Life L10, Signal Beam L24, Reflect L41, Moonblast L45 | Quick Attack L15→L14, Bug Buzz L41→L40 |
| Wailmer | Tackle L1, Curse L45 | Growl L10→L3, Water Gun L7→L5, Rollout L16→L8, Rest L37→L24 |
| Wailord | Double-Edge L1, Tackle L1, Astonish L13, Mist L16, Curse L45, Amnesia L46 |  |
| Numel | Focus Energy L7, Flame Wheel L17, Take Down L20, Rock Slide L32, Double-Edge L46 | Mud-Slap L10→L1, Ember L7→L4, Amnesia L40→L17, Flamethrower L43→L36 |
| Camerupt | Mud-Slap L1, Focus Energy L7, Flame Wheel L17, Take Down L20, Rock Slide L32, Double-Edge L46 | Amnesia L46→L17, Flamethrower L51→L36 |
| Torkoal | Flame Wheel L17, Sunny Day L24, Body Slam L25 | Smokescreen L19→L1, Smog L4→L1, Fire Spin L31→L6, Amnesia L49→L37 |
| Trapinch | Magnitude L38, Hyper Beam L55 | Sand Attack L4→L1, Mud-Slap L7→L4, Sandstorm L31→L15, Dig L28→L21, Rock Slide L43→L22, Crunch L37→L25 |
| Vibrava | Supersonic L1, Rock Slide L22, Crunch L25, Signal Beam L33, Dragon Dance L39 | Dragon Breath L35→L30, Earth Power L42→L36, Bug Buzz L54→L44, Earthquake L59→L47 |
| Flygon | Sandstorm L1, Bite L1, Supersonic L1, Rock Slide L22, Crunch L25, Dig L27, Signal Beam L33, Dragon Dance L39, Dragon Claw L42 | Bug Buzz L57→L44, Earthquake L62→L47 |
| Cacnea | Growth L4, Pursuit L7, Leech Seed L11, Seed Bomb L24 | Absorb L4→L1, Giga Drain L37→L34, Dark Pulse L40→L37, Energy Ball L49→L45 |
| Cacturne | Sand Attack L7, Pursuit L7, Feint Attack L19, Seed Bomb L24, Sandstorm L45 | Giga Drain L39→L34, Dark Pulse L43→L37, Energy Ball L55→L45, Destiny Bond L51→L48 |
| Swablu | Safeguard L7, Hyper Voice L33 | Astonish L10→L1, Sing L13→L3, Take Down L28→L19, Mist L25→L23 |
| Altaria | Safeguard L7, Heal Bell L29, Hyper Voice L33 | Dragon Breath L35→L30, Dragon Claw L58→L42, Dragon Pulse L46→L43 |
| Lunatone | Icy Wind L12, Psybeam L19, Calm Mind L21, Ice Beam L46 | Ancient Power L41→L28, Moonlight L57→L34, Power Gem L54→L38 |
| Solrock | Will-O-Wisp L9, Curse L21, Psybeam L25, Flare Blitz L54 | Zen Headbutt L48→L33, Morning Sun L57→L34 |
| Cradily | Rock Throw L1, Leech Seed L1, Mega Drain L12, Confuse Ray L14, Ancient Power L17 | Energy Ball L46→L42 |
| Anorith | Rock Throw L15, Swords Dance L50 | Water Gun L10→L6, Fury Cutter L22→L11 |
| Armaldo | Iron Tail L1, Fury Cutter L11, Metal Claw L14, Rock Throw L15, Ancient Power L17, Swords Dance L50 |  |
| Milotic | Sing L1, Dragon Breath L30, Light Screen L40 | Attract L20→L1, Wrap L10→L1, Safeguard L45→L5, Twister L15→L7, Recover L48→L25, Dragon Pulse L51→L46 |
| Shuppet | Lick L1, Will-O-Wisp L29, Substitute L34 | Screech L34→L3, Night Shade L13→L11, Curse L22→L17 |
| Banette | Lick L1, Spite L1, Play Rough L1, Astonish L14, Will-O-Wisp L29, Substitute L34 | Shadow Claw L39→L37 |
| Duskull | Will-O-Wisp L18, Hypnosis L31 | Disable L7→L4, Astonish L10→L6, Foresight L19→L8, Pain Split L44→L37 |
| Dusclops | Astonish L1, Foresight L8, Pursuit L11, Will-O-Wisp L18, Hypnosis L31, Future Sight L48 | Pain Split L49→L37 |
| Chimecho | Take Down L16, Safeguard L32 | Growl L5→L1, Astonish L9→L1, Recover L43→L1, Confusion L13→L8, Heal Bell L36→L22, Psychic L46→L38, Hyper Voice L52→L47 |
| Absol | Crunch L40, Air Slash L44 | Leer L5→L1, Pursuit L20→L7, Bite L35→L18, Double Team L23→L20, Slash L32→L23, Night Slash L48→L30, Perish Song L53→L45 |
| Snorunt | Body Slam L40 | Hail L19→L13, Headbutt L28→L18, Crunch L34→L30 |
| Glalie | Hail L15, Headbutt L18, Scary Face L23, Body Slam L40 | Blizzard L52→L43, Explosion L56→L47 |
| Relicanth | Take Down L22, Sleep Talk L30, Double-Edge L41 | Water Gun L7→L6 |
| Bagon | Dragon Claw L40, Flamethrower L53 | Ember L13→L4, Zen Headbutt L34→L33 |
| Shelgon | Ember L1, Twister L15, Dragon Claw L40, Flamethrower L53 | Zen Headbutt L40→L33, Crunch L44→L38 |
| Salamence | Ember L1, Twister L15, Dragon Breath L28, Scary Face L33, Dragon Claw L40, Flamethrower L53 | Double-Edge L63→L61 |
| Metang | Scary Face L25, Psybeam L30 | Pursuit L42→L22, Bullet Punch L30→L27, Flash Cannon L46→L37 |
| Metagross | Thunder Punch L1, Ice Punch L1, Psybeam L30, Iron Defense L39, Hyper Beam L60 | Flash Cannon L47→L37, Meteor Mash L57→L50, Agility L62→L58 |
| Kyogre | Icy Wind L10, Surf L40 | Ancient Power L15→L1, Calm Mind L80→L45, Double-Edge L100→L50 |
| Groudon | Iron Tail L1, Fire Punch L10, Fire Blast L60 | Ancient Power L15→L1, Earth Power L50→L15, Bulk Up L80→L45 |
| Rayquaza | Dragon Claw L20, Sky Attack L75 | Earth Power L70→L1, Ancient Power L15→L1, Rest L20→L15, Dragon Dance L80→L45 |
| Mewtwo | Metronome L1, Psybeam L7 | Zen Headbutt L25→L1, Drain Punch L15→L1, Swift L20→L1, Barrier L95→L55, Aura Sphere L80→L67 |
| Pichu | Thunder Wave L8 | Tail Whip L10→L4, Spark L18→L11 |
| Tyrogue | Rock Smash L10 |  |
| Blissey | Take Down L17, Light Screen L37 | Tail Whip L7→L1, Double Slap L10→L8, Sing L34→L22, Hyper Voice L49→L46 |
| Ralts | Fairy Wind L1, Double Team L9, Charm L23, Moonblast L58 | Confusion L7→L5, Psybeam L19→L18 |
| Cranidos | Iron Head L42, Agility L49 | Focus Energy L10→L5, Scary Face L22→L18, Screech L37→L28, Zen Headbutt L40→L35 |
| Rampardos | Focus Energy L1, Pursuit L1, Ancient Power L23, Iron Head L42, Agility L49 | Screech L42→L28, Zen Headbutt L47→L35, Head Smash L52→L46 |
| Shieldon | Counter L14, Swagger L21, Endure L27 | Iron Defense L34→L16, Iron Head L37→L32 |
| Bastiodon | Counter L14, Swagger L21, Ancient Power L23, Endure L27 | Iron Defense L38→L16, Iron Head L43→L32 |
| Drifloon | Whirlwind L1, Self-Destruct L32, Air Slash L42 | Gust L10→L7 |
| Drifblim | Whirlwind L1, Focus Energy L11, Self-Destruct L32, Air Slash L42 | Shadow Ball L40→L36 |
| Buneary | Double Kick L16, Baton Pass L24 | Endure L36→L5, Frustration L25→L10, Dizzy Punch L33→L22 |
| Lopunny | Return L10, Double Kick L16, Baton Pass L24 | Endure L56→L5, Quick Attack L15→L13, Dizzy Punch L48→L22, High Jump Kick L60→L53 |
| Mismagius | Icy Wind L22, Sing L24 | Confuse Ray L20→L8, Mean Look L50→L10, Psybeam L25→L14, Pain Split L38→L29, Shadow Ball L46→L38, Perish Song L62→L43 |
| Chingling | Recover L24 | Growl L3→L1, Astonish L6→L3, Confusion L9→L5 |
| Spiritomb | Ancient Power L1, Outrage L65 | Feint Attack L15→L5, Hypnosis L20→L10, Dream Eater L25→L10, Nasty Plot L45→L35, Shadow Ball L48→L40 |
| Garchomp | Dig L36, Scary Face L40 | Earthquake L56→L55 |
| Riolu | Dizzy Punch L33 | Screech L22→L21 |
| Lucario | Iron Head L47 | Counter L20→L1 |
| Skorupi | Night Slash L37 | Poison Jab L41→L31, X-Scissor L44→L40 |
| Drapion | Focus Energy L1, Pursuit L1, Night Slash L37, Scary Face L42 | Poison Jab L42→L31, X-Scissor L47→L40 |
| Weavile | Nasty Plot L18 | Pursuit L4→L1, Icy Wind L10→L9, Screech L34→L30, Ice Punch L46→L35 |
| Magnezone | Thunder Shock L1, Thunder Wave L11, Screech L19, Light Screen L47 | Tri Attack L48→L30 |
| Rhyperior | Take Down L29, Double-Edge L56 |  |
| Tangrowth | Energy Ball L43 | Absorb L14→L1, Sleep Powder L43→L1, Mega Drain L22→L19, Stun Spore L31→L25, Giga Drain L46→L31, Body Slam L65→L37 |
| Electivire | Ice Punch L1, Thunderbolt L42 | Thunder Wave L53→L16 |
| Magmortar | Aura Sphere L1, Zap Cannon L1, Fire Punch L25, Will-O-Wisp L28, Flamethrower L42, Dark Pulse L48, Hyper Beam L57 |  |
| Togekiss | Return L10, Encore L15, Ancient Power L27, Safeguard L32, Tri Attack L45, Soft-Boiled L50 | Growl L4→L1, Charm L38→L1, Fairy Wind L7→L1, Sweet Kiss L20→L7 |
| Yanmega | Leech Life L1, Twister L12, Supersonic L20, Dragon Pulse L53 |  |
| Leafeon | Growl L1, Quick Attack L6, Double Kick L14 | Sand Attack L10→L4, Bite L30→L17, X-Scissor L54→L48 |
| Glaceon | Growl L1, Quick Attack L6, Disable L12, Double Kick L14, Haze L22, Ice Beam L37 | Sand Attack L10→L4, Powder Snow L15→L9 |
| Gliscor | Fury Cutter L14 | Quick Attack L20→L1, Wing Attack L25→L18, Screech L30→L24, Earthquake L50→L44 |
| Mamoswine | Mud-Slap L8, Endure L12, Take Down L26 |  |
| Porygon-Z | Curse L1, Signal Beam L24, Tri Attack L38, Hyper Beam L52 | Psybeam L25→L4, Swift L15→L10, Recover L49→L14 |
| Gallade | Double Kick L1, Fury Cutter L15 | Cross Chop L69→L1, Psycho Cut L59→L32 |
| Dusknoir | Astonish L1, Foresight L8, Pursuit L11, Will-O-Wisp L18, Future Sight L48, Drain Punch L58 |  |
| Froslass | Blizzard L47, Curse L49 | Hail L42→L15, Draining Kiss L20→L18, Ice Beam L50→L37, Shadow Ball L46→L43 |
| Sylveon | Quick Attack L6, Swift L12, Double Kick L14, Wrap L25, Amnesia L32, Encore L48 | Sand Attack L10→L4, Bite L30→L17, Hyper Voice L54→L52 |
| Hitmonlee |  | Foresight L10→L1, Focus Energy L28→L14, Mind Reader L52→L23 |
| Igglybuff |  | Defense Curl L9→L3, Sweet Kiss L21→L10, Double Slap L16→L14, Perish Song L31→L25 |
| Makuhita |  | Seismic Toss L16→L1, Sand Attack L10→L3, Whirlwind L37→L14, Body Slam L34→L32 |
| Lileep |  | Acid L10→L4, Rock Throw L13→L7, Mega Drain L19→L12, Confuse Ray L22→L14, Ancient Power L25→L17, Giga Drain L31→L26, Energy Ball L44→L42 |
| Kadabra |  | Psybeam L35→L25 |
| Alakazam |  | Disable L20→L1, Psybeam L35→L25, Calm Mind L44→L38 |
| Magikarp |  | Flail L30→L25 |
| Feebas |  | Flail L30→L25 |
| Shinx |  | Spark L19→L11, Bite L22→L14, Roar L25→L16, Thunder Fang L31→L22, Swagger L34→L24, Crunch L40→L31, Wild Charge L43→L34 |
| Luxio |  | Spark L21→L11, Bite L25→L14, Roar L29→L16, Thunder Fang L37→L22, Swagger L41→L24, Crunch L49→L31, Wild Charge L53→L34 |
| Luxray |  | Thunder Fang L39→L22, Swagger L44→L24, Crunch L54→L31, Wild Charge L59→L34 |
| Bronzor |  | Confuse Ray L23→L10 |
| Gible |  | Sandstorm L13→L10 |

</details>

Engine learnset caps may stop adds short of this list (never overflow); Legacy learnset adds never remove a move.

### Planned: evolution changes (23)

- Goldeen → Seaking: level 33 → 26 (xy)
- Spinarak → Ariados: level 22 → 21 (crystal)
- Pineco → Forretress: level 31 → 25 (crystal)
- Slugma → Magcargo: level 38 → 27 (crystal)
- Ralts → Kirlia: level 20 → 16 (emerald)
- Aron → Lairon: level 32 → 28 (emerald)
- Trapinch → Vibrava: level 35 → 30 (xy)
- Vibrava → Flygon: level 45 → 42 (emerald)
- Snorunt → Glalie: level 42 → 36 (emerald)
- Venonat → Venomoth: level 31 → 28 (xy)
- Swablu → Altaria: level 35 → 30 (xy)
- Kadabra → Alakazam: **added** method level (42) (yellow)
- Machoke → Machamp: **added** method level (38) (yellow)
- Graveler → Golem: **added** method level (38) (yellow)
- Haunter → Gengar: **added** method level (42) (yellow)
- Slowpoke → Slowking: **added** method item (King's Rock) (crystal)
- Onix → Steelix: **added** method item (Metal Coat) (crystal)
- Scyther → Scizor: **added** method item (Metal Coat) (crystal)
- Porygon → Porygon2: **added** method item (Up-Grade) (crystal)
- Magneton → Magnezone: **added** method item (Thunder Stone) (xy)
- Eevee → Leafeon: **added** method item (Leaf Stone) (xy)
- Porygon2 → Porygon-Z: **added** method item (Dubious Disc) (xy)
- Feebas → Milotic: **added** method item (Prism Scale) (xy)

Skipped (engine lacks it): Tyrogue -> Hitmontop: item Brick Piece not found in this engine; Rhydon -> Rhyperior: engine has no "held_day" method (no probe species uses it); Rhydon -> Rhyperior: engine has no "held_night" method (no probe species uses it); Electabuzz -> Electivire: engine has no "held_day" method (no probe species uses it); Electabuzz -> Electivire: engine has no "held_night" method (no probe species uses it); Magmar -> Magmortar: engine has no "held_day" method (no probe species uses it); Magmar -> Magmortar: engine has no "held_night" method (no probe species uses it); Eevee -> Glaceon: item Dawn Stone not found in this engine; Dusclops -> Dusknoir: engine has no "held_night" method (no probe species uses it)
