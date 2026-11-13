; Wild-intro roster hint (QoL B9). BattleStartMessage (0F:763A) ends `0F:769D push hl / rst $08 0B:4000 / pop hl /
; jp StdBattleTextbox` (hl = the intro text). Those 9 bytes become a far JUMP to CM_IntroTail (rst $08 keeps hl), which
; runs the same three steps and then, in a wild battle with Character Mode on, draws one more box:
; "It is (not) on your roster." by CatchBoost's own test (CM_OnRoster on wEnemyMonSpecies).
; Prism's PrintText wants Huffman scripts, so (as the Extras heal message does) it is a drawn box + plain strings.
; Control: -DCM_NO_INTROHINT (hook not emitted).
DEF wBattleMode EQU $D22D
DEF wBattleType EQU $D230
DEF BATTLETYPE_TUTORIAL EQU 3

IF !DEF(CM_NO_INTROHINT)
SECTION "IntroHintHook", ROMX[$769D], BANK[$0F]
	rst $08
	db BANK(CM_IntroTail) | $80
	dw CM_IntroTail
	nop
	nop
	nop
	nop
	nop
ENDC

SECTION "CMIntroHint", ROMX[$5D80], BANK[118]
CM_IntroTail::
	push hl
	rst $08                 ; the displaced farcall 0B:4000
	db $0B
	dw $4000
	pop hl
	call $07B8              ; StdBattleTextbox: the game's own intro
	ld a, [wBattleMode]
	dec a
	ret nz                  ; trainer battle
	ld a, [wBattleType]
	cp BATTLETYPE_TUTORIAL
	ret z
	call CM_GetChar
	ret z
	dec a
	ld d, a
	ld a, [wEnemyMonSpecies]
	call CM_OnRoster
	jr nc, CM_IntroHintOff
CM_IntroHintOn::            ; separate labels: the live test counts which line was printed
	ld de, CM_IntroOnL1
	ld bc, CM_IntroOnL2
	jr CM_IntroDraw
CM_IntroHintOff::
	ld de, CM_IntroOffL1
	ld bc, CM_IntroOffL2
CM_IntroDraw:
	push bc
	push de
	ld hl, TILEMAP + 20 * 12
	ld b, 4
	ld c, 18
	call ROM_Textbox
	pop de
	ld hl, TILEMAP + 20 * 14 + 1
	call ROM_PlaceString
	pop de
	ld hl, TILEMAP + 20 * 15 + 1
	call ROM_PlaceString
	call ROM_WaitBGMap
	call ROM_WaitBGMap
.wait
	call ROM_DelayFrame
	call ROM_GetJoypad
	ldh a, [hJoyPressed]
	and %00000011           ; A or B
	jr z, .wait
	ret

CM_IntroOnL1:  db $88, $B3, $7F, $A8, $B2, $7F, $AE, $AD, $7F, $B8, $AE, $B4, $B1, $50   ; "It is on your"
CM_IntroOnL2:  db $B1, $AE, $B2, $B3, $A4, $B1, $E7, $50                                  ; "roster!"
CM_IntroOffL1: db $88, $B3, $7F, $A8, $B2, $7F, $AD, $AE, $B3, $7F, $AE, $AD, $7F, $B8, $AE, $B4, $B1, $50 ; "It is not on your"
CM_IntroOffL2: db $B1, $AE, $B2, $B3, $A4, $B1, $E8, $50                                  ; "roster."
