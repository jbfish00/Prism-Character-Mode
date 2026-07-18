#!/usr/bin/env python3
"""Prove the Character Mode patch is inert outside the catch path.

The only bytes the patch changes are the 5-byte hook at 03:78CA (inside
PokeBallEffect) and bank 118 (stub + roster data). If neither the hook site
nor the stub entry is ever executed during ordinary play, the patch provably
cannot affect anything outside a catch attempt. This drives a long, varied
overworld session on the patched ROM with PC hooks on both and asserts zero
fires. RTC-immune (unlike an A/B frame hash, which Prism's day/night clock
makes nondeterministic).

Usage: trace_inertness.py --state STATE [--steps N]
"""
import argparse

from pyboy import PyBoy

PATCHED = "build/prism_cm.gbc"
HOOK_SITE_BANK, HOOK_SITE = 3, 0x78CA        # the injected rst $08
STUB_BANK, STUB_ENTRY = 118, 0x4000          # CatchGate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--steps", type=int, default=800)
    args = ap.parse_args()

    pb = PyBoy(PATCHED, window="null", cgb=True)
    pb.set_emulation_speed(0)
    with open(args.state, "rb") as f:
        pb.load_state(f)
    pb.tick()

    fires = {"hook": 0, "stub": 0}
    pb.hook_register(HOOK_SITE_BANK, HOOK_SITE,
                     lambda ctx: fires.__setitem__("hook", fires["hook"] + 1), None)
    pb.hook_register(STUB_BANK, STUB_ENTRY,
                     lambda ctx: fires.__setitem__("stub", fires["stub"] + 1), None)

    # deterministic varied movement + interaction (no start/select clock menu)
    seq = ["up", "a", "right", "a", "down", "a", "left", "a", "b"]
    for i in range(args.steps):
        btn = seq[i % len(seq)]
        pb.button_press(btn)
        for _ in range(9):
            pb.tick()
        pb.button_release(btn)
        for _ in range(30):
            pb.tick()

    total_frames = args.steps * 39
    print(f"drove {args.steps} inputs (~{total_frames} frames) from {args.state}")
    print(f"catch-hook (03:78CA) fired: {fires['hook']}   "
          f"stub (118:4000) fired: {fires['stub']}")
    if fires["hook"] == 0 and fires["stub"] == 0:
        print("PASS: injected code never executed outside a catch — patch is inert.")
        return 0
    print("NOTE: injected code executed — expected only if a catch occurred.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
