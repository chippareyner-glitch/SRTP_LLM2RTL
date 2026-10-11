"""Interpretation-diverse sampling (IDS).

Step "list": one call per problem asks the model which behaviourally relevant aspects the spec
leaves ambiguous or unstated, each with two concrete alternative readings (JSON).
Step "gen":  for the top-K ambiguities, generate one design per reading, with the reading stated
explicitly.  Designs are written next to an existing pool's samples into a new pool tag:
  pools/<out_tag>/gen/<case>/s*.sv  (copied base samples)  +  i<a><r>.sv  (IDS designs)
so the normal grade_pool -> phase1_eval -> queries -> online/defects pipeline can run on it.

DRY-RUN BY DEFAULT.  Usage:
  python -I ids.py list --bench verilogeval --base ve_ds41 --out ve_ds41_ids [--live]
  python -I ids.py gen  --bench verilogeval --base ve_ds41 --out ve_ds41_ids [--live] [--top 2]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import shutil
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
PROJ = RESEARCH.parent
sys.path.insert(0, str(RESEARCH))
sys.path.insert(0, str(RESEARCH / "pools"))
from bench import Bench  # noqa: E402
from gen_pool import extract_sv  # noqa: E402

LOCK = threading.Lock()

LIST_SYSTEM = """You are a senior RTL design reviewer. Read the hardware specification and identify the
places where it is AMBIGUOUS, CONTRADICTORY or SILENT about something that changes the observable
cycle-by-cycle behaviour of the module's outputs. Typical sources: reset/initial values, whether a
register updates during reset, output latency (same cycle vs next cycle), bit/index ordering,
behaviour on invalid or "never occurring" inputs, overflow/edge cases, priority between signals,
contradictions between two parts of the text or a diagram.

Only list issues where two competent engineers could reasonably implement DIFFERENT output behaviour.
Do not list purely stylistic choices. If the spec is fully clear, return an empty list.

Return ONLY JSON:
{"ambiguities": [{"aspect": "<short name>", "severity": "high|medium|low",
                  "readings": ["<concrete reading 1>", "<concrete reading 2>"]}]}
Order by severity (most likely to change behaviour first). At most 4 entries."""


def parse_json(text: str) -> dict:
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        return {"ambiguities": [], "parse_error": True}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"ambiguities": [], "parse_error": True}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("list", "gen"))
    ap.add_argument("--bench", choices=("verilogeval", "rtllm", "cvdp"), required=True)
    ap.add_argument("--base", required=True, help="existing pool tag whose samples are copied")
    ap.add_argument("--out", required=True, help="new pool tag")
    ap.add_argument("--top", type=int, default=2)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--cases", nargs="*")
    a = ap.parse_args()
    b = Bench(a.bench)
    out = RESEARCH / "pools" / a.out
    lists = out / "ambiguities"
    cases = [c for c in b.cases() if not a.cases or any(c.startswith(x) for x in a.cases)]
    if a.live:
        sys.path.insert(0, str(PROJ))
        from llm_client import call_llm  # noqa: E402

    if a.step == "list":
        todo = [c for c in cases if not (lists / f"{c}.json").exists()]
        print(f"{len(todo)} listing calls pending")
        if not a.live:
            print("dry run")
            return
        lists.mkdir(parents=True, exist_ok=True)

        def do_list(c: str) -> None:
            try:
                reply, meta = call_llm(LIST_SYSTEM, b.spec(c), case_id=c, reasoning_effort="high",
                                       return_metadata=True, log_dir=str(out / "api_logs_list"))
                res = parse_json(reply)
            except Exception as e:  # noqa: BLE001
                res = {"ambiguities": [], "error": str(e)}
            (lists / f"{c}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
        with cf.ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(do_list, todo))
        n_amb = [len(json.loads((lists / f"{c}.json").read_text(encoding="utf-8")).get("ambiguities", []))
                 for c in cases]
        print(f"done; problems with >=1 ambiguity: {sum(x > 0 for x in n_amb)}/{len(cases)}")
        return

    # ---- gen: copy base samples, then one design per reading of the top-K ambiguities
    system = b.system_prompt()
    jobs = []
    for c in cases:
        src = RESEARCH / "pools" / a.base / "gen" / c
        dst = out / "gen" / c
        dst.mkdir(parents=True, exist_ok=True)
        for f in src.glob("s*.sv") if src.exists() else []:
            if not (dst / f.name).exists():
                shutil.copy2(f, dst / f.name)
        lf = lists / f"{c}.json"
        if not lf.exists():
            continue
        amb = json.loads(lf.read_text(encoding="utf-8")).get("ambiguities", [])[: a.top]
        for ai, item in enumerate(amb):
            for ri, reading in enumerate(item.get("readings", [])[:2]):
                f = dst / f"i{ai}{ri}.sv"
                if not f.exists():
                    user = (b.spec(c) + "\n\nIMPORTANT - resolve the following point exactly as stated, and follow "
                            f"the specification everywhere else:\n- {item.get('aspect', '')}: {reading}\n")
                    jobs.append((c, f, user))
    print(f"{len(jobs)} IDS generation calls pending")
    if not a.live:
        print("dry run")
        return

    def do_gen(job: tuple[str, Path, str]) -> None:
        c, f, user = job
        try:
            reply, meta = call_llm(system, user, case_id=c, reasoning_effort="high", return_metadata=True,
                                   log_dir=str(out / "api_logs_gen"))
            code = extract_sv(reply, a.bench != "verilogeval")
            if code.strip():
                f.write_text(code, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            with LOCK:
                print("ERR", c, f.name, str(e)[:80], flush=True)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(do_gen, jobs))
    print("done")


if __name__ == "__main__":
    main()
