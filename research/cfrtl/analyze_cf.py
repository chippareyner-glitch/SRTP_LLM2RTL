"""Analyse a graded CF pilot run (no API).

Reports per variant / per delta category:
  base pass, CF pass, exact reversion, other failure,
  the go/no-go gate from DIRECTIONS_V2.md,
  RQ2: is reversion shared across samples (would behavioural majority vote miss it?),
  and a bootstrap CI for the mean (base - CF) pass-rate drop.

Usage: python -I analyze_cf.py out_cf/<run>
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    run = Path(sys.argv[1])
    rows = [json.loads(l) for l in (run / "graded.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    meta = {d.name: json.loads((d / "meta.json").read_text(encoding="utf-8"))
            for d in (HERE / "variants").iterdir()}
    base = defaultdict(list)
    cf = defaultdict(list)
    for r in rows:
        (base if r["kind"] == "base" else cf)[r["id"]].append(r)
    base_rate = {b: sum(x["grade"]["pass"] for x in v) / len(v) for b, v in base.items()}
    table, drops = [], []
    for vid, v in sorted(cf.items()):
        n = len(v)
        p = sum(x["grade"]["pass"] for x in v)
        rv = sum(x["grade"]["reverted"] for x in v)
        other = n - p - rv
        b = base_rate.get(meta[vid]["base"])
        # behavioural majority (approximation): pass-cluster vs reverted-cluster; "other" failures are
        # counted as one cluster, which is generous to voting
        maj_ok = p > max(rv, other)
        table.append({"id": vid, "cat": meta[vid]["category"], "n": n, "base": b, "pass": p / n,
                      "rev": rv / n, "other": other / n, "maj_ok": maj_ok,
                      "all_fail_reverted": p == 0 and rv == n})
        if b is not None:
            drops.append(b - p / n)
    print(f"{'variant':<44}{'cat':<6}{'base':>6}{'cf':>6}{'rev':>6}{'oth':>6}  majority-ok")
    for t in table:
        print(f"{t['id']:<44}{t['cat']:<6}{t['base']:>6.2f}{t['pass']:>6.2f}{t['rev']:>6.2f}{t['other']:>6.2f}  "
              f"{t['maj_ok']}")
    by = defaultdict(list)
    for t in table:
        by[t["cat"]].append(t)
    print("\nby category:")
    for c, ts in by.items():
        print(f"  {c:<6} n={len(ts):<3} base={sum(t['base'] for t in ts) / len(ts):.2f} "
              f"cf={sum(t['pass'] for t in ts) / len(ts):.2f} rev={sum(t['rev'] for t in ts) / len(ts):.2f}")
    fails = sum(t["n"] * (1 - t["pass"]) for t in table)
    revs = sum(t["n"] * t["rev"] for t in table)
    big_drop = [t["id"] for t in table if t["base"] is not None and t["base"] - t["pass"] >= 0.10]
    print(f"\nmean base pass {sum(t['base'] for t in table) / len(table):.3f}  "
          f"mean CF pass {sum(t['pass'] for t in table) / len(table):.3f}")
    print(f"CF failures: {fails:.0f}; exact reversions: {revs:.0f} ({revs / max(fails, 1):.0%})")
    print(f"variants with >=10pt drop: {len(big_drop)} {big_drop}")
    rng = random.Random(0)
    boots = sorted(sum(rng.choice(drops) for _ in drops) / len(drops) for _ in range(5000))
    print(f"mean drop {sum(drops) / len(drops):.3f}  95% bootstrap CI [{boots[125]:.3f}, {boots[4875]:.3f}]")
    gate = len(big_drop) >= 4 or revs / max(fails, 1) >= 0.30
    print(f"GATE (>=4 variants with >=10pt drop OR >=30% of failures are reversions): "
          f"{'GO' if gate else 'NO-GO'}")
    print(f"RQ2: variants where majority vote picks the wrong behaviour: "
          f"{[t['id'] for t in table if not t['maj_ok']]}")
    print(f"     variants where every sample reverted: {[t['id'] for t in table if t['all_fail_reverted']]}")
    (run / "analysis.json").write_text(json.dumps(table, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
