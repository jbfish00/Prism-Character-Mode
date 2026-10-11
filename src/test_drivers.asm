; Test-only drivers (assembled only with -DCM_TEST, i.e. build/prism_cm_test.gbc; never shipped).
; PyBoy slows to ~30 ms/frame once any PC hook is registered, so statistical tests run their
; loops INSIDE the emulator and read a tally back out of WRAM bank 7 ($D000, the engine's
; decompression scratch bank, otherwise idle).

SECTION "CMTestDrivers", ROMX[$7000], BANK[118]
; One OverrideWildSpecies per iteration (c = 16 is the 'vanilla' species the engine rolled).
; in: bc = iterations, d = level.  Out: WRAM7 $D000 + 2*species = 16-bit count of how often that
; species came out; index 0 = 'no override' (the engine's own roll stands). The caller zeroes the table.
CMTestWildLoop::
	ldh a, [rSVBK]
	push af
.loop:
	push bc
	push de
	ld a, 1
	ldh [rSVBK], a              ; the game's own bank while the code under test runs
	ld b, d
	ld c, 16
	call OverrideWildSpecies
	jr c, .hit
	xor a
.hit:
	ld e, a
	ld a, 7
	ldh [rSVBK], a
	ld l, e
	ld h, 0
	add hl, hl
	ld de, $D000
	add hl, de
	inc [hl]
	jr nz, .counted
	inc hl
	inc [hl]
.counted:
	pop de
	pop bc
	dec bc
	ld a, b
	or c
	jr nz, .loop
	pop af
	ldh [rSVBK], a
	ret
