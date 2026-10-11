"""H2: minimal-trace questions vs long-trace comparison, on a common footing (no API).

Common metric: for every question whose pair separates a CORRECT cluster from an INCORRECT
one (correctness from the pilot pool), does the judge's answer point to the correct cluster?
  right    - answer selects the correct cluster's option / trace
  wrong    - answer selects the incorrect cluster's option / trace
  abstain  - ANY / NONE / UNCLEAR / parse or API error (no direction)

Usage: python -I h2_compare.py out_judge/<min_run> out_judge/<long_run>
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
QDIR = HERE / "out_queries"


def load(run: str) -> list[dict]:
    return [json.loads(l) for l in (Path(run) / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]


def decide(r: dict, q: dict, good: dict, variant: str) -> str | None:
    a, b = q["pair"]
    if good[a] == good[b]:
        return None  # not a correct-vs-incorrect question
    correct, wrong = (a, b) if good[a] else (b, a)
    ans = r["answer"]
    if variant == "long":
        pick = {"A": a, "B": b}.get(ans)
    else:
        opts = q["cluster_option"]
        pick = correct if opts.get(correct) == ans else (wrong if opts.get(wrong) == ans else None)
        if pick is None and len(ans) == 1 and ans.isalpha():
            return "wrong"  # chose a third option that neither member of the pair produced
    if pick is None:
        return "abstain"
    return "right" if pick == correct else "wrong"


def main() -> None:
    out = {}
    for variant, run in (("min", sys.argv[1]), ("long", sys.argv[2])):
        res = load(run)
        c = Counter()
        lens = Counter()
        for r in res:
            d = json.loads((QDIR / f"{r['case']}.json").read_text(encoding="utf-8"))
            q = d["queries"][r["qi"]]
            good = {cl["rep"]: all(cl["correct"]) for cl in d["clusters"]}
            v = decide(r, q, good, variant)
            if v:
                c[v] += 1
                lens[v] += (q["long"]["cycles"] if variant == "long" else q["len"])
        n = sum(c.values())
        out[variant] = c
        dec = c["right"] + c["wrong"]
        print(f"{variant:<5} correct-vs-incorrect questions={n}  right={c['right']}  wrong={c['wrong']}  "
              f"abstain={c['abstain']}  | decision acc={c['right'] / max(dec, 1):.3f}  "
              f"overall right={c['right'] / max(n, 1):.3f}")
        print(f"      raw label accuracy={sum(r['correct'] for r in res) / max(len(res), 1):.3f} over {len(res)}")


if __name__ == "__main__":
    main()
