; Pokemon Prism Character Mode — catch gate (Phase 4 step 1)
;
; Target: Pokemon Prism v0.95 build 254 Hotfix 5
;         (sha1 752076692ae3387cf426ce5f51a98c6b60e8df6a — see rom.sha1)
; Build:  tools/bin/rgbasm -o build/character_mode.o src/character_mode.asm
;         tools/bin/rgblink -O rom/<prism>.gbc -o build/prism_cm.gbc build/character_mode.o
;
; How it works (all addresses RE'd this project, see CLAUDE.md session 4-5):
;   Prism's PokeBallEffect (03:7853) computes the catch verdict via a
;   farcall-to-hl (rst $20, bank $1E) that leaves the verdict in $C64E
;   (wWildMon): nonzero = caught, zero = broke free. The 5-byte sequence at
;   03:78CA   rst $20 / db $1E / ld a,[$C64E]
;   is replaced with a farcall (rst $08, 4 bytes) to CatchGate below + nop.
;   CatchGate replays the original calc, then — if the mon was caught and
;   Character Mode is active — clears the verdict for off-roster species, so
;   the ball plays the normal "broke free" flow. Every catch path (incl.
;   Master Ball) flows through this verdict read.
;
; rst conventions (Prism-specific, RE'd session 4):
;   rst $08 = farcall,      inline: db bank, dw addr
;   rst $20 = farcall-to-hl, inline: db bank   (hl preserved into stub by
;             the rst $08 trampoline, so replaying it here is equivalent)

DEF WILD_MON_VERDICT  EQU $C64E  ; wWildMon: catch verdict (0 = escaped)
DEF ENEMY_MON_SPECIES EQU $D206  ; wEnemyMonSpecies (vanilla-compatible addr)
DEF CATCH_CALC_BANK   EQU $1E    ; bank of Prism's catch/shake calculator

; Active character, in the SAVED player-data block (WRAM $D47B..$DCA4 is copied
; to SRAM $A009 by the save, and the backup is a copy of that). $DC96 is one of
; Crystal's 22 padding bytes after wPhoneList ($DC87-$DC9C); Prism never
; references $DC93/$DC94/$DC96-$DC9B (docs/SELECTION_MECHANISM.md).
; 0 = Character Mode off, N = character id N-1 (id order = roster_index.tsv).
DEF wCharMode         EQU $DC96
DEF wCharModeCheck    EQU $DC97   ; = wCharMode xor CM_CHECK_XOR (validity pair)
DEF CM_CHECK_XOR      EQU $A5


SECTION "CatchGateHook", ROMX[$78CA], BANK[3]
	; overwrites: rst $20 / db $1E / ld a,[$C64E]  (5 bytes)
	rst $08
	db BANK(CatchGate)
	dw CatchGate
	nop


SECTION "CharacterModeGate", ROMX[$4000], BANK[118]
CatchGate::
	; replay the displaced catch calculation (hl arrived preserved)
	rst $20
	db CATCH_CALC_BANK
	ld a, [WILD_MON_VERDICT]
	and a
	ret z                   ; broke free on its own — nothing to gate

	call CM_GetChar         ; 0 = Character Mode off
	jr z, .allow
	dec a                   ; stored value is id + 1
	push de
	ld d, a
	ld a, [ENEMY_MON_SPECIES]
	call CM_OnRoster        ; carry = on the roster (preserves bc, de, hl)
	pop de
	jr nc, .block
.allow:
	ld a, [WILD_MON_VERDICT]
	ret
.block:
	xor a
	ld [WILD_MON_VERDICT], a
	ret

; The roster bitmaps live in their own bank (bank 120, sections fixed): with 150+ characters the table no
; longer fits beside the code, so every reader goes through CM_OnRoster (gates.asm), which reads it with
; the home bank's far-byte helper.
INCLUDE "tools/character_mode/rosters.asm"


INCLUDE "src/charselect.asm"

INCLUDE "src/gates.asm"

INCLUDE "src/wildmon_override.asm"
INCLUDE "src/free_tutors.asm"

IF DEF(CM_TEST)
INCLUDE "src/test_drivers.asm"
ENDC


