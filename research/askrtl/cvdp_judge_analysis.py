"""Score CVDP judge answers against official test outcomes (no reference RTL, so no trace label).

For each answered question, an option is "pass" if every cluster mapped to it passes the official
cocotb tests, "fail" if every such cluster fails, "mixed" otherwise.  The question is
  informative  - at least one pass option and one fail option,
  all-pass     - every option passes (the tests cannot tell the readings apart),
  all-fail     - every option fails.
On informative questions we report how often the judge picked a pass option.

Usage: python -I cvdp_judge_analysis.py [run_dir]   (env ASKRTL_TAG=cvdp_ds41 ASKRTL_BENCH=cvdp)
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import QDIR  # noqa: E402


def option_status(q: dict, clusters: dict) -> dict[str, str]:
    by_opt = defaultdict(list)
    for rep, letter in q["cluster_option"].items():
        by_opt[letter].extend(clusters[rep])
    out = {}
    for letter, cs in by_opt.items():
        out[letter] = "pass" if all(cs) else ("fail" if not any(cs) else "mixed")
    return out


def main() -> None:
    run = Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "out_judge_cvdp_ds41" / "online")
    rows = [json.loads(l) for l in (run / "online_results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    kinds, verdict = Counter(), Counter()
    conf = defaultdict(list)
    per_case = defaultdict(list)
    detail = []
    for r in rows:
        qf = json.loads((QDIR / f"{r['case']}.json").read_text(encoding="utf-8"))
        clusters = {c["rep"]: c["correct"] for c in qf["clusters"]}
        q = qf["queries"][r["qi"]]
        st = option_status(q, clusters)
        vals = set(st.values())
        kind = ("informative" if "pass" in vals and "fail" in vals else
                "all-pass" if vals == {"pass"} else "all-fail" if vals == {"fail"} else "mixed")
        kinds[kind] += 1
        a = r["answer"]
        if kind == "informative":
            if a in st:
                v = "picked-" + st[a]
            elif a == "ANY":
                v = "ANY"
            else:
                v = a  # NONE / UNCLEAR / errors
            verdict[v] += 1
            conf[v].append(r.get("confidence"))
            per_case[r["case"]].append(v)
        detail.append({"case": r["case"], "qi": r["qi"], "kind": kind, "answer": a, "status": st,
                       "confidence": r.get("confidence"), "spec_gap": r.get("spec_gap")})
    print("question kinds:", dict(kinds))
    print("judge on informative questions:", dict(verdict))
    for v, cs in conf.items():
        print(f"  {v:14s} confidence {Counter(cs).most_common()}")
    print("\nper case (informative only):")
    for c, vs in sorted(per_case.items()):
        print(f"  {c:60s} {vs}")
    (run / "official_analysis.json").write_text(json.dumps(detail, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
