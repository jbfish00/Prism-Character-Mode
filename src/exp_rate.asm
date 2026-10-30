; Exp. Rate option (2026-10-29): 0.5x / 1x / 1.5x / 2x / 3x of the EXP every Pokemon gets from a battle. Always on
; (Character Mode on or off). The rate is a row on the second Options page.
;
; Storage: wExpRate ($DC98), one of Crystal's padding bytes after wPhoneList in the SAVED player block, next to
; wCharMode/wCharModeCheck ($DC96/$DC97); Prism never references $DC98-$DC9B (docs/SELECTION_MECHANISM.md). Old saves
; read 0 = 1x. 1 = 1.5x, 2 = 2x, 3 = 3x, 4 = 0.5x (the Options row cycles in that order: LEFT from 1x is 0.5x).
;
; The award: GiveExperiencePoints ($0F) leaves each mon's final award (Exp. Share split, traded/trainer/Lucky Egg
; boosts) as a 16-bit value in hQuotient+2/+3 ($FFB5/$FFB6), then copies it to wStringBuffer2 ($D086/$D087) for the
; "gained N EXP" text and the add. At 0F:6894 `ldh a,[$FFB6] / ld [$D087],a` becomes a farcall to ExpRateApply,
; which scales the award (x*N/2, clamped to $FFFF, a nonzero award never becomes 0) and replays the two instructions.
;
; The Options menu (bank $18, OptionsMenu 18:44BA) is table driven: 7-byte entries at 18:45B5 + page*42 + row*7
; (dw WRAM address - $C000 | bit << 13, db max value, dw value strings (bit 15 = a draw routine instead), dw
; callback), rows per page at 18:4788 (db last row, dw compressed labels). Page 2 had 4 rows; its 5th slot (18:45FB)
; held the "Page" entry that row 6 reads directly. That entry moves to free space at 18:7FE8 (24 bytes of $FF at the
; end of the bank), the slot becomes the Exp. Rate entry, and page 2 gets 5 rows. Its label is plain text placed by
; a home hook on the label loop's last call (the shipped labels are compressed); its value is drawn by a bank-118
; routine reached through a 4-byte stub in bank $18 (the strings do not fit the bank's free bytes).
; CM_NO_EXPRATE: the award is left alone (the Options row stays).

DEF wExpRate           EQU $DC98
DEF hExpHi             EQU $FFB5   ; hQuotient + 2
DEF hExpLo             EQU $FFB6   ; hQuotient + 3
DEF wExpTextHi         EQU $D086   ; wStringBuffer2
DEF wExpTextLo         EQU $D087
DEF wOptionsRow        EQU $CF63
DEF wOptionsPage       EQU $CF65
DEF ROM_PlaceCompressed EQU $3245
DEF ROM_Coord          EQU $341F   ; b = tile row, c = tile column -> hl = wTilemap address
DEF OPTIONS_CALLBACK   EQU $45B3   ; the callback every plain option row uses

; ---------------------------------------------------------------------------------------------- the award
SECTION "ExpRateHook", ROMX[$6894], BANK[$0F]
	rst $08                 ; overwrites: ldh a,[$FFB6] / ld [$D087],a  (5 bytes)
	db BANK(ExpRateApply)
	dw ExpRateApply
	nop

SECTION "CMExpRate", ROMX[$5800], BANK[118]
ExpRateApply::
IF !DEF(CM_NO_EXPRATE)
	push bc
	push de
	push hl
	ld a, [wExpRate]
	and a
	jr z, .done             ; 1x
	cp 5
	jr nc, .done
	ld c, a
	ld b, 0
	ld hl, ExpRateHalves - 1
	add hl, bc
	ld c, [hl]              ; c = the rate in halves
	ldh a, [hExpHi]
	ld d, a
	ldh a, [hExpLo]
	ld e, a                 ; de = the award
	or d
	jr z, .done
	xor a
	ld h, a
	ld l, a                 ; a:hl = de * c
.mul:
	add hl, de
	adc a, 0
	dec c
	jr nz, .mul
	srl a                   ; / 2
	rr h
	rr l
	and a
	jr z, .fits
	ld hl, $FFFF            ; past 16 bits: clamp
.fits:
	ld a, h
	or l
	jr nz, .store
	inc l                   ; a nonzero award never rounds down to 0
.store:
	ld a, h
	ldh [hExpHi], a
	ld a, l
	ldh [hExpLo], a
.done:
	pop hl
	pop de
	pop bc
ENDC
	ldh a, [hExpLo]         ; displaced
	ld [wExpTextLo], a
	ret

ExpRateHalves::         ; wExpRate 1..4: 1.5x 2x 3x 0.5x
	db 3, 4, 6, 1

; ---------------------------------------------------------------------------------------------- the Options row
; value: d = the row's value (the menu has stored it already); drawn at the menu's value column of this row
ExpRateDraw::
	ld a, [wOptionsRow]
	add a
	add 3
	ld b, a
	ld c, $0B
	call ROM_Coord
	ld a, d
	cp 5
	jr c, .ok
	xor a
.ok:
	push hl
	ld e, a
	ld d, 0
	ld hl, ExpRateStrings
	add hl, de
	add hl, de
	ld a, [hl+]
	ld d, [hl]
	ld e, a
	pop hl
	jp ROM_PlaceString

ExpRateStrings:
	dw .x1, .x15, .x2, .x3, .x05
.x1:	db $F7, $B7, $7F, $7F, $50              ; "1x  "
.x15:	db $F7, $E8, $FB, $B7, $50              ; "1.5x"
.x2:	db $F8, $B7, $7F, $7F, $50              ; "2x  "
.x3:	db $F9, $B7, $7F, $7F, $50              ; "3x  "
.x05:	db $F6, $E8, $FB, $B7, $50              ; "0.5x"

SECTION "OptionsPageEntryPtr", ROMX[$44FD], BANK[$18]
	dw OptionsPageEntry     ; row 6 ("Page") reads its entry here (was 18:45FB)

SECTION "OptionsExpRateEntry", ROMX[$45FB], BANK[$18]
	dw (wExpRate - $C000) | (0 << 13)
	db 4                    ; values 0..4 (3 bits)
	dw $8000 | ExpRateDrawStub
	dw OPTIONS_CALLBACK

SECTION "OptionsPage2Rows", ROMX[$478B], BANK[$18]
	db 4                    ; page 2: rows 0..4 (was 3)

SECTION "OptionsLabelHook", ROMX[$4701], BANK[$18]
	call ExpRateLabelHome   ; was call ROM_PlaceCompressed (the label loop)

SECTION "OptionsBankTail", ROMX[$7FE8], BANK[$18]
OptionsPageEntry:
	db $65, $0F, $01, $C2, $C6, $D6, $46    ; the shipped "Page" entry, moved byte for byte
ExpRateDrawStub:
	rst $08
	db BANK(ExpRateDraw) | $80
	dw ExpRateDraw

SECTION "ExpRateLabelHomeCode", ROM0[$3DA0]
; The label loop calls this with a = labels left (1 = the last), hl = where, de = the compressed label. Page 2's
; last label is ours, in plain text.
ExpRateLabelHome::
	push af
	cp 1
	jr nz, .vanilla
	ld a, [wOptionsPage]
	cp 1
	jr nz, .vanilla
	pop af
	ld de, ExpRateLabelText
	jp ROM_PlaceString
.vanilla:
	pop af
	jp ROM_PlaceCompressed

ExpRateLabelText:
	db $84, $B7, $AF, $E8, $7F, $91, $A0, $B3, $A4, $50   ; "Exp. Rate"
