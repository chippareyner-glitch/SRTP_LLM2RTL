"""Rebuild a local RTLLM benchmark from the 2026-10-08 reference-check run (no download).

The RTLLM harness copied each case directory (spec, testbench, data files, reference) into
experiments/rtllm_20261008_200242_454947/<case>/reference/work/.  We keep only cases whose
reference passed its own testbench under this machine's Icarus build.

Output: research/benchmarks/rtllm_local/<case>/{spec.txt, ref.sv, testbench.v, <data files>, meta.json}
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
SRC = RESEARCH.parent / "experiments" / "rtllm_20261008_200242_454947"
OUT = RESEARCH / "benchmarks" / "rtllm_local"
SKIP = {"sim.vvp", "candidate_0.sv"}


def strip(code: str) -> str:
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", code, flags=re.S)


def main() -> None:
    summary = json.loads((SRC / "summary.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    kept, dropped = [], []
    for row in summary["results"]:
        case = row["case_id"]
        if (row.get("reference") or {}).get("status") != "pass":
            dropped.append((case, (row.get("reference") or {}).get("status")))
            continue
        work = SRC / case / "reference" / "work"
        ref = (work / "candidate_0.sv").read_text(encoding="utf-8")  # reference with verified_ prefix removed
        tbs = [p for p in work.iterdir() if p.suffix in (".v", ".sv") and p.name not in SKIP
               and re.search(r"\$finish|\$display", p.read_text(encoding="utf-8", errors="replace"))
               and not p.name.startswith("verified_")]
        tb_text = "\n".join(strip(p.read_text(encoding="utf-8", errors="replace")) for p in tbs)
        defined = re.findall(r"^\s*module\s+(\w+)", strip(ref), flags=re.M)
        body = strip(ref)
        inst = {m for m in defined if len(re.findall(rf"\b{m}\b", body)) > 1}  # used besides its declaration
        tops = [m for m in defined if m not in inst and re.search(rf"\b{m}\b", tb_text)]
        if len(tops) != 1:
            dropped.append((case, f"top ambiguous {tops}"))
            continue
        d = OUT / case
        shutil.rmtree(d, ignore_errors=True)
        d.mkdir()
        for p in work.iterdir():
            if p.is_file() and p.name not in SKIP and not p.name.startswith("verified_"):
                shutil.copy2(p, d / p.name)
        (d / "ref.sv").write_text(ref, encoding="utf-8")
        spec = work / "design_description.txt"
        (d / "spec.txt").write_text(spec.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        (d / "meta.json").write_text(json.dumps({"case": case, "category": row.get("category"), "top": tops[0],
                                                 "testbenches": [p.name for p in tbs],
                                                 "modules": defined}, indent=1), encoding="utf-8")
        kept.append(case)
    print(f"kept {len(kept)}; dropped {len(dropped)}: {dropped}")


if __name__ == "__main__":
    main()
