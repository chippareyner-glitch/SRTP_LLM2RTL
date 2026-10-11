"""E2: recall extension for spec-defect detection (benchmark audit with the reference).

Divergence among samples cannot flag a defect when every sample fails the same way. For problems where no
base-pool sample passes the official tests, the consensus design (largest behaviour cluster) is
differential-simulated against the *reference*, the first divergence the official testbench would care
about (X/Z in the reference = don't care) is minimised, and the judge is asked about it, blind to which
option is the reference.

  judge picks the consensus value         -> flag: spec contradicts the reference
  judge allows both (ANY / UNCLEAR)       -> flag: the spec does not decide, the test does
  judge picks the reference value         -> no flag: a genuine generation error
Two prompts: the original "which option" judge, and the permissibility prompt (permissive.py, conv),
which doubles as a held-out test of E1.

Usage:
  python -I -X utf8 consensus_ref.py build
  python -I -X utf8 consensus_ref.py judge --prompt which|conv [--live --max-calls N --max-tokens T]
  python -I -X utf8 consensus_ref.py report
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import random
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import diffsim as ds  # noqa: E402
from bench import Bench  # noqa: E402
from defects import OURS, RTLBENCHMT  # noqa: E402
from queries import LETTERS, ref_matches, render, suite_rows  # noqa: E402

PROJ = HERE.parents[1]
POOLS = HERE.parent / "pools"
OUT = HERE / "out_consensus"
LOCK = threading.Lock()
TAGS = {"ve_ds41": "verilogeval", "rtllm_ds41": "rtllm"}
MIN_LIMIT = 2000


def first_ref_div(s: list[list[str]], st0: int) -> int | None:
    """First sample where the candidate (index 0) differs from the reference (index 1) on a cared bit."""
    for k in range(st0, len(s)):
        if not ref_matches(s[k][1], s[k][0]):
            return k
    return None


def minimise(vvp: Path, iface: ds.Interface, rows: list[list[int]], budget: int = 300) -> list[list[int]]:
    """ds.minimise with the reference-aware divergence test (same ddmin + value simplification)."""
    calls = 0

    def cut(stim: list[list[int]]) -> list[list[int]] | None:
        nonlocal calls
        calls += 1
        s = ds.simulate(vvp, iface, stim, f"m{calls}")
        k = first_ref_div(s, ds.start_index(iface)) if s else None
        return None if k is None else stim[: ds.sample_index_to_cycle(k, iface)[0] + 1]

    cur = cut(rows) or rows
    keep = 1 if (iface.sequential and iface.reset) else 0
    chunk = max(1, (len(cur) - keep) // 2)
    while chunk >= 1 and calls < budget:
        changed, start = False, keep
        while start < len(cur) - 1 and calls < budget:
            trial = cur[:start] + cur[start + chunk:]
            res = cut(trial) if len(trial) > keep else None
            if res is not None and len(res) <= len(cur) - 1:
                cur, changed = res, True
                continue
            start += chunk
        if not changed:
            chunk //= 2
    for t in range(keep, len(cur)):
        for q, p in enumerate(iface.inputs):
            if calls >= budget or t >= len(cur) or (iface.sequential and p.name == iface.reset):
                continue
            for v in ([cur[t - 1][q]] if t > 0 else []) + [0]:
                if cur[t][q] == v:
                    break
                trial = [r[:] for r in cur]
                trial[t][q] = v
                res = cut(trial)
                if res is not None and len(res) <= len(cur):
                    cur = res
                    break
    return cur


def build_case(tag: str, case: str) -> dict:
    b = Bench(TAGS[tag])
    pool = json.loads((POOLS / tag / "out" / f"{case}.json").read_text(encoding="utf-8"))
    p1f = HERE / f"out_phase1_{tag}" / f"{case}.json"
    p1 = json.loads(p1f.read_text(encoding="utf-8")) if p1f.exists() else {}
    votes = {c["id"]: len(c["sources"]) for c in pool["candidates"]}
    if p1.get("status") == "ok":
        cl = max(p1["clusters"], key=lambda m: sum(votes[x] for x in m))
        order, share = [cl[0]], sum(votes[x] for x in cl)
    else:
        order, share = sorted(votes, key=lambda x: -votes[x]), None
    work = ds.scratch_root() / f"cons_{case}"
    ds.clean(work)
    by_id = {c["id"]: c for c in pool["candidates"]}
    for cid in order:  # first candidate that compiles stand-alone
        code = b.to_top(Path(by_id[cid]["path"]).read_text(encoding="utf-8", errors="replace"), case)
        try:
            iface = ds.extract_interface(code, work / "if", b.params(case))
            break
        except Exception:  # noqa: BLE001
            continue
    else:
        return {"case": case, "tag": tag, "status": "no_compilable_candidate"}
    pol = b.reset_active_low(case, iface.reset)
    if pol is not None:
        iface.reset_active_low = pol
    try:
        vvp = ds.build_harness([ds.Candidate("cand", code), ds.Candidate("ref", b.ref_as_top(case))], iface,
                               work / "h", b.params(case))
    except Exception as e:  # noqa: BLE001
        return {"case": case, "tag": tag, "status": "harness_error", "error": str(e)[-300:]}
    names = ["exhaustive"] if ds.exhaustive_comb(iface) is not None else \
        [f"{p}{s}" for p in ds.PROFILES for s in range(3)] + (["dense9"] if iface.sequential else [])
    st0 = ds.start_index(iface)
    found = None
    for name in names:
        rows = suite_rows(iface, name)
        s = ds.simulate(vvp, iface, rows, "s")
        k = first_ref_div(s, st0) if s else None
        if k is not None:
            found = (name, rows[: ds.sample_index_to_cycle(k, iface)[0] + 1])
            break
    res = {"case": case, "tag": tag, "cand": cid, "cand_votes": votes[cid], "cluster_votes": share,
           "n_samples": sum(votes.values()),
           "iface": {"sequential": iface.sequential, "clock": iface.clock, "reset": iface.reset,
                     "reset_active_low": iface.reset_active_low,
                     "inputs": [(p.name, p.width) for p in iface.inputs],
                     "outputs": [(p.name, p.width) for p in iface.outputs]}}
    if not found:
        ds.clean(work)
        return {**res, "status": "no_divergence"}
    stim = found[1] if len(found[1]) > MIN_LIMIT else minimise(vvp, iface, found[1])
    s = ds.simulate(vvp, iface, stim, "q")
    k = first_ref_div(s, st0)
    ds.clean(work)
    return {**res, "status": "ok", "suite": found[0], "stim": stim, "k": k, "hist": [x[0] for x in s[:k]],
            "options": [s[k][0], s[k][1]], "len": len(stim)}  # A = consensus, B = reference


def build(_: argparse.Namespace) -> None:
    OUT.mkdir(exist_ok=True)
    jobs = []
    for tag in TAGS:
        for f in sorted((POOLS / tag / "out").glob("*.json")):
            p = json.loads(f.read_text(encoding="utf-8"))
            if not any(c.get("correct") for c in p["candidates"]):
                jobs.append((tag, p["case"]))
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda j: build_case(*j), jobs))
    (OUT / "questions.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    for r in res:
        print(f"{r['tag']:11} {r['case'][:40]:40} {r['status']:24} {r.get('len', '')}")


def judge(a: argparse.Namespace) -> None:
    import judge as jd  # noqa: E402
    import permissive as pm  # noqa: E402
    qs = [q for q in json.loads((OUT / "questions.json").read_text(encoding="utf-8")) if q["status"] == "ok"]
    out = OUT / f"judge_{a.prompt}.jsonl"
    done = {json.loads(l)["case"] for l in out.read_text(encoding="utf-8").splitlines()} if out.exists() else set()
    todo = [q for q in qs if q["case"] not in done][: a.max_calls or None]
    print(f"prompt={a.prompt}: {len(qs)} questions, {len(done)} done, {len(todo)} to call")
    if not a.live:
        print("dry run")
        return
    sys.path.insert(0, str(PROJ))
    from llm_client import call_llm  # noqa: E402
    state = {"tokens": 0}

    def one(q: dict) -> None:
        with LOCK:
            if state["tokens"] >= a.max_tokens:
                return
        perm = [0, 1]
        random.Random(f"cons:{q['case']}").shuffle(perm)
        shown = [q["options"][i] for i in perm]
        back = {LETTERS[d]: LETTERS[o] for d, o in enumerate(perm)}
        per = 2 if q["iface"]["sequential"] else 1
        text = render(Bench(TAGS[q["tag"]]).spec(q["case"]), q["iface"], q["stim"][: q["k"] // per + 1],
                      q["hist"], q["k"], shown)
        rec = {"case": q["case"], "tag": q["tag"]}
        try:
            system = jd.SYSTEM if a.prompt == "which" else pm.SYSTEMS["conv"]
            reply, meta = call_llm(system, text, case_id=q["case"], reasoning_effort="high", return_metadata=True,
                                   log_dir=str(OUT / f"api_logs_{a.prompt}"))
            tok = (meta.get("usage") or {}).get("total_tokens", 0)
            if a.prompt == "which":
                p = jd.parse_answer(reply)
                ans = back.get(p["answer"], p["answer"])
                allowed = [ans] if ans in ("A", "B") else (["A", "B"] if ans in ("ANY", "UNCLEAR") else [])
            else:
                p = pm.parse(reply)
                ans, allowed = pm.derive(p.get("verdicts", {}), back)
            rec.update(answer=ans, allowed=allowed, confidence=p.get("confidence"), tokens=tok, reply=reply)
        except Exception as e:  # noqa: BLE001
            tok = 0
            rec.update(answer="ERROR", allowed=[], error=str(e)[:300], tokens=0)
        with LOCK:
            state["tokens"] += tok
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"  {q['case']:40} -> {rec['answer']} ({tok} tok, total {state['tokens']})", flush=True)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))


def report(_: argparse.Namespace) -> None:
    qs = json.loads((OUT / "questions.json").read_text(encoding="utf-8"))
    known = {c for b in ("verilogeval", "rtllm") for c in RTLBENCHMT.get(b, set()) | OURS.get(b, set())}
    for f in sorted(OUT.glob("judge_*.jsonl")):
        res = {json.loads(l)["case"]: json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()}
        print(f"== {f.stem}")
        for q in qs:
            r = res.get(q["case"])
            if r is None:
                print(f"  {q['case'][:40]:40} {q['status']}{' [known]' if q['case'] in known else ''}")
                continue
            al = set(r["allowed"])
            kind = ("spec-vs-ref conflict" if al == {"A"} else "spec silent" if al == {"A", "B"} else
                    "model error" if al == {"B"} else "none allowed / error")
            print(f"  {q['case'][:40]:40} {kind:22}{' [known]' if q['case'] in known else ''}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("build", "judge", "report"))
    ap.add_argument("--prompt", choices=("which", "conv"), default="conv")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=600_000)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    {"build": build, "judge": judge, "report": report}[a.cmd](a)


if __name__ == "__main__":
    main()
