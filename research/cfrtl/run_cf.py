"""Counterfactual spec-to-RTL evaluation: does the model follow the spec delta or revert?

For each CF variant and its unmodified base problem (control), sample N designs and grade:
  pass_cf    - matches the counterfactual reference (official stimulus, CF ref swapped in)
  reverted   - fails CF but matches the ORIGINAL reference exactly  (recitation)
  other_fail - fails both (syntax, compile, or some third behaviour)
  pass_base  - control: on the unmodified base spec, matches the original reference

DRY-RUN BY DEFAULT (renders prompts, estimates tokens).  Live: --live --max-calls N.

Usage:
  python -I run_cf.py                       # dry run
  python -I run_cf.py --live --max-calls 200 --samples 5
  python -I run_cf.py --grade out_cf/<run>  # (re)grade saved generations, no API
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
DATASET = PROJ / "dataset_spec-to-rtl_gcc"
sys.path.insert(0, str(HERE))
from verify_seed import as_top, grade  # noqa: E402

SYSTEM = (PROJ / "prompts" / "direct" / "baseline.system.txt").read_text(encoding="utf-8").strip()


def extract_sv(text: str) -> str:
    blocks = re.findall(r"```(?:systemverilog|verilog|sv)?\s*\n(.*?)```", text, flags=re.I | re.S)
    cand = max(blocks, key=len) if blocks else text
    s = re.search(r"\bmodule\s+TopModule\b", cand)
    if s:
        cand = cand[s.start():]
    ends = [m.end() for m in re.finditer(r"\bendmodule\b", cand)]
    return (cand[:ends[-1]] if ends else cand).strip() + "\n"


def tasks(samples: int) -> list[dict]:
    out, bases = [], set()
    for d in sorted((HERE / "variants").iterdir()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        if not meta.get("verify", {}).get("ok"):
            continue
        for s in range(samples):
            out.append({"kind": "cf", "id": meta["id"], "base": meta["base"], "sample": s,
                        "spec": (d / "prompt.txt").read_text(encoding="utf-8")})
        bases.add(meta["base"])
    for b in sorted(bases):
        for s in range(samples):
            out.append({"kind": "base", "id": b, "base": b, "sample": s,
                        "spec": (DATASET / f"{b}_prompt.txt").read_text(encoding="utf-8")})
    return out


def grade_one(t: dict, code: str) -> dict:
    orig = (DATASET / f"{t['base']}_ref.sv").read_text(encoding="utf-8")
    tag = f"g_{t['id']}_{t['sample']}"
    if t["kind"] == "base":
        g = grade(t["base"], orig, code, tag)
        return {"pass": g.get("status") == "ok" and g["mismatches"] == 0, "vs_orig": g}
    cf = (HERE / "variants" / t["id"] / "ref.sv").read_text(encoding="utf-8")
    g_cf = grade(t["base"], cf, code, tag + "_cf")
    g_or = grade(t["base"], orig, code, tag + "_or")
    pass_cf = g_cf.get("status") == "ok" and g_cf["mismatches"] == 0
    reverted = (not pass_cf) and g_or.get("status") == "ok" and g_or["mismatches"] == 0
    return {"pass": pass_cf, "reverted": reverted, "vs_cf": g_cf, "vs_orig": g_or}


def report(rows: list[dict]) -> None:
    by = defaultdict(list)
    for r in rows:
        by[(r["kind"], r["id"])].append(r)
    print(f"{'variant':<46}{'base pass':>10}{'cf pass':>9}{'reverted':>10}")
    base_pass = {k[1]: sum(x["grade"]["pass"] for x in v) / len(v) for k, v in by.items() if k[0] == "base"}
    tot = defaultdict(float)
    n_cf = 0
    for (kind, vid), v in sorted(by.items()):
        if kind != "cf":
            continue
        n_cf += 1
        p = sum(x["grade"]["pass"] for x in v) / len(v)
        rv = sum(x["grade"]["reverted"] for x in v) / len(v)
        bp = base_pass.get(v[0]["base"], float("nan"))
        tot["p"] += p
        tot["r"] += rv
        tot["b"] += bp
        print(f"{vid:<46}{bp:>10.2f}{p:>9.2f}{rv:>10.2f}")
    if n_cf:
        print(f"{'MEAN':<46}{tot['b'] / n_cf:>10.2f}{tot['p'] / n_cf:>9.2f}{tot['r'] / n_cf:>10.2f}")
        fails = [x for k, v in by.items() if k[0] == "cf" for x in v if not x["grade"]["pass"]]
        if fails:
            print(f"reversion share among CF failures: "
                  f"{sum(x['grade']['reverted'] for x in fails)}/{len(fails)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--effort", default="high")
    ap.add_argument("--temperature", type=float, default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--grade", help="re-grade an existing run directory")
    a = ap.parse_args()
    if a.grade:
        run = Path(a.grade)
        rows = [json.loads(l) for l in (run / "gen.jsonl").read_text(encoding="utf-8").splitlines()]
        for r in rows:
            r["grade"] = grade_one(r, r["code"])
        (run / "graded.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        report(rows)
        return
    ts = tasks(a.samples)
    chars = sum(len(t["spec"]) + len(SYSTEM) for t in ts)
    print(f"{len(ts)} generation calls ({sum(t['kind'] == 'cf' for t in ts)} CF + "
          f"{sum(t['kind'] == 'base' for t in ts)} base controls); ~{chars / 3.5 / 1e3:.0f}K input tokens "
          f"+ reasoning/output")
    if not a.live:
        print("dry run: no API calls (use --live --max-calls N)")
        return
    if a.max_calls <= 0:
        sys.exit("--live requires --max-calls > 0")
    sys.path.insert(0, str(PROJ))
    from llm_client import call_llm  # noqa: E402
    run = HERE / "out_cf" / datetime.now().strftime("%Y%m%d_%H%M%S")
    run.mkdir(parents=True)
    rows = []
    for i, t in enumerate(ts[: a.max_calls]):
        try:
            reply, meta = call_llm(SYSTEM, t["spec"], model=a.model, case_id=t["id"], reasoning_effort=a.effort,
                                   temperature=a.temperature, return_metadata=True, log_dir=str(run / "api_logs"))
            code = extract_sv(reply)
        except Exception as e:  # noqa: BLE001
            code, meta = "", {"error": str(e)}
        r = {k: t[k] for k in ("kind", "id", "base", "sample")}
        r.update({"code": code, "usage": meta.get("usage"), "error": meta.get("error")})
        rows.append(r)
        with (run / "gen.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(r) + "\n")
        print(i, t["kind"], t["id"], "ok" if code else "ERR", flush=True)
    for r in rows:
        r["grade"] = grade_one(r, r["code"])
    (run / "graded.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    report(rows)


if __name__ == "__main__":
    main()
