; Character Mode: new-game character selection (Prism front 2 + 3).
;
; Hook: the intro routine in bank 1 ends  ...call $5E15 (gender+name) ;
;   ld hl,$5D8D ; jp $2F57 (print "Why not tell me a little about...").
; The 6 bytes at 01:5B86 become `jp CharSelectHook` (home bank, $3CC7 free
; filler), which farcalls CharSelect (bank 119) and then does the displaced
; `ld hl,$5D8D / jp $2F57`. The intro is reached ONLY from New Game, so the
; picker cannot be skipped and never runs on Continue.
;
; Home-bank routines used (mapped by tools/home_vote.py, verified in game):
DEF ROM_ByteFill    EQU $0BE1
DEF ROM_WaitBGMap   EQU $0F22
DEF ROM_DelayFrame  EQU $0F45
DEF ROM_GetJoypad   EQU $1386
DEF ROM_Textbox     EQU $2EB2   ; hl = tilemap dest, b = inner height, c = inner width
DEF ROM_PlaceString EQU $2FC5   ; de = string, hl = tilemap dest
DEF TILEMAP         EQU $C4A0
DEF hJoyPressed     EQU $FFA7
DEF rSVBK           EQU $FF70

DEF CS_ROWS         EQU 12
DEF CS_FIRST_ROW    EQU 3
DEF TILE_CURSOR     EQU $ED
DEF TILE_BLANK      EQU $7F
DEF TILEMAP_SIZE    EQU 360

SECTION "CharSelectHookSite", ROMX[$5B86], BANK[1]
	jp CharSelectHook
	nop
	nop
	nop

SECTION "CharSelectHome", ROM0[$3CC7]
CharSelectHook::
	rst $08
	db BANK(CharSelect)
	dw CharSelect
	ld hl, $5D8D            ; displaced: intro text pointer
	jp $2F57                ; displaced: PrintText (tail call)

; Test scaffolding (6 bytes of home filler): tests enter a routine through
; CMTestEnter (hl = target; PyBoy leaves IME cleared after a PC rewrite) and return
; to CMTestPark, which spins. Nothing in the game references either.
CMTestPark::
	jr CMTestPark
CMTestEnter::
	ei
	jp hl

INCLUDE "tools/character_mode/select_data.asm"

SECTION "CharSelectCode", ROMX[$5000], BANK[119]
CharSelect::
	call CS_SaveScreen
	xor a
	ld [wCharMode], a       ; New Game: off until a character is picked
	ld a, CM_CHECK_XOR
	ld [wCharModeCheck], a
	ld hl, TILEMAP
	ld b, 16
	ld c, 18
	call ROM_Textbox
	ld de, CharSelectTitle
	ld hl, TILEMAP + 20 * 1 + 2
	call ROM_PlaceString
	ld de, CharSelectHint
	ld hl, TILEMAP + 20 * 16 + 2
	call ROM_PlaceString
	ld de, 0                ; d = cursor entry, e = top visible entry
.redraw:
	push de
	call CS_DrawList
	call ROM_WaitBGMap
	pop de
.input:
	push de
	call ROM_DelayFrame
	call ROM_GetJoypad
	pop de
	ldh a, [hJoyPressed]
	bit 0, a
	jr nz, .confirm
	bit 6, a
	jr nz, .up
	bit 7, a
	jr nz, .down
	bit 5, a
	jr nz, .left
	bit 4, a
	jr nz, .right
	jr .input
.up:
	ld a, d
	and a
	jr nz, .up_dec
	ld a, CHARSEL_COUNT
.up_dec:
	dec a
	ld d, a
	jr .scroll
.down:
	ld a, d
	inc a
	cp CHARSEL_COUNT
	jr c, .down_ok
	xor a
.down_ok:
	ld d, a
	jr .scroll
.left:
	ld a, d
	sub CS_ROWS
	jr nc, .left_ok
	xor a
.left_ok:
	ld d, a
	jr .scroll
.right:
	ld a, d
	add CS_ROWS
	cp CHARSEL_COUNT
	jr c, .right_ok
	ld a, CHARSEL_COUNT - 1
.right_ok:
	ld d, a
.scroll:                    ; keep the cursor inside [top, top + CS_ROWS)
	ld a, d
	cp e
	jr nc, .not_above
	ld e, a
	jr .redraw
.not_above:
	sub e
	cp CS_ROWS
	jr c, .redraw
	ld a, d
	sub CS_ROWS - 1
	ld e, a
	jr .redraw
.confirm:
	ld a, d
	and a
	jr z, .store            ; entry 0 = Normal game -> mode off
	ld e, a
	ld d, 0
	ld hl, CharSelectIds - 1
	add hl, de
	ld a, [hl]
	inc a                   ; stored as id + 1
.store:
	ld [wCharMode], a
	xor CM_CHECK_XOR
	ld [wCharModeCheck], a  ; ($DC97 = $A5 for Normal game: a nonzero pair never reads as off)
	call CS_RestoreScreen
	jp ROM_WaitBGMap

; in: d = cursor entry, e = top visible entry
CS_DrawList:
	ld b, 0
.row:
	ld a, b
	add CS_FIRST_ROW
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl              ; hl = r * 4
	push de
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl              ; hl = r * 16
	add hl, de              ; hl = r * 20
	ld de, TILEMAP + 1
	add hl, de              ; hl = (row, col 1)
	pop de
	push hl
	push bc
	push de
	ld a, TILE_BLANK
	ld bc, 18
	call ROM_ByteFill
	pop de
	pop bc
	pop hl
	ld a, e
	add b                   ; a = entry index for this row
	cp CHARSEL_COUNT
	jr nc, .next_row        ; past the end: leave the row blank
	cp d
	jr nz, .no_cursor
	ld [hl], TILE_CURSOR
.no_cursor:
	push de
	push bc
	push hl
	ld l, a
	ld h, 0
	ld d, h
	ld e, l
	add hl, hl              ; 2n
	add hl, de              ; 3n
	add hl, hl              ; 6n
	add hl, de              ; 7n
	add hl, hl              ; 14n
	ld de, CharSelectNames
	add hl, de
	ld d, h
	ld e, l                 ; de = name
	pop hl
	inc hl                  ; hl = (row, col 2)
	call ROM_PlaceString
	pop bc
	pop de
.next_row:
	inc b
	ld a, b
	cp CS_ROWS
	jr c, .row
	ret

; The picker draws over the intro scene, so the tilemap is parked in WRAM bank 7
; ($D000, the decompression scratch bank) and put back afterwards.
CS_SaveScreen:
	ldh a, [rSVBK]
	push af
	ld a, 7
	ldh [rSVBK], a
	ld hl, TILEMAP
	ld de, $D000
	ld bc, TILEMAP_SIZE
	rst $30
	pop af
	ldh [rSVBK], a
	ret

CS_RestoreScreen:
	ldh a, [rSVBK]
	push af
	ld a, 7
	ldh [rSVBK], a
	ld hl, $D000
	ld de, TILEMAP
	ld bc, TILEMAP_SIZE
	rst $30
	pop af
	ldh [rSVBK], a
	ret


; ===========================================================================
; Roster screen (Character Mode only): the START menu's EXIT row becomes ROSTER.
;
; The START menu (bank 4) draws and runs items through a 9-entry table at 04:606F, 4 bytes
; per item = (function, label), read by one routine at 04:60E0 (hl = [$CF97] + 4 * de). Item 7
; is EXIT. With Character Mode on, that routine hands back our own entry instead of EXIT's:
;   function CMRosterFunc (home bank, shaped like StartMenu_Pokegear: FadeToMenu / body /
;   CloseSubmenu / ld a,0), label "Roster". Mode off: the table is read exactly as shipped.
; The 4 bytes at 04:60E0 become a jump-variant tail call, so GetMenuItemCM's `ret` returns to
; the caller of the original routine.
SECTION "GetMenuItemHook", ROMX[$60E0], BANK[4]
	rst $08
	db BANK(GetMenuItemCM) | $80
	dw GetMenuItemCM

SECTION "CMRosterHome", ROM0[$3CD7]
CMRosterEntry::
	dw CMRosterFunc
	dw CMRosterLabel
CMRosterLabel::
	db $91, $AE, $B2, $B3, $A4, $B1, $50      ; "Roster@"
CMRosterFunc::
	call $1E8E                  ; FadeToMenu
	rst $08
	db BANK(RosterScreen)
	dw RosterScreen
	call $1E9F                  ; CloseSubmenu
	ld a, 0
	ret

SECTION "CMGetMenuItem", ROMX[$5400], BANK[118]
GetMenuItemCM::
	ld a, [$CF97]               ; displaced: ld hl,[$CF97] / ld a,[hl+] / ld b,[hl] / ld c,a ...
	ld c, a
	ld a, [$CF98]
	ld b, a
	ld l, e
	ld h, d
	add hl, hl
	add hl, hl
	add hl, bc                  ; hl = table + 4 * item (the shipped result)
	ld a, d
	and a
	ret nz
	ld a, e
	cp 7                        ; EXIT
	ret nz
	call CM_GetChar             ; preserves bc, de, hl
	ret z
	ld hl, CMRosterEntry
	ret

SECTION "CharRosterCode", ROMX[$5600], BANK[119]
DEF RS_ROWS         EQU 11
DEF RS_FIRST_ROW    EQU 3
DEF wNamedObjectIndex EQU $D265
DEF wStringBuffer1  EQU $D073
DEF ROM_GetPokemonName EQU $1163

RosterScreen::
	ld a, [wCharMode]
	and a
	ret z
	dec a
	ld l, a
	ld h, 0
	add hl, hl
	ld de, CharRosterOffsets
	add hl, de
	ld a, [hl+]
	ld h, [hl]
	ld l, a                     ; hl = this character's root list
	ld b, h
	ld c, l                     ; bc = list base
	ld d, 0                     ; d = N roots
.count:
	ld a, [hl+]
	and a
	jr z, .counted
	inc d
	jr .count
.counted:
	push bc
	push de
	ld hl, TILEMAP
	ld b, 16
	ld c, 18
	call ROM_Textbox
	ld a, [wCharMode]
	dec a                       ; name = CharAllNames + id * 14
	ld l, a
	ld h, 0
	ld d, h
	ld e, l
	add hl, hl
	add hl, de
	add hl, hl
	add hl, de
	add hl, hl
	ld de, CharAllNames
	add hl, de
	ld d, h
	ld e, l
	ld hl, TILEMAP + 20 * 1 + 1
	call ROM_PlaceString        ; returns bc = the tile after the name
	ld h, b
	ld l, c
	ld de, RosterTitleTail
	call ROM_PlaceString
	ld de, RosterHintA
	ld hl, TILEMAP + 20 * 15 + 1
	call ROM_PlaceString
	ld de, RosterHintB
	ld hl, TILEMAP + 20 * 16 + 1
	call ROM_PlaceString
	pop de
	pop bc
	ld e, 0                     ; e = first visible root
.redraw:
	push bc
	push de
	call RS_DrawList
	call ROM_WaitBGMap
	pop de
	pop bc
.input:
	push bc
	push de
	call ROM_DelayFrame
	call ROM_GetJoypad
	pop de
	pop bc
	ldh a, [hJoyPressed]
	and %00001011               ; A, B, Start leave
	ret nz
	ldh a, [hJoyPressed]
	bit 6, a
	jr nz, .up
	bit 7, a
	jr nz, .down
	bit 5, a
	jr nz, .pgup
	bit 4, a
	jr nz, .pgdn
	jr .input
.up:
	ld a, e
	and a
	jr z, .input
	dec e
	jr .redraw
.down:
	call RS_MaxTop              ; a = max top
	cp e
	jr z, .input
	jr c, .input
	inc e
	jr .redraw
.pgup:
	ld a, e
	sub RS_ROWS
	jr nc, .pgup_ok
	xor a
.pgup_ok:
	ld e, a
	jr .redraw
.pgdn:
	call RS_MaxTop
	ld h, a
	ld a, e
	add RS_ROWS
	cp h
	jr c, .pgdn_ok
	ld a, h
.pgdn_ok:
	ld e, a
	jr .redraw

; out: a = highest valid first-visible index for N = d (0 when everything fits). Preserves bc, de.
RS_MaxTop:
	ld a, d
	sub RS_ROWS
	ret nc
	xor a
	ret

; in: bc = list base, d = N, e = first visible
RS_DrawList:
	ld a, 0
.row:
	push af                     ; row index
	ld l, a
	ld h, 0
	add a, e                    ; a = list index
	push af                     ; list index
	ld a, l
	add RS_FIRST_ROW
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl                  ; r*4
	push de
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl                  ; r*16
	add hl, de                  ; r*20
	ld de, TILEMAP + 1
	add hl, de                  ; hl = (row, col 1)
	pop de
	push hl
	push bc
	push de
	ld a, TILE_BLANK
	ld bc, 18
	call ROM_ByteFill
	pop de
	pop bc
	pop hl
	pop af                      ; a = list index
	cp d
	jr nc, .next                ; past the end: row stays blank
	push hl
	push de
	ld h, b
	ld l, c
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hl]                  ; a = root species
	ld [wNamedObjectIndex], a
	push bc
	call ROM_GetPokemonName
	pop bc
	pop de
	pop hl
	inc hl
	push bc
	push de
	ld de, wStringBuffer1
	call ROM_PlaceString
	pop de
	pop bc
.next:
	pop af
	inc a
	cp RS_ROWS
	jr c, .row
	ret

RosterTitleTail:
	db $E0, $B2, $7F, $B1, $AE, $B2, $B3, $A4, $B1, $50      ; "'s roster@"
RosterHintA:
	db $84, $B5, $AE, $AB, $B4, $B3, $A8, $AE, $AD, $B2, $7F, $A2, $AE, $B4, $AD, $B3, $50  ; "Evolutions count"
RosterHintB:
	db $B3, $AE, $AE, $E8, $7F, $7F, $81, $E3, $A1, $A0, $A2, $AA, $50                      ; "too.  B-back"

; Far byte read from home-bank code (the only place that may switch ROMX while it runs; CM_OnRoster
; lives in bank 118, so it cannot switch the bank under itself). The engine's own helper ($004B) needs
; the interrupt machinery, which the CPU-level unit tests run without.
; in: a = bank, hl = address.  out: a = byte.  Preserves bc, de, hl.
SECTION "CMFarByteHome", ROM0[$3D40]
CMFarByte::
	push bc
	ld c, a
	ldh a, [$FF9D]          ; the engine's current-bank variable
	ld b, a
	ld a, c
	ldh [$FF9D], a
	ld [$2000], a
	ld c, [hl]
	ld a, b
	ldh [$FF9D], a
	ld [$2000], a
	ld a, c
	pop bc
	ret
