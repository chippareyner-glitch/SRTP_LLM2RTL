"""Judge accuracy on the questions an online run actually asked (no API).

For each asked question: label agreement, and - when the question separates a correct
cluster from an incorrect one - whether the answer pointed to the correct cluster.

Usage: python -I -X utf8 online_stats.py <online_run_dir>   (ASKRTL_TAG / ASKRTL_BENCH as for the run)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import QDIR  # noqa: E402


def main() -> None:
    rows = [json.loads(l) for l in (Path(sys.argv[1]) / "online_results.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()]
    dec = Counter()
    for r in rows:
        d = json.loads((QDIR / f"{r['case']}.json").read_text(encoding="utf-8"))
        q = d["queries"][r["qi"]]
        good = {cl["rep"]: all(cl["correct"]) for cl in d["clusters"]}
        a, b = q["pair"]
        kind = "label-match" if (r["answer"] == r["label"] or (r["label"].startswith("ANY") and r["answer"] == "ANY")) \
            else "label-miss"
        if good[a] != good[b]:
            correct, wrong = (a, b) if good[a] else (b, a)
            opts = q["cluster_option"]
            v = ("right" if opts.get(correct) == r["answer"] else
                 "wrong" if r["answer"] in (opts.get(wrong), *[o for o in "ABCDEFGH" if o != opts.get(correct)])
                 and len(r["answer"]) == 1 else "abstain")
            dec[v] += 1
        print(f"{r['case']:<34} q{r['qi']:<3} label={r['label']:<7} answer={r['answer']:<8} {kind:<12} "
              f"conf={r.get('confidence')}  {(r.get('spec_gap') or '')[:90]}")
    n = len(rows)
    lm = sum(r["answer"] == r["label"] or (r["label"].startswith("ANY") and r["answer"] == "ANY") for r in rows)
    print(f"\nasked {n}; label agreement {lm}/{n}; decisive questions: right={dec['right']} wrong={dec['wrong']} "
          f"abstain={dec['abstain']}")


if __name__ == "__main__":
    main()
