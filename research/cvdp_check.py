"""Independent check of the CVDP grading path (no API).

Runs the official solved example (cvdp_copilot_lfsr_0001) through the same subprocess path as
grade.grade_cvdp, with: (1) the official solution -> must pass; (2) a functionally broken copy
(output inverted) -> must fail; (3) a syntax-broken copy -> must not pass.
Also times one run.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
EX = (RESEARCH.parents[1] / "benchmarks" / "cvdp" / "upstream" / "cvdp_benchmark-main" / "example_dataset" /
      "cvdp_v1.1.0_example_nonagentic_code_generation_no_commercial_with_solutions.jsonl")
SCRIPT = RESEARCH.parents[1] / "benchmarks" / "cvdp" / "scripts" / "cvdp_local.py"
PY = Path(os.environ.get("CVDP_PYTHON", r"E:\SRTP\benchmarks\cvdp\.venv\Scripts\python.exe"))
SCRATCH = Path(os.environ.get("GRADE_SCRATCH", r"E:\SRTP\benchmarks\cvdp\local_runs"))


def run(task: dict, code: str, tag: str) -> dict:
    p = subprocess.run([str(PY), str(SCRIPT), "--scratch", str(SCRATCH), "--tag", tag, "--timeout", "300"],
                       input=json.dumps({"task": task, "code": code}), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=360)
    if p.returncode:
        return {"status": "environment_error", "stderr": p.stderr[-600:]}
    return json.loads(p.stdout)


def main() -> None:
    task = next(json.loads(l) for l in EX.read_text(encoding="utf-8").splitlines() if "lfsr_0001" in l)
    target = next(iter(task["output"]["context"]))
    sol = task["output"]["context"][target]
    # mutate the next-state logic (a wrong tap); the testbench checks next-state consistency
    broken = sol.replace("lfsr_out[6] ^ lfsr_out[0]", "lfsr_out[6] ^ lfsr_out[1]", 1)
    assert broken != sol
    stuck = re.sub(r"lfsr_out <= \{.*?\};", "lfsr_out <= lfsr_out;", sol, count=1)
    syntax = sol.replace("endmodule", "endmodul", 1)
    for name, code in (("official solution", sol), ("wrong tap", broken), ("stuck register", stuck),
                       ("syntax broken", syntax)):
        t0 = time.time()
        r = run(task, code, f"check_{name.split()[0]}")
        print(f"{name:<22} -> {r.get('status'):<18} suites={r.get('xml_suites')}  ({time.time() - t0:.0f}s)")


if __name__ == "__main__":
    main()
