"""D: does judge disagreement with the reference detect benchmark defects? (no API)

A problem is FLAGGED when, on at least one of its questions, the judge either
  * picks a single option that contradicts the reference label with confidence >= --conf, or
  * answers ANY / UNCLEAR where the reference has a single required value.
Flags are compared with two errata lists:
  INDEPENDENT - RTL-BenchMT (2605.15537) per-case-analysis folders (fetched 2026-10-09)
  OURS        - defects verified in this project (spec contradicts reference, testbench race, ...)

Usage: python -I -X utf8 defects.py <judge_run_dir> [<judge_run_dir> ...] [--conf 0.9]
       (set ASKRTL_TAG / ASKRTL_BENCH to match the runs)
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import BENCH, QDIR, case_files  # noqa: E402

RTLBENCHMT = {
    "verilogeval": {"Prob148_2013_q2afsm", "Prob034_dff8", "Prob066_edgecapture", "Prob116_m2014_q3",
                    "Prob053_m2014_q4d", "Prob136_m2014_q6", "Prob131_mt2015_q4", "Prob150_review2015_fsmonehot"},
    "rtllm": {"adder_pipe_64bit", "freq_divbyeven", "freq_divbyfrac", "parallel2serial", "serial2parallel"},
}
OURS = {
    "verilogeval": {"Prob062_bugs_mux2", "Prob093_ece241_2014_q3", "Prob149_ece241_2013_q4",  # spec vs reference
                    "Prob099_m2014_q6c", "Prob139_2013_q2bfsm"},  # testbench port bug, testbench race
    "rtllm": set(),
}


def flag_problems(runs: list[str], conf_min: float = 0.9) -> dict[str, list[str]]:
    """Problems whose judge answers contradict the reference (confidently) or call it unconstrained."""
    answers = defaultdict(list)
    for run in runs:
        for name in ("results.jsonl", "online_results.jsonl"):
            f = Path(run) / name
            if f.exists():
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        r = json.loads(line)
                        answers[r["case"]].append(r)
    flagged = {}
    for case, rs in answers.items():
        why = []
        for r in rs:
            lab, ans = r["label"], r["answer"]
            single = not lab.startswith("ANY") and lab not in ("NONE", "UNKNOWN")
            try:
                conf = float(r.get("confidence"))
            except (TypeError, ValueError):
                conf = 0.0
            if single and len(ans) == 1 and ans.isalpha() and ans != lab and conf >= conf_min:
                why.append(f"q{r['qi']}: picks {ans}, reference {lab} (conf {conf:.2f})")
            elif single and ans in ("ANY", "UNCLEAR"):
                why.append(f"q{r['qi']}: says {ans}, reference {lab}")
        if why:
            flagged[case] = why
    return flagged


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--conf", type=float, default=0.9)
    a = ap.parse_args()
    answers = defaultdict(list)
    for run in a.runs:
        for name in ("results.jsonl", "online_results.jsonl"):
            f = Path(run) / name
            if f.exists():
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        r = json.loads(line)
                        answers[r["case"]].append(r)
    queried = {f.stem for f in case_files(QDIR) if json.loads(f.read_text(encoding="utf-8")).get("status") == "ok"}
    flagged = {}
    for case, rs in answers.items():
        why = []
        for r in rs:
            lab, ans, conf = r["label"], r["answer"], r.get("confidence")
            single = not lab.startswith("ANY") and lab != "NONE"
            try:
                conf = float(conf)
            except (TypeError, ValueError):
                conf = 0.0
            if single and len(ans) == 1 and ans.isalpha() and ans != lab and conf >= a.conf:
                why.append(f"q{r['qi']}: picks {ans}, reference {lab} (conf {conf:.2f})")
            elif single and ans in ("ANY", "UNCLEAR"):
                why.append(f"q{r['qi']}: says {ans}, reference {lab}" +
                           (f" - {r.get('spec_gap')}" if r.get("spec_gap") else ""))
        if why:
            flagged[case] = why
    ind = RTLBENCHMT[BENCH.name] & queried
    ours = OURS[BENCH.name] & queried
    known = ind | ours
    print(f"problems with judge questions: {len(queried)}; flagged: {len(flagged)}")
    print(f"independent errata (RTL-BenchMT) among queried problems: {sorted(ind)}")
    hit_ind = sorted(set(flagged) & ind)
    print(f"  recall vs RTL-BenchMT: {len(hit_ind)}/{len(ind)} {hit_ind}")
    print(f"  recall vs our verified errata: {len(set(flagged) & ours)}/{len(ours)}")
    prec = len(set(flagged) & known) / max(len(flagged), 1)
    print(f"  precision vs (RTL-BenchMT U ours): {len(set(flagged) & known)}/{len(flagged)} = {prec:.2f}")
    print("flagged problems:")
    for c in sorted(flagged):
        tag = "RTL-BenchMT" if c in ind else ("ours" if c in ours else "NEW?")
        print(f"  [{tag:<11}] {c}: {flagged[c][0]}" + (f"  (+{len(flagged[c]) - 1} more)" if len(flagged[c]) > 1 else ""))
    print(f"errata problems with NO judge question (unanimous or not divergent): "
          f"{sorted((RTLBENCHMT[BENCH.name] | OURS[BENCH.name]) - queried)}")


if __name__ == "__main__":
    main()
