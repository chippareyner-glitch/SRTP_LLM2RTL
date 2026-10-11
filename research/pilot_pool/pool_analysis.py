"""Zero-API-cost pilot: behavioural structure of existing DeepSeek candidate pools.

For every VerilogEval spec-to-rtl problem, collect the *initial* (pre-repair)
candidates already produced by earlier runs, then
  1. grade each candidate against the official reference (ground truth), and
  2. compare candidates pairwise by renaming one to RefModule and reusing the
     official testbench stimulus (a cheap differential-testing proxy).

Outputs per-problem JSON + a summary used to estimate the headroom of
selection-, disambiguation- and diversity-based methods.  The official
stimulus is used here only for *analysis*, never inside a method.

Usage: python -I pool_analysis.py [--cases Prob035 ...] [--jobs 8]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(r"E:\SRTP")
PROJ = ROOT / "SRTP_LLM2RTL"
DATASET = PROJ / "dataset_spec-to-rtl_gcc"
EXP = PROJ / "experiments"
IVERILOG = r"D:\iverilog\bin\iverilog.exe"
VVP = r"D:\iverilog\bin\vvp.exe"
OUT = Path(__file__).resolve().parent / "out"
SCRATCH = Path(os.environ.get("POOL_SCRATCH", tempfile.gettempdir())) / "pool_pilot"
SIM_TIMEOUT = 60

# (source label, model, glob relative to the problem dir, problem-dir root)
SOURCES = [
    ("deepseek_full", "deepseek-v4-pro", "attempt_00/module.sv", ROOT / "deepseek_full_20260920"),
    ("legacy_v2", "deepseek", "module_initial.sv", EXP / "legacy_v2_20260921_092109_394863"),
    ("direct_batch", "deepseek-flash", "module.sv", EXP / "direct_batch_20260924_185024_475217"),
    ("json_ir", "deepseek-flash", "final.sv", EXP / "json_pipeline_20260926_004134_869935"),
    ("tri0926", "deepseek-flash", "candidate_*/attempt_00.sv",
     EXP / "candidate_selection" / "three_candidate_select_20260926_234951"),
    ("tri0927", "deepseek-flash", "candidate_*/attempt_00.sv",
     EXP / "candidate_selection" / "three_candidate_select_20260927_235104"),
]

# The reference itself hits the testbench's TIMEOUT under Icarus 12 (verified 2026-10-08),
# so for these problems "0 mismatches + TIMEOUT" is the best any design can do.
REF_TIMES_OUT = {"Prob082_lfsr32", "Prob141_count_clock"}

MISMATCH_RE = re.compile(r"Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples")


def problems() -> list[str]:
    return sorted(p.name[: -len("_prompt.txt")] for p in DATASET.glob("Prob*_prompt.txt"))


def normalise(code: str) -> str:
    code = re.sub(r"//.*", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"\s+", " ", code).strip()


def collect(case: str) -> list[dict]:
    cands, seen = [], {}
    for label, model, pattern, root in SOURCES:
        pdir = root / case
        if not pdir.is_dir():
            continue
        for f in sorted(pdir.glob(pattern)):
            code = f.read_text(encoding="utf-8", errors="replace")
            if "module" not in code or "TopModule" not in code:
                continue
            h = hashlib.sha1(normalise(code).encode()).hexdigest()[:12]
            src = f"{label}:{f.parent.name}" if "*" in pattern else label
            if h in seen:
                seen[h]["sources"].append(src)
                continue
            entry = {"id": f"c{len(cands)}", "hash": h, "sources": [src], "model": model,
                     "path": str(f), "code": code}
            seen[h] = entry
            cands.append(entry)
    return cands


def run_tb(case: str, ref_code: str, dut_code: str, tag: str) -> dict:
    """Compile official testbench with given RefModule/TopModule code; return mismatch info."""
    work = SCRATCH / case / tag
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    (work / "tb.sv").write_text((DATASET / f"{case}_test.sv").read_text(encoding="utf-8"), encoding="utf-8")
    (work / "ref.sv").write_text(ref_code, encoding="utf-8")
    (work / "dut.sv").write_text(dut_code, encoding="utf-8")
    try:
        c = subprocess.run([IVERILOG, "-g2012", "-s", "tb", "-o", "sim.vvp", "tb.sv", "ref.sv", "dut.sv"],
                           cwd=work, capture_output=True, text=True, timeout=SIM_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"status": "compile_timeout"}
    if c.returncode != 0:
        return {"status": "compile_error", "log": (c.stdout + c.stderr)[-600:]}
    try:
        s = subprocess.run([VVP, "-n", "sim.vvp"], cwd=work, capture_output=True, text=True,
                           timeout=SIM_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"status": "sim_timeout"}
    out = s.stdout + s.stderr
    m = MISMATCH_RE.search(out)
    if not m or ("TIMEOUT" in out and case not in REF_TIMES_OUT):
        return {"status": "sim_incomplete", "log": out[-600:]}
    mism, samples = int(m.group(1)), int(m.group(2))
    return {"status": "ok", "mismatches": mism, "samples": samples, "tb_timeout": "TIMEOUT" in out}


def as_ref(code: str) -> str:
    return re.sub(r"\bmodule\s+TopModule\b", "module RefModule", code, count=1)


def analyse(case: str) -> dict:
    ref = (DATASET / f"{case}_ref.sv").read_text(encoding="utf-8")
    cands = collect(case)
    for c in cands:
        r = run_tb(case, ref, c["code"], f"gold_{c['id']}")
        c["gold"] = r
        c["correct"] = r.get("status") == "ok" and r["mismatches"] == 0
        c["compiles"] = r.get("status") not in ("compile_error", "compile_timeout")
    live = [c for c in cands if c["compiles"]]
    # pairwise agreement under official stimulus, both directions (X-wildcard is asymmetric)
    agree: dict[tuple[str, str], bool] = {}
    for i, a in enumerate(live):
        for b in live[i + 1:]:
            r1 = run_tb(case, as_ref(a["code"]), b["code"], f"p_{a['id']}_{b['id']}")
            r2 = run_tb(case, as_ref(b["code"]), a["code"], f"p_{b['id']}_{a['id']}")
            ok = all(r.get("status") == "ok" and r["mismatches"] == 0 for r in (r1, r2))
            agree[(a["id"], b["id"])] = ok
    # clusters = connected components of the agreement graph
    parent = {c["id"]: c["id"] for c in live}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for (x, y), ok in agree.items():
        if ok:
            parent[find(x)] = find(y)
    groups: dict[str, list[str]] = {}
    for c in live:
        groups.setdefault(find(c["id"]), []).append(c["id"])
    by_id = {c["id"]: c for c in cands}
    clusters = []
    for members in groups.values():
        weight = sum(len(by_id[m]["sources"]) for m in members)  # duplicates count as votes
        clusters.append({"members": members, "votes": weight,
                         "correct": any(by_id[m]["correct"] for m in members),
                         "mixed": len({by_id[m]["correct"] for m in members}) > 1})
    clusters.sort(key=lambda k: -k["votes"])
    for c in cands:
        c.pop("code")
    return {"case": case, "n_samples": sum(len(c["sources"]) for c in cands),
            "n_distinct": len(cands), "n_compiling": len(live),
            "candidates": cands, "clusters": clusters,
            "nontransitive_pairs": sum(1 for v in agree.values() if not v)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="*")
    ap.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    args = ap.parse_args()
    cases = problems()
    if args.cases:
        cases = [c for c in cases if any(c.startswith(p) for p in args.cases)]
    OUT.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        futs = {ex.submit(analyse, c): c for c in cases}
        for f in cf.as_completed(futs):
            case = futs[f]
            try:
                res = f.result()
            except Exception as e:  # keep going; record the failure
                res = {"case": case, "error": repr(e)}
            (OUT / f"{case}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
            print(case, res.get("n_distinct"), len(res.get("clusters", [])), flush=True)


if __name__ == "__main__":
    main()
