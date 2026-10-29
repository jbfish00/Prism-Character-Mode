; QoL A3 (2026-10-28): new games start with battle animations off.
; Crystal's options are global: wOptions comes from the save, or from DefaultOptions when there is no valid save
; (TryLoadSaveFile's .corrupt path, Prism 05:5086 copies 6 bytes from 05:5093 to wOptions $CFCC). Byte 0 is
; wOptions itself: $21 = text delay 1 + stereo. Bit 7 is BATTLE_SCENE (off when set), as Prism's own
; CheckBattleScene reads it at 00:0893 (ld a,[wOptions] / and $80 / ret z). A save keeps whatever the player chose;
; the Options menu still turns animations back on.
IF !DEF(CM_NO_ANIMDEFAULT)
SECTION "QolDefaultOptions", ROMX[$5093], BANK[5]
	db $21 | (1 << 7)
ENDC

; QoL A3 instant HP bar (2026-10-28). HPBarAnim_UpdateVariables ($40:40B7, pokecrystal's: ld hl,wCurHPBarPixels /
; ld a,c / and a / jr nz,.inc ...) steps the bar one pixel per call. After its ld hl, `inc hl; jr .animdone` ($40:40F3,
; which reads the target at wCurHPBarPixels + 1 with ld a,[hld]) sets the bar and the HP to the target at once: one
; redraw, then the loop ends. Replaces `ld a,c / and a / jr nz` ($79 $A7 $20).
IF !DEF(CM_NO_INSTANTHP)
SECTION "QolInstantHP", ROMX[$40BA], BANK[$40]
	inc hl
	jr @ + 2 + $36           ; -> .animdone $40F3
ENDC
