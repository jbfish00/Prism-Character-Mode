; QoL (user 2026-10-17): the move relearner is free and also teaches egg moves.
; Prism's relearner (Moraga Town, bank 2 $7504..$759D) took one Heart Scale (item $38) per move:
;   $750F  jp nc, $7559        ; CheckItem failed -> "come back with a Heart Scale"   -> 3 nops
;   $7590  call $12DB          ; TossItem (one Heart Scale)                           -> 3 nops
;   $7593  ld hl,$7605 / call $2F57 / call $13B8   ; "handed over" message            -> 9 nops
; Its move list ($D003.., count $D002, $FF-terminated) is built at $768F from the level-up learnsets of the mon and its
; pre-evolutions. The builder's tail `ld a,b / ld [$D002],a` ($76FB) becomes a call to RelearnerEggAppend, which adds
; the egg moves of the mon's base species (EggMovePointers, bank 8 $4100, indexed by species-1, $FF-terminated lists),
; skipping moves already listed ($7701) or known ($770F), capped at 32 entries ($D003..$D023; $D073 is the next buffer
; the relearner uses). CM_NO_EGGRELEARN (test images only) keeps the vanilla list for the control.

SECTION "RelearnerFreeCheck", ROMX[$750F], BANK[2]
	nop
	nop
	nop

SECTION "RelearnerFreeToss", ROMX[$7590], BANK[2]
	ds 12, 0                    ; call TossItem + the "handed over" message: nops; $759C `jr $7559` stays

; QoL A2 (2026-10-24): the relearner lists every level-up move, not only up to the mon's level. The builder loads the
; level with `ld a, MON_LEVEL ($1F) / call GetPartyParam ($2967)` ($769F) into wCurPartyLevel ($D143) and stops at the
; first learnset entry above it; it now loads 100. Its list ($D003..) is deduped against itself and the known moves and
; has room up to $D073 (the relearner's next buffer). CM_NO_ANYLEVEL (test images only) keeps the level cut.
IF !DEF(CM_NO_ANYLEVEL)
SECTION "RelearnerAnyLevel", ROMX[$769F], BANK[2]
	ld a, 100                   ; was: ld a, MON_LEVEL / call GetPartyParam
	nop
	nop
	nop
ENDC

IF !DEF(CM_NO_EGGRELEARN)
SECTION "RelearnerEggHook", ROMX[$76FB], BANK[2]
	call RelearnerEggAppend
	nop

SECTION "RelearnerEggAppend", ROMX[$7D20], BANK[2]
RelearnerEggAppend::            ; in: b = moves listed, de = the $FF slot after them, [$D108] = species
	push bc
	push de
	ld a, [$D108]
	push af
.base                           ; walk to the base species (the builder's own pre-evolution farcall)
	rst $08
	db $10
	dw $5D9B
	jr c, .base
	ld a, [$D108]
	dec a
	ld c, a
	ld b, 0
	ld hl, $4100
	add hl, bc
	add hl, bc
	ld a, $08
	call $0BFF                  ; GetFarHalfword: hl = this species' egg-move list (bank 8)
	pop af
	ld [$D108], a               ; the species again (the builder restores it the same way)
	pop de
	pop bc
.loop
	ld a, $08
	call $001B                  ; GetFarByte, hl++
	cp $FF
	jr z, .done
	ld c, a
	ld a, b
	cp 32
	jr nc, .done
	call $7701                  ; carry: already listed
	jr c, .loop
	call $770F                  ; carry: the mon knows it
	jr c, .loop
	ld a, c
	ld [de], a
	inc de
	ld a, $FF
	ld [de], a
	inc b
	jr .loop
.done
	ld a, b
	ld [$D002], a
	ret
ENDC
