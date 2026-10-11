"""Start a REAL wild battle in the harness.

The overworld's own encounter path ends in `jp CallScript` with the script at 25:56DC
(randomwildmon / startbattle / reloadmapafterbattle / end).  We reproduce exactly the state
CallScript + StartScript leave behind ($D438 = $FF, script bank/pos at $D439-$D43B, script
mode $D437 = 1) and let the game's own main loop run the script, so everything after that
(battle transition, StartBattle, the real DoBattle) is the shipped engine.
The wild species/level come from $D22E/$D143, the same two bytes the three wild-roll hooks write.
"""
import sys, os
sys.path.insert(0, "tools")
from cmlib import CM

PARTY = 0xDCDF
SHOTS = "/home/jbfish00/.claude/jobs/7bf68530/tmp/"

def make_party(cm, mons):
    """mons: [(species, level, [moves])]  -- hand-built party structs (0x30 bytes each)"""
    cm.wb(0xDCD7, len(mons))
    for i, (s, lv, mv) in enumerate(mons):
        cm.wb(0xDCD8 + i, s)
        o = PARTY + i * 0x30
        for k in range(0x30):
            cm.wb(o + k, 0)
        cm.wb(o, s)
        for k, m in enumerate(mv):
            cm.wb(o + 2 + k, m); cm.wb(o + 23 + k, 25)
        cm.wb(o + 6, 0x12); cm.wb(o + 7, 0x34)
        cm.wb(o + 31, lv)
        for off in (34, 36):
            cm.wb(o + off, 0); cm.wb(o + off + 1, 60)
        for k in range(5):
            cm.wb(o + 38 + k * 2, 0); cm.wb(o + 39 + k * 2, 40)
    cm.wb(0xDCD8 + len(mons), 0xFF)

def give_mon(cm, species, level):
    """Add a mon with the game's OWN TryAddMonToParty (3C:4000), as the gift path does.
    cm.call() leaves the CPU parked in a loop, so run it on a snapshot and copy only the
    resulting party bytes back: the live main loop is untouched and the battle can follow."""
    snap = cm.snapshot()
    for a, v in ((0xD108, species), (0xD143, level), (0xD106, 0), (0xCF5F, 0)):
        cm.wb(a, v)
    cm.call((0x3C, 0x4000), frames=120)
    party = cm.rd(0xDCD7, 0x1A0)
    cm.restore(snap, settle=0)
    for i, v in enumerate(party):
        cm.wb(0xDCD7 + i, v)

def run_script(cm, bank, pos):
    """What CallScript + StartScript leave behind: the main loop then runs the script."""
    for a, v in ((0xD439, bank), (0xD43A, pos & 0xFF), (0xD43B, pos >> 8), (0xD438, 0xFF), (0xD437, 1)):
        cm.wb(a, v)

def start_wild(cm, species, level):
    cm.wb(0xD22E, species); cm.wb(0xD143, level)
    run_script(cm, 0x25, 0x56DC)

def open_start_menu(cm):
    """The START menu is the script at 25:5537 (what the overworld's START check calls)."""
    run_script(cm, 0x25, 0x5537)
    cm.tick(60)

def wait_battle(cm, frames=900):
    for _ in range(frames):
        cm.tick()
        if cm.rb(0xD22D) == 1 and cm.rb(0xD206):
            cm.tick(60)
            return True
    return False

def shot(cm, name):
    cm.pb.screen.image.save(SHOTS + name)

if __name__ == "__main__":
    cm = CM(sys.argv[1] if len(sys.argv) > 1 else "build/prism_cm.gbc")
    cm.load("tools/emu_states/ck9.state")
    cm.wb(0xDCD7, 0); cm.wb(0xDCD8, 0xFF)
    give_mon(cm, 25, 20); print("party", cm.party())
    start_wild(cm, 19, 5)
    print("battle", wait_battle(cm))
    for i in range(6):
        cm.tap("a", 4, 40); shot(cm, f"d{i}.png")
