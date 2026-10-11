"""Aggregate out_phase1/*.json into the Phase 1 gate metrics (writes out_phase1/summary.json)."""
from __future__ import annotations

import json
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(HERE))
from paths import P1, case_files  # noqa: E402

CATS = json.loads((HERE.parents[1] / "case_categories.json").read_text(encoding="utf-8"))


def coarse(c: str) -> str:
    return "fsm" if c.startswith("fsm") else ("combinational" if c.startswith("combinational")
                                              else ("blackbox" if c.startswith("blackbox") else "sequential"))


def main() -> None:
    rows = [json.loads(f.read_text(encoding="utf-8")) for f in case_files(P1)]
    status = Counter(r.get("status") for r in rows)
    ok = [r for r in rows if r.get("status") == "ok"]
    ci_p = sum(r["ci_pairs"] for r in ok)
    ci_f = sum(r["ci_found"] for r in ok)
    off_p = sum(r["off_pairs"] for r in ok)
    off_f = sum(r["off_found"] for r in ok)
    prob_ci = [r for r in ok if r["ci_pairs"]]
    prob_sep = [r for r in prob_ci if r["ci_found"] == r["ci_pairs"]]
    mins = [m for r in ok for m in r.get("minimised", []) if m.get("ok")]
    long_h = [m for m in mins if m.get("long_horizon")]
    hi_ph = [m for m in mins if m.get("hi_phase")]
    mins = [m for m in mins if not m.get("long_horizon") and not m.get("hi_phase")]
    ci_mins = [m for m in mins if m["correct"][0] != m["correct"][1]]
    by_cat = defaultdict(lambda: [0, 0])
    for r in prob_ci:
        k = coarse(CATS.get(r["case"], "?"))
        by_cat[k][0] += r["ci_found"] == r["ci_pairs"]
        by_cat[k][1] += 1
    seq_lens = [m["min_len"] for m in ci_mins]
    summary = {
        "status": dict(status),
        "pair_recall_correct_vs_incorrect": f"{ci_f}/{ci_p} = {ci_f / max(ci_p, 1):.3f}",
        "problems_fully_separated": f"{len(prob_sep)}/{len(prob_ci)}",
        "separated_by_category": {k: f"{a}/{b}" for k, (a, b) in by_cat.items()},
        "missed_problems": {r["case"]: r["ci_missed"] for r in prob_ci if r["ci_found"] < r["ci_pairs"]},
        "official_pair_recall": f"{off_f}/{off_p} = {off_f / max(off_p, 1):.3f}",
        "extra_splits(total, x-involved)": [sum(r["extra_splits"] for r in ok), sum(r["extra_x"] for r in ok)],
        "impure_clusters": sum(r["impure_clusters"] for r in ok),
        "minimised_pairs": len(mins),
        "long_horizon_pairs(windowed)": {f"{m['pair']}": m["min_len"] for m in long_h},
        "clock_high_only_pairs": len(hi_ph),
        "ci_trace_len(orig_median, min_median, min_max)": [
            st.median(m["orig_len"] for m in ci_mins) if ci_mins else None,
            st.median(seq_lens) if seq_lens else None, max(seq_lens) if seq_lens else None],
        "ci_trace_len_hist": dict(sorted(Counter(seq_lens).items())),
        "ci_toggles_median": st.median(m["toggles"] for m in ci_mins) if ci_mins else None,
        "sim_calls_median": st.median(m["calls"] for m in mins) if mins else None,
    }
    (P1 / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    for k, v in summary.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
