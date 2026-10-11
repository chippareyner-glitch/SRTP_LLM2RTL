"""Ground-truth grading for both benchmarks (used only for evaluation, never inside a method).

verilogeval: official testbench, RefModule = reference, TopModule = candidate; pass = 0 mismatches
             (for problems whose reference itself hits the testbench TIMEOUT, 0 mismatches + TIMEOUT passes)
rtllm      : original RTLLM testbench in a copy of the case directory; verdict as in rtllm_validator
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import RTLLM_DIR, VE_DIR, Bench  # noqa: E402

IVERILOG = r"D:\iverilog\bin\iverilog.exe"
VVP = r"D:\iverilog\bin\vvp.exe"
MIS = re.compile(r"Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples")
REF_TIMES_OUT = {"Prob082_lfsr32", "Prob141_count_clock",
                 "Prob156_review2015_fancytimer"}  # 156 added 2026-10-11: the reference itself hits TIMEOUT
SCRATCH = Path(os.environ.get("GRADE_SCRATCH", tempfile.gettempdir())) / "grade"


def _run(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str, bool]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return p.returncode, p.stdout + "\n" + p.stderr, False
    except subprocess.TimeoutExpired:
        return -1, "", True


def grade_ve(case: str, code: str, tag: str, ref_code: str | None = None) -> dict:
    w = SCRATCH / tag
    shutil.rmtree(w, ignore_errors=True)
    w.mkdir(parents=True)
    (w / "ref.sv").write_text(ref_code or (VE_DIR / f"{case}_ref.sv").read_text(encoding="utf-8"), encoding="utf-8")
    (w / "dut.sv").write_text(code, encoding="utf-8")
    rc, log, to = _run([IVERILOG, "-g2012", "-s", "tb", "-o", "s.vvp", str(VE_DIR / f"{case}_test.sv"),
                        "ref.sv", "dut.sv"], w, 60)
    if rc or to:
        return {"status": "compile_error", "correct": False, "compiles": False, "log": log[-400:]}
    rc, log, to = _run([VVP, "-n", "s.vvp"], w, 120)
    m = MIS.search(log)
    shutil.rmtree(w, ignore_errors=True)
    if to or not m or ("TIMEOUT" in log and case not in REF_TIMES_OUT):
        return {"status": "sim_incomplete", "correct": False, "compiles": True}
    mis, n = int(m.group(1)), int(m.group(2))
    return {"status": "ok", "mismatches": mis, "samples": n, "correct": mis == 0, "compiles": True}


def rtllm_verdict(text: str, rc: int, timed_out: bool) -> str:
    if timed_out or re.search(r"\btimeout\b", text, re.I):
        return "timeout"
    if rc != 0:
        return "simulation_error"
    if re.search(r"\b(error|failed|fatal|mismatch)\b", text, re.I):
        return "functional_failed"
    if any(int(n) for n in re.findall(r"(\d+)\s*(?:/\s*\d+\s*)?failures", text, re.I)):
        return "functional_failed"
    if re.search(r"Your\s+Design\s+Passed", text, re.I):
        return "pass"
    return "unconfirmed"


def grade_rtllm(case: str, code: str, tag: str) -> dict:
    import json
    meta = json.loads((RTLLM_DIR / case / "meta.json").read_text(encoding="utf-8"))
    w = SCRATCH / tag
    shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(RTLLM_DIR / case, w, ignore=shutil.ignore_patterns("ref.sv", "meta.json", "spec.txt"))
    (w / "candidate.sv").write_text(code, encoding="utf-8")
    tops = []
    for tb in meta["testbenches"]:
        txt = re.sub(r"/\*.*?\*/|//[^\n]*", "", (w / tb).read_text(encoding="utf-8", errors="replace"), flags=re.S)
        tops += re.findall(r"\bmodule\s+(\w+)", txt)
    rc, log, to = _run([IVERILOG, "-g2012", "-I", ".", *[x for t in tops for x in ("-s", t)], "-o", "s.vvp",
                        *meta["testbenches"], "candidate.sv"], w, 60)
    if rc or to:
        shutil.rmtree(w, ignore_errors=True)
        return {"status": "compile_error", "correct": False, "compiles": False, "log": log[-400:]}
    rc, log, to = _run([VVP, "-n", "s.vvp"], w, 60)
    shutil.rmtree(w, ignore_errors=True)
    v = rtllm_verdict(log, rc, to)
    return {"status": v, "correct": v == "pass", "compiles": True}


CVDP_PY = Path(os.environ.get("CVDP_PYTHON", r"E:\SRTP\benchmarks\cvdp\.venv\Scripts\python.exe"))


def grade_cvdp(case: str, code: str, tag: str, timeout: int = 600) -> dict:
    """Offline official CVDP harness; preserve unique work directories and logs."""
    from bench import cvdp_tasks
    import json
    script = Path(__file__).resolve().parents[2] / "benchmarks" / "cvdp" / "scripts" / "cvdp_local.py"
    # Run the adapter in its venv even when research scripts use another Python.
    # The parent does not need cocotb, yaml, or dotenv installed globally.
    env = dict(os.environ, CVDP_PYTHON=str(CVDP_PY))
    try:
        p = subprocess.run([str(CVDP_PY), str(script), "--scratch", str(SCRATCH),
                            "--tag", tag, "--timeout", str(timeout)],
                           input=json.dumps({"task":cvdp_tasks()[case], "code":code}),
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           env=env, timeout=timeout + 30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status":"environment_error", "correct":False, "compiles":False, "log":str(exc)}
    if p.returncode:
        return {"status":"environment_error", "correct":False, "compiles":False, "log":p.stderr[-4000:]}
    return json.loads(p.stdout)


def grade(bench: Bench, case: str, code: str, tag: str) -> dict:
    if bench.name == "cvdp":
        return grade_cvdp(case, code, tag)
    return grade_ve(case, code, tag) if bench.name == "verilogeval" else grade_rtllm(case, code, tag)


if __name__ == "__main__":  # self-test: every RTLLM reference must pass its own testbench
    import sys
    b = Bench("rtllm")
    bad = []
    for c in b.cases():
        r = grade_rtllm(c, (RTLLM_DIR / c / "ref.sv").read_text(encoding="utf-8"), f"self_{c}")
        if not r["correct"]:
            bad.append((c, r["status"]))
    print(f"RTLLM references passing: {len(b.cases()) - len(bad)}/{len(b.cases())}; failing: {bad}")
    sys.exit(1 if bad else 0)
