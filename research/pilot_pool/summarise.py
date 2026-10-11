"""Summarise pool_analysis.py outputs into headroom numbers (writes out/summary.json + prints a table)."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CATS = json.loads((HERE.parents[1] / "case_categories.json").read_text(encoding="utf-8"))


def coarse(cat: str) -> str:
    if cat.startswith("fsm"):
        return "fsm"
    if cat.startswith("sequential") or cat.startswith("special"):
        return "sequential/other"
    if cat.startswith("combinational"):
        return "combinational"
    return "blackbox"


def classify(r: dict) -> str:
    cl = r["clusters"]
    if not cl:
        return "no_compiling_candidate"
    has_correct = any(c["correct"] for c in cl)
    top = cl[0]
    tie = len(cl) > 1 and cl[1]["votes"] == top["votes"]
    if not has_correct:
        return "unanimous_wrong" if len(cl) == 1 else "no_correct_divergent"
    if len(cl) == 1:
        return "unanimous_correct"
    if top["correct"] and not tie:
        return "majority_correct_divergent"
    return "correct_but_not_majority"  # minority or tied: selection by votes is unreliable


def main() -> None:
    rows = []
    src_acc = defaultdict(list)
    for f in sorted((HERE / "out").glob("Prob*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if "error" in r:
            rows.append({"case": r["case"], "cls": "analysis_error"})
            continue
        cands = r["candidates"]
        votes = sum(len(c["sources"]) for c in cands)
        correct_votes = sum(len(c["sources"]) for c in cands if c["correct"])
        single = next((c["correct"] for c in cands if "deepseek_full" in c["sources"]), None)
        rows.append({
            "case": r["case"], "cat": coarse(CATS.get(r["case"], "?")), "cls": classify(r),
            "n_samples": votes, "n_clusters": len(r["clusters"]),
            "sample_acc": correct_votes / votes if votes else 0.0,
            "v4pro_single": single,
            "compile_fail_samples": sum(len(c["sources"]) for c in cands if not c["compiles"]),
        })
        # don't-care-aware view: clusters that all pass the reference differ only where the
        # reference is X, so merge them before asking whether voting would pick a correct one
        good = sum(c["votes"] for c in r["clusters"] if c["correct"])
        worst_bad = max((c["votes"] for c in r["clusters"] if not c["correct"]), default=0)
        rows[-1]["dc_vote_ok"] = good > worst_bad
        for c in cands:
            for s in c["sources"]:
                key = s.split(":")[0] + (":" + s.split(":")[1].split("_", 2)[-1] if ":" in s else "")
                src_acc[key].append(c["correct"])
    ok = [x for x in rows if x["cls"] != "analysis_error"]
    n = len(ok)
    cls = Counter(x["cls"] for x in ok)
    sel_majority = sum(x["cls"] in ("unanimous_correct", "majority_correct_divergent") for x in ok)
    coverage = sum(x["cls"] in ("unanimous_correct", "majority_correct_divergent",
                                "correct_but_not_majority") for x in ok)
    v4 = [x["v4pro_single"] for x in ok if x["v4pro_single"] is not None]
    # queries a perfect oracle needs to isolate the correct cluster by binary splits
    q = [math.ceil(math.log2(x["n_clusters"])) for x in ok
         if x["cls"] in ("majority_correct_divergent", "correct_but_not_majority")]
    by_cat = defaultdict(Counter)
    for x in ok:
        by_cat[x["cat"]][x["cls"]] += 1
    summary = {
        "problems": n, "errors": len(rows) - n,
        "mean_samples_per_problem": sum(x["n_samples"] for x in ok) / n,
        "mean_sample_accuracy(pass@1 estimate)": sum(x["sample_acc"] for x in ok) / n,
        "v4pro_single_shot_acc": sum(v4) / len(v4) if v4 else None,
        "majority_vote_acc(oracle-stimulus upper bound)": sel_majority / n,
        "majority_vote_acc_dontcare_merged": sum(x.get("dc_vote_ok", False) for x in ok) / n,
        "pool_coverage(pass@any)": coverage / n,
        "per_source_acc": {k: round(sum(v) / len(v), 3) for k, v in sorted(src_acc.items())},
        "dc_vote_fail_but_covered": [x["case"] for x in ok if not x.get("dc_vote_ok") and
                                     x["cls"] not in ("unanimous_wrong", "no_correct_divergent",
                                                      "no_compiling_candidate")],
        "classes": dict(cls),
        "perfect_oracle_queries_hist": dict(Counter(q)),
        "by_category": {k: dict(v) for k, v in by_cat.items()},
        "cases": {c: [x["case"] for x in ok if x["cls"] == c] for c in cls},
    }
    (HERE / "out" / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for k, v in summary.items():
        if k != "cases":
            print(f"{k}: {v}")
    for c in ("correct_but_not_majority", "unanimous_wrong", "no_correct_divergent"):
        print(c, summary["cases"].get(c, []))


if __name__ == "__main__":
    main()
