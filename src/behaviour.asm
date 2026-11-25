; Move best-version behaviour cards, batch 1 (2026-11-25). Design + card-by-card status:
;   ../game_plans/move_ability_best_2026-11-22/behaviour_all/PRISM.md
; Everything here is behind IF !DEF(CM_NO_BEHAVIOUR); that control build is the previous release byte for byte.
; Checker: tools/tests/check_behaviour.py (asserts the release bytes in the control and these bytes in the build).
; Prism's battle counters hold turns + 1 (Disable 5 = 4 turns, Wrap 3-6 = 2-5 turns: pokecrystal's values + 1), so the
; Gen IV/VI turn ranges below are written in that convention.
; Helpers used (RE'd 2026-11-25): GetBattleVar $0733 (var $0E = move anim = move id), BattleRandom $29CE (keeps bc/de/hl).

IF !DEF(CM_NO_BEHAVIOUR)

DEF BV_GetBattleVar EQU $0733
DEF BV_BattleRandom EQU $29CE
DEF BV_PerfectAcc   EQU $762D      ; CheckHit's perfect-accuracy-effect check (z = can't miss)
DEF MOVE_DRAGON_PULSE EQU 49
DEF MOVE_DARK_PULSE   EQU 198

; --- never-miss (best accuracy "can't miss"): Dragon Pulse, Dark Pulse. Mirror Move never rolls accuracy itself. ---
SECTION "BehNeverMissHook", ROMX[$7534], BANK[$0D]
	call CM_NeverMiss             ; was: call $762D (ret z follows)

; --- Disable 4-7 turns (Gen IV): counter 5..8 ---
SECTION "BehDisableHook", ROMX[$6AAD], BANK[$0D]
	call CM_DisableTurns          ; was: ld a,$05 / inc c

; --- Encore 4-8 turns (Gen IV): counter 5..9 ---
SECTION "BehEncoreHook", ROMX[$6B17], BANK[$0D]
	call CM_EncoreTurns           ; was: call BattleRandom / and 3 / add 4  (7 bytes)
	nop
	nop
	nop
	nop

; --- Protect / Detect / Endure: odds halve per consecutive use, floor 1/8 (Gen IV-V) ---
SECTION "BehProtectHook", ROMX[$6F01], BANK[$0D]
	call CM_ProtectCap            ; was: ld b,[hl] / call BattleRandom  (4 bytes)
	nop

; --- Wrap / Fire Spin / Bind...: 4-5 turns (Gen VI-VII): counter 5..6 (damage is already 1/8) ---
SECTION "BehTrapTurns", ROMX[$5A79], BANK[$0D]
	and $01                       ; was: and $03 / add $03
	add $05

; --- Roar / Whirlwind never fail on level difference (Gen V+) ---
SECTION "BehRoarLevel", ROMX[$4C9B], BANK[$0D]
	and a                         ; was: call $4CCF (level roll; carry = fail)
	nop
	nop

; --- Flail / Reversal: Gen IV HP bands (64ths) ---
SECTION "BehFlailMult", ROMX[$61E8], BANK[$0D]
	db $40                        ; was: ld a,$30 (HP x48)
SECTION "BehFlailTable", ROMX[$6221], BANK[$0D]
	db  1, 200,  5, 150, 12, 100, 21,  80, 42,  40, 64,  20   ; was 1/4/9/16/32/48

; --- routines, in bank $0D's unused tail (0D:7F6D-7FFF is $FF, nothing points into it) ---
SECTION "BehBank0D", ROMX[$7F80], BANK[$0D]
CM_NeverMiss::
	call BV_PerfectAcc
	ret z
	ld a, $0E
	call BV_GetBattleVar
	cp MOVE_DRAGON_PULSE
	ret z
	cp MOVE_DARK_PULSE
	ret                           ; z = can't miss

CM_DisableTurns::
	call BV_BattleRandom
	and $03
	add $05
	inc c                         ; the displaced instruction
	ret

CM_EncoreTurns::
.roll
	call BV_BattleRandom
	and $07
	cp $05
	jr nc, .roll
	add $05
	ret

CM_ProtectCap::
	ld a, [hl]                    ; consecutive uses incl. this one
	cp $04
	jr c, .ok
	ld a, $04                     ; at most 3 halvings
.ok
	ld b, a
	jp BV_BattleRandom

ENDC
