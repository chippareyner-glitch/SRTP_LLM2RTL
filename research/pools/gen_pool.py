"""Generate i.i.d. candidate pools with one model/config (Phase 3, A and B).

Writes pools/<tag>/gen/<case>/s<k>.sv and appends one JSON line per call to
pools/<tag>/gen_log.jsonl.  Resumable: existing sample files are skipped.

Usage:
  python -I gen_pool.py --bench verilogeval --tag ve_ds41 --samples 5 --workers 6            # dry run
  python -I gen_pool.py --bench verilogeval --tag ve_ds41 --samples 5 --workers 6 --live
  python -I gen_pool.py --bench rtllm --tag rtllm_ds41 --samples 5 --workers 6 --live
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
from bench import Bench  # noqa: E402

LOCK = threading.Lock()


def extract_sv(text: str, multi: bool) -> str:
    blocks = re.findall(r"```(?:systemverilog|verilog|sv)?\s*\n(.*?)```", text, flags=re.I | re.S)
    if multi:  # RTLLM designs may need submodules: keep every block
        return ("\n\n".join(blocks) if blocks else text).strip() + "\n"
    cand = max(blocks, key=len) if blocks else text
    s = re.search(r"\bmodule\s+TopModule\b", cand)
    if s:
        cand = cand[s.start():]
    ends = [m.end() for m in re.finditer(r"\bendmodule\b", cand)]
    return (cand[:ends[-1]] if ends else cand).strip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bench", choices=("verilogeval", "rtllm", "cvdp"), required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--effort", default="high")
    ap.add_argument("--model", default=None)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases", nargs="*")
    a = ap.parse_args()
    b = Bench(a.bench)
    root = HERE / a.tag
    jobs = []
    for case in b.cases():
        if a.cases and not any(case.startswith(c) for c in a.cases):
            continue
        for k in range(a.samples):
            f = root / "gen" / case / f"s{k}.sv"
            if not f.exists():
                jobs.append((case, k, f))
    system = b.system_prompt()
    chars = sum(len(b.spec(c)) + len(system) for c, _, _ in jobs)
    print(f"{len(jobs)} generation calls pending ({a.bench}, tag={a.tag}); ~{chars / 3.5 / 1e3:.0f}K input tokens "
          f"+ ~2-3K reasoning/output each")
    if not a.live:
        print("dry run: no API calls (use --live)")
        return
    sys.path.insert(0, str(PROJ))
    from llm_client import call_llm  # noqa: E402
    (root / "config.json").parent.mkdir(parents=True, exist_ok=True)
    (root / "config.json").write_text(json.dumps({"bench": a.bench, "samples": a.samples, "effort": a.effort,
                                                  "model": a.model or "DEEPSEEK_MODEL", "system": system},
                                                 indent=1), encoding="utf-8")
    done = [0]

    def work(job: tuple[str, int, Path]) -> None:
        case, k, f = job
        t0 = time.time()
        try:
            reply, meta = call_llm(system, b.spec(case), model=a.model, case_id=case, reasoning_effort=a.effort,
                                   return_metadata=True, log_dir=str(root / "api_logs"))
            code, err = extract_sv(reply, a.bench != "verilogeval"), None
        except Exception as e:  # noqa: BLE001
            code, meta, err = "", {}, str(e)
        if code:
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(code, encoding="utf-8")
        with LOCK:
            done[0] += 1
            with (root / "gen_log.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"case": case, "sample": k, "usage": meta.get("usage"), "error": err,
                                     "returned_model": meta.get("returned_model"),
                                     "secs": round(time.time() - t0, 1)}) + "\n")
            if done[0] % 20 == 0 or err:
                print(f"{done[0]}/{len(jobs)} {case} s{k} {'ERR ' + err[:80] if err else 'ok'}", flush=True)

    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, jobs))
    print("done")


if __name__ == "__main__":
    main()
