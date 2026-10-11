"""Evaluate interpretation-diverse sampling (IDS) as a specification-defect detector (no API).

Detectors (per problem):
  text       - the ambiguity listing returned >= 1 item
  text_high  - the listing returned >= 1 'high' severity item
  base_div   - the original 5-sample pool already diverges (Phase 1 >= 2 clusters)
  ids_beh    - some IDS design behaves differently from the base pool's main behaviour
               (the reading changes observable outputs after reset)
  combined   - base_div OR ids_beh
Ground truth:
  independent - RTL-BenchMT per-case list (restricted to problems present locally)
  all         - independent U defects verified in this project (spec contradictions, testbench bugs)
Also reports pass@any gained by adding IDS designs.

Usage: python -I -X utf8 ids_eval.py --bench verilogeval --base ve_ds41 --ids ve_ds41_ids
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
sys.path.insert(0, str(RESEARCH))
sys.path.insert(0, str(RESEARCH / "askrtl"))
from bench import Bench  # noqa: E402
from defects import OURS, RTLBENCHMT  # noqa: E402

VERIFIED_NEW = {"verilogeval": {"Prob135_m2014_q6b"},
                "rtllm": {"fixed_point_adder", "fixed_point_substractor", "alu"}}


def load(d: Path) -> dict:
    return {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in d.glob("*.json")
            if f.stem not in ("summary", "divtypes", "policy_sim")}


def prf(flag: set, gt: set, universe: set) -> str:
    tp = len(flag & gt)
    p = tp / len(flag) if flag else 0.0
    r = tp / len(gt) if gt else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return f"flagged {len(flag):>3}/{len(universe):<3} P={p:.2f} R={r:.2f} F1={f:.2f} (TP={tp})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--ids", required=True)
    a = ap.parse_args()
    b = Bench(a.bench)
    cases = set(b.cases())
    pools = RESEARCH / "pools"
    lists = {c: json.loads((pools / a.ids / "ambiguities" / f"{c}.json").read_text(encoding="utf-8"))
             for c in cases if (pools / a.ids / "ambiguities" / f"{c}.json").exists()}
    p1_base = load(RESEARCH / "askrtl" / f"out_phase1_{a.base}")
    p1_ids = load(RESEARCH / "askrtl" / f"out_phase1_{a.ids}")
    pool_base = load(pools / a.base / "out")
    pool_ids = load(pools / a.ids / "out")

    def n_clusters(p1: dict, c: str) -> int:
        r = p1.get(c, {})
        return len(r.get("clusters", [])) if r.get("status") == "ok" else 1

    text = {c for c, l in lists.items() if l.get("ambiguities")}
    text_high = {c for c, l in lists.items() if any(x.get("severity") == "high" for x in l.get("ambiguities", []))}
    base_div = {c for c in cases if n_clusters(p1_base, c) >= 2}
    ids_beh = set()
    for c in cases:
        r, pool = p1_ids.get(c, {}), pool_ids.get(c)
        if r.get("status") != "ok" or not pool or len(r.get("clusters", [])) < 2:
            continue
        src = {x["id"]: x["sources"] for x in pool["candidates"]}
        base_votes = [sum(1 for m in cl for s in src[m] if not s.startswith("ids:")) for cl in r["clusters"]]
        main = max(range(len(base_votes)), key=lambda i: base_votes[i])
        # an IDS design outside the base pool's main behaviour = the reading changes observable outputs
        if any(any(s.startswith("ids:") for m in cl for s in src[m]) for i, cl in enumerate(r["clusters"]) if i != main):
            ids_beh.add(c)
    combined = base_div | ids_beh
    judged = set()
    jdir = RESEARCH / "askrtl" / f"out_judge_{a.ids}" / "online"
    if jdir.exists():
        from defects import flag_problems  # noqa: E402
        judged = set(flag_problems([str(jdir)])) & cases
    gt_ind = RTLBENCHMT[b.name] & cases
    gt_all = gt_ind | (OURS[b.name] & cases) | (VERIFIED_NEW.get(b.name, set()) & cases)
    print(f"{b.name}: {len(cases)} problems | ground truth independent={len(gt_ind)} all={len(gt_all)}")
    for name, flag in (("text listing (any)", text), ("text listing (high)", text_high),
                       ("base divergence", base_div), ("IDS behavioural", ids_beh), ("combined", combined),
                       ("IDS + judge filter", judged)):
        print(f"  {name:<22} indep: {prf(flag, gt_ind, cases)}   all: {prf(flag, gt_all, cases)}")
    new_unan = sorted(ids_beh - base_div)
    print(f"  IDS-only detections (base pool unanimous): {len(new_unan)}; of which in ground truth: "
          f"{sorted(set(new_unan) & gt_all)}")
    print(f"  ground-truth problems still missed by combined: {sorted(gt_all - combined)}")

    def anyc(pool: dict) -> set:
        return {c for c, r in pool.items() if any(x.get("correct") for x in r.get("candidates", []))}
    gained = sorted(anyc(pool_ids) - anyc(pool_base))
    print(f"  pass@any: base {len(anyc(pool_base))}/{len(cases)} -> with IDS {len(anyc(pool_ids))}/{len(cases)}; "
          f"problems gaining a correct candidate: {gained}")


if __name__ == "__main__":
    main()
