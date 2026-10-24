; QoL A1 (2026-10-24): Mart evolution items. game_plans/tools/evo_item_census.py + tools/character_mode/emit_mart_evo.py:
; Prism's Marts sell every evolution stone its rosters need, but no Mart sells a Razor Claw (Sneasel -> Weavile) or a
; Razor Fang (Gligar -> Gliscor); only the points shop has them. 18 of 115 offered characters could not finish those
; families. With Character Mode on, every Mart also lists the item for each MartEvoPairs entry whose evolved species is
; on the character's roster (Mart price: both cost 2100, the ItemAttributes price).
;
; ReadMart (45:6E78) copies the Mart (count, items..., $FF) to wCurMart, then prices each item. Its
; `ld hl,$D002 / ld de,$D0F1` (45:6E8A, 6 bytes) becomes a farcall to MartEvoAppend, which appends to wCurMart and then
; sets hl/de itself (the farcall trampoline returns the callee's hl; it never touches de). The priced shops (types 5-7)
; have their own readers and are untouched. wCurMart holds 14 items; the largest Mart lists 11.

DEF wCurMart       EQU $D0F0
DEF wMartItemBCD   EQU $D002
DEF MART_MAX_ITEMS EQU 14

SECTION "MartEvoHook", ROMX[$6E8A], BANK[$45]
	; overwrites: ld hl,$D002 / ld de,$D0F1  (6 bytes)
	rst $08
	db BANK(MartEvoAppend)
	dw MartEvoAppend
	nop
	nop

SECTION "CMMartEvo", ROMX[$5540], BANK[118]
MartEvoAppend::
IF !DEF(CM_NO_MART)
	call CM_GetChar
	jr z, .done
	dec a
	ld d, a                 ; character id (0-based)
	ld hl, MartEvoPairs
.next:
	ld a, [hli]             ; evolved species, 0 = end
	and a
	jr z, .done
	call CM_OnRoster        ; carry = on the roster (preserves bc, de, hl)
	ld a, [hli]             ; item (flags untouched)
	jr nc, .next
	call MartAddItem
	jr .next
.done:
ENDC
	ld hl, wMartItemBCD     ; displaced
	ld de, wCurMart + 1
	ret

; in: a = item. Appends it to wCurMart unless already listed or the list is full. Preserves d, hl.
MartAddItem:
	push hl
	ld e, a
	ld hl, wCurMart
	ld a, [hli]             ; count
	cp MART_MAX_ITEMS
	jr nc, .ret
	ld c, a
	ld b, a
.scan:
	ld a, b
	and a
	jr z, .add
	ld a, [hli]
	cp e
	jr z, .ret              ; the Mart already sells it
	dec b
	jr .scan
.add:                       ; hl = the old $FF slot
	ld a, e
	ld [hli], a
	ld [hl], $FF
	ld a, c
	inc a
	ld [wCurMart], a
.ret:
	pop hl
	ret

INCLUDE "tools/character_mode/mart_evo.asm"
