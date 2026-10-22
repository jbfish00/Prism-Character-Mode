; Character Mode: acquisition gates (gift now; trade/egg/PC-withdraw follow).
; All code in bank 118 so it shares CharacterModeRosters / CharStarters.

DEF ROM_GetFarByte  EQU $004B   ; a = bank, hl = address -> a = byte (bank restored)
DEF wPartyCount     EQU $DCD7
DEF wCurPartySpecies EQU $D108
DEF TRYADD_BANK     EQU $3C
DEF TRYADD_ADDR     EQU $4000   ; 3C:4000 TryAddMonToParty (carry = added)

; GivePoke (3C:48D4) = scripted gifts. Displaced 6 bytes at 3C:48D7:
;   ea 5f cf   ld [$CF5F], a      (a = 0 here)
;   cd 00 40   call TryAddMonToParty
SECTION "GiveGateHook", ROMX[$48D7], BANK[$3C]
	rst $08
	db BANK(GiveGate)
	dw GiveGate
	nop
	nop

SECTION "CMGates", ROMX[$5000], BANK[118]

; The active character, validated: $DC96 holds id + 1 and $DC97 holds ($DC96 xor $A5).
; A save made by an unpatched Prism (or any junk in those padding bytes) fails the
; pair check and reads as "off", so Character Mode can never turn on by accident.
; out: a = 0 (off) or id + 1, Z set when off. Preserves bc, de, hl.
CM_GetChar::
	ld a, [wCharMode]
	and a
	ret z
	cp NUM_CM_CHARACTERS + 1
	jr nc, .off
	push bc
	ld b, a
	ld a, [wCharModeCheck]
	xor CM_CHECK_XOR
	cp b
	pop bc
	jr nz, .off
	ld a, [wCharMode]
	and a                   ; nonzero: Z clear
	ret
.off:
	xor a                   ; a = 0, Z set
	ret

; in: a = species (1-255), d = character id (0-based)
; out: carry set = species is on the character's roster.  Preserves bc, de, hl.
CM_OnRoster::
	push hl
	push bc
	push de
	push af                 ; species
	ld l, d
	ld h, 0
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, hl              ; hl = id * 32
	srl a
	srl a
	srl a                   ; a = species >> 3
	ld e, a
	ld d, 0
	add hl, de
	ld de, CharacterModeRosters
	add hl, de              ; the bitmap byte holding this species
	ld a, BANK(CharacterModeRosters)
	call CMFarByte          ; a = that byte (the table is in another bank; home-bank helper)
	ld c, a
	pop af                  ; species
	and 7
	jr z, .test
.shift:
	srl c
	dec a
	jr nz, .shift
.test:
	bit 0, c
	pop de
	pop bc
	pop hl
	jr z, .off
	scf
	ret
.off:
	and a
	ret

; Replays `ld [$CF5F], a / call TryAddMonToParty` with the gift gated.
;   mode off / on-roster species : unchanged
;   off-roster, party empty      : species swapped to the character's starter, so
;                                  the party is never left without a legal mon
;   off-roster, party not empty  : the party is shown as full for the add, so the
;                                  engine's own "party full" path boxes the mon
GiveGate::
	ld [$CF5F], a
	call CM_GetChar
	jr z, .normal
	dec a
	ld d, a
	ld a, [wCurPartySpecies]
	call CM_OnRoster
	jr c, .normal
	ld a, [wPartyCount]
	and a
	jr nz, .to_box
	ld e, d                 ; sole mon: swap in the character's starter
	ld d, 0
	ld hl, CharStarters
	add hl, de
	ld a, [hl]
	and a
	jr z, .normal           ; no starter on file (hidden character): leave as is
	ld [wCurPartySpecies], a
	jr .normal
.to_box:
	ld b, a                 ; b = real party count
	ld a, 6
	ld [wPartyCount], a
	rst $08
	db TRYADD_BANK
	dw TRYADD_ADDR          ; returns carry clear (party "full")
	ld a, b
	ld [wPartyCount], a     ; ld/a don't touch flags
	ret
.normal:
	rst $08
	db TRYADD_BANK
	dw TRYADD_ADDR
	ret


; ---------------------------------------------------------------------------
; PC withdraw (Prism bank 56 = Bill's PC). 56:6DA7 is the withdraw routine:
;   6DA7 call $6357         ; wCurPartyMon = cursor + scroll
;   6DAA rst $10 / db $81   ; open SRAM bank 1
;   6DAC ld a,[$D109] ... predef SendGetMonIntoFromBox ...
; and its failure tail at 56:6E06 prints "The party's full!" through
;   6E09 call $67E5         ; text box + PlaceText(de), then SFX, scf, ret.
; The first 4 bytes become a tail-call (rst $08 with bank bit 7 = jump variant) into
; WithdrawGate (the hook also swallows the `rst $10 / db $81` at 6DAA, which the stub
; replays), which either tail-calls back into 56:6DAC (allowed) or into 56:6E09
; with our own text (blocked), so the routine's own return path is reused either way.
DEF PC_BANK         EQU $38
DEF PC_WITHDRAW_OK  EQU $6DAC   ; just past the displaced `rst $10 / db $81`
DEF PC_FAIL_PRINT   EQU $6E09
DEF sBoxSpecies     EQU $AD11   ; SRAM bank 1: active box species list ($FF-terminated)

SECTION "WithdrawHook", ROMX[$6DA7], BANK[$38]
	rst $08
	db BANK(WithdrawGate) | $80
	dw WithdrawGate

SECTION "WithdrawBlockedText", ROMX[$7FC3], BANK[$38]
WithdrawBlockedText::
	db $8D, $AE, $B3, $7F, $AE, $AD, $7F, $B3, $A7, $A4, $7F, $B1, $AE, $B2, $B3, $A4, $B1, $E7, $50, $50  ; "Not on the roster!" (string @, then the script @)

SECTION "CMWithdrawGate", ROMX[$5100], BANK[118]
WithdrawGate::
	ld a, [$CB2B]               ; displaced: call $6357
	ld hl, $CB2A
	add a, [hl]
	ld [$D109], a
	call CM_GetChar
	jr z, .allow
	dec a
	ld b, a                     ; b = character id
	rst $10
	db $81                      ; open SRAM bank 1
	ld a, [$D109]
	ld e, a
	ld d, 0
	ld hl, sBoxSpecies
	add hl, de
	ld c, [hl]                  ; c = species of the selected box mon
	rst $10
	db $9A                      ; close SRAM
	ld a, c
	and a
	jr z, .allow
	cp $FF
	jr z, .allow
	ld d, b
	call CM_OnRoster
	jr c, .allow
	ld de, WithdrawBlockedText
	rst $08
	db PC_BANK | $80
	dw PC_FAIL_PRINT            ; prints, plays the error SFX, scf, returns to our caller
.allow:
	rst $10
	db $81                      ; displaced: open SRAM bank 1
	rst $08
	db PC_BANK | $80
	dw PC_WITHDRAW_OK           ; the rest of the withdraw routine, returns to our caller

; ---------------------------------------------------------------------------
; In-game NPC trades (Prism bank 63 = $3F, NPCTrade at 63:4082, same shape as
; pokecrystal's NPCTrade). The Pokemon you RECEIVE is fixed per NPC (trade attribute 2),
; so an off-roster one is refused before the offer is made:
;   4092 ld a, 0 / call $439F   ; PrintTradeText(INTRO)
;   4097 call YesNoBox ...
;   40DE jp $439F               ; the common `.done` (PrintTradeText(a), return to caller)
; The 5 bytes at 4092 become a tail-call (jump variant) into TradeGate, which either
; replays the intro and tail-calls 63:4097, or tail-calls 63:40DE with a = 1 (CANCEL).
DEF TRADE_BANK      EQU $3F
DEF TRADE_GETATTR   EQU $4283   ; e = attribute, returns hl -> attribute byte
DEF TRADE_PRINT     EQU $439F   ; a = dialog id
DEF TRADE_AFTER_INTRO EQU $4097
DEF TRADE_DONE      EQU $40DE
DEF NPCTRADE_GETMON EQU 2

SECTION "TradeHook", ROMX[$4092], BANK[$3F]
	rst $08
	db BANK(TradeGate) | $80
	dw TradeGate

SECTION "CMTradeGate", ROMX[$5180], BANK[118]
TradeGate::
	call CM_GetChar
	jr z, .intro
	dec a
	ld b, a                     ; b = character id (GetTradeAttr clobbers d/e)
	ld e, NPCTRADE_GETMON
	rst $08
	db TRADE_BANK
	dw TRADE_GETATTR
	ld a, TRADE_BANK            ; hl points into bank 63; bank 118 is mapped again now
	call ROM_GetFarByte         ; a = species the NPC would hand over
	ld d, b
	call CM_OnRoster
	jr c, .intro
	ld a, 1                     ; TRADE_DIALOG_CANCEL, then return to the caller
	rst $08
	db TRADE_BANK | $80
	dw TRADE_DONE
.intro:
	xor a                       ; displaced: ld a, 0 (TRADE_DIALOG_INTRO) / call PrintTradeText
	rst $08
	db TRADE_BANK
	dw TRADE_PRINT
	rst $08
	db TRADE_BANK | $80
	dw TRADE_AFTER_INTRO

; ---------------------------------------------------------------------------
; Catch odds (PokeBallEffect, 03:7853). After the capture value X is computed into
; HRAM $FFB3..$FFB6 (call $7C60), 03:788C starts the engine's own "is X >= 256?" test:
;   788C ld hl, $FFB3 / ld a, [hl+] / ld b, a / ld a, [hl+] / or [hl] / or b / jr z, ...
; X >= 256 takes the guaranteed-catch branch (the same one a Master Ball uses), which
; also drives the ball's wobbling animation, so the visuals agree with the result.
;   CM on, species ON the roster  : $FFB5 = 1, $FFB6 = $FF -> X >= 256 -> always caught (100%)
;   CM on, species OFF the roster : X = 0 (the engine raises it to its minimum of 1) so the
;                                   ball dodges/breaks free at once; CatchGate still vetoes
;                                   the 1-in-256 success afterwards
DEF hCatchX         EQU $FFB3
DEF wEnemyMonSpecies EQU $D206

SECTION "CatchBoostHook", ROMX[$788C], BANK[3]
	rst $08
	db BANK(CatchBoost)
	dw CatchBoost

SECTION "CMCatchBoost", ROMX[$5200], BANK[118]
CatchBoost::
	push bc
	push de
	call CM_GetChar
	jr z, .plain
	dec a
	ld d, a
	ld a, [wEnemyMonSpecies]
	call CM_OnRoster
	jr nc, .off_roster
	ld a, 1
	ldh [hCatchX + 2], a        ; X >= 256: the engine's guaranteed-catch branch
	ld a, $FF
	ldh [hCatchX + 3], a        ; and the highest low byte, so the ball wobbles like a sure thing
	jr .plain
.off_roster:
	xor a
	ldh [hCatchX], a
	ldh [hCatchX + 1], a
	ldh [hCatchX + 2], a
	ldh [hCatchX + 3], a        ; X = 0 (-> 1)
.plain:
	pop de
	pop bc
	ld hl, hCatchX              ; displaced: ld hl, $FFB3 / ld a, [hl+]
	ld a, [hl+]
	ret

; ---------------------------------------------------------------------------
; Exp. Share, party-wide (ALWAYS, Character Mode on or off: user, 2026-10-21). 0F:6C3A
; IsAnyMonHoldingExpShare returns d = bitmask of alive party mons that "hold" the item, e = how
; many, Z = none; the battle code then gives the Exp. Share half to exactly those mons. Every alive
; party member counts as a holder, so the whole party shares experience from the first battle (no
; item needed), in a normal game too. The first 4 bytes become a jump-variant tail call, so this
; routine's own `ret` returns to the original caller.
DEF EXPSHARE_BANK   EQU $0F
DEF EXP_SHARE_ITEM  EQU $39
DEF wPartyMons      EQU $DCDF
DEF PARTYMON_LEN    EQU $30
DEF MON_ITEM_OFS    EQU 1
DEF MON_HP_OFS      EQU $22

SECTION "ExpShareHook", ROMX[$6C3A], BANK[$0F]
	rst $08
	db BANK(ExpShareHolders) | $80
	dw ExpShareHolders

SECTION "CMExpShare", ROMX[$5300], BANK[118]
ExpShareHolders::
	ld a, [wPartyCount]
	ld b, a
	ld hl, wPartyMons
	ld c, 1                     ; c = bit of this mon
	ld d, 0                     ; d = holder mask
.loop:
	push hl
	push de
	ld de, MON_HP_OFS
	add hl, de
	pop de
	ld a, [hl+]
	or [hl]
	pop hl
	jr z, .next                 ; fainted; every alive mon is a holder
	ld a, d
	or c
	ld d, a
.next:
	sla c
	push de
	ld de, PARTYMON_LEN
	add hl, de
	pop de
	dec b
	jr nz, .loop
	ld a, d
	ld e, 0
	ld b, 6
.count:
	srl a
	jr nc, .skip
	inc e
.skip:
	dec b
	jr nz, .count
	ld a, e
	and a
	ret

; ---------------------------------------------------------------------------
; Field moves with no compatible Pokemon (Character Mode only). 2C:5924 CheckPartyMove
; (d = move; carry clear + $D109 = party slot of a mon knowing it) is what the overworld gates
; ask before Surf, Strength, Headbutt, Rock Smash and Cut; the callers have already checked
; that the HM/TM has been obtained (flags in $DED9), so the only thing a roster can lack is a
; learner. With Character Mode on those five moves are answered "yes, party slot 0".
DEF FIELD_BANK      EQU $2C
DEF wCurPartyMon    EQU $D109
DEF CPM_RESUME      EQU $592A   ; `ld c, e` after the displaced 6 bytes (the hook swallows 4, the other 2 are dead)

SECTION "CheckPartyMoveHook", ROMX[$5924], BANK[$2C]
	rst $08
	db BANK(CheckPartyMoveCM) | $80
	dw CheckPartyMoveCM

SECTION "CMCheckPartyMove", ROMX[$5380], BANK[118]
CheckPartyMoveCM::
	ld a, d
	cp $39                      ; Surf
	jr z, .field
	cp $46                      ; Strength
	jr z, .field
	cp $1D                      ; Headbutt
	jr z, .field
	cp $F9                      ; Rock Smash
	jr z, .field
	cp $0F                      ; Cut
	jr nz, .vanilla
.field:
	call CM_GetChar
	jr z, .vanilla
	xor a
	ld [wCurPartyMon], a
	ret                         ; a = 0, carry clear: "found"
.vanilla:
	ld e, 0                     ; displaced: ld e, 0 / xor a / ld [wCurPartyMon], a
	xor a
	ld [wCurPartyMon], a
	rst $08
	db FIELD_BANK | $80
	dw CPM_RESUME

; ---------------------------------------------------------------------------------------------
; Party-menu rows for Fly and Flash with no learner.
; GetMonSubmenuItems (09:46DA) lists a mon's own field moves, then Stats/Switch/Item. Fly and
; Flash have no overworld interaction (they are only ever used from this menu), so with Character
; Mode on they are offered to every mon. The row's own action keeps its badge check, so without
; the badge it still answers "can't use that here" exactly as it does for a mon that knows it.
; The other field moves need no row: their overworld interaction asks CheckPartyMove (hooked above).
DEF MONMENU_BANK     EQU $09
DEF MONMENU_ADDITEM  EQU $4773    ; a = MonMenuOptions item id; appends to wMonSubmenuItems ($D1EB..)
DEF MONMENU_RESUME   EQU $470C    ; `ld a,$10` (Switch) -- Stats is replayed below
DEF wMonSubmenuCount EQU $D1EA
DEF wMonSubmenuItems EQU $D1EB
DEF MMI_FLY          EQU $02
DEF MMI_FLASH        EQU $06
DEF MMI_STATS        EQU $0F

SECTION "MonSubmenuHook", ROMX[$4707], BANK[MONMENU_BANK]
	; overwrites: ld a,$0F / call AddMonMenuItem (5 bytes)
	rst $08
	db BANK(MonSubmenuCM) | $80
	dw MonSubmenuCM
	nop

SECTION "CMMonSubmenu", ROMX[$5440], BANK[118]
MonSubmenuCM::
	call CM_GetChar
	jr z, .stats
	ld a, MMI_FLY
	call .add_unique
	ld a, MMI_FLASH
	call .add_unique
.stats:
	ld a, MMI_STATS             ; displaced: ld a,$0F / call AddMonMenuItem
	rst $08
	db MONMENU_BANK
	dw MONMENU_ADDITEM
	rst $08
	db MONMENU_BANK | $80
	dw MONMENU_RESUME

; a = item id; adds it unless the list already has it (the mon may know the move itself)
.add_unique:
	ld b, a
	ld a, [wMonSubmenuCount]
	and a
	jr z, .do_add
	ld c, a
	ld hl, wMonSubmenuItems
.scan:
	ld a, [hl+]
	cp b
	ret z
	dec c
	jr nz, .scan
.do_add:
	ld a, b
	rst $08
	db MONMENU_BANK
	dw MONMENU_ADDITEM
	ret

; ---------------------------------------------------------------------------------------------
; Scripted eggs. `giveegg SPECIES, LEVEL` (25:657B) loads wCurPartySpecies/wCurPartyLevel and farcalls
; GiveEgg (3C:4632); GiveEgg adds the egg to the party unconditionally (the script checked for room),
; so an off-roster egg cannot be boxed or refused without stranding the script. With Character Mode on
; an off-roster egg becomes an egg of the character's starter instead (the same swap a gift gets when
; the party is empty), so an egg can never hatch something the character may not keep.
; Day-Care eggs come from on-roster parents and rosters are closed over evolution families, so they
; pass through unchanged. 25:658B was `rst $08 / db $3C / dw $4632`; the stub makes that same call.
DEF GIVEEGG_BANK    EQU $3C
DEF GIVEEGG_ADDR    EQU $4632

SECTION "GiveEggHook", ROMX[$658B], BANK[$25]
	rst $08
	db BANK(GiveEggGate)
	dw GiveEggGate

SECTION "CMGiveEggGate", ROMX[$54C0], BANK[118]
GiveEggGate::
	call CM_GetChar
	jr z, .go
	dec a
	ld d, a
	ld a, [wCurPartySpecies]
	call CM_OnRoster
	jr c, .go
	ld e, d
	ld d, 0
	ld hl, CharStarters
	add hl, de
	ld a, [hl]
	and a
	jr z, .go               ; no starter on file (hidden character): leave as is
	ld [wCurPartySpecies], a
.go:
	rst $08
	db GIVEEGG_BANK
	dw GIVEEGG_ADDR
	ret                     ; carry (= added) comes straight back from GiveEgg

; ---------------------------------------------------------------------------------------------
; Link-cable trades (Cable Club). LinkTrade's confirm menu (0A:4A96..4AA9) sends "cancel" when the
; player picks Cancel or presses B, "trade" when the cursor is on the first row. Either side
; cancelling cancels the trade for both, so the gate is a veto on OUR side, the same shape as the
; NPC-trade gate: with Character Mode on, if the mon being offered to us is off-roster the confirm
; reads as Cancel (the engine's own "too bad the trade was canceled" text, and the partner sees
; the cancel). Eggs are exempt, as everywhere. PyBoy has no link cable, so this is tested by running
; the real decision code with the offered species planted (tools/tests/test_linktrade.py).
DEF LINK_BANK        EQU $0A
DEF wMenuCursorYLink EQU $CFA9    ; 1 = first row (Trade), 2 = Cancel
DEF wCurOTTradeMon   EQU $D003
DEF wOTPartySpecies  EQU $D281
DEF SPECIES_EGG_CM   EQU $FD

SECTION "LinkTradeHook", ROMX[$4AA5], BANK[LINK_BANK]
	; overwrites: ld a,[wMenuCursorY] / dec a  (4 bytes); the `jr z,.try_trade` after it is untouched
	rst $08
	db BANK(LinkTradeGate)
	dw LinkTradeGate

SECTION "CMLinkTradeGate", ROMX[$5500], BANK[118]
LinkTradeGate::
	ld a, [wMenuCursorYLink]        ; displaced
	dec a
	ret nz                          ; Cancel row: nothing to decide
	call CM_GetChar
	jr z, .allow
	dec a
	ld d, a
	ld a, [wCurOTTradeMon]
	ld c, a
	ld b, 0
	ld hl, wOTPartySpecies
	add hl, bc
	ld a, [hl]
	cp SPECIES_EGG_CM
	jr z, .allow
	call CM_OnRoster                ; carry = on the roster
	jr c, .allow
	ld a, 1
	and a                           ; NZ: the caller's `jr z,.try_trade` is not taken -> canceled
	ret
.allow:
	xor a                           ; Z, exactly what `dec a` left for the Trade row
	ret
