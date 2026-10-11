#!/usr/bin/env python3
"""Map pokecrystal home-bank (and other fixed-address) routines to Prism addresses.

For each anchored routine (tools/prism_anchor_map.tsv), walk the donor routine
and the Prism routine in lockstep (same opcode skeleton, Prism's rst inline
bytes honoured). Every call/jp/ld-rr operand pair <donor target, prism target>
is a vote that donor symbol -> Prism address. The winner per donor symbol is
reported with its vote count and the runner-up.

Usage: home_vote.py [--max 0x4000]   (writes tools/home_map.tsv)
"""
import re, sys, collections
sys.path.insert(0, "tools")
import match_code as mc

DONOR = "tools/pokecrystal_donor/pokecrystal.gbc"
SYM = "tools/pokecrystal_donor/pokecrystal.sym"
PRISM = "rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
PRISM_RST_INLINE = {0xCF: 3, 0xD7: 1, 0xE7: 1, 0xEF: 2, 0xDF: 0, 0xF7: 0}
CALLS = {0xCD, 0xC3, 0xC4, 0xCC, 0xD4, 0xDC, 0xC2, 0xCA, 0xD2, 0xDA}
LD16 = {0x01, 0x11, 0x21}


def main():
    donor = open(DONOR, "rb").read()
    prism = open(PRISM, "rb").read()
    syms = mc.load_sym(SYM)
    by_off = {}
    for off, name in syms:
        by_off.setdefault(off, name)
    votes = collections.defaultdict(collections.Counter)
    rows = [l.split("\t") for l in open("tools/prism_anchor_map.tsv").read().splitlines()[1:]]
    used = 0
    for lab, doff, poff, ch, tot, frac in rows:
        if float(frac) < 0.95:
            continue
        try:
            start, code = mc.routine_bytes(donor, syms, lab)
        except SystemExit:
            continue
        p = int(poff, 16)
        d = 0
        q = p
        ok = True
        pairs = []
        while d < len(code):
            dop, pop = code[d], prism[q]
            if dop != pop:
                # donor rst has no inline; Prism may differ -> stop trusting
                ok = False
                break
            if dop == 0xCB:
                d += 2; q += 2; continue
            n = mc.ilen(code, d)
            if d + n > len(code):
                break
            if dop in CALLS or dop in LD16:
                dv = code[d+1] | code[d+2] << 8
                pv = prism[q+1] | prism[q+2] << 8
                pairs.append((dv, pv, dop))
            if dop in PRISM_RST_INLINE:
                q += 1 + PRISM_RST_INLINE[dop]; d += 1
                continue
            d += n; q += n
        if not ok and not pairs:
            continue
        used += 1
        for dv, pv, dop in pairs:
            if dv < 0x4000 and pv < 0x4000 and dop in CALLS:
                nm = by_off.get(dv)
                if nm:
                    votes[nm][pv] += 1
    out = []
    for nm, c in sorted(votes.items(), key=lambda kv: min(k for k in [0]) ):
        (a, n), *rest = c.most_common(2) + [(None, 0)] * 0
        r = c.most_common(2)[1] if len(c) > 1 else (None, 0)
        out.append((nm, a, n, r[0], r[1]))
    with open("tools/home_map.tsv", "w") as f:
        f.write("donor_label\tprism_addr\tvotes\trunnerup\trvotes\n")
        for nm, a, n, ra, rn in sorted(out, key=lambda x: x[0]):
            f.write(f"{nm}\t0x{a:04X}\t{n}\t{'' if ra is None else hex(ra)}\t{rn}\n")
    print("routines used", used, "symbols", len(out))


main()
