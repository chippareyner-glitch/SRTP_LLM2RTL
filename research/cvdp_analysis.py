"""Offline analysis of the CVDP cid003 pool (no API): failure patterns, difficulty, diversity.

Usage: python -I -X utf8 cvdp_analysis.py [--tag cvdp_ds41] [--ids cvdp_ds41_ids]
Writes research/cvdp_analysis.json and prints a report.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
sys.path.insert(0, str(RESEARCH))
from bench import Bench, cvdp_tasks  # noqa: E402

SAMPLES = 5


def family(task_id: str) -> str:
    return re.sub(r"^cvdp_copilot_|_\d{4}$", "", task_id)


def pytest_instances(workdir: str) -> tuple[int, int]:
    """(instances, failed) from the pytest JUnit file: one instance per parameter set."""
    f = Path(workdir) / "pytest-results.xml"
    if not f.exists():
        return 0, 0
    try:
        tests = list(ET.parse(f).getroot().iter("testcase"))
    except ET.ParseError:
        return 0, 0
    failed = sum(t.find("failure") is not None or t.find("error") is not None for t in tests)
    return len(tests), failed


def compile_reason(code_path: str, top: str) -> str:
    """Re-run Icarus on the candidate (cocotb's runner does not keep iverilog's stderr)."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = subprocess.run([r"D:\iverilog\bin\iverilog.exe", "-g2012", "-s", top, "-o", str(Path(d) / "x.vvp"),
                            code_path], capture_output=True, text=True, encoding="utf-8", errors="replace")
    log = p.stdout + p.stderr
    if p.returncode == 0:
        return "compiles standalone (fails only inside the harness)"
    if "Unable to find the root module" in log:
        return "top module name differs from harness TOPLEVEL"
    lines = [l.strip() for l in log.splitlines()
             if re.search(r"\.s?v:\d+: (error|sorry)|syntax error|Unknown module|Unable to bind|sorry:", l)]
    if not lines:
        return "other (no iverilog message)"
    l = lines[0]
    if "sorry" in l:
        return "icarus unsupported: " + re.sub(r".*sorry:\s*", "", l)[:70]
    if "syntax error" in l:
        return "syntax error"
    m = re.search(r"error:\s*(.*)", l)
    msg = m.group(1) if m else l
    msg = re.sub(r"`[^`]*`|'[^']*'|\b\w+\.\w+\b", "<x>", msg)
    return "error: " + msg[:70]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="cvdp_ds41")
    ap.add_argument("--ids", default="cvdp_ds41_ids")
    a = ap.parse_args()
    tasks = cvdp_tasks()
    b = Bench("cvdp")
    pools = RESEARCH / "pools"
    pool = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (pools / a.tag / "out").glob("*.json")}
    p1 = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in
          (RESEARCH / "askrtl" / f"out_phase1_{a.tag}").glob("*.json") if f.stem != "summary"}
    amb = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (pools / a.ids / "ambiguities").glob("*.json")}
    pool_ids = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (pools / a.ids / "out").glob("*.json")}
    rows = []
    status_w = Counter()
    comp = Counter()
    partial = []
    for tid in b.cases():
        t = tasks[tid]
        r = pool.get(tid, {"candidates": [], "n_samples": 0})
        cands = r["candidates"]
        n = sum(len(c["sources"]) for c in cands)
        status_w["missing (not generated)"] += SAMPLES - n
        for c in cands:
            s = c["gold"]["status"]
            status_w[s] += len(c["sources"])
            if s == "compile_error":
                comp[compile_reason(c["path"], t["_top"])] += len(c["sources"])
            if s == "functional_failed":
                inst, fail = pytest_instances(c["gold"].get("workdir", ""))
                if inst > 1 and 0 < fail < inst:
                    partial.append((tid, c["id"], inst, fail))
        correct_w = sum(len(c["sources"]) for c in cands if c["correct"])
        r1 = p1.get(tid, {})
        clusters = r1.get("clusters", []) if r1.get("status") == "ok" else []
        by = {c["id"]: c for c in cands}
        # classify the behavioural situation of the task
        if n == 0:
            kind = "no sample generated"
        elif not any(c["compiles"] for c in cands):
            kind = "nothing compiles"
        elif not clusters:
            kind = "single behaviour (unanalysable)" if r1.get("status") != "ok" else "?"
        elif len(clusters) == 1:
            kind = "unanimous correct" if all(by[m]["correct"] for m in clusters[0]) else "unanimous wrong"
        else:
            votes = [sum(len(by[m]["sources"]) for m in cl) for cl in clusters]
            good = [all(by[m]["correct"] for m in cl) for cl in clusters]
            top = max(range(len(clusters)), key=lambda i: votes[i])
            if not any(good):
                kind = "divergent, no correct"
            elif good[top] and votes.count(votes[top]) == 1:
                kind = "divergent, majority correct"
            else:
                kind = "divergent, correct minority/tie"
        rows.append({"task": tid, "family": family(tid), "difficulty": t["categories"][1],
                     "spec_chars": len(t["input"]["prompt"]), "samples": n, "distinct": len(cands),
                     "clusters": len(clusters), "pass1": correct_w / SAMPLES,
                     "any": any(c["correct"] for c in cands), "kind": kind,
                     "ambiguities": len(amb.get(tid, {}).get("ambiguities", [])),
                     "ids_any": any(c["correct"] for c in pool_ids.get(tid, {}).get("candidates", []))})
    N = len(rows)
    print(f"=== CVDP cid003: {N} tasks, {N * SAMPLES} requested samples")
    print("sample outcomes:", {k: f"{v} ({v / (N * SAMPLES):.0%})" for k, v in status_w.most_common()})
    print("\ncompile-error causes (weighted by samples):")
    for k, v in comp.most_common(12):
        print(f"  {v:>3}  {k}")
    ff = status_w["functional_failed"]
    print(f"\nfunctional failures that pass SOME parameter instances: {len(partial)} distinct candidates "
          f"(of {sum(1 for r in pool.values() for c in r['candidates'] if c['gold']['status'] == 'functional_failed')})")
    for p in partial[:12]:
        print(f"   {p[0]} {p[1]}: failed {p[3]}/{p[2]} instances")
    print("\nby difficulty:")
    for d in ("easy", "medium"):
        rs = [r for r in rows if r["difficulty"] == d]
        print(f"  {d:<7} n={len(rs):<3} pass@1={st.mean(r['pass1'] for r in rs):.3f}  "
              f"pass@any={sum(r['any'] for r in rs) / len(rs):.3f}")
    print("\nby spec length (quartiles):")
    qs = sorted(rows, key=lambda r: r["spec_chars"])
    for i in range(4):
        part = qs[i * N // 4:(i + 1) * N // 4]
        print(f"  Q{i + 1} chars {part[0]['spec_chars']:>5}-{part[-1]['spec_chars']:<5} "
              f"pass@1={st.mean(r['pass1'] for r in part):.3f} pass@any={sum(r['any'] for r in part) / len(part):.3f} "
              f"missing samples={sum(SAMPLES - r['samples'] for r in part)}")
    print("\nbehavioural situation per task:")
    for k, v in Counter(r["kind"] for r in rows).most_common():
        ex = [r["task"].replace("cvdp_copilot_", "") for r in rows if r["kind"] == k][:6]
        print(f"  {v:>3}  {k:<34} e.g. {ex}")
    fam = defaultdict(list)
    for r in rows:
        fam[r["family"]].append(r)
    multi = {k: v for k, v in fam.items() if len(v) > 1}
    print(f"\nfamilies with >1 task: {len(multi)}; tasks in them: {sum(len(v) for v in multi.values())}")
    for k, v in sorted(multi.items(), key=lambda kv: st.mean(r['pass1'] for r in kv[1])):
        print(f"  {k:<28} tasks={len(v)} pass@1={st.mean(r['pass1'] for r in v):.2f}")
    print("\ndistinct behaviours per task (where analysable):",
          dict(Counter(r["clusters"] for r in rows if r["clusters"])))
    low = [r for r in rows if r["samples"] and r["pass1"] == 0]
    print(f"\ntasks with 0 correct samples (generated): {len(low)} -> kinds {dict(Counter(r['kind'] for r in low))}")
    amb_corr = st.correlation([r["ambiguities"] for r in rows], [r["pass1"] for r in rows])
    len_corr = st.correlation([r["spec_chars"] for r in rows], [r["pass1"] for r in rows])
    print(f"\ncorrelation(pass@1, #listed ambiguities) = {amb_corr:+.2f};  correlation(pass@1, spec length) = {len_corr:+.2f}")
    gained = [r["task"] for r in rows if r["ids_any"] and not r["any"]]
    print(f"partial IDS: tasks gaining a correct candidate: {gained}")
    (RESEARCH / "cvdp_analysis.json").write_text(json.dumps({"rows": rows, "status": status_w, "compile": comp,
                                                             "partial": partial}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
