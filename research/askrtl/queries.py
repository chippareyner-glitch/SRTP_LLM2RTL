"""Build disambiguation queries from Phase 1 traces (+ hidden ground-truth labels).

A query = (spec, minimal stimulus, shared output history, options at the divergence sample).
Each behaviour cluster maps to the option it would produce, or to "other" if its history
differs from the displayed one.  The reference model is simulated *only* to label the
query for evaluation (which option(s) the spec's ground truth produces); the label is
never shown to any method.

Writes out_queries/<case>.json with rendered question text, cluster->option maps and labels.
Usage: python -I queries.py [--cases ...] [--jobs 8]
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import diffsim as ds  # noqa: E402

from paths import BENCH, P1, POOL, QDIR as OUT, case_files  # noqa: E402

LETTERS = "ABCDEFGH"
MAX_ROWS, TAIL_ROWS = 40, 16  # traces longer than MAX_ROWS are shown as their last TAIL_ROWS cycles
LONG_SEED, LONG_CYCLES = 9, 60000  # must match phase1_eval


def split_outputs(bits: str, outs: list[tuple[str, int]]) -> dict[str, str]:
    res, pos = {}, 0
    for name, w in outs:
        res[name] = bits[pos:pos + w]
        pos += w
    return res


def fmt_val(b: str) -> str:
    if len(b) <= 4 or any(ch in "xz" for ch in b):
        return f"{len(b)}'b{b}"
    return f"{len(b)}'h{int(b, 2):0{(len(b) + 3) // 4}x}"


def ref_matches(ref: str, val: str) -> bool:
    """Official-testbench semantics: X/Z in the reference matches anything."""
    return all(r in "xz" or r == v for r, v in zip(ref, val))


def render(spec: str, iface: dict, stim: list[list[int]], hist: list[str], k: int,
           options: list[str]) -> str:
    seq = iface["sequential"]
    ins = [n for n, _ in iface["inputs"]]
    widths = dict(iface["inputs"])
    outs = iface["outputs"]
    lines = []
    if seq:
        lines.append(f"Clock: `{iface['clock']}` (rising-edge). Each row is one clock cycle. Inputs are "
                     "applied at the start of the cycle and held until the next cycle. "
                     "`pre` = output values just BEFORE the rising edge of that cycle; "
                     "`post` = output values just AFTER that rising edge. Note: outputs may depend "
                     "combinationally on the inputs (e.g. Mealy outputs), so a `post` value reflects the state "
                     "AFTER the edge combined with the inputs of the SAME row, which are still applied.")
    else:
        lines.append("Combinational test: each row is one independent input vector; "
                     "`out` is the settled output value.")
    lines.append("")
    hdr = ["cycle" if seq else "row"] + ins + (["pre", "post"] if seq else ["out"])
    lines.append("| " + " | ".join(hdr) + " |")
    lines.append("|" + "---|" * len(hdr))
    per_row = 2 if seq else 1
    first = 0
    if len(stim) > MAX_ROWS:  # long-horizon divergence: show only the final window
        first = len(stim) - TAIL_ROWS
        lines.append(f"| ... | *cycles 0-{first - 1} omitted ({first} cycles; all candidates produced identical "
                     f"outputs there; the outputs in the next row summarise the state reached)* |")
    for t, row in enumerate(stim):
        if t < first:
            continue
        cells = [str(t)] + [fmt_val(format(v, f"0{widths[n]}b")) for n, v in zip(ins, row)]
        for ph in range(per_row):
            idx = t * per_row + ph
            if idx < k:
                cells.append(", ".join(f"{n}={fmt_val(b)}" for n, b in split_outputs(hist[idx], outs).items()))
            elif idx == k:
                cells.append("**?**")
            else:
                cells.append("")
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(f"At the cell marked **?** the candidate implementations disagree. Options:")
    for L, v in zip(LETTERS, options):
        lines.append(f"- **{L}**: " + ", ".join(f"{n}={fmt_val(b)}" for n, b in split_outputs(v, outs).items()))
    table = "\n".join(lines)
    return (f"## Specification\n\n{spec.strip()}\n\n## Concrete scenario\n\n{table}\n")


def suite_rows(iface: "ds.Interface", name: str, cycles: int = 256) -> list[list[int]]:
    """Regenerate the Phase 1 stimulus run `name` (deterministic seeds, see phase1_eval)."""
    if name == "exhaustive":
        return ds.exhaustive_comb(iface)
    prof, s = name.rstrip("0123456789"), int(name[len(name.rstrip("0123456789")):])
    n = cycles if iface.sequential else max(cycles, 512)
    if iface.sequential and s == LONG_SEED:
        n = LONG_CYCLES
    return ds.gen_stimulus(iface, prof, n, 1000 * s + ds.PROFILES.index(prof))


def render_long(spec: str, iface: dict, stim: list[list[int]], outs_a: list[str], outs_b: list[str],
                st0: int, first_cycle: int = 0) -> str:
    """SpecLens-style: show two complete output traces and ask which one the spec allows."""
    seq = iface["sequential"]
    ins = [n for n, _ in iface["inputs"]]
    widths = dict(iface["inputs"])
    outs = iface["outputs"]
    per = 2 if seq else 1
    hdr = ["cycle" if seq else "row"] + ins + (["A pre", "A post", "B pre", "B post"] if seq else ["A out", "B out"])
    lines = []
    if seq:
        lines.append(f"Clock: `{iface['clock']}` (rising-edge). Each row is one clock cycle. Inputs are applied at "
                     "the start of the cycle and held until the next cycle. `pre` = outputs just BEFORE the "
                     "rising edge of that cycle; `post` = outputs just AFTER it.")
    else:
        lines.append("Combinational test: each row is one independent input vector.")
    lines += ["", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
    if first_cycle and seq:
        lines.append(f"| ... | *cycles 0-{first_cycle - 1} omitted ({first_cycle} cycles; both traces were "
                     "identical there)* |")

    def cell(v: str, idx: int) -> str:
        if idx < st0:
            return "-"
        return ", ".join(f"{n}={fmt_val(b)}" for n, b in split_outputs(v, outs).items())
    for t, row in enumerate(stim):
        cells = [str(t + first_cycle)] + [fmt_val(format(v, f"0{widths[n]}b")) for n, v in zip(ins, row)]
        for trace in (outs_a, outs_b):
            for ph in range(per):
                cells.append(cell(trace[t * per + ph], t * per + ph))
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "Two candidate implementations produced output traces A and B for the same inputs. "
              "Options: **A** = trace A is the correct behaviour, **B** = trace B is."]
    return f"## Specification\n\n{spec.strip()}\n\n## Concrete scenario\n\n" + "\n".join(lines) + "\n"


def build_case(case: str) -> dict:
    p1 = json.loads((P1 / f"{case}.json").read_text(encoding="utf-8"))
    if p1.get("status") != "ok" or len(p1["clusters"]) < 2:
        return {"case": case, "status": "no_divergence"}
    pool = json.loads((POOL / f"{case}.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in pool["candidates"]}
    reps = [cl[0] for cl in p1["clusters"]]
    spec = BENCH.spec(case)
    ref_code = BENCH.ref_as_top(case)
    cands = [ds.Candidate(cid, BENCH.to_top(Path(by_id[cid]["path"]).read_text(encoding="utf-8", errors="replace"),
                                            case)) for cid in reps]
    has_ref = ref_code is not None  # CVDP withholds references: questions are built but left unlabelled
    if has_ref:
        cands.append(ds.Candidate("ref", ref_code))  # last index; used only for labels
    work = ds.scratch_root() / f"q_{case}"
    ds.clean(work)
    iface = ds.extract_interface(cands[0].code, work / "if", BENCH.params(case))
    pol = BENCH.reset_active_low(case, iface.reset)  # must match phase1_eval's stimulus convention
    if pol is not None:
        iface.reset_active_low = pol
    vvp = ds.build_harness(cands, iface, work / "h", BENCH.params(case))
    st0 = ds.start_index(iface)
    queries = []
    for m in p1["minimised"]:
        if not m.get("ok") or m.get("hi_phase"):  # clock-high divergences cannot be rendered as questions
            continue
        a, b = m["pair"]
        if a not in reps or b not in reps:
            continue
        ia, ib = reps.index(a), reps.index(b)
        samples = ds.simulate(vvp, iface, m["stim"], "q")
        if not samples:
            continue
        k = ds.first_divergence(samples, ia, ib, st0)
        if k is None:
            continue
        hist = [s[ia] for s in samples[:k]]
        options = [samples[k][ia], samples[k][ib]]
        cmap = {}
        for ci, cid in enumerate(reps):
            same_hist = all(samples[t][ci] == hist[t] for t in range(st0, k))
            if not same_hist:
                cmap[cid] = "other"
                continue
            v = samples[k][ci]
            if v not in options:
                options.append(v)
            cmap[cid] = LETTERS[options.index(v)]
        ref = samples[k][-1] if has_ref else ""
        ref_hist_ok = has_ref and all(ref_matches(samples[t][-1], hist[t]) for t in range(st0, k))
        match = [LETTERS[i] for i, v in enumerate(options) if has_ref and ref_matches(ref, v)]
        if not has_ref:
            label = "UNKNOWN"
        elif not ref_hist_ok:
            label = "NONE"  # the displayed history itself contradicts the reference
        elif len(match) == 0:
            label = "NONE"
        elif len(match) == 1:
            label = match[0]
        else:
            label = "ANY:" + "".join(match)
        long = None
        if m.get("suite") and has_ref:
            rows = suite_rows(iface, m["suite"])
            per = 2 if iface.sequential else 1
            div_c = m["orig_cycle"]
            if iface.sequential:  # simulate from cycle 0; show at most the last 32 cycles
                hi = max(32, div_c + 1)
                lo = max(0, hi - 32)
            else:  # window of 24 vectors ending at the divergence row
                lo, hi = max(0, div_c - 23), div_c + 1
            sim_from = 0 if iface.sequential else lo
            ls = ds.simulate(vvp, iface, rows[sim_from:hi], "long")
            if ls:
                ok_a = all(ref_matches(s[-1], s[ia]) for s in ls[st0:])
                ok_b = all(ref_matches(s[-1], s[ib]) for s in ls[st0:])
                ll = {(True, False): "A", (False, True): "B", (True, True): "ANY:AB"}.get((ok_a, ok_b), "NONE")
                off = (lo - sim_from) * per
                win = rows[lo:hi]
                wa, wb = [s[ia] for s in ls[off:]], [s[ib] for s in ls[off:]]
                w_st0 = st0 if lo == 0 else 0
                long = {"label": ll, "cycles": len(win), "first_cycle": lo, "stim": win, "st0": w_st0,
                        "outs": [wa, wb],
                        "text": render_long(spec, p1["iface"], win, wa, wb, w_st0, lo if iface.sequential else 0)}
        queries.append({
            "long": long,
            "pair": [a, b], "k": k, "len": len(m["stim"]), "toggles": m.get("toggles"),
            "stim": m["stim"], "options": options, "cluster_option": cmap, "label": label,
            "ref_value": ref, "x_involved": m.get("x_involved"), "hist": hist,
            "text": render(spec, p1["iface"], m["stim"][: (k // (2 if iface.sequential else 1)) + 1],
                           hist, k, options),
        })
    ds.clean(work)
    clusters = [{"rep": cl[0], "members": cl,
                 "votes": sum(len(by_id[c]["sources"]) for c in cl),
                 "correct": [by_id[c]["correct"] for c in cl]} for cl in p1["clusters"]]
    return {"case": case, "status": "ok", "iface": p1["iface"], "clusters": clusters, "queries": queries}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", nargs="*")
    ap.add_argument("--jobs", type=int, default=8)
    a = ap.parse_args()
    cases = [f.stem for f in case_files(P1)]
    if a.cases:
        cases = [c for c in cases if any(c.startswith(x) for x in a.cases)]
    OUT.mkdir(exist_ok=True)
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        futs = {ex.submit(build_case, c): c for c in cases}
        for fu in cf.as_completed(futs):
            c = futs[fu]
            try:
                res = fu.result()
            except Exception as e:  # noqa: BLE001
                res = {"case": c, "status": "crash", "error": repr(e)[-500:]}
            (OUT / f"{c}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
            print(c, res["status"], len(res.get("queries", [])), flush=True)


if __name__ == "__main__":
    main()
