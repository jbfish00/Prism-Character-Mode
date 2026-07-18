#!/usr/bin/env python3
"""Savestate-BFS auto-explorer for Pokemon Prism.

Breadth-first-searches the current map by snapshotting emulator state at
every newly reached tile and probing all four directions from it. Finds map
exits (map-id/coord-jump transitions) without any knowledge of the map's
layout. Textboxes encountered mid-probe are auto-dismissed with A taps.

RAM addresses (RE'd this project): player X $D4E6, Y $D4E7,
map group/number $DCB5/$DCB6, shadow tilemap base $C4A0 (textbox detect).

Usage:
  explore_bfs.py --load STATE --out-dir DIR [--max-nodes N] [--rom ROM]

Writes:
  DIR/exit_<n>_<mapg>_<mapn>_<x>_<y>.state   state just after each transition
  DIR/report.txt                             visited tiles + transitions found
"""
import argparse
import io
import os
from collections import deque

from pyboy import PyBoy

X_ADDR, Y_ADDR = 0xD4E6, 0xD4E7
MAPG, MAPN = 0xDCB5, 0xDCB6
TILEMAP, COLS = 0xC4A0, 20


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rom", default="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc")
    ap.add_argument("--load", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--max-nodes", type=int, default=400)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    pb = PyBoy(args.rom, window="null", cgb=True)
    pb.set_emulation_speed(0)
    with open(args.load, "rb") as f:
        pb.load_state(f)
    pb.tick()

    def pos():
        return (pb.memory[MAPG], pb.memory[MAPN], pb.memory[X_ADDR], pb.memory[Y_ADDR])

    def textbox_visible():
        base = TILEMAP + 13 * COLS
        raw = bytes(pb.memory[base:base + COLS])
        return any(0x79 <= b <= 0x7E for b in raw)

    def dismiss_text(max_taps=6):
        taps = 0
        while textbox_visible() and taps < max_taps:
            pb.button_press("a")
            for _ in range(12):
                pb.tick()
            pb.button_release("a")
            for _ in range(120):
                pb.tick()
            taps += 1
        return taps

    def snap():
        buf = io.BytesIO()
        pb.save_state(buf)
        return buf.getvalue()

    def restore(state):
        pb.load_state(io.BytesIO(state))
        pb.tick()

    start_map = pos()[:2]
    start = snap()
    visited = {pos()[2:]: True}
    queue = deque([(pos()[2:], start)])
    transitions = []
    report = [f"start map {start_map} at {pos()[2:]}"]
    nodes = 0

    while queue and nodes < args.max_nodes:
        (x, y), state = queue.popleft()
        nodes += 1
        for d, (dx, dy) in (("up", (0, -1)), ("down", (0, 1)),
                            ("left", (-1, 0)), ("right", (1, 0))):
            tgt = (x + dx, y + dy)
            if tgt in visited:
                continue
            restore(state)
            pb.button_press(d)
            for _ in range(20):
                pb.tick()
            pb.button_release(d)
            for _ in range(14):
                pb.tick()
            texted = dismiss_text()
            g, n, nx, ny = pos()
            if (g, n) != start_map or abs(nx - x) + abs(ny - y) > 2:
                # map transition (warp/exit) — save it, don't queue further
                name = f"exit_{len(transitions)}_{g}_{n}_{nx}_{ny}.state"
                with open(os.path.join(args.out_dir, name), "wb") as f:
                    f.write(snap())
                transitions.append((d, (x, y), (g, n, nx, ny), name))
                report.append(f"TRANSITION {d} from {(x,y)} -> map {(g,n)} pos {(nx,ny)} [{name}]")
                continue
            if (nx, ny) == (x, y):
                continue  # blocked
            if (nx, ny) not in visited:
                visited[(nx, ny)] = True
                queue.append(((nx, ny), snap()))
                if texted:
                    report.append(f"text near {(nx,ny)} (approached {d} from {(x,y)})")

    report.append(f"visited {len(visited)} tiles, {len(transitions)} transitions, "
                  f"{nodes} nodes expanded")
    with open(os.path.join(args.out_dir, "report.txt"), "w") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report[-12:]))
    pb.stop(save=False)


if __name__ == "__main__":
    main()
