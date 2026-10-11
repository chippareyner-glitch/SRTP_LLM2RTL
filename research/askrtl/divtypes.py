"""Classify behavioural divergences between candidate clusters (no API).

For every pair of Phase 1 clusters in a problem we re-simulate the cluster representatives on
the full Phase 1 stimulus suite and label the pair by the *kind* of difference:

  init     - every divergent sample has X/Z on one side (uninitialised state / initial value)
  latency  - one trace equals the other shifted by a constant 1/2 or 1 cycle (registered vs
             combinational output, extra pipeline stage)
  reset    - all divergent samples fall in a reset cycle or the cycle right after one
             (behaviour of state during / just after reset)
  value    - anything else (a genuine functional difference)

The first three are "convention" differences: the spec usually leaves them implicit.
Correctness (from the pilot) is used only to report which pairs separate a correct cluster
from an incorrect one.  Writes out_phase1/divtypes.json.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diffsim as ds  # noqa: E402
from queries import suite_rows  # noqa: E402

POOL = HERE.parent / "pilot_pool" / "out"
P1 = HERE / "out_phase1"
SHIFTS = (1, 2, -1, -2)  # in samples; sequential designs have 2 samples per cycle


def has_x(v: str) -> bool:
    return any(c in "xz" for c in v)


def classify(runs: list[tuple[list[list[int]], list[list[str]]]], i: int, j: int,
             iface: ds.Interface, quiet_runs: list | None = None) -> str:
    st0 = ds.start_index(iface)
    div = []  # (run, sample)
    for r, (_, smp) in enumerate(runs):
        for k in range(st0, len(smp)):
            if smp[k][i] != smp[k][j]:
                div.append((r, k))
    if not div:
        return "equal"
    if all(has_x(runs[r][1][k][i]) or has_x(runs[r][1][k][j]) for r, k in div):
        return "init"
    if iface.sequential:
        for d in SHIFTS:
            ok = True
            for _, smp in runs:
                a = [s[i] for s in smp[st0:]]
                b = [s[j] for s in smp[st0:]]
                if d > 0 and any(a[k] != b[k + d] for k in range(4, len(a) - d)):
                    ok = False
                    break
                if d < 0 and any(a[k - d] != b[k] for k in range(4, len(b) + d)):
                    ok = False
                    break
            if ok:
                return "latency"
        if quiet_runs is not None:
            # causal test: identical when other inputs are held at 0 while reset is asserted
            if all(smp[k][i] == smp[k][j] for _, smp in quiet_runs for k in range(st0, len(smp))):
                return "reset"
    return "value"


def quiet_during_reset(rows: list[list[int]], iface: ds.Interface) -> list[list[int]]:
    q = [p.name for p in iface.inputs].index(iface.reset)
    active = int(not iface.reset_active_low)
    return [[v if (n == q or r[q] != active) else 0 for n, v in enumerate(r)] for r in rows]


def run_case(f: Path) -> dict | None:
    p1 = json.loads(f.read_text(encoding="utf-8"))
    if p1.get("status") != "ok" or len(p1["clusters"]) < 2:
        return None
    pool = json.loads((POOL / f.name).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in pool["candidates"]}
    reps = [cl[0] for cl in p1["clusters"]]
    cands = [ds.Candidate(c, Path(by_id[c]["path"]).read_text(encoding="utf-8", errors="replace")) for c in reps]
    work = ds.scratch_root() / f"dt_{p1['case']}"
    ds.clean(work)
    iface = ds.extract_interface(cands[0].code, work / "if")
    vvp = ds.build_harness(cands, iface, work / "h")
    names = sorted({m["suite"] for m in p1["minimised"] if m.get("suite")})
    if not names:  # combinational problems use the single exhaustive / random runs
        names = ["exhaustive"] if ds.exhaustive_comb(iface) is not None else ["uniform0", "sparse0", "dense0"]
    runs = []
    for n in names:
        rows = suite_rows(iface, n)
        if iface.sequential and len(rows) > 4000:  # long run: the prefix is enough to type the divergence
            rows = rows[:4000]
        smp = ds.simulate(vvp, iface, rows, n)
        if smp:
            runs.append((rows, smp))
    quiet = None
    if iface.sequential and iface.reset:
        quiet = []
        for k, (rows, _) in enumerate(runs):
            qr = quiet_during_reset(rows, iface)
            smp = ds.simulate(vvp, iface, qr, f"quiet{k}")
            if smp:
                quiet.append((qr, smp))
    out = []
    for i, j in combinations(range(len(reps)), 2):
        ci = all(by_id[m]["correct"] for m in p1["clusters"][i])
        cj = all(by_id[m]["correct"] for m in p1["clusters"][j])
        out.append({"pair": [reps[i], reps[j]], "correct": [ci, cj],
                    "type": classify(runs, i, j, iface, quiet)})
    ds.clean(work)
    return {"case": p1["case"], "sequential": iface.sequential, "pairs": out}


def main() -> None:
    files = sorted(P1.glob("Prob*.json"))
    res = []
    with cf.ThreadPoolExecutor(8) as ex:
        for r in ex.map(run_case, files):
            if r:
                res.append(r)
    (P1 / "divtypes.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    ci = Counter()
    per_wrong = defaultdict(set)  # wrong cluster -> its difference types vs correct clusters
    for r in res:
        for p in r["pairs"]:
            if p["correct"][0] != p["correct"][1]:
                ci[p["type"]] += 1
                wrong = p["pair"][0] if not p["correct"][0] else p["pair"][1]
                per_wrong[(r["case"], wrong)].add(p["type"])
    allp = Counter(p["type"] for r in res for p in r["pairs"])
    print("all cluster pairs:", dict(allp))
    print("correct-vs-incorrect pairs:", dict(ci), f"convention share = "
          f"{sum(ci[t] for t in ('init', 'latency', 'reset')) / max(sum(ci.values()), 1):.2f}")
    only_conv = [k for k, v in per_wrong.items() if v <= {"init", "latency", "reset"}]
    print(f"wrong clusters whose ONLY difference from a correct cluster is a convention: "
          f"{len(only_conv)}/{len(per_wrong)}")
    for k in sorted(only_conv):
        print("  ", k, sorted(per_wrong[k]))


if __name__ == "__main__":
    main()
