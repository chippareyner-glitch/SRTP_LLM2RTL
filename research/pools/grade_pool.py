"""Grade a generated pool and write pilot-format JSON (pools/<tag>/out/<case>.json).

Per case: deduplicate samples (normalised code), grade each distinct candidate with the
official testbench (ground truth, evaluation only), and for VerilogEval also cluster candidates
by agreement under the official stimulus (swap trick, both directions).  RTLLM testbenches
check hard-coded expectations, so no official clustering is possible there (clusters = []).

Usage: python -I grade_pool.py --tag ve_ds41 --bench verilogeval [--jobs 8]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import re
import sys
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bench import Bench  # noqa: E402
from grade import grade, grade_ve  # noqa: E402


def normalise(code: str) -> str:
    code = re.sub(r"//.*", "", code)
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.S)
    return re.sub(r"\s+", " ", code).strip()


def as_ref(code: str) -> str:
    return re.sub(r"\bmodule\s+TopModule\b", "module RefModule", code, count=1)


def run_case(b: Bench, tag: str, case: str) -> dict:
    gdir = HERE / tag / "gen" / case
    cands, seen = [], {}
    for f in sorted(gdir.glob("*.sv")) if gdir.exists() else []:
        code = f.read_text(encoding="utf-8", errors="replace")
        h = hashlib.sha1(normalise(code).encode()).hexdigest()[:12]
        # i*.sv = interpretation-diverse designs: a separate sampling configuration ("ids")
        src = f"ids:{f.stem}" if f.stem.startswith("i") else f"{tag}:{f.stem}"
        if h in seen:
            seen[h]["sources"].append(src)
            continue
        c = {"id": f"c{len(cands)}", "hash": h, "sources": [src], "model": tag, "path": str(f)}
        seen[h] = c
        cands.append(c)
    for c in cands:
        g = grade(b, case, Path(c["path"]).read_text(encoding="utf-8", errors="replace"), f"{tag}_{case}_{c['id']}")
        c.update(gold=g, correct=g["correct"], compiles=g["compiles"])
    clusters = []
    if b.name == "verilogeval":
        live = [c for c in cands if c["compiles"]]
        parent = {c["id"]: c["id"] for c in live}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        code = {c["id"]: Path(c["path"]).read_text(encoding="utf-8", errors="replace") for c in live}
        for x, y in combinations(live, 2):
            if find(x["id"]) == find(y["id"]):
                continue
            ok = all(r.get("status") == "ok" and r["mismatches"] == 0 for r in (
                grade_ve(case, code[y["id"]], f"{tag}_{case}_p{x['id']}{y['id']}", as_ref(code[x["id"]])),
                grade_ve(case, code[x["id"]], f"{tag}_{case}_p{y['id']}{x['id']}", as_ref(code[y["id"]]))))
            if ok:
                parent[find(x["id"])] = find(y["id"])
        groups: dict[str, list[str]] = {}
        for c in live:
            groups.setdefault(find(c["id"]), []).append(c["id"])
        by = {c["id"]: c for c in cands}
        for members in groups.values():
            clusters.append({"members": members, "votes": sum(len(by[m]["sources"]) for m in members),
                             "correct": any(by[m]["correct"] for m in members)})
        clusters.sort(key=lambda k: -k["votes"])
    return {"case": case, "n_samples": sum(len(c["sources"]) for c in cands), "n_distinct": len(cands),
            "candidates": cands, "clusters": clusters}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--bench", choices=("verilogeval", "rtllm", "cvdp"), required=True)
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    b = Bench(a.bench)
    out = HERE / a.tag / "out"
    out.mkdir(parents=True, exist_ok=True)
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(run_case, b, a.tag, c): c for c in b.cases()}
        for fu in cf.as_completed(futs):
            c = futs[fu]
            try:
                r = fu.result()
            except Exception as e:  # noqa: BLE001
                r = {"case": c, "error": repr(e)}
            (out / f"{c}.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
    rows = [json.loads(f.read_text(encoding="utf-8")) for f in out.glob("*.json")]
    rows = [r for r in rows if "candidates" in r]
    n = len(rows)
    acc = sum(sum(len(c["sources"]) for c in r["candidates"] if c["correct"]) / max(r["n_samples"], 1)
              for r in rows) / n
    anyc = sum(any(c["correct"] for c in r["candidates"]) for r in rows) / n
    print(f"{a.tag}: {n} problems, mean per-sample accuracy (pass@1) {acc:.3f}, pass@any {anyc:.3f}")


if __name__ == "__main__":
    main()
