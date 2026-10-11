"""CVDP deep-dive 2 (no API): test under-constraint, missing-sample causes, parameter failures."""
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
sys.path.insert(0, str(RESEARCH))

POOL = RESEARCH / "pools" / "cvdp_ds41"
P1 = RESEARCH / "askrtl" / "out_phase1_cvdp_ds41"


def main() -> None:
    pool = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (POOL / "out").glob("*.json")}
    # 1. under-constrained tests: >=2 behaviourally distinct clusters that all pass the official tests
    split, tasks_with_correct = [], 0
    for f in P1.glob("*.json"):
        if f.stem == "summary":
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("status") != "ok":
            continue
        by = {c["id"]: c for c in pool[f.stem]["candidates"]}
        ok_clusters = [cl for cl in r["clusters"] if all(by[m]["correct"] for m in cl)]
        if ok_clusters:
            tasks_with_correct += 1
        if len(ok_clusters) >= 2:
            split.append((f.stem.replace("cvdp_copilot_", ""), len(ok_clusters)))
    print(f"[under-constrained] tasks where >=2 behaviourally different designs ALL pass the official tests: "
          f"{len(split)}/{tasks_with_correct} tasks that have a passing design")
    print("   ", sorted(split, key=lambda x: -x[1]))
    # 2. missing samples by cause
    cause = defaultdict(Counter)
    for line in (POOL / "gen_log.jsonl").read_text(encoding="utf-8").splitlines():
        g = json.loads(line)
        if not g.get("error"):
            continue
        e = g["error"]
        k = "402 balance" if "402" in e else "length cap" if "length" in e else "429 rate" if "429" in e else "empty/other"
        cause[g["case"].replace("cvdp_copilot_", "")][k] += 1
    present = {d.name.replace("cvdp_copilot_", ""): len(list(d.glob("s*.sv"))) for d in (POOL / "gen").iterdir()}
    miss = {t: 5 - present.get(t, 0) for t in {k.replace("cvdp_copilot_", "") for k in pool}}
    print("\n[missing samples] task: missing / error causes logged")
    for t, m in sorted(miss.items(), key=lambda kv: -kv[1]):
        if m:
            print(f"   {t:<40} missing={m} causes={dict(cause[t])}")
    tot = Counter()
    for t, m in miss.items():
        if m:
            # attribute missing samples to the most frequent logged cause for that task
            c = cause[t].most_common(1)[0][0] if cause[t] else "unknown"
            tot[c] += m
    print("   missing samples by dominant cause:", dict(tot))
    # 3. which parameter instances fail for parameter-dependent candidates
    print("\n[parameter instances] tasks where a candidate passes some instances and fails others:")
    for t, r in sorted(pool.items()):
        for c in r["candidates"]:
            f = Path(c["gold"].get("workdir", "")) / "pytest-results.xml"
            if not f.exists():
                continue
            try:
                tc = list(ET.parse(f).getroot().iter("testcase"))
            except ET.ParseError:
                continue
            ok = [x.get("name") for x in tc if x.find("failure") is None and x.find("error") is None]
            bad = [x.get("name") for x in tc if x not in [] and (x.find("failure") is not None or x.find("error") is not None)]
            if ok and bad:
                print(f"   {t.replace('cvdp_copilot_', ''):<40} {c['id']} pass={len(ok)} fail={len(bad)}  "
                      f"e.g. pass {ok[0][:60]} | fail {bad[0][:60]}")
                break


if __name__ == "__main__":
    main()
