#!/usr/bin/env python3
"""Determinism control for ab_regression: run the SAME rom twice from the same
state with the same inputs and see whether it diverges from itself. If stock
vs stock also diverges, the divergence is emulator/RTC nondeterminism (Prism is
MBC3 + real-time clock), not the Character Mode patch."""
import argparse
import hashlib
from pyboy import PyBoy

BUTTONS = ["a", "b", "up", "down", "left", "right", "start", "select"]


def input_plan(steps, seed):
    x = seed & 0xFFFFFFFF
    out = []
    for _ in range(steps):
        x = (1103515245 * x + 12345) & 0xFFFFFFFF
        out.append(BUTTONS[(x >> 16) % len(BUTTONS)])
    return out


def run(rom, state, plan):
    pb = PyBoy(rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    with open(state, "rb") as f:
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
        sigs.append(hashlib.md5(pb.screen.image.tobytes()
                                + bytes(pb.memory[0xC000:0xE000])).hexdigest())
    pb.stop(save=False)
    return sigs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    plan = input_plan(a.steps, a.seed)
    r1 = run(a.rom, a.state, plan)
    r2 = run(a.rom, a.state, plan)
    div = next((i for i, (x, y) in enumerate(zip(r1, r2)) if x != y), None)
    if div is None:
        print(f"SELF-DETERMINISTIC across {len(plan)} steps ({a.rom})")
    else:
        print(f"SELF-DIVERGES at step {div} (input {plan[div]!r}) — "
              f"emulator/RTC nondeterminism, not the patch ({a.rom})")


if __name__ == "__main__":
    main()
