"""Shared emulator helpers for the Prism Character Mode tests.

  cm = CM()                       # build/prism_cm.gbc, build/prism_cm.sym
  cm.load("tools/emu_states/ck1.state")
  cm.call("GiveGate", a=0, b=0)   # run a routine to its ret (interrupts stay ON)
  cm.sram(bank)                   # real SRAM bytes (MBC latch opened, then restored)

call() maps the routine's ROM bank (and mirrors it into hFF9D, the engine's
current-bank variable that its farcall trampolines save/restore), plants a
`jr -2` park loop in WRAM, points the return address at it, and ticks until PC
reaches the park. The game's own interrupts keep running, so routines that print
text or wait for vblank still work; `buttons` can be pressed while it runs.
"""
import io, os
from pyboy import PyBoy

ROM = "build/prism_cm.gbc"
SYM = "build/prism_cm.sym"
WCHAR = 0xDC96


class CM:
    def __init__(self, rom=ROM, sym=SYM):
        self.pb = PyBoy(rom, window="null", cgb=True)
        self.pb.set_emulation_speed(0)
        self.sym = {}
        for l in open(sym):
            p = l.split(";")[0].split()
            if len(p) == 2 and ":" in p[0]:
                b, a = p[0].split(":")
                self.sym[p[1]] = (int(b, 16), int(a, 16))

    def load(self, state, settle=4):
        with open(state, "rb") as f:
            self.pb.load_state(f)
        self.tick(settle)

    def snapshot(self):
        b = io.BytesIO(); self.pb.save_state(b); return b.getvalue()

    def restore(self, snap, settle=2):
        self.pb.load_state(io.BytesIO(snap)); self.tick(settle)

    def tick(self, n=1):
        for _ in range(n):
            self.pb.tick()

    def tap(self, btn, hold=4, wait=8):
        self.pb.button_press(btn); self.tick(hold)
        self.pb.button_release(btn); self.tick(wait)

    # memory ----------------------------------------------------------------
    def rb(self, a): return self.pb.memory[a]
    def wb(self, a, v): self.pb.memory[a] = v & 0xFF
    def rd(self, a, n): return bytes(self.pb.memory[a:a + n])
    def party(self):
        n = self.rb(0xDCD7)
        return [self.rb(0xDCD8 + i) for i in range(n)]

    def set_char(self, cid):
        """cid: 0-based character id, or None for Character Mode off."""
        v = 0 if cid is None else cid + 1
        self.wb(WCHAR, v)
        self.wb(WCHAR + 1, v ^ 0xA5)      # validity pair read by CM_GetChar

    def sram(self, bank=0):
        """Real SRAM bytes. Opens then re-closes the MBC latch."""
        m = self.pb.memory
        m[0x0000] = 0x0A
        m[0x4000] = bank
        self.tick(1)
        data = bytes(m[0xA000:0xC000])
        m[0x0000] = 0x00
        return data

    # calls -----------------------------------------------------------------
    def call(self, target, frames=900, buttons=(), script=(), probe=None, **regs):
        """Run `target` (symbol name or (bank, addr)) until it returns.
        regs: a,b,c,d,e,h,l (8-bit), f. Returns a dict of the registers after."""
        bank, addr = self.sym[target] if isinstance(target, str) else target
        m, rf = self.pb.memory, self.pb.register_file
        park = self.sym["CMTestPark"][1]
        enter = self.sym["CMTestEnter"][1]
        if bank:
            m[0x2000] = bank
            m[0xFF9D] = bank
        # Push the park address onto the game's REAL stack region. The engine's ISR demands SP in
        # $C0xx with the $C000/$C001 = 00 FE canary intact, and its crash handler walks frames.
        # Use a FIXED depth: after tick() the CPU is usually inside the VBlank ISR, so `rf.SP - 2`
        # would leak the ISR's frame on every call and walk SP down through the canary.
        sp = 0xC0E0
        m[sp] = park & 0xFF
        m[sp + 1] = park >> 8
        rf.SP = sp
        for k, v in regs.items():
            setattr(rf, k.upper(), v & 0xFF)
        rf.HL = addr
        rf.PC = enter
        if not hasattr(self, "_park_state"):
            self._park_state = {}

            def parked(ctx=None):
                st = self._park_state
                if st.get("armed") and "regs" not in st:
                    st["regs"] = {r: getattr(self.pb.register_file, r) for r in "A F B C D E HL SP".split()}
            # A hook, not a PC poll: the game's own ISR/main loop may run on after the routine
            # returns, so frame-end PC samples can miss the moment it parked. Registered ONCE.
            self.pb.hook_register(0, park, parked, None)
        state = self._park_state
        state.clear()
        state["armed"] = True
        bi = 0
        held = {}
        try:
            for f in range(frames):
                for (sf, sb, sh) in script:            # scripted presses: (frame, button, hold_frames)
                    if f == sf:
                        self.pb.button_press(sb)
                        held[sb] = f + sh
                for b_, until in list(held.items()):
                    if f >= until:
                        self.pb.button_release(b_)
                        del held[b_]
                if probe is not None:
                    probe(f)
                if buttons and f % 20 == 5:
                    self.pb.button_press(buttons[bi % len(buttons)])
                if buttons and f % 20 == 9:
                    self.pb.button_release(buttons[bi % len(buttons)]); bi += 1
                self.pb.tick()
                if "regs" in state:
                    break
            else:
                raise TimeoutError(f"{target} did not return in {frames} frames (PC={rf.PC:04X})")
        finally:
            state["armed"] = False
            for b in set(buttons) | set(held):
                self.pb.button_release(b)
        return state["regs"]

    def stop(self):
        self.pb.stop(save=False)


# ---- ground truth from the generated data (independent of the ROM bytes) ----
def _rosters():
    import re
    rows, cur = [], None
    for line in open("tools/character_mode/rosters.asm"):
        if re.match(r"^; +\d+:", line):
            cur = []
            rows.append(cur)
        elif cur is not None and line.strip().startswith("db "):
            cur += [int(x, 16) for x in re.findall(r"\$([0-9A-Fa-f]{2})", line)]
    return rows


_R = None


def roster_has(cid, sp):
    global _R
    if _R is None:
        _R = _rosters()
    return bool(_R[cid][sp >> 3] >> (sp & 7) & 1)


def char_info():
    """id -> dict(name, selectable, starter) from selectable.tsv"""
    out = {}
    for l in open("tools/character_mode/selectable.tsv").read().splitlines()[1:]:
        p = l.split("\t")
        out[int(p[0])] = dict(name=p[1], selectable=p[5] == "1", starter=int(p[6]))
    return out


def species_names():
    names = {}
    for line in open("tools/character_mode/prism_species_table.tsv"):
        if line.startswith("#") or not line.strip():
            continue
        i, nm = line.rstrip("\n").split("\t")[:2]
        names[int(i)] = nm
    return names
