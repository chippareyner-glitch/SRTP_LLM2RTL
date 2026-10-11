"""Check every CF variant before it is used for evaluation.

  self   : CF ref vs CF ref on the official testbench -> must be 0 mismatches (tb sanity)
  delta  : original ref as DUT vs CF ref as RefModule  -> must be > 0 mismatches
           (the testbench can tell the counterfactual from the canonical original,
            which is what lets us measure *reversion* to the original later)

Usage: python -I verify_seed.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATASET = HERE.parents[1] / "dataset_spec-to-rtl_gcc"
IVERILOG = r"D:\iverilog\bin\iverilog.exe"
VVP = r"D:\iverilog\bin\vvp.exe"
MIS = re.compile(r"Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples")
SCRATCH = Path(os.environ.get("CF_SCRATCH", tempfile.gettempdir())) / "cf_verify"


def as_top(code: str) -> str:
    return re.sub(r"\bmodule\s+RefModule\b", "module TopModule", code, count=1)


def grade(base: str, ref_code: str, dut_code: str, tag: str) -> dict:
    w = SCRATCH / tag
    shutil.rmtree(w, ignore_errors=True)
    w.mkdir(parents=True)
    (w / "ref.sv").write_text(ref_code, encoding="utf-8")
    (w / "dut.sv").write_text(dut_code, encoding="utf-8")
    tb = DATASET / f"{base}_test.sv"
    c = subprocess.run([IVERILOG, "-g2012", "-s", "tb", "-o", "s.vvp", str(tb), "ref.sv", "dut.sv"],
                       cwd=w, capture_output=True, text=True, timeout=120)
    if c.returncode:
        return {"status": "compile_error", "log": (c.stdout + c.stderr)[-400:]}
    s = subprocess.run([VVP, "-n", "s.vvp"], cwd=w, capture_output=True, text=True, timeout=300)
    m = MIS.search(s.stdout)
    if not m:
        return {"status": "no_result", "log": s.stdout[-400:]}
    return {"status": "ok", "mismatches": int(m.group(1)), "samples": int(m.group(2)),
            "timeout": "TIMEOUT" in s.stdout}


def main() -> None:
    rows = []
    for d in sorted((HERE / "variants").iterdir()):
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
        base = meta["base"]
        cf = (d / "ref.sv").read_text(encoding="utf-8")
        orig = (DATASET / f"{base}_ref.sv").read_text(encoding="utf-8")
        selfc = grade(base, cf, as_top(cf), f"{d.name}_self")
        delta = grade(base, cf, as_top(orig), f"{d.name}_delta")
        ok = (selfc.get("status") == "ok" and selfc["mismatches"] == 0 and
              delta.get("status") == "ok" and delta["mismatches"] > 0)
        meta["verify"] = {"self": selfc, "delta": delta, "ok": ok}
        (d / "meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        rows.append((d.name, ok, selfc.get("mismatches", selfc.get("status")),
                     f"{delta.get('mismatches')}/{delta.get('samples')}" if delta.get("status") == "ok"
                     else delta.get("status")))
    for r in rows:
        print(f"{r[0]:<45} ok={r[1]!s:<5} self={r[2]!s:<6} orig-vs-cf={r[3]}")
    print(f"{sum(r[1] for r in rows)}/{len(rows)} variants usable")


if __name__ == "__main__":
    main()
