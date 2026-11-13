; START > Extras menu (QoL round 2 item 3). Called through CMExtrasFunc (home, charselect.asm) from the START menu.
; Roster (Character Mode only) / Heal party / PC / Cancel. Every path is a balanced FadeToMenu ... CloseSubmenu pair
; and leaves with a = 0, the shape of CMRosterFunc. Heal = the game's own HealParty (0B:6F18, special #28); PC = the
; game's own PokemonCenterPC (71:5E6A, special #29), both read from the ROM's special table at 1E:... (0x784EA).
; Control: -DCM_NO_EXTRAS (the row is Roster-only again, as before).
DEF ROM_GetMenu2    EQU $23D1     ; LoadMenuHeader / VerticalMenu / CloseWindow; a = cursor, carry = B (flags kept)
DEF ROM_PlaySFX     EQU $0477
DEF ROM_FadeToMenu  EQU $1E8E
DEF ROM_CloseSubmenu EQU $1E9F
DEF SFX_FULL_HEAL   EQU $05

SECTION "CMExtras", ROMX[$5C00], BANK[118]
ExtrasMenu::
	ld a, [wPartyCount]
	and a
	jr z, .roster               ; no Pokemon: the row exists only for Character Mode, so it is the roster
	call CM_GetChar
	ld hl, ExtrasMenuRoster
	ld c, 0
	jr nz, .choose
	ld hl, ExtrasMenuPlain
	ld c, 1                     ; no Roster item: cursor 1 is Heal (item 2 of the full list)
.choose
	push bc
	call ROM_GetMenu2
	pop bc
	jr c, .cancel
	add c
	dec a
	jr z, .roster
	dec a
	jr z, .heal
	dec a
	jr z, .pc
.cancel
	xor a
	ret
.roster
	call ROM_FadeToMenu
	rst $08
	db BANK(RosterScreen)
	dw RosterScreen
	call ROM_CloseSubmenu
	xor a
	ret
.heal
	call ROM_FadeToMenu
	rst $08
	db $0B
	dw $6F18                    ; HealParty
	ld de, SFX_FULL_HEAL
	call ROM_PlaySFX
	call ROM_SetPalettes        ; FadeToMenu left every palette white (as RosterScreen found)
	ld hl, TILEMAP + 20 * 7     ; Prism's PrintText wants Huffman text scripts: draw a box + two plain strings instead
	ld b, 3
	ld c, 18
	call ROM_Textbox
	ld de, ExtrasHealedLine1
	ld hl, TILEMAP + 20 * 8 + 1
	call ROM_PlaceString
	ld de, ExtrasHealedLine2
	ld hl, TILEMAP + 20 * 9 + 1
	call ROM_PlaceString
	call ROM_WaitBGMap
	call ROM_WaitBGMap
.wait
	call ROM_DelayFrame
	call ROM_GetJoypad
	ldh a, [hJoyPressed]
	and %00001011               ; A, B, Start leave
	jr z, .wait
	call ROM_CloseSubmenu
	xor a
	ret
.pc
	call ROM_FadeToMenu
	call ROM_SetPalettes
	rst $08
	db $71
	dw $5E6A                    ; PokemonCenterPC
	call ROM_CloseSubmenu
	xor a
	ret

ExtrasMenuRoster:
	db $40                      ; tile backup
	db 0, 7                     ; start coords (y, x)
	db 10, 19                   ; end coords
	dw .data
	db 1                        ; default option
.data
	db $80                      ; flags
	db 4                        ; items
	db $91, $AE, $B2, $B3, $A4, $B1, $50                          ; "Roster"
	db $87, $A4, $A0, $AB, $7F, $AF, $A0, $B1, $B3, $B8, $50      ; "Heal party"
	db $8F, $82, $50                                              ; "PC"
	db $82, $A0, $AD, $A2, $A4, $AB, $50                          ; "Cancel"

ExtrasMenuPlain:
	db $40
	db 0, 7
	db 8, 19
	dw .data
	db 1
.data
	db $80
	db 3
	db $87, $A4, $A0, $AB, $7F, $AF, $A0, $B1, $B3, $B8, $50      ; "Heal party"
	db $8F, $82, $50                                              ; "PC"
	db $82, $A0, $AD, $A2, $A4, $AB, $50                          ; "Cancel"

ExtrasHealedLine1:
	db $98, $AE, $B4, $B1, $7F, $AF, $A0, $B1, $B3, $B8, $7F, $B6, $A0, $B2, $50      ; "Your party was"
ExtrasHealedLine2:
	db $A5, $B4, $AB, $AB, $B8, $7F, $A7, $A4, $A0, $AB, $A4, $A3, $E7, $50           ; "fully healed!"
