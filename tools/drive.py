#!/usr/bin/env python3
"""Checkpointed PyBoy driver for Pokemon Prism.

Applies a sequence of inputs starting from a savestate checkpoint, saving
screenshots along the way and a new checkpoint at the end. Designed for
iterative use: inspect the screenshots, decide the next input plan, re-run.

Usage:
  drive.py --load STATE --save STATE --shots DIR --plan "a*5; up; a; wait 120; shot; a*10"

Plan grammar (semicolon-separated):
  a, b, start, select, up, down, left, right   press+release (10 frames hold, 60 wait)
  <btn>*N          repeat N times
  wait N           run N frames
  shot             save screenshot now (numbered)
  hold <btn> N     hold button for N frames then release
"""
import argparse
import os

from pyboy import PyBoy

BUTTONS = {"a", "b", "start", "select", "up", "down", "left", "right"}


def run_plan(pb, plan, shots_dir, prefix):
    shot_n = 0

    def shot():
        nonlocal shot_n
        pb.screen.image.save(os.path.join(shots_dir, f"{prefix}_{shot_n:02d}.png"))
        shot_n += 1

    for step in [s.strip() for s in plan.split(";") if s.strip()]:
        parts = step.split()
        if parts[0] == "wait":
            for _ in range(int(parts[1])):
                pb.tick()
        elif parts[0] == "shot":
            shot()
        elif parts[0] == "hold":
            btn, n = parts[1], int(parts[2])
            pb.button_press(btn)
            for _ in range(n):
                pb.tick()
            pb.button_release(btn)
            for _ in range(30):
                pb.tick()
        else:
            token = parts[0]
            if "*" in token:
                btn, n = token.split("*")
                n = int(n)
            else:
                btn, n = token, 1
            if btn not in BUTTONS:
                raise SystemExit(f"unknown button {btn!r}")
            for _ in range(n):
                pb.button_press(btn)
                for _ in range(10):
                    pb.tick()
                pb.button_release(btn)
                for _ in range(70):
                    pb.tick()
    shot()  # always final screenshot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc")
    ap.add_argument("--load", help="savestate to start from (omit = cold boot)")
    ap.add_argument("--save", required=True, help="savestate to write at end")
    ap.add_argument("--shots", required=True, help="directory for screenshots")
    ap.add_argument("--prefix", default="s", help="screenshot filename prefix")
    ap.add_argument("--plan", required=True)
    args = ap.parse_args()

    os.makedirs(args.shots, exist_ok=True)
    pb = PyBoy(args.rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    if args.load:
        with open(args.load, "rb") as f:
            pb.load_state(f)
        pb.tick()
    run_plan(pb, args.plan, args.shots, args.prefix)
    with open(args.save, "wb") as f:
        pb.save_state(f)
    pb.stop(save=False)
    print("ok")


if __name__ == "__main__":
    main()
