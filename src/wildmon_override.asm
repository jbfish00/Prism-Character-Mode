; Pokemon Prism Character Mode — wild encounter override (Phase 5)
;
; Target: Pokemon Prism v0.95 build 254 Hotfix 5 (sha1 in rom.sha1)
; Build: see src/character_mode.asm's header (same rgbasm/rgblink invocation;
;        this file is INCLUDEd from there).
;
; Spec: after the game's normal wild-species+level roll, 10% chance to
; replace the rolled SPECIES (never the level) with a random, non-
; legendary/mythical member of the active character's roster, choosing
; whichever evolution stage of that member's family best fits the level
; that was already rolled. Mode off / no character selected => fully inert.
;
; --- RE summary (this session) -------------------------------------------
; Vanilla pokecrystal's wild-encounter species+level roll always ends by
; writing wTempWildMonSpecies ($D22E) and wCurPartyLevel ($D143) — verified
; byte-identical addresses in Prism (same pattern as the catch gate's
; $C64E/$D206/$D22D). There are exactly THREE independent roll routines in
; the donor (ChooseWildEncounter for grass/cave AND surfing — one routine,
; branches internally on CheckOnWater; SelectTreeMon for headbutt trees
; AND rock smash — one routine, both callers converge on it; Fish for all
; three rod tiers — rod is a parameter, not separate code per tier). Static/
; scripted encounters use a different code path (Script_loadwildmon) that
; is untouched by this patch, per spec.
;
; Prism hook sites found via the operand-masked matcher + hand disassembly
; (bank:addr, file offset in parens):
;   A. bank $71 $423D (0x1C423D) — ChooseWildEncounter-equivalent's species
;      write, inside the routine anchored by TryWildEncounter/
;      LookUpWildmonsForMapDE (bank $71, roughly $4137-$4295).
;      Replaces `ld [$d22e],a` + `ret` (4 bytes: EA 2E D2 C9). Level
;      ($D143) is already written earlier in the same routine by the time
;      this runs.
;   B. bank $14 $4F73 (0x050F73) — SelectTreeMon-equivalent (anchored at
;      100% chunk match). Replaces `ld a,[hl+]` + `ld [$d22e],a` (4 bytes:
;      2A EA 2E D2). Level is the NEXT byte at [hl] (peeked, not yet
;      consumed — the untouched tail at hook+4 writes it right after we
;      return).
;   C. bank $2C $59A3 (0x0B19A3) — FishFunction's `.goodtofish`-equivalent,
;      right after farcalling Fish (bank $18 ~$43CF, itself unmodified —
;      it already handles all 3 rod tiers via its rod-in-e parameter).
;      Replaces `ld [$d22e],a` + `ld a,e` (4 bytes: EA 2E D2 7B). Level is
;      in register e (Fish's own output convention), untouched by us.
;
; All three replaced spans are exactly 4 bytes so the `rst $08` farcall
; (CF, bank, addr lo, addr hi) fits with no padding, and each site's stub
; deliberately REPLAYS the displaced instruction(s) before doing anything
; else, exactly like the catch gate's CatchGate replays its displaced
; `rst $20`. Register conventions differ per site because the three donor
; routines don't share a calling convention for "species so far" / "level
; so far" — only the two WRAM destinations are common.
;
; Data provenance for the level-band/legendary tables this relies on:
; tools/character_mode/build_wildmon_data.py + wildmon_families.tsv/.asm.
; See that script's docstring and CLAUDE.md for what's real donor data vs.
; hand-curated Gen 3/4 chains vs. honestly-unconstrained (no canonical
; level exists) bands.

DEF WILD_SPECIES  EQU $D22E  ; wTempWildMonSpecies
DEF WILD_LEVEL    EQU $D143  ; wCurPartyLevel
DEF PCT_ROLL      EQU $2AA8  ; Prism's own "uniform 0-99" percent-roll
                              ; helper (home bank; observed in use by the
                              ; vanilla surf level-buff check we're hooking
                              ; right next to, so reusing it is idiomatic,
                              ; not a new dependency). Confirmed to
                              ; push/pop bc/de/hl internally (only clobbers
                              ; a+flags) by disassembly this session.
DEF RAW_RANDOM    EQU $29D8  ; Prism's raw 0-255 RNG primitive (home bank;
                              ; the same one PCT_ROLL and the encounter-
                              ; rate roll both call). Also confirmed to
                              ; preserve bc/de/hl.


; ---------------------------------------------------------------------------
; Hook A: grass/cave + surfing (both branches of ChooseWildEncounter).
SECTION "WildmonHookGrassWater", ROMX[$423D], BANK[$71]
	; overwrites: ld [$d22e],a / ret  (4 bytes)
	rst $08
	db BANK(WildStubGrassWater)
	dw WildStubGrassWater

SECTION "WildmonStubGrassWater", ROMX[$4F00], BANK[118]
WildStubGrassWater::
	ld [WILD_SPECIES], a    ; replay the displaced write
	ld c, a                  ; c = original species (fallback)
	ld a, [WILD_LEVEL]         ; level was already written earlier in this
	ld b, a                     ; same routine — safe to read back
	call OverrideWildSpecies
	ret nc                        ; no override: $D22E already correct
	ld [WILD_SPECIES], a
	ret


; ---------------------------------------------------------------------------
; Hook B: headbutt trees + rock smash (both funnel through SelectTreeMon).
SECTION "WildmonHookTreeRock", ROMX[$4F73], BANK[$14]
	; overwrites: ld a,[hl+] / ld [$d22e],a  (4 bytes)
	rst $08
	db BANK(WildStubTreeRock)
	dw WildStubTreeRock

SECTION "WildmonStubTreeRock", ROMX[$4F40], BANK[118]
WildStubTreeRock::
	ld a, [hl+]              ; replay: species -> a, hl -> level byte
	ld [WILD_SPECIES], a      ; replay: original write
	ld c, a                    ; c = original species (fallback)
	ld b, [hl]                  ; peek level (hl NOT consumed — the
	                              ; untouched tail at hook+4 re-reads [hl]
	                              ; itself right after we return)
	call OverrideWildSpecies
	ret nc
	ld [WILD_SPECIES], a
	ret


; ---------------------------------------------------------------------------
; Hook C: fishing, all 3 rod tiers (Fish() takes the rod as a parameter).
SECTION "WildmonHookFish", ROMX[$59A3], BANK[$2C]
	; overwrites: ld [$d22e],a / ld a,e  (4 bytes)
	rst $08
	db BANK(WildStubFish)
	dw WildStubFish

SECTION "WildmonStubFish", ROMX[$4F80], BANK[118]
WildStubFish::
	ld [WILD_SPECIES], a      ; replay: original write
	ld c, a                    ; c = original species (fallback)
	ld b, e                     ; peek level (Fish's own output register;
	                              ; e is untouched here, so the untouched
	                              ; tail's `ld [$d143],a` still works once
	                              ; we replay `ld a,e` below)
	call OverrideWildSpecies
	jr nc, .no_override
	ld [WILD_SPECIES], a
.no_override:
	ld a, e                       ; replay the displaced `ld a,e`
	ret


; ---------------------------------------------------------------------------
; Shared core. In: b = rolled level (1-100), c = original rolled species
; (already committed to WILD_SPECIES by the caller, so "do nothing" is
; always safe). Out: carry set + a = replacement species, or carry clear.
SECTION "WildmonOverrideCore", ROMX[$4900], BANK[118]
OverrideWildSpecies::
	ld a, [CharModeCharId]
	inc a
	jr z, .noop              ; $FF (+1=0) = Character Mode off
	dec a
	ld d, a                    ; d = active character id (0-based)

	call PCT_ROLL                ; a = uniform 0-99
	cp 10
	jr nc, .noop                  ; 90%: no override, keep the normal roll

	; Pick a random ELIGIBLE (roster-set AND non-legendary) species via a
	; bounded linear scan from a random start point. A full scan (rather
	; than pure rejection sampling) guarantees termination even for the
	; sparsest/most-legendary-heavy rosters instead of ever spinning.
	call RAW_RANDOM
	ld l, a                        ; l = scan cursor
	ld h, 255                       ; h = iterations remaining
.scan:
	ld a, l
	and a
	jr z, .scan_next                  ; species id 0 is never valid
	call CheckEligible                  ; in: a=species,d=char_id
	jr c, .found                          ; carry set -> eligible, use it
.scan_next:
	inc l
	dec h
	jr nz, .scan
	jr .noop                                ; nothing eligible -> no-op

.found:
	; l = an eligible roster species. Pick the sibling stage (possibly l
	; itself) in the same evolution family whose canon level band best
	; fits the already-rolled level in b.
	call PickFamilyStage
	scf
	ret

.noop:
	xor a                    ; a=0 also clears carry
	ret


; In: a = species id (1-255), d = active character id.
; Out: carry set if roster bit `a` is set for character `d` AND species
;      `a` is not flagged legendary/mythical in WildmonFamilies. bc/de/hl
;      are preserved except for the deliberate carry/a return value.
CheckEligible::
	push hl
	push bc
	push de
	ld c, a                    ; c = species, kept across the roster-bit calc

	; roster bit test — identical algorithm to CatchGate's (must agree on
	; "is this species on the roster" with the already-shipped/tested
	; catch gate).
	ld l, d
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, CharacterModeRosters
	add hl, de
	ld a, c
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	add hl, de
	ld b, [hl]                  ; roster bitmap byte
	ld a, c
	and 7
	jr z, .testbit
.shiftloop:
	srl b
	dec a
	jr nz, .shiftloop
.testbit:
	bit 0, b
	jr z, .not_eligible

	; roster bit set -> reject legendary/mythical
	ld a, c
	call GetFamilyRecord          ; hl -> WildmonFamilies[species]
	inc hl
	inc hl
	inc hl
	ld a, [hl]                     ; flags byte
	bit 0, a
	jr nz, .not_eligible

	pop de
	pop bc
	pop hl
	scf
	ret

.not_eligible:
	pop de
	pop bc
	pop hl
	and a
	ret


; In: a = species id. Out: hl = &WildmonFamilies[species] (4-byte record:
; family_root, stage_min, stage_max, flags). Trashes de.
GetFamilyRecord::
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl                  ; hl = species * 4
	ld de, WildmonFamilies
	add hl, de
	ret


; In: l = an eligible family member's species id, b = rolled level.
; Out: a = the chosen stage's species id. Always succeeds — l's own
;      family always contains at least l itself, which is always a valid
;      (if not perfectly level-matched) answer.
;
; Scans the whole 255-entry WildmonFamilies table for every species
; sharing l's family_root, and keeps whichever one's [stage_min,stage_max]
; band contains b. Bands are constructed (see build_wildmon_data.py) to
; partition 1-100 contiguously for ordinary level-based chains, so exactly
; one match is the normal case; ties happen only when the real games have
; no canonical level fact distinguishing two stages (item/trade/happiness
; evolutions), in which case the LAST matching stage found in table order
; wins — a simple deterministic policy, not a claim that later table rows
; are somehow more "correct". If (implausibly) nothing at all matches, the
; original `l` is kept, which is itself always a family member and the
; most defensible "nearest" answer available. Trashes bc/de/hl (level in
; b is a read-only input, not preserved for the caller — the caller
; doesn't need it again).
PickFamilyStage::
	ld e, l                     ; e = current best answer, defaults to l
	ld a, l
	call GetFamilyRecord           ; hl -> record[l]
	ld a, [hl]                       ; family_root
	ld d, a                            ; d = root to match against every record

	ld hl, WildmonFamilies + 4            ; record for species id 1
.loop:
	ld a, [hl]                              ; this record's family_root
	cp d
	jr nz, .advance

	push hl
	inc hl
	ld a, [hl]                                ; stage_min
	ld c, a
	inc hl
	ld a, [hl]                                  ; stage_max (read now, used
	                                              ; immediately below, before
	                                              ; hl is restored)
	pop hl
	sub b                                         ; stage_max - level
	jr c, .advance                                  ; level > stage_max: fail
	ld a, b
	sub c                                             ; level - stage_min
	jr c, .advance                                      ; level < stage_min: fail

	; Match: recover this record's species id from hl's byte offset into
	; the table (id = (hl - WildmonFamilies) / 4) instead of keeping a
	; separate RAM/register counter alongside the walking pointer.
	push hl
	ld a, l
	sub LOW(WildmonFamilies)
	ld l, a
	ld a, h
	sbc a, HIGH(WildmonFamilies)
	ld h, a
	srl h
	rr l
	srl h
	rr l
	ld e, l
	pop hl

.advance:
	inc hl
	inc hl
	inc hl
	inc hl                                                 ; hl += 4
	ld a, l
	cp LOW(WildmonFamiliesEnd)
	jr nz, .loop
	ld a, h
	cp HIGH(WildmonFamiliesEnd)
	jr nz, .loop

	ld a, e
	ret


INCLUDE "tools/character_mode/wildmon_families.asm"
