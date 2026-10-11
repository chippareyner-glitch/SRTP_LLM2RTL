"""CVDP deep-dive (no API): parameter sensitivity, selection failures, timeouts, confounds.

Reads research/cvdp_analysis.json (from cvdp_analysis.py) and the pool / harness data.
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
sys.path.insert(0, str(RESEARCH))
from bench import cvdp_tasks  # noqa: E402


def instances(workdir: str) -> list[tuple[str, bool]]:
    f = Path(workdir) / "pytest-results.xml"
    if not f.exists():
        return []
    try:
        return [(t.get("name", ""), t.find("failure") is None and t.find("error") is None)
                for t in ET.parse(f).getroot().iter("testcase")]
    except ET.ParseError:
        return []


def runner_params(task: dict) -> list[str]:
    """Parameter names swept by the task's pytest runner (parametrize decorators)."""
    src = task["harness"]["files"].get("src/test_runner.py", "")
    return re.findall(r"@pytest\.mark\.parametrize\(\s*[\"']([\w, ]+)[\"']", src)


def partial_corr(x: list[float], y: list[float], z: list[float]) -> float:
    rxy, rxz, ryz = st.correlation(x, y), st.correlation(x, z), st.correlation(y, z)
    return (rxy - rxz * ryz) / (((1 - rxz ** 2) * (1 - ryz ** 2)) ** 0.5)


def main() -> None:
    data = json.loads((RESEARCH / "cvdp_analysis.json").read_text(encoding="utf-8"))
    rows = {r["task"]: r for r in data["rows"]}
    T = cvdp_tasks()
    pool = {f.stem: json.loads(f.read_text(encoding="utf-8"))
            for f in (RESEARCH / "pools" / "cvdp_ds41" / "out").glob("*.json")}
    # 1. parameter sweeps and parameter-dependent failures
    swept = {t: runner_params(T[t]) for t in rows}
    n_swept = sum(1 for v in swept.values() if v)
    print(f"[params] tasks whose runner sweeps parameters: {n_swept}/{len(rows)}")
    dep = Counter()
    for tid, r in pool.items():
        for c in r["candidates"]:
            inst = instances(c["gold"].get("workdir", ""))
            if len(inst) > 1:
                ok = sum(p for _, p in inst)
                dep["all instances pass" if ok == len(inst) else "none pass" if ok == 0 else "SOME pass"] += 1
    print(f"[params] candidates with >1 test instance: {dict(dep)}")
    unan = [t for t, r in rows.items() if r["kind"] == "unanimous wrong"]
    for t in unan:
        fails = [sum(not p for _, p in instances(c["gold"]["workdir"])) for c in pool[t]["candidates"]]
        tot = [len(instances(c["gold"]["workdir"])) for c in pool[t]["candidates"]]
        print(f"  unanimous-wrong {t.replace('cvdp_copilot_', ''):<44} swept={swept[t]} failing instances per "
              f"candidate={list(zip(fails, tot))}")
    # 2. selection failures: correct behaviour exists but is not the majority
    print("\n[selection] correct candidate exists but majority/tie loses:")
    for t, r in rows.items():
        if r["kind"] == "divergent, correct minority/tie":
            p1 = json.loads((RESEARCH / "askrtl" / "out_phase1_cvdp_ds41" / f"{t}.json").read_text(encoding="utf-8"))
            by = {c["id"]: c for c in pool[t]["candidates"]}
            shape = [(sum(len(by[m]["sources"]) for m in cl), "OK" if all(by[m]["correct"] for m in cl) else "x")
                     for cl in p1["clusters"]]
            print(f"  {t.replace('cvdp_copilot_', ''):<40} clusters (votes, correct): {shape}")
    # 3. divergent with no correct candidate: what do the failures look like?
    print("\n[no correct] divergent tasks without any correct candidate:")
    for t, r in rows.items():
        if r["kind"] in ("divergent, no correct", "single behaviour (unanalysable)", "unanimous wrong"):
            st_ = Counter(c["gold"]["status"] for c in pool[t]["candidates"] for _ in c["sources"])
            print(f"  {r['kind'][:20]:<20} {t.replace('cvdp_copilot_', ''):<40} {r['difficulty']:<6} "
                  f"spec={r['spec_chars']:>5} samples={r['samples']} {dict(st_)}")
    # 4. timeouts
    print("\n[timeouts]", [(t.replace('cvdp_copilot_', ''), c["id"]) for t, r in pool.items()
                           for c in r["candidates"] if c["gold"]["status"] == "timeout"])
    # 5. confound: ambiguity count vs spec length
    R = list(rows.values())
    p1v = [r["pass1"] for r in R]
    amb = [float(r["ambiguities"]) for r in R]
    ln = [float(r["spec_chars"]) for r in R]
    med = [1.0 if r["difficulty"] == "medium" else 0.0 for r in R]
    print(f"\n[confounds] corr(pass, ambiguities)={st.correlation(p1v, amb):+.2f}  corr(pass, length)={st.correlation(p1v, ln):+.2f}"
          f"  corr(ambiguities, length)={st.correlation(amb, ln):+.2f}  corr(pass, medium)={st.correlation(p1v, med):+.2f}")
    print(f"[confounds] partial corr(pass, ambiguities | length) = {partial_corr(p1v, amb, ln):+.2f};"
          f"  partial corr(pass, length | ambiguities) = {partial_corr(p1v, ln, amb):+.2f}")
    # 6. truncation: missing samples vs spec length
    miss = [(r["task"].replace('cvdp_copilot_', ''), 5 - r["samples"], r["spec_chars"]) for r in R if r["samples"] < 5]
    print(f"\n[missing samples] {sorted(miss, key=lambda x: -x[2])}")


if __name__ == "__main__":
    main()
