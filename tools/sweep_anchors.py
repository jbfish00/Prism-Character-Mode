#!/usr/bin/env python3
"""Sweep every top-level pokecrystal routine against the Prism ROM with the
operand-masked skeleton matcher (match_code.py) and emit an anchor map TSV:

    donor_label  donor_fileoff  prism_fileoff  matched_chunks/total  fraction

Only routines whose best cluster covers >= --min-frac of chunks are emitted.
This is the global "what survived the relink, and where did it land" map.
"""
import argparse
import re
import sys
sys.path.insert(0, "tools")
import match_code as mc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donor", default="tools/pokecrystal_donor/pokecrystal.gbc")
    ap.add_argument("--sym", default="tools/pokecrystal_donor/pokecrystal.sym")
    ap.add_argument("--target",
                    default="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc")
    ap.add_argument("--out", default="tools/prism_anchor_map.tsv")
    ap.add_argument("--chunk", type=int, default=8)
    ap.add_argument("--min-lit", type=int, default=6)
    ap.add_argument("--min-frac", type=float, default=0.5)
    ap.add_argument("--min-size", type=int, default=24)
    ap.add_argument("--max-size", type=int, default=2000)
    args = ap.parse_args()

    donor = open(args.donor, "rb").read()
    target = open(args.target, "rb").read()
    syms = mc.load_sym(args.sym)
    tops = [(o, n) for o, n in syms if "." not in n]

    rows = []
    swept = 0
    for i, (off, name) in enumerate(tops):
        end = next((o for o, n in tops[i + 1:] if o > off), off)
        size = end - off
        if size < args.min_size or size > args.max_size:
            continue
        code = donor[off:end]
        insn_offs = []
        o = 0
        while o < len(code) and o + mc.ilen(code, o) <= len(code):
            insn_offs.append(o)
            o += mc.ilen(code, o)
        hits = {}
        nch = 0
        stride = 4
        for i0 in range(0, max(1, len(insn_offs) - args.chunk + 1), stride):
            i1 = min(i0 + args.chunk, len(insn_offs))
            pat, nlit = mc.skeleton_regex(code, i0, i1, insn_offs)
            if nlit < args.min_lit:
                continue
            nch += 1
            for m in re.finditer(pat, target, re.DOTALL):
                base = m.start() - insn_offs[i0]
                key = next((k for k in hits if abs(k - base) <= 64), base)
                hits.setdefault(key, set()).add(insn_offs[i0])
        swept += 1
        if swept % 200 == 0:
            print(f"...{swept} routines swept, {len(rows)} anchors so far",
                  flush=True)
        if not nch or not hits:
            continue
        base, cov = max(hits.items(), key=lambda kv: len(kv[1]))
        frac = len(cov) / nch
        if frac < args.min_frac:
            continue
        toff = base  # cluster delta key == target_off - donor_chunk_off ~ start
        rows.append((name, off, toff, len(cov), nch, frac))

    rows.sort(key=lambda r: r[1])
    with open(args.out, "w") as f:
        f.write("donor_label\tdonor_off\tprism_off\tchunks\ttotal\tfrac\n")
        for name, doff, toff, cov, nch, frac in rows:
            f.write(f"{name}\t0x{doff:06X}\t0x{toff:06X}\t{cov}\t{nch}"
                    f"\t{frac:.2f}\n")
    print(f"swept {swept} routines; wrote {len(rows)} anchors to {args.out}")


if __name__ == "__main__":
    main()
