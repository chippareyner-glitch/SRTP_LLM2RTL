"""Phase 1: can reference-free differential simulation find the divergences that matter?

For each VerilogEval problem in the pilot pool:
  1. co-simulate all compiling candidates on profile-based random stimulus (diffsim),
  2. partition candidates by output trace,
  3. minimise one distinguishing trace per pair of clusters,
and score against ground truth that the method never sees:
  * sep_recall   - fraction of (correct, incorrect) candidate pairs we distinguish
  * off_recall   - fraction of pairs distinguished by official stimulus that we distinguish
  * extra_splits - pairs we split that the official stimulus does not (don't-care / X / invalid inputs)

Usage: python -I phase1_eval.py [--cases Prob035 ...] [--jobs 8] [--cycles 256] [--seeds 3]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diffsim as ds  # noqa: E402

from paths import BENCH, HI, P1 as OUT, POOL, case_files  # noqa: E402
LONG_SEED, LONG_CYCLES = 9, 60000  # one long dense run for deep-state divergences
MIN_LIMIT = 2000  # do not delta-debug traces longer than this; render a window instead
HI_SUITE = "uniform_hi"  # run whose inputs change while the clock is high


def load_problem(case_json: Path) -> tuple[dict, list[ds.Candidate]]:
    r = json.loads(case_json.read_text(encoding="utf-8"))
    cands = []
    for c in r["candidates"]:
        if not c.get("compiles"):
            continue
        code = BENCH.to_top(Path(c["path"]).read_text(encoding="utf-8", errors="replace"), r["case"])
        cands.append(ds.Candidate(c["id"], code, {"correct": c["correct"], "votes": len(c["sources"]),
                                                   "sources": c["sources"]}))
    return r, cands


def official_cluster_of(r: dict) -> dict[str, int]:
    return {m: k for k, cl in enumerate(r["clusters"]) for m in cl["members"]}


def run_case(case_json: Path, cycles: int, seeds: int, do_min: bool) -> dict:
    r, cands = load_problem(case_json)
    case = r["case"]
    work = ds.scratch_root() / case
    ds.clean(work)
    res: dict = {"case": case}
    if not cands:  # no candidate compiles with the official testbench (e.g. Prob099 port bug)
        return {**res, "status": "ungradable"}
    # interfaces; keep the majority signature
    for c in cands:
        try:
            c.iface = ds.extract_interface(c.code, work / f"if_{c.cid}", BENCH.params(case))
        except Exception as e:  # noqa: BLE001
            c.error = str(e)
    sigs = Counter(c.iface.ports for c in cands if c.iface)
    if not sigs:
        return {**res, "status": "no_interface"}
    sig = sigs.most_common(1)[0][0]
    live = [c for c in cands if c.iface and c.iface.ports == sig]
    res["excluded_iface"] = [c.cid for c in cands if c not in live]
    iface = live[0].iface
    pol = BENCH.reset_active_low(case, iface.reset)  # spec text overrides the name-based guess
    if pol is not None:
        iface.reset_active_low = pol
    res["iface"] = {"sequential": iface.sequential, "clock": iface.clock, "reset": iface.reset,
                    "reset_active_low": iface.reset_active_low,
                    "inputs": [(p.name, p.width) for p in iface.inputs],
                    "outputs": [(p.name, p.width) for p in iface.outputs]}
    if len(live) < 2:
        return {**res, "status": "single_candidate", "n_live": len(live)}
    try:
        vvp = ds.build_harness(live, iface, work / "h", BENCH.params(case))
    except Exception as e:  # noqa: BLE001
        return {**res, "status": "harness_error", "error": str(e)[-400:]}
    # stimulus suite
    suite: list[tuple[str, list[list[int]]]] = []
    ex = ds.exhaustive_comb(iface)
    if ex is not None:
        suite.append(("exhaustive", ex))
    else:
        for prof in ds.PROFILES:
            for s in range(seeds):
                n = cycles if iface.sequential else max(cycles, 512)
                suite.append((f"{prof}{s}", ds.gen_stimulus(iface, prof, n, 1000 * s + ds.PROFILES.index(prof))))
        if iface.sequential and HI:
            # inputs changing while the clock is HIGH (latch / dual-edge behaviour); search only
            suite.append((HI_SUITE, ds.gen_stimulus(iface, "uniform", cycles, 4242)))
            # long-horizon run last, so short divergences are preferred
            suite.append((f"dense{LONG_SEED}", ds.gen_stimulus(iface, "dense", LONG_CYCLES,
                                                              1000 * LONG_SEED + ds.PROFILES.index("dense"))))
    n = len(live)
    traces = {c.cid: [] for c in live}
    first_div: dict[tuple[int, int], tuple[int, int]] = {}  # (i,j) -> (suite idx, sample idx)
    sims_failed = 0
    for si, (name, rows) in enumerate(suite):
        samples = ds.simulate(vvp, iface, rows, f"suite{si}", hi=(name == HI_SUITE))
        if samples is None or len(samples) == 0:
            sims_failed += 1
            continue
        st0 = ds.start_index(iface)
        for i, c in enumerate(live):
            traces[c.cid].append(ds.trace_hash(samples, i, st0))
        for i, j in combinations(range(n), 2):
            if (i, j) not in first_div:
                k = ds.first_divergence(samples, i, j, st0)
                if k is not None:
                    first_div[(i, j)] = (si, k, samples[k][i], samples[k][j])
    res["sims_failed"] = sims_failed
    parts = ds.partition({cid: "|".join(h) for cid, h in traces.items()})
    res["clusters"] = parts
    # ---- scoring against hidden ground truth
    off = official_cluster_of(r)
    idx = {c.cid: i for i, c in enumerate(live)}
    split = lambda a, b: (min(idx[a], idx[b]), max(idx[a], idx[b])) in first_div  # noqa: E731
    corr = {c.cid: c.meta["correct"] for c in live}
    ci_pairs = [(a, b) for a, b in combinations(corr, 2) if corr[a] != corr[b]]
    off_pairs = [(a, b) for a, b in combinations(corr, 2) if off.get(a) != off.get(b)]
    same_pairs = [(a, b) for a, b in combinations(corr, 2) if off.get(a) == off.get(b)]
    res["ci_pairs"] = len(ci_pairs)
    res["ci_found"] = sum(split(a, b) for a, b in ci_pairs)
    res["ci_missed"] = [(a, b) for a, b in ci_pairs if not split(a, b)]
    res["off_pairs"] = len(off_pairs)
    res["off_found"] = sum(split(a, b) for a, b in off_pairs)
    extra = [(a, b) for a, b in same_pairs if split(a, b)]
    res["extra_splits"] = len(extra)
    res["extra_x"] = sum(ds.x_involved(*first_div[(min(idx[a], idx[b]), max(idx[a], idx[b]))][2:])
                         for a, b in extra)
    # does each our-cluster have pure correctness?
    res["impure_clusters"] = sum(1 for p in parts if len({corr[m] for m in p}) > 1)
    # ---- minimise one trace per pair of cluster representatives
    mins = []
    if do_min:
        reps = [p[0] for p in parts]
        for a, b in combinations(reps, 2):
            i, j = sorted((idx[a], idx[b]))
            si, k, va, vb = first_div[(i, j)]
            rows = suite[si][1]
            cyc, _ = ds.sample_index_to_cycle(k, iface)
            if suite[si][0] == HI_SUITE:  # clock-high timing: not minimised, not turned into a question
                stim = rows[: cyc + 1]
                st = {"ok": True, "calls": 0, "orig_len": cyc + 1, "min_len": cyc + 1, "toggles": None,
                      "hi_phase": True}
            elif cyc + 1 > MIN_LIMIT:
                stim = rows[: cyc + 1]
                st = {"ok": True, "calls": 0, "orig_len": cyc + 1, "min_len": cyc + 1, "toggles": None,
                      "long_horizon": True}
            else:
                stim, st = ds.minimise(vvp, iface, rows[: cyc + 1], i, j)
            mins.append({"pair": [live[i].cid, live[j].cid],
                         "correct": [corr[live[i].cid], corr[live[j].cid]],
                         "x_involved": ds.x_involved(va, vb), "orig_cycle": cyc,
                         "suite": suite[si][0],
                         "stim": stim, **st})
    res["minimised"] = mins
    res["status"] = "ok"
    res["n_live"] = n
    ds.clean(work)
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="*")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--cycles", type=int, default=256)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--no-min", action="store_true")
    a = ap.parse_args()
    files = case_files(POOL)
    if a.cases:
        files = [f for f in files if any(f.name.startswith(c) for c in a.cases)]
    OUT.mkdir(exist_ok=True)
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(run_case, f, a.cycles, a.seeds, not a.no_min): f for f in files}
        for fu in cf.as_completed(futs):
            f = futs[fu]
            try:
                res = fu.result()
            except Exception as e:  # noqa: BLE001
                res = {"case": f.stem, "status": "crash", "error": repr(e)}
            (OUT / f"{res['case']}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
            print(res["case"], res.get("status"), f"ci {res.get('ci_found')}/{res.get('ci_pairs')}",
                  f"off {res.get('off_found')}/{res.get('off_pairs')}", f"extra {res.get('extra_splits')}",
                  flush=True)


if __name__ == "__main__":
    main()
