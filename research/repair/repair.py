"""Question-guided repair: turn judge answers about minimal disagreements into constraints,
regenerate with them, and use the same constraints as reference-free regression tests.

Steps (DRY-RUN BY DEFAULT for anything that would call the API):
  plan   - for each divergent task, collect constraints from recorded judge answers
           (option letter -> "at cycle k the outputs must be V"); report which questions still
           need a judge answer (run askrtl/online.py first for those).
  gen    - generate M new designs per task with the constraints appended (arm "fresh"), and M
           edits of the cluster representative most consistent with the answers (arm "edit").
  check  - simulate every candidate (old and new) on each constraint trace: a candidate is
           *consistent* if it produces the required value at the constrained sample and the
           agreed history before it.  Then grade with the official tests (evaluation only).
  selftest - validate the constraint checker on existing pools: for answered questions whose
           answer equals the hidden label, correct clusters must pass and the wrong option fail.

Usage (env ASKRTL_TAG / ASKRTL_BENCH select the pool, as for the other scripts):
  python -I -X utf8 repair.py plan     --judge <run_dir> [--cases ...]
  python -I -X utf8 repair.py gen      --judge <run_dir> --out <new_tag> [--m 3] [--live]
  python -I -X utf8 repair.py check    --judge <run_dir> --out <new_tag>
  python -I -X utf8 repair.py selftest --judge <run_dir>
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
sys.path.insert(0, str(RESEARCH))
sys.path.insert(0, str(RESEARCH / "askrtl"))
sys.path.insert(0, str(RESEARCH / "pools"))
import diffsim as ds  # noqa: E402
from paths import BENCH, P1, POOL, QDIR, case_files  # noqa: E402
from queries import LETTERS, fmt_val, split_outputs  # noqa: E402

PROJ = RESEARCH.parent


def load_answers(run: str) -> dict:
    rec = {}
    for name in ("results.jsonl", "online_results.jsonl"):
        f = Path(run) / name
        if f.exists():
            for line in f.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    rec[(r["case"], r["qi"])] = r
    return rec


def constraint_of(q: dict, ans: str) -> dict | None:
    """A decisive judge answer -> constraint {stim, k, value, hist}; ANY/NONE/UNCLEAR -> None."""
    if len(ans) != 1 or ans not in LETTERS[: len(q["options"])]:
        return None
    return {"stim": q["stim"], "k": q["k"], "value": q["options"][LETTERS.index(ans)], "hist": q["hist"],
            "letter": ans, "cluster_option": q["cluster_option"]}


def render_constraint(c: dict, iface: dict, n: int) -> str:
    """Compact human-readable form of a constraint for the generation prompt."""
    seq = iface["sequential"]
    ins = [name for name, _ in iface["inputs"]]
    widths = dict(iface["inputs"])
    per = 2 if seq else 1
    last = c["k"] // per
    rows = []
    for t in range(last + 1):
        cells = ", ".join(f"{nm}={fmt_val(format(v, f'0{widths[nm]}b'))}" for nm, v in zip(ins, c["stim"][t]))
        rows.append(f"  cycle {t}: {cells}" if seq else f"  inputs: {cells}")
    when = ("just after the rising clock edge of cycle" if c["k"] % 2 else "just before the rising clock edge of cycle") \
        if seq else "for"
    outs = ", ".join(f"{nm}={fmt_val(b)}" for nm, b in split_outputs(c["value"], iface["outputs"]).items())
    head = f"Example {n}: apply" + (" (one row per clock cycle; inputs change while the clock is low)" if seq else "")
    return head + ":\n" + "\n".join(rows[-24:]) + f"\n  => required outputs {when} {last}: {outs}" if seq else \
        head + ":\n" + "\n".join(rows) + f"\n  => required outputs: {outs}"


def build_constraints(answers: dict, cases: list[str] | None) -> dict:
    plan = {}
    for f in case_files(QDIR):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("status") != "ok" or (cases and not any(d["case"].startswith(c) for c in cases)):
            continue
        cons, pending = [], []
        for qi, q in enumerate(d["queries"]):
            r = answers.get((d["case"], qi))
            if r is None:
                pending.append(qi)
                continue
            back = r["answer"]
            c = constraint_of(q, back)
            if c:
                c["qi"] = qi
                cons.append(c)
        plan[d["case"]] = {"iface": d["iface"], "constraints": cons, "pending": pending, "clusters": d["clusters"]}
    return plan


def consistent(code: str, case: str, cons: list[dict], iface_d: dict, work: Path) -> list[bool] | None:
    """Simulate one design on each constraint trace; None if it cannot be simulated."""
    try:
        iface = ds.extract_interface(code, work / "if", BENCH.params(case))
        pol = BENCH.reset_active_low(case, iface.reset)
        if pol is not None:
            iface.reset_active_low = pol
        vvp = ds.build_harness([ds.Candidate("x", code)], iface, work / "h", BENCH.params(case))
    except Exception:  # noqa: BLE001
        return None
    st0 = ds.start_index(iface)
    out = []
    for i, c in enumerate(cons):
        s = ds.simulate(vvp, iface, c["stim"], f"c{i}")
        if not s or len(s) <= c["k"]:
            out.append(False)
            continue
        hist_ok = all(s[t][0] == c["hist"][t] for t in range(st0, c["k"]))
        out.append(hist_ok and s[c["k"]][0] == c["value"])
    ds.clean(work)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=("plan", "gen", "check", "selftest"))
    ap.add_argument("--judge", required=True)
    ap.add_argument("--out")
    ap.add_argument("--m", type=int, default=3)
    ap.add_argument("--cases", nargs="*")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    answers = load_answers(a.judge)
    plan = build_constraints(answers, a.cases)
    pool = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in case_files(POOL)}

    if a.step == "plan":
        n_c = sum(len(p["constraints"]) for p in plan.values())
        n_p = sum(len(p["pending"]) for p in plan.values())
        print(f"{len(plan)} divergent tasks; constraints from recorded answers: {n_c}; questions without an answer: {n_p}")
        for case, p in sorted(plan.items()):
            print(f"  {case:<44} constraints={len(p['constraints'])} pending={len(p['pending'])}")
        return

    if a.step == "selftest":
        scratch = ds.scratch_root() / "repair_selftest"
        tot = ok = 0
        for case, p in sorted(plan.items()):
            d = json.loads((QDIR / f"{case}.json").read_text(encoding="utf-8"))
            by = {c["id"]: c for c in pool[case]["candidates"]}
            for c in p["constraints"]:
                q = d["queries"][c["qi"]]
                if answers[(case, c["qi"])]["answer"] != q["label"]:
                    continue  # only judge answers that agree with the reference are ground truth here
                for cl in p["clusters"]:
                    rep = cl["rep"]
                    code = BENCH.to_top(Path(by[rep]["path"]).read_text(encoding="utf-8", errors="replace"), case)
                    res = consistent(code, case, [c], p["iface"], scratch / f"{case}_{rep}")
                    if res is None:
                        continue
                    expected = q["cluster_option"].get(rep) == q["label"]
                    tot += 1
                    ok += res[0] == expected
        print(f"constraint checker agrees with the cluster/option map in {ok}/{tot} checks")
        return

    out = RESEARCH / "pools" / a.out if a.out else None
    if a.step == "gen":
        system = BENCH.system_prompt()
        jobs = []
        for case, p in sorted(plan.items()):
            if not p["constraints"]:
                continue
            uniq, seen = [], set()  # two cluster pairs can yield the same trace and answer
            for c in p["constraints"]:
                key = (json.dumps(c["stim"]), c["k"], c["value"])
                if key not in seen:
                    seen.add(key)
                    uniq.append(c)
            text = "\n\n".join(render_constraint(c, p["iface"], i + 1) for i, c in enumerate(uniq))
            extra = ("\n\nVERIFIED BEHAVIOUR EXAMPLES. The following concrete scenarios were checked against the "
                     "specification; your design must reproduce them exactly (they resolve points where candidate "
                     "implementations disagreed):\n\n" + text)
            # edit arm: start from the cluster representative that satisfies most answered constraints
            best = max(p["clusters"], key=lambda cl: sum(c["cluster_option"].get(cl["rep"]) == c["letter"]
                                                         for c in p["constraints"]))
            by = {c["id"]: c for c in pool[case]["candidates"]}
            base_code = Path(by[best["rep"]]["path"]).read_text(encoding="utf-8", errors="replace")
            # Tell the model the truth about the starting point.  The old text always claimed a disagreement,
            # but the most-consistent representative usually satisfies every example already (VE 13/15 tasks);
            # those false-premise prompts hit the 32K output cap in ~half the calls (36/71 vs 1/12).
            bad = [i + 1 for i, c in enumerate(uniq) if c["cluster_option"].get(best["rep"]) != c["letter"]]
            if bad:
                status = ("It disagrees with example(s) " + ", ".join(map(str, bad)) + ". Fix it so that it meets "
                          "the specification and every example, changing as little as necessary, and return the "
                          "complete corrected RTL:")
            else:
                status = ("It already reproduces every example above but has not been checked against the rest of "
                          "the specification. Fix only genuine deviations from the specification (return it "
                          "unchanged if you find none), and return the complete RTL:")
            for k in range(a.m):
                jobs.append((case, f"r{k}", BENCH.spec(case) + extra))
                jobs.append((case, f"e{k}", BENCH.spec(case) + extra + "\n\nHere is an existing implementation. " +
                             status + "\n```systemverilog\n" + base_code + "\n```"))
        todo = [j for j in jobs if not (out / "gen" / j[0] / f"{j[1]}.sv").exists()]
        chars = sum(len(j[2]) + len(system) for j in todo)
        print(f"{len(todo)} repair generations pending over {len({j[0] for j in todo})} tasks; "
              f"~{chars / 3.5 / 1e3:.0f}K input tokens + reasoning")
        if not a.live:
            (out / "prompts_preview.jsonl").parent.mkdir(parents=True, exist_ok=True)
            with (out / "prompts_preview.jsonl").open("w", encoding="utf-8") as fh:
                for j in todo[:20]:
                    fh.write(json.dumps({"case": j[0], "arm": j[1], "user": j[2]}, ensure_ascii=False) + "\n")
            print(f"dry run: no API calls; first prompts written to {out / 'prompts_preview.jsonl'}")
            return
        sys.path.insert(0, str(PROJ))
        from gen_pool import extract_sv  # noqa: E402
        from llm_client import call_llm  # noqa: E402

        def work(j: tuple[str, str, str]) -> None:
            case, name, user = j
            try:
                reply = call_llm(system, user, case_id=case, reasoning_effort="high", log_dir=str(out / "api_logs"))
                code = extract_sv(reply, BENCH.name != "verilogeval")
                f = out / "gen" / case / f"{name}.sv"
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(code, encoding="utf-8")
            except Exception as e:  # noqa: BLE001
                print("ERR", case, name, str(e)[:80], flush=True)
        with cf.ThreadPoolExecutor(a.workers) as ex:
            list(ex.map(work, todo))
        print("done")
        return

    # check: consistency with constraints (reference-free) + official grading (evaluation only)
    from grade import grade  # noqa: E402
    scratch = ds.scratch_root() / "repair_check"
    rows = []
    for case, p in sorted(plan.items()):
        gdir = out / "gen" / case
        if not p["constraints"] or not gdir.exists():
            continue
        before_any = any(c["correct"] for c in pool[case]["candidates"])
        for f in sorted(gdir.glob("*.sv")):
            code = f.read_text(encoding="utf-8", errors="replace")
            cons = consistent(BENCH.to_top(code, case), case, p["constraints"], p["iface"], scratch / f"{case}_{f.stem}")
            g = grade(BENCH, case, code, f"repair_{case}_{f.stem}")
            rows.append({"case": case, "file": f.stem, "arm": "edit" if f.stem.startswith("e") else "fresh",
                         "constraints_ok": None if cons is None else all(cons), "correct": g["correct"],
                         "before_any": before_any})
    (out / "check.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for arm in ("fresh", "edit"):
        rs = [r for r in rows if r["arm"] == arm]
        if not rs:
            continue
        tasks = {r["case"] for r in rs}
        gained = {r["case"] for r in rs if r["correct"] and not r["before_any"]}
        filt = [r for r in rs if r["constraints_ok"]]
        print(f"{arm:<6} designs={len(rs)} correct={sum(r['correct'] for r in rs)} | tasks={len(tasks)} "
              f"newly solved (no correct candidate before)={len(gained)} {sorted(gained)} | "
              f"constraint-consistent designs={len(filt)}, of which correct={sum(r['correct'] for r in filt)}")


if __name__ == "__main__":
    main()
