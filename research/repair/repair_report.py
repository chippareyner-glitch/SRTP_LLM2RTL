"""Per-task view of a repair run: before (AskRTL selection) vs after (repair pipeline).

Pipeline "repair+filter": pool = repaired designs that satisfy every constraint; pick the largest
behaviour group by official-test outcome proxy is not allowed (no reference), so we report
  any_ok   - some constraint-consistent repaired design is correct (oracle over the filtered set)
  frac_ok  - fraction of constraint-consistent repaired designs that are correct
             (= expected accuracy of picking one filtered design at random)
Usage: python -I repair_report.py <out_tag> <askrtl per_task.json>
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    rows = json.loads((HERE.parent / "pools" / sys.argv[1] / "check.json").read_text(encoding="utf-8"))
    per = {x["case"]: x for x in json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))}
    by = defaultdict(list)
    for r in rows:
        by[r["case"]].append(r)
    tot_before = tot_after = 0.0
    print(f"{'task':40s} before_any askrtl | n  cons  ok  cons&ok  rand_pick")
    for case, rs in sorted(by.items()):
        cons = [r for r in rs if r["constraints_ok"]]
        ok = sum(r["correct"] for r in rs)
        cok = sum(r["correct"] for r in cons)
        rand = cok / len(cons) if cons else 0.0
        ask = per.get(case, {}).get("askrtl", float("nan"))
        tot_before += ask
        tot_after += rand
        print(f"{case:40s} {str(rs[0]['before_any']):10s} {ask:5.2f} | {len(rs):2d} {len(cons):4d} {ok:3d} {cok:7d}  {rand:5.2f}")
    print(f"sum over {len(by)} tasks: AskRTL selection {tot_before:.2f}  vs random constraint-consistent repair {tot_after:.2f}")


if __name__ == "__main__":
    main()
