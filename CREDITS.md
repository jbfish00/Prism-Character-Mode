# Credits

## Picker portraits (2026-10-28)

Every portrait is a 56x56, 4-colour GBC pic built by `tools/character_mode/build_portraits.py`
(`art/portraits/manifest.json` records each one's source).

### Polished Crystal (Rangi42 and the Polished Crystal contributors), 37 pics, used as drawn

https://github.com/Rangi42/polishedcrystal (`gfx/trainers/`). Their palette files supply the two middle colours.

Agatha, Anabel, Archer, Ariana, Blaine, Blue, Brock, Bruno, Bugsy, Caitlin, Chuck, Clair, Cynthia, Elm, Erika, Falkner, Flannery, Giovanni, Janine, Jasmine, Karen, Koga, Kukui, Leaf, Lorelei, Lt. Surge, Maylene, Misty, Morty, Oak, Pryce, Red, Sabrina, Steven, Valerie, Whitney, Will

### Platinum Character Mode portraits, 7 pics, reduced to GBC format (2026-11-03)

Taken from the Platinum Character Mode repo's `res/graphics/character_mode/` (its CREDITS.md: Pokemon Showdown /
smogon/sprites trainer avatars, themselves from the DS games) and reduced here to 56x56 with 4 colours, the
background taken from the corner pixel. The original artists keep all credit.

| character | source file |
|---|---|
| Ash | `015_ash.png` |
| Adaman | `210_adaman.png` |
| Beni | `214_beni.png` |
| Ingo | `222_ingo.png` |
| Irida | `223_irida.png` |
| Volo | `197_volo.png` |
| Zisu | `237_zisu.png` |

Still without a portrait (no source found): Samson Oak, Chloe, Goh, Paul, Zoey.

### R.O.W.E. Character Mode front pics, 68 pics, reduced to GBC format

Taken from the ROWE Character Mode decomp's `graphics/trainers/front_pics/` and reduced here to 56x56 with
4 colours. Those pics are Game Freak's own Gen 3 trainer art plus the fan art credited in that repo
(`Pokemon Rowe Alteration` credits: pokeemerald-rogue / Pokabbie, Pokesho, Emerald Enhanced, Wolfang62 and
others). The original artists keep all credit; this project only re-sizes and re-colours.

| character | source file |
|---|---|
| Acerola | `cm_donor_acerola.png` |
| Archie | `aqua_leader_archie_front_pic.png` |
| Bede | `cm_donor_bede.png` |
| Bertha | `cm_bertha.png` |
| Birch | `cm_donor_birch.png` |
| Brandon | `pyramid_king_brandon_front_pic.png` |
| Brawly | `leader_brawly_front_pic.png` |
| Brendan | `brendan_front_pic.png` |
| Byron | `cm_byron.png` |
| Calem | `cm_donor_calem.png` |
| Candice | `cm_candice.png` |
| Crasher Wake | `cm_crasher_wake.png` |
| Cyrus | `cm_cyrus.png` |
| Dahlia | `cm_donor_dahlia.png` |
| Dawn | `cm_dawn.png` |
| Elio | `cm_donor_elio.png` |
| Ethan | `cm_ethan.png` |
| Fantina | `cm_fantina.png` |
| Flint | `cm_donor_flint.png` |
| Gardenia | `cm_gardenia.png` |
| Gary | `cm_blue.png` |
| Gladion | `cm_donor_gladion.png` |
| Greta | `arena_tycoon_greta_front_pic.png` |
| Hau | `cm_donor_hau.png` |
| Hilbert | `hilbert.png` |
| Hilda | `front.png` |
| Hop | `cm_donor_hop.png` |
| Iono | `cm_donor_iono.png` |
| James | `cm_donor_james.png` |
| Juan | `leader_juan_front_pic.png` |
| Jupiter | `cm_jupiter.png` |
| Kabu | `cm_donor_kabu.png` |
| Kiawe | `cm_donor_kiawe_anime.png` |
| Korrina | `cm_donor_korrina.png` |
| Kris | `cm_kris.png` |
| Lana | `cm_donor_lana_anime.png` |
| Lance | `cm_lance.png` |
| Liza | `leader_tate_and_liza_front_pic.png` |
| Lucas | `cm_lucas.png` |
| Lucian | `cm_lucian.png` |
| Lucy | `pike_queen_lucy_front_pic.png` |
| Lusamine | `cm_donor_lusamine.png` |
| Lyra | `cm_donor_lyra.png` |
| Marnie | `cm_donor_marnie.png` |
| Mars | `cm_mars.png` |
| Maxie | `magma_leader_maxie_front_pic.png` |
| May | `may_front_pic.png` |
| N | `cm_donor_n.png` |
| Noland | `factory_head_noland_front_pic.png` |
| Penny | `cm_donor_penny.png` |
| Phoebe | `elite_four_phoebe_front_pic.png` |
| Ritchie | `cm_donor_ritchie.png` |
| Roark | `cm_roark.png` |
| Roxanne | `leader_roxanne_front_pic.png` |
| Saturn | `cm_saturn.png` |
| Selene | `cm_donor_selene.png` |
| Serena | `cm_donor_serena.png` |
| Shauna | `cm_donor_shauna.png` |
| Shauntal | `cm_donor_shauntal.png` |
| Silver | `cm_donor_silver.png` |
| Spenser | `palace_maven_spenser_front_pic.png` |
| Sycamore | `cm_donor_sycamore.png` |
| Tate | `leader_tate_and_liza_front_pic.png` |
| Volkner | `cm_volkner.png` |
| Wallace | `champion_wallace_front_pic.png` |
| Wally | `wally_front_pic.png` |
| Wattson | `leader_wattson_front_pic.png` |
| Winona | `leader_winona_front_pic.png` |

Pokemon and every original character design are (c) Nintendo, Creatures Inc. and GAME FREAK inc. This is a
non-commercial fan project distributed as a patch only.

## Player overworld sprite (2026-11-04)

Every sheet is native Game Boy Color art (16x96, Crystal's walking-sprite layout), built by
`tools/character_mode/build_ow_sprites.py` (`art/overworld/manifest.json` records each one's source and palette).
Shrinking the GBA/DS overworld sheets to 16x16 was tried and rejected (unreadable at 4 shades), so a character
without their own GBC sprite walks as a **stand-in**: the nearest native GBC sprite, in a matching palette.

### The character's own sprite: Polished Crystal (Rangi42 and contributors), https://github.com/Rangi42/polishedcrystal `gfx/sprites/`, 43

Agatha, Anabel, Archer, standing frames only, Ariana, Blaine, Blue, Brock, Bruno, Bugsy, Caitlin, Chuck, Clair, Cynthia, Elm, Erika, Ethan (sprite `chris`), Falkner, Flannery, Giovanni, James, Janine, Jasmine, Karen, standing frames only, Koga, Kris, Kukui, standing frames only, Lance, Leaf, Lorelei, Lt. Surge (sprite `surge`), Lyra, Maylene, Misty, Morty, Oak, Pryce, Red, Sabrina, Silver (sprite `rival`), Steven, Valerie, Whitney, Will, standing frames only

### Stand-ins, 74 (the sprite is another character's or a trainer class's)

| character | sprite | from | palette |
|---|---|---|---|
| Acerola | `twin` | polishedcrystal | purple |
| Adaman | `ace_trainer_m` | polishedcrystal | blue |
| Archie | `sailor` | polishedcrystal | blue |
| Ash | `red` | polishedcrystal | blue |
| Bede | `psychic` | polishedcrystal | purple |
| Beni | `ninja` | crystal-inheritance | blue |
| Bertha | `granny` | polishedcrystal | brown |
| Birch | `elm` | polishedcrystal | brown |
| Brandon | `hiker` | polishedcrystal | brown |
| Brawly | `cool_dude` | polishedcrystal | blue |
| Brendan | `youngster` | polishedcrystal | red |
| Byron | `hiker` | polishedcrystal | brown |
| Calem | `ace_trainer_m` | polishedcrystal | red |
| Candice | `skier` | polishedcrystal | green |
| Chloe | `schoolgirl` | polishedcrystal | brown |
| Crasher Wake | `black_belt` | polishedcrystal | blue |
| Cyrus | `gentleman` | polishedcrystal | blue |
| Dahlia | `beauty` | polishedcrystal | red |
| Dawn | `lass` | polishedcrystal | red |
| Elio | `chris` | polishedcrystal | blue |
| Fantina | `beauty` | polishedcrystal | purple |
| Flint | `firebreather` | polishedcrystal | red |
| Gardenia | `picnicker` | polishedcrystal | green |
| Gary | `blue` | polishedcrystal | purple |
| Gladion | `rocker` | polishedcrystal | brown |
| Goh | `youngster` | polishedcrystal | blue |
| Greta | `battle_girl` | polishedcrystal | red |
| Hau | `camper` | polishedcrystal | green |
| Hilbert | `schoolboy` | polishedcrystal | blue |
| Hilda | `ace_trainer_f` | polishedcrystal | blue |
| Hop | `youngster` | polishedcrystal | purple |
| Ingo | `gentleman` | polishedcrystal | silver |
| Iono | `cute_girl` | polishedcrystal | purple |
| Irida | `skier` | polishedcrystal | red |
| Juan | `gentleman` | polishedcrystal | purple |
| Jupiter | `rocket_girl` | polishedcrystal | purple |
| Kabu | `veteran_m` | polishedcrystal | red |
| Kiawe | `beach_guy` | polishedcrystal | red |
| Korrina | `battle_girl` | polishedcrystal | blue |
| Lana | `lass` | polishedcrystal | blue |
| Liza | `twin` | polishedcrystal | red |
| Lucas | `schoolboy` | polishedcrystal | red |
| Lucian | `gentleman` | polishedcrystal | red |
| Lucy | `ace_trainer_f` | polishedcrystal | purple |
| Lusamine | `lady` | polishedcrystal | yellow |
| Marnie | `cute_girl` | polishedcrystal | red |
| Mars | `rocket_girl` | polishedcrystal | red |
| Maxie | `gentleman` | polishedcrystal | brown |
| May | `picnicker` | polishedcrystal | red |
| N | `ace_trainer_m` | polishedcrystal | green |
| Noland | `cool_dude` | polishedcrystal | brown |
| Paul | `rocker` | polishedcrystal | purple |
| Penny | `schoolgirl` | polishedcrystal | yellow |
| Phoebe | `picnicker` | polishedcrystal | purple |
| Ritchie | `chris` | polishedcrystal | green |
| Roark | `hiker` | polishedcrystal | red |
| Roxanne | `schoolgirl` | polishedcrystal | blue |
| Samson Oak | `oak` | polishedcrystal | red |
| Saturn | `rocket` | polishedcrystal | blue |
| Selene | `lass` | polishedcrystal | green |
| Serena | `ace_trainer_f` | polishedcrystal | red |
| Shauna | `picnicker` | polishedcrystal | yellow |
| Shauntal | `teacher` | polishedcrystal | purple |
| Spenser | `gramps` | polishedcrystal | green |
| Sycamore | `elm` | polishedcrystal | blue |
| Tate | `youngster` | polishedcrystal | brown |
| Volkner | `cool_dude` | polishedcrystal | yellow |
| Volo | `sage` | polishedcrystal | yellow |
| Wallace | `gentleman` | polishedcrystal | blue |
| Wally | `youngster` | polishedcrystal | green |
| Wattson | `pokefan_m` | polishedcrystal | yellow |
| Winona | `bird_keeper` | polishedcrystal | blue |
| Zisu | `battle_girl` | polishedcrystal | yellow |
| Zoey | `cute_girl` | polishedcrystal | brown |
