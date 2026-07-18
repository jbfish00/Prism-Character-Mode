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

	ld a, [CharModeCharId]
	inc a                   ; $FF (mode off) -> 0
	jr z, .allow
	dec a

	push hl
	push bc
	; hl = CharacterModeRosters + char_id * 32
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	ld bc, CharacterModeRosters
	add hl, bc
	; hl += species >> 3 (byte holding this species' bit)
	ld a, [ENEMY_MON_SPECIES]
	srl a
	srl a
	srl a
	ld c, a
	ld b, 0
	add hl, bc
	ld c, [hl]              ; roster bitmap byte
	; shift the species' bit (species & 7, LSB-first) down to bit 0
	ld a, [ENEMY_MON_SPECIES]
	and 7
	jr z, .test
.shiftloop:
	srl c
	dec a
	jr nz, .shiftloop
.test:
	bit 0, c
	pop bc
	pop hl
	jr z, .block
.allow:
	ld a, [WILD_MON_VERDICT]
	ret
.block:
	xor a
	ld [WILD_MON_VERDICT], a
	ret

INCLUDE "tools/character_mode/rosters.asm"


SECTION "CharModeCharId", ROMX[$7FFE], BANK[118]
; Active character index into CharacterModeRosters ($FF = Character Mode off).
; Fixed address so tests can flip it by patching one byte:
;   file offset 0x1DBFFE in the built ROM.
; Dev default: 8 = Brock (37 species — see tools/character_mode/roster_index.tsv)
CharModeCharId::
	db 8
