"""Spec-test alignment and small-scope statistics over existing runs (no API).

1. Small scope: lengths of the minimised distinguishing traces (Phase 1), for correct-vs-incorrect pairs.
2. Spec x test matrix over judged questions. Each divergence question is classified by
     tests  - official pass/fail of the clusters behind its options (informative = one passes, one fails;
              all-pass = the official tests cannot tell the options apart);
     spec   - the judge's answer (a specific option = the spec decides; ANY/UNCLEAR = the spec is silent).
   aligned   informative + specific
   OVER      informative + ANY/UNCLEAR   -> the tests reject a reading the spec allows (false-fail risk)
   UNDER     all-pass + specific         -> the tests accept a reading the spec rules out (false-pass risk)
   lenient   all-pass + ANY/UNCLEAR      -> correct leniency
3. Officially passing samples rejected by a confident (>=0.9) non-X judge answer.

Needs official_analysis.json in each judge run (written by cvdp_judge_analysis.py, which works for any
pool: set ASKRTL_TAG / ASKRTL_BENCH and pass the run dir).

Usage: python -I -X utf8 alignment.py
"""
from __future__ import annotations

import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from queries import split_outputs  # noqa: E402
POOLS = HERE.parent / "pools"
TAGS = ["ve_ds41", "ve_ds41_ids", "rtllm_ds41", "rtllm_ds41_ids", "cvdp_ds41", "cvdp_ds41_ids"]


def small_scope(tag: str) -> str:
    d = HERE / ("out_phase1" if tag == "old" else f"out_phase1_{tag}")
    xs = []
    for f in d.glob("*.json"):
        if f.stem in ("summary", "divtypes", "policy_sim"):
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        for m in r.get("minimised", []) if r.get("status") == "ok" else []:
            c = m.get("correct")
            if m.get("ok") and m.get("min_len") is not None and c and len(c) == 2 and c[0] != c[1]:
                xs.append(m["min_len"])
    if not xs:
        return f"{tag:16} no pairs"
    share = lambda k: sum(x <= k for x in xs) / len(xs)  # noqa: E731
    return (f"{tag:16} pairs={len(xs):4} median={st.median(xs):g} max={max(xs)} "
            f"<=1:{share(1):.0%} <=3:{share(3):.0%} <=8:{share(8):.0%}")


def matrix(tag: str) -> str:
    rows = json.loads((HERE / f"out_judge_{tag}" / "online" / "official_analysis.json").read_text(encoding="utf-8"))
    m, over, under = Counter(), set(), set()
    for r in rows:
        if r["kind"] not in ("informative", "all-pass"):
            continue
        specific, silent = r["answer"] in r["status"], r["answer"] in ("ANY", "UNCLEAR")
        if not (specific or silent):
            continue
        cell = {("informative", True): "aligned", ("informative", False): "OVER",
                ("all-pass", True): "UNDER", ("all-pass", False): "lenient"}[(r["kind"], specific)]
        m[cell] += 1
        {"OVER": over, "UNDER": under}.get(cell, set()).add(r["case"])
    return (f"{tag:16} aligned={m['aligned']:3} OVER={m['OVER']:2} ({len(over)} tasks) "
            f"UNDER={m['UNDER']:2} ({len(under)} tasks) lenient={m['lenient']}")


def rejected_passing(tag: str, conf: float = 0.9) -> str:
    rows = [json.loads(l) for l in (HERE / f"out_judge_{tag}" / "online" / "online_results.jsonl")
            .read_text(encoding="utf-8").splitlines() if l.strip()]
    rej = defaultdict(set)
    for r in rows:
        if (r.get("confidence") or 0) < conf:
            continue
        qf = json.loads((HERE / f"out_queries_{tag}" / f"{r['case']}.json").read_text(encoding="utf-8"))
        q = qf["queries"][r["qi"]]
        if q.get("x_involved") or r["answer"] not in set(q["cluster_option"].values()):
            continue
        members = {c["rep"]: c["members"] for c in qf["clusters"]}
        for rep, opt in q["cluster_option"].items():
            if opt != r["answer"]:
                rej[r["case"]].update(members[rep])
    passed = hit = 0
    cases = set()
    for f in (POOLS / tag / "out").glob("*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        for c in p["candidates"]:
            if c.get("correct"):
                passed += len(c["sources"])
                if c["id"] in rej[p["case"]]:
                    hit += len(c["sources"])
                    cases.add(p["case"])
    return f"{tag:16} passing samples={passed:4} rejected={hit:3} ({hit / passed:.1%}) on {len(cases)} tasks"


VALID_RE = re.compile(r"(valid|vld|done|rdy|ready|start)", re.I)


def valid_gated(q: dict, outs: list) -> bool:
    """Rule: the options differ only in data outputs while every valid/done/ready/start-type output is low
    in all options (data is don't-care by convention)."""
    fields = [split_outputs(v, outs) for v in q["options"]]
    names = [n for n, _ in outs]
    disputed = [n for n in names if len({f[n] for f in fields}) > 1]
    flags = [n for n in names if VALID_RE.search(n)]
    return (bool(flags) and not any(VALID_RE.search(n) for n in disputed)
            and all(set(f[n]) <= {"0"} for f in fields for n in flags))


def adjudicated() -> None:
    adj = json.loads((HERE / "adjudication_n1.json").read_text(encoding="utf-8"))["items"]
    for cell in ("OVER", "UNDER"):
        for bench in ("ve", "rtllm", "cvdp"):
            its = [i for i in adj if i["cell"] == cell and i["tag"].startswith(bench + "_")]
            if its:
                c = Counter(i["verdict"] for i in its)
                print(f"  {cell:5} {bench:5} {len(its):2} unique questions: {dict(c.most_common())}")
    tp = fp = fn = 0
    for i in adj:
        if i["cell"] != "UNDER":
            continue
        qf = json.loads((HERE / f"out_queries_{i['tag']}" / f"{i['case']}.json").read_text(encoding="utf-8"))
        rule = valid_gated(qf["queries"][i["qi"]], qf["iface"]["outputs"])
        lab = i["verdict"] == "valid_gated"
        tp += rule and lab
        fp += rule and not lab
        fn += lab and not rule
    print(f"  valid-gating rule vs hand labels on UNDER: TP={tp} FP={fp} FN={fn}")


def main() -> None:
    print("1. small scope (correct-vs-incorrect minimal traces)")
    for t in ["old"] + TAGS:
        print("  " + small_scope(t))
    print("2. spec x test matrix")
    for t in TAGS:
        print("  " + matrix(t))
    print("3. officially passing samples rejected by a confident non-X judge answer")
    for t in TAGS:
        print("  " + rejected_passing(t))
    print("4. hand adjudication of every OVER/UNDER question (adjudication_n1.json)")
    adjudicated()


if __name__ == "__main__":
    main()
