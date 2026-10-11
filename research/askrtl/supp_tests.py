"""Spec-derived supplementary tests from hand-confirmed test gaps (no API).

Every `genuine` UNDER item in adjudication_n1.json is a place where the official tests accept a design
that violates an explicit statement of the spec. Each becomes an executable test:
  stimulus = the question's minimal input trace,
  check    = at sample k, every output on which the options disagree must equal the option the spec
             requires (no X/Z).
The test does not depend on the candidates that exposed the gap. It is run on every design of the
benchmark's IDS pool (base samples + interpretation-specific designs) and, where available, on the
reference. Designs that the question was not built from (IDS designs for base-pool questions) are
reported separately as a held-out check.

Writes supp_tests/<bench>.json (the tests, reusable) and supp_tests/results.json.
Usage: python -I -X utf8 supp_tests.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import diffsim as ds  # noqa: E402
from bench import Bench  # noqa: E402
from queries import LETTERS, split_outputs  # noqa: E402

POOLS = HERE.parent / "pools"
OUT = HERE / "supp_tests"
BENCH_OF = {"ve": "verilogeval", "rtllm": "rtllm", "cvdp": "cvdp"}


def make_test(item: dict) -> dict:
    tag = item["tag"]
    qf = json.loads((HERE / f"out_queries_{tag}" / f"{item['case']}.json").read_text(encoding="utf-8"))
    q = qf["queries"][item["qi"]]
    judged = [json.loads(l) for l in (HERE / f"out_judge_{tag}" / "online" / "online_results.jsonl")
              .read_text(encoding="utf-8").splitlines() if l.strip()]
    ans = next(r["answer"] for r in judged if r["case"] == item["case"] and r["qi"] == item["qi"])
    if ans != item["expected"]:  # genuine UNDER = the judge was right; letters are canonical, not as shown
        raise ValueError(f"{item['case']} q{item['qi']}: expected {item['expected']} but judge said {ans}")
    outs = qf["iface"]["outputs"]
    exp = q["options"][LETTERS.index(item["expected"])]
    fields = {n: split_outputs(v, outs) for n, v in zip(LETTERS, q["options"])}
    e = fields[item["expected"]]
    check = {name: e[name] for name, _ in outs
             if any(f[name] != e[name] for f in fields.values())}
    return {"bench": BENCH_OF[tag.split("_")[0]], "case": item["case"], "from": f"{tag}:q{item['qi']}",
            "iface": qf["iface"], "stim": q["stim"], "k": q["k"], "expected_full": exp, "check": check,
            "note": item["note"]}


def iface_of(d: dict) -> ds.Interface:
    ports = [ds.Port(n, "INPUT", w) for n, w in d["inputs"]]
    if d.get("clock"):
        ports.append(ds.Port(d["clock"], "INPUT", 1))
    ports += [ds.Port(n, "OUTPUT", w) for n, w in d["outputs"]]
    return ds.Interface(tuple(ports), clock=d.get("clock"), reset=d.get("reset"),
                        reset_active_low=bool(d.get("reset_active_low")))


def run_test(t: dict, code: str, work: Path) -> str:
    """pass / fail / x / error for one design."""
    b = Bench(t["bench"])
    iface = iface_of(t["iface"])
    ds.clean(work)
    try:
        vvp = ds.build_harness([ds.Candidate("d", code)], iface, work, b.params(t["case"]))
    except Exception:  # noqa: BLE001 - design does not compile against the interface
        return "error"
    samples = ds.simulate(vvp, iface, t["stim"], "t")
    ds.clean(work)
    if not samples or len(samples) <= t["k"]:
        return "error"
    got = split_outputs(samples[t["k"]][0], t["iface"]["outputs"])
    if any(ch in "xz" for n in t["check"] for ch in got[n]):
        return "x"
    return "pass" if all(got[n] == v for n, v in t["check"].items()) else "fail"


def main() -> None:
    adj = json.loads((HERE / "adjudication_n1.json").read_text(encoding="utf-8"))["items"]
    tests = [make_test(i) for i in adj if i["cell"] == "UNDER" and i["verdict"] == "genuine"]
    OUT.mkdir(exist_ok=True)
    for bname in sorted({t["bench"] for t in tests}):
        (OUT / f"{bname}.json").write_text(json.dumps([t for t in tests if t["bench"] == bname], indent=1),
                                           encoding="utf-8")
    work = ds.scratch_root() / "supp_tests"
    results = []
    for t in tests:
        b = Bench(t["bench"])
        prefix = {"verilogeval": "ve", "rtllm": "rtllm", "cvdp": "cvdp"}[t["bench"]]
        pool = json.loads((POOLS / f"{prefix}_ds41_ids" / "out" / f"{t['case']}.json").read_text(encoding="utf-8"))
        base_q = not t["from"].split(":")[0].endswith("_ids")
        rows = []
        for c in pool["candidates"]:
            code = b.to_top(Path(c["path"]).read_text(encoding="utf-8", errors="replace"), t["case"])
            r = run_test(t, code, work)
            ids = [s for s in c["sources"] if s.startswith("ids:")]
            rows.append({"id": c["id"], "official": bool(c.get("correct")), "supp": r,
                         "n_base": len(c["sources"]) - len(ids), "n_ids": len(ids)})
        ref = b.ref_as_top(t["case"])
        ref_r = run_test(t, ref, work) if ref else None
        results.append({"case": t["case"], "from": t["from"], "check": t["check"], "reference": ref_r,
                        "held_out_ids": base_q, "designs": rows})
        bad = [r for r in rows if r["official"] and r["supp"] != "pass"]
        print(f"{t['case'][:44]:44} {t['from']:22} ref={ref_r} | officially passing designs failing the "
              f"supplementary test: {len(bad)} ({sum(r['n_base'] for r in bad)} base samples, "
              f"{sum(r['n_ids'] for r in bad)} IDS designs){' [IDS designs held out]' if base_q else ''}")
    (OUT / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    summarise(results)


def summarise(results: list[dict]) -> None:
    """Benchmark-level effect on the base 5-sample pools: pass@1 (sample-weighted) and pass@any."""
    by_case = defaultdict(list)
    for r in results:
        by_case[r["case"]].append(r)
    for prefix, bname in (("ve", "verilogeval"), ("rtllm", "rtllm"), ("cvdp", "cvdp")):
        pool_dir = POOLS / f"{prefix}_ds41_ids" / "out"
        n_tasks = tot = p_before = p_after = any_before = any_after = 0
        for f in pool_dir.glob("*.json"):
            p = json.loads(f.read_text(encoding="utf-8"))
            fails = set()
            for r in by_case.get(p["case"], []):
                fails |= {d["id"] for d in r["designs"] if d["supp"] != "pass"}
            base = [(c, len([s for s in c["sources"] if not s.startswith("ids:")])) for c in p["candidates"]]
            base = [(c, n) for c, n in base if n]
            if not base:
                continue
            n_tasks += 1
            tot += sum(n for _, n in base)
            p_before += sum(n for c, n in base if c.get("correct"))
            p_after += sum(n for c, n in base if c.get("correct") and c["id"] not in fails)
            any_before += any(c.get("correct") for c, _ in base)
            any_after += any(c.get("correct") and c["id"] not in fails for c, _ in base)
        print(f"{bname:12} base pool: pass@1 {p_before / tot:.1%} -> {p_after / tot:.1%} "
              f"({p_before - p_after} samples), pass@any {any_before}/{n_tasks} -> {any_after}/{n_tasks}")


if __name__ == "__main__":
    main()
