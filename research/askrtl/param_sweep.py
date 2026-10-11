"""Parameter-space differential testing (no API, no reference, no test files).

For each task whose candidates declare integer parameters, build up to 5 parameter settings from
the candidates' own defaults (default; each of the first 2 parameters doubled and halved), run the
reference-free simulation suite at every setting, and partition candidates by their traces across
all settings.  Compared with default-only partitioning (Phase 1) on:
  * correct-vs-incorrect pair separation (ground truth = official tests, evaluation only),
  * false splits between two correct candidates.

Usage: python -I -X utf8 param_sweep.py   (ASKRTL_TAG / ASKRTL_BENCH select the pool)
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diffsim as ds  # noqa: E402
from paths import BENCH, POOL, TAG, case_files  # noqa: E402

PARAM_RE = re.compile(r"\bparameter\s+(?:int(?:eger)?\s+|unsigned\s+|logic\s+(?:\[[^\]]*\]\s*)?)?(\w+)\s*=\s*(\d+)\b")


def top_params(code: str) -> dict[str, int]:
    m = re.search(r"\bmodule\s+TopModule\b(.*?)(\)\s*;)", ds.strip_comments(code), flags=re.S)
    header = m.group(1) if m else ""
    return {k: int(v) for k, v in PARAM_RE.findall(header)}


def settings(cands: list[ds.Candidate]) -> list[dict[str, str]]:
    votes = Counter()
    for c in cands:
        for k, v in top_params(c.code).items():
            votes[(k, v)] += 1
    common = {}
    for (k, v), n in votes.most_common():
        if k not in common and n * 2 > len(cands):  # parameter (and default) shared by a majority
            common[k] = v
    out = [{}]
    for k, v in list(common.items())[:2]:
        for nv in (v * 2, max(1, v // 2)):
            if nv != v:
                out.append({k: str(nv)})
    return out[:5]


def traces(cands: list[ds.Candidate], case: str, params: dict[str, str], work: Path) -> dict[str, str]:
    """Trace signature per candidate at one parameter setting (candidates that fail to elaborate drop out)."""
    full = {**BENCH.params(case), **params}
    ok = []
    for c in cands:
        try:
            c.iface = ds.extract_interface(c.code, work / f"if_{c.cid}", full)
            ok.append(c)
        except Exception:  # noqa: BLE001
            continue
    if len(ok) < 2:
        return {}
    sig = Counter(c.iface.ports for c in ok).most_common(1)[0][0]
    live = [c for c in ok if c.iface.ports == sig]
    iface = live[0].iface
    pol = BENCH.reset_active_low(case, iface.reset)
    if pol is not None:
        iface.reset_active_low = pol
    try:
        vvp = ds.build_harness(live, iface, work / "h", full)
    except Exception:  # noqa: BLE001
        return {}
    st0 = ds.start_index(iface)
    hashes = {c.cid: [] for c in live}
    for si, prof in enumerate(ds.PROFILES):
        rows = ds.gen_stimulus(iface, prof, 256 if iface.sequential else 512, 7000 + si)
        smp = ds.simulate(vvp, iface, rows, f"s{si}")
        if not smp:
            continue
        for i, c in enumerate(live):
            hashes[c.cid].append(ds.trace_hash(smp, i, st0))
    return {cid: "|".join(h) for cid, h in hashes.items()}


def run_case(f: Path) -> dict | None:
    r = json.loads(f.read_text(encoding="utf-8"))
    cands = [ds.Candidate(c["id"], BENCH.to_top(Path(c["path"]).read_text(encoding="utf-8", errors="replace"), r["case"]),
                          {"correct": c["correct"]}) for c in r["candidates"] if c.get("compiles")]
    if len(cands) < 2:
        return None
    sets = settings(cands)
    if len(sets) < 2:
        return None
    work = ds.scratch_root() / f"ps_{TAG}_{r['case']}"
    per_setting = []
    for i, p in enumerate(sets):
        per_setting.append(traces(cands, r["case"], p, work / f"p{i}"))
    ds.clean(work)
    corr = {c.cid: c.meta["correct"] for c in cands}

    def split(a: str, b: str, use: list[dict]) -> bool:
        return any(a in t and b in t and t[a] != t[b] for t in use)
    res = {"case": r["case"], "settings": sets}
    for name, use in (("default", per_setting[:1]), ("sweep", per_setting)):
        ci = [(a, b) for a, b in combinations(corr, 2) if corr[a] != corr[b]]
        cc = [(a, b) for a, b in combinations(corr, 2) if corr[a] and corr[b]]
        res[name] = {"ci_pairs": len(ci), "ci_split": sum(split(a, b, use) for a, b in ci),
                     "cc_pairs": len(cc), "cc_split": sum(split(a, b, use) for a, b in cc)}
    return res


def main() -> None:
    files = case_files(POOL)
    rows = []
    with cf.ThreadPoolExecutor(6) as ex:
        for res in ex.map(run_case, files):
            if res:
                rows.append(res)
    (HERE / f"param_sweep_{TAG}.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"{TAG}: tasks with >=2 compiling candidates and sweepable parameters: {len(rows)}")
    for name in ("default", "sweep"):
        ci = sum(r[name]["ci_pairs"] for r in rows)
        cis = sum(r[name]["ci_split"] for r in rows)
        cc = sum(r[name]["cc_pairs"] for r in rows)
        ccs = sum(r[name]["cc_split"] for r in rows)
        print(f"  {name:<8} correct-vs-incorrect separated {cis}/{ci}   correct-vs-correct split (false alarm) {ccs}/{cc}")
    gained = [(r["case"], r["sweep"]["ci_split"] - r["default"]["ci_split"]) for r in rows
              if r["sweep"]["ci_split"] > r["default"]["ci_split"]]
    print("  tasks where the sweep separates more correct/incorrect pairs:", gained)


if __name__ == "__main__":
    main()
