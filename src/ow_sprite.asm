; Player overworld sprite follows the character (2026-11-04).
;
; Art: tools/character_mode/build_ow_sprites.py -> ow_sprites.asm (OWArtTable in bank 118 $7400: per character
; db bank / dw LZ sheet / db OBJ palette; the sheets in bank $7F and bank $78 from $5800). Native GBC art only
; (the character's own Polished Crystal / Crystal Inheritance / pokecrystal sprite, or a stand-in GBC sprite).
;
; Three hooks, all inert with Character Mode off or for a character without a sheet:
;  1. GetPlayerSprite (05:405D `ld a,[wPlayerState]`): while walking (state 0) the outfit table is replaced by the
;     default one at 05:40B2, so the walking sprite is always id 1 (Prism's outfits use ids $60..$86).
;     Bike, surf and the other states keep Prism's own sprites.
;  2. GetSprite (05:4184 `ld hl,OverworldSprites`): id 1 returns the character's sheet (de = LZ, b = bank,
;     c = 12 tiles, l = type 1 walking, h = palette) and returns straight to GetSprite's caller. Every reader of
;     a sprite's data/palette goes through GetSprite (the home palette helper 00:20A4 farcalls 05:417F).
;  3. SpawnPlayer (0B:6B72): the player's map object palette is $80 (OBJ palette 0, Prism's outfit colours);
;     with a sheet it becomes (palette << 4), one of the NPC palettes 1-7 (blue, green, brown, red, silver,
;     yellow, purple). The follower-Pokemon branch (bit 1 of $D84C) is unchanged.

DEF wPlayerState    EQU $D9A0
DEF wPlayerSpriteFl EQU $D84C

IF !DEF(CM_NO_OWSPRITE)

SECTION "OWHookPlayerSprite", ROMX[$405D], BANK[5]
	call CM_PlayerSpriteHook          ; was: ld a,[wPlayerState]

SECTION "OWHookGetSprite", ROMX[$4184], BANK[5]
	call CM_GetSpriteHook             ; was: ld hl,$45DC

SECTION "OWHookSpawnPal", ROMX[$6B72], BANK[$0B]
	call CM_PlayerPalHook             ; was: ld a,[$D84C] / bit 1,a / ld a,$80 / jr z,$6B8F
	jr z, @ + 2 + ($6B8F - $6B77)
	nop
	nop
	nop
	nop

SECTION "OWBank5Stubs", ROMX[$7F00], BANK[5]
CM_PlayerSpriteHook:
	ld a, [wPlayerState]
	and a
	ret nz                            ; not walking: Prism's outfit table as is
	push hl
	rst $08
	db BANK(CM_OWArt)
	dw CM_OWArt
	pop hl
	jr nc, .done
	ld hl, $40B2                      ; the default outfit: walking -> sprite 1
.done:
	xor a                             ; a = wPlayerState (0)
	ret

CM_GetSpriteHook:                     ; a = sprite id (1-based)
	cp 1
	jr nz, .vanilla
	rst $08
	db BANK(CM_OWArt)
	dw CM_OWArt
	jr nc, .vanilla1
	add sp, 2                         ; drop the return into GetSprite: back to its caller with de/b/c/l/h
	ret
.vanilla1:
	ld a, 1
.vanilla:
	ld hl, $45DC
	ret

SECTION "OWBank0BStub", ROMX[$7F00], BANK[$0B]
CM_PlayerPalHook:
	ld a, [wPlayerSpriteFl]
	bit 1, a
	ld a, $80
	ret nz                            ; follower branch, Z clear as before
	push bc
	push de
	push hl
	rst $08
	db BANK(CM_OWArt)
	dw CM_OWArt
	ld a, h                           ; palette 1..7 (flags kept)
	pop hl
	pop de
	pop bc
	jr c, .cm
	ld a, $80
	cp a                              ; Z set: the store path
	ret
.cm:
	swap a
	cp a
	ret

ENDC

SECTION "CMOWArt", ROMX[$6E00], BANK[118]
; out: carry set = the active character has a sheet; then de = LZ sheet, b = its bank, c = 12, l = 1 (walking
; sprite), h = OBJ palette (1..7). Carry clear: nothing changed but b/c/d/e/h/l.
CM_OWArt::
	call CM_GetChar
	jr z, .no
	dec a
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld de, OWArtTable
	add hl, de
	ld a, [hl+]
	and a
	jr z, .no
	ld b, a
	ld e, [hl]
	inc hl
	ld d, [hl]
	inc hl
	ld h, [hl]
	ld l, 1
	ld c, 12
	ld a, 1
	scf
	ret
.no:
	ld a, 1
	and a
	ret

INCLUDE "tools/character_mode/ow_sprites.asm"
