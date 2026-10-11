#!/usr/bin/env python3
"""Build a non-destructive official-test candidate pool from existing runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT / "experiments"
from candidate_runtime import DEFAULT_DATASET as DATASET, DEFAULT_IVERILOG as IVERILOG, DEFAULT_VVP as VVP, as_text
CASE_RE = re.compile(r"^(Prob\d{3}_[^\\/]+)$")
MISMATCH_RE = re.compile(r"Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples", re.I)


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path)
    p.add_argument("--max-candidates", type=int, default=0, help="0 means unlimited")
    return p.parse_args()


def run(cmd: list[str], cwd: Path, timeout: int = 30) -> tuple[int, str, str, bool]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        return 124, as_text(exc.stdout), as_text(exc.stderr), True


def case_from_path(path: Path) -> str | None:
    for part in reversed(path.parts):
        if CASE_RE.match(part):
            return part
    return None


def priority(path: Path) -> tuple[int, int, str]:
    name = path.name.lower()
    if name == "module_final.sv": rank = 0
    elif name == "final.sv": rank = 1
    elif "final" in name: rank = 2
    elif name == "module.sv": rank = 3
    elif name.startswith("attempt_"): rank = 4
    elif name.startswith("module_v"): rank = 5
    elif name in {"generated.sv", "module_initial.sv"}: rank = 6
    else: rank = 9
    try:
        mtime = -path.stat().st_mtime_ns
    except OSError:
        mtime = 0
    return rank, mtime, str(path)


def discover() -> dict[str, list[Path]]:
    by_case: dict[str, dict[str, Path]] = {}
    for path in WORKSPACE.rglob("*.sv"):
        try:
            path.relative_to(DATASET)
            continue
        except ValueError:
            pass
        lowered = path.name.lower()
        if any(token in lowered for token in ("testbench", "generated_directed_tb", "_test", "_ref")):
            continue
        case_id = case_from_path(path)
        if not case_id:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if not re.search(r"\bmodule\s+TopModule\b", text):
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        existing = by_case.setdefault(case_id, {}).get(digest)
        if existing is None or priority(path) < priority(existing):
            by_case[case_id][digest] = path
    return {case: sorted(paths.values(), key=priority) for case, paths in by_case.items()}


def evaluate(case_id: str, candidate: Path) -> dict[str, Any]:
    test = DATASET / f"{case_id}_test.sv"
    ref = DATASET / f"{case_id}_ref.sv"
    with tempfile.TemporaryDirectory(prefix=f"pool_{case_id}_") as tmp_name:
        tmp = Path(tmp_name)
        sim = tmp / "sim.vvp"
        rc, out, err, timed_out = run([
            str(IVERILOG), "-g2012", "-s", "tb", "-o", str(sim),
            str(test), str(ref), str(candidate),
        ], tmp)
        if rc != 0 or timed_out or not sim.exists():
            return {"status": "compile_failed", "pass": False, "mismatches": None, "samples": None,
                    "error": (out + "\n" + err)[-2000:]}
        rc, out, err, timed_out = run([str(VVP), str(sim)], tmp)
        full = out + "\n" + err
        match = MISMATCH_RE.search(full)
        if timed_out:
            status, mismatches, samples = "timeout", None, None
        elif match and rc == 0 and int(match.group(2)) > 0:
            mismatches, samples = int(match.group(1)), int(match.group(2))
            status = "pass" if mismatches == 0 else "mismatch"
        else:
            status, mismatches, samples = "unknown_sim_fail", None, None
        return {"status": status, "pass": status == "pass", "mismatches": mismatches,
                "samples": samples, "returncode": rc, "log_tail": full[-2000:]}


def main() -> int:
    ns = args()
    output = (
        ns.output
        or WORKSPACE / "candidate_pool" / f"candidate_pool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ).resolve()
    if output.exists():
        raise FileExistsError(f"output exists: {output}")
    output.mkdir(parents=True)
    candidates = discover()
    cases = sorted(p.name[:-11] for p in DATASET.glob("*_prompt.txt"))
    rows: list[dict[str, Any]] = []
    for index, case_id in enumerate(cases, 1):
        paths = candidates.get(case_id, [])
        if ns.max_candidates:
            paths = paths[:ns.max_candidates]
        row: dict[str, Any] = {"case_id": case_id, "unique_candidates": len(paths), "evaluated": 0,
                               "passed": False, "selected_source": None, "best_failure": None}
        print(f"[{index}/{len(cases)}] {case_id}: {len(paths)} candidates", flush=True)
        best: tuple[int, Path, dict[str, Any]] | None = None
        for path in paths:
            result = evaluate(case_id, path)
            row["evaluated"] += 1
            if result["pass"]:
                case_out = output / case_id
                case_out.mkdir()
                shutil.copy2(path, case_out / "selected.sv")
                row["passed"] = True
                row["selected_source"] = str(path.resolve())
                row["selected_evaluation"] = result
                break
            mismatches = result.get("mismatches")
            score = mismatches if isinstance(mismatches, int) else 10**18
            if best is None or score < best[0]:
                best = score, path, result
        if not row["passed"] and best is not None:
            case_out = output / case_id
            case_out.mkdir()
            shutil.copy2(best[1], case_out / "best_failure.sv")
            row["best_failure"] = {"source": str(best[1].resolve()), "evaluation": best[2]}
        rows.append(row)
        summary = {
            "total": len(cases), "completed": len(rows),
            "passed": sum(r["passed"] for r in rows),
            "unsolved": [r["case_id"] for r in rows if not r["passed"]],
            "rows": rows,
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {'PASS' if row['passed'] else 'UNSOLVED'} after {row['evaluated']}", flush=True)
    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
