"""Sample-matched control for IDS (no API): is the pass@any gain just "more samples"?

Base pools have 5 samples per problem; IDS adds up to 4 interpretation-specific designs.
Comparing base(5) with base(5)+IDS(4) mixes two effects. Here the pool size is held fixed:
  - n=4: unbiased base pass@4 vs. the 4 IDS designs alone;
  - n=5: base pass@5 vs. k random base samples swapped for IDS designs (expected over subsets).
Problems whose base pool has fewer than 5 samples (API failures) are excluded, since IDS
would otherwise get credit for filling missing data.

Usage: python -I -X utf8 ids_matched.py ve_ds41_ids rtllm_ds41_ids cvdp_ds41_ids
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from math import comb
from pathlib import Path

POOLS = Path(__file__).resolve().parent.parent / "pools"


def load(pool: Path) -> dict:
    out = {}
    for f in (pool / "out").glob("*.json"):
        r = json.loads(f.read_text(encoding="utf-8"))
        base, ids = [], []
        for c in r.get("candidates", []):
            for s in c["sources"]:
                (ids if s.startswith("ids:") else base).append(bool(c.get("correct")))
        out[f.stem] = (base, ids)
    return out


def p_any(flags: list, k: int) -> float:
    """unbiased pass@k from n samples with c correct"""
    n, c = len(flags), sum(flags)
    return 1.0 - comb(n - c, k) / comb(n, k)


def mix_any(base: list, ids: list, kb: int, ki: int) -> float:
    """expected pass@any of kb random base samples plus ki random IDS designs"""
    hits = total = 0
    for bs in combinations(range(len(base)), kb):
        for js in combinations(range(len(ids)), ki):
            hits += any(base[i] for i in bs) or any(ids[j] for j in js)
            total += 1
    return hits / total


def main() -> None:
    for name in sys.argv[1:]:
        d = load(POOLS / name)
        full = {c: v for c, v in d.items() if len(v[0]) == 5}
        four = {c: v for c, v in full.items() if len(v[1]) >= 4}
        print(f"\n{name}: {len(d)} problems, {len(full)} with 5 base samples, {len(four)} also with >=4 IDS designs")
        if four:
            n = len(four)
            for label, fn in (("base pass@1", lambda b, i: p_any(b, 1)),
                              ("IDS pass@1", lambda b, i: mix_any(b, i, 0, 1)),
                              ("base pass@4", lambda b, i: p_any(b, 4)),
                              ("IDS only, 4", lambda b, i: mix_any(b, i, 0, 4)),
                              ("base pass@5", lambda b, i: p_any(b, 5)),
                              ("4 base + 1 IDS", lambda b, i: mix_any(b, i, 4, 1)),
                              ("3 base + 2 IDS", lambda b, i: mix_any(b, i, 3, 2)),
                              ("1 base + 4 IDS", lambda b, i: mix_any(b, i, 1, 4)),
                              ("5 base + 4 IDS (unmatched)", lambda b, i: mix_any(b, i, 5, 4))):
                print(f"  {label:<28} {100 * sum(fn(*v) for v in four.values()) / n:6.1f}%")
        b5 = sum(p_any(b, 5) for b, _ in full.values())
        sw = sum(mix_any(b, i, 5 - min(len(i), 4), min(len(i), 4)) for b, i in full.values())
        un = sum(any(b) or any(i) for b, i in full.values())
        print(f"  all {len(full)} problems, solved: base n=5 {b5:.1f} | IDS swapped in, n=5 {sw:.1f} | "
              f"base + IDS, unmatched {un}")


if __name__ == "__main__":
    main()
