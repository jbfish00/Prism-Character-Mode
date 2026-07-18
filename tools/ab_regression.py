#!/usr/bin/env python3
"""A/B determinism regression: patched build must match the stock ROM exactly
outside the catch path.

The Character Mode patch only touches bank 3 (the 5-byte catch hook) and bank
118 (stub + roster data + dev id byte). Therefore ANY divergence between stock
and patched ROM during ordinary play — where PokeBallEffect never runs — is a
regression. This drives a long, deterministic (seed-derived, no RNG-in-Python)
input sequence on both ROMs from a shared savestate and asserts the full frame
buffer + a wide WRAM window hash identically at every checkpoint.

Usage:
  ab_regression.py --state STATE [--steps N] [--seed S]
"""
import argparse
import hashlib

from pyboy import PyBoy

STOCK = "rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
PATCHED = "build/prism_cm.gbc"
ALL_BUTTONS = ["a", "b", "up", "down", "left", "right", "start", "select"]

# NOTE: Prism is MBC3 + real-time clock. The START menu shows the clock, so
# any input path that opens it makes the frame buffer depend on WALL-CLOCK
# time — stock-vs-stock (and even stock-vs-itself) then "diverges" for reasons
# unrelated to the patch (confirmed via tools/ab_control.py). Exclude
# start/select by default so a reported divergence is a genuine regression.


def input_plan(steps, seed, buttons):
    """Deterministic pseudo-random button plan (LCG, no Python RNG state)."""
    x = seed & 0xFFFFFFFF
    plan = []
    for _ in range(steps):
        x = (1103515245 * x + 12345) & 0xFFFFFFFF
        plan.append(buttons[(x >> 16) % len(buttons)])
    return plan


def run(rom, plan):
    pb = PyBoy(rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    with open(args.state, "rb") as f:
        pb.load_state(f)
    pb.tick()
    sigs = []
    for btn in plan:
        pb.button_press(btn)
        for _ in range(10):
            pb.tick()
        pb.button_release(btn)
        for _ in range(50):
            pb.tick()
        frame = pb.screen.image.tobytes()
        ram = bytes(pb.memory[0xC000:0xE000])       # all of WRAM
        sigs.append(hashlib.md5(frame + ram).hexdigest())
    pb.stop(save=False)
    return sigs


def main():
    buttons = [b for b in ALL_BUTTONS if b not in args.exclude]
    plan = input_plan(args.steps, args.seed, buttons)
    a = run(STOCK, plan)
    b = run(PATCHED, plan)
    first_div = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            first_div = i
            break
    if first_div is None:
        print(f"IDENTICAL across all {len(plan)} steps "
              f"(frame+WRAM hash) — no regression, seed={args.seed}")
        return 0
    print(f"DIVERGENCE at step {first_div} (input {plan[first_div]!r}): "
          f"stock={a[first_div][:8]} patched={b[first_div][:8]}")
    print("  (a divergence outside a catch is a real bug — investigate)")
    return 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--exclude", nargs="*", default=["start", "select"],
                    help="buttons to omit (default: start/select — they open "
                         "the RTC clock menu and cause wall-clock nondeterminism)")
    args = ap.parse_args()
    raise SystemExit(main())
