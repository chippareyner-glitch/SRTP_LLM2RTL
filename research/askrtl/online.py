"""End-to-end AskRTL evaluation with the *online* Bayesian question policy.

For every divergent problem the policy (per-configuration prior, EIG question choice, assumed
judge accuracy --p, stop at posterior >= tau or after --budget questions) asks questions one at
a time.  A question already answered in the Phase 2a run reuses that recorded answer (a recorded
truncation/API error counts as an abstention); an unanswered question is sent to the live judge,
subject to --max-calls and --max-tokens guards.  Prints final benchmark accuracy vs baselines.

Usage: python -I online.py out_judge/<min_run> [--live --max-calls 24 --max-tokens 500000]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJ = HERE.parents[1]
sys.path.insert(0, str(HERE))
import policy_sim as ps  # noqa: E402
from judge import SYSTEM, build_prompt, parse_answer  # noqa: E402


def to_policy_answer(ans: str, q: dict) -> str:
    if ans == "ANY":
        return "ANY:" + "".join(sorted(set(v for v in q["cluster_option"].values() if v != "other")))
    if ans in ("NONE", "UNCLEAR", "PARSE_ERROR", "API_ERROR") or not ans:
        return "NONE" if ans == "NONE" else "ABSTAIN"
    return ans


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=500_000)
    ap.add_argument("--p", type=float, default=0.8)
    ap.add_argument("--budget", type=int, default=3)
    ap.add_argument("--tau", type=float, default=0.95)
    a = ap.parse_args()
    run = Path(a.run)
    run.mkdir(parents=True, exist_ok=True)
    recorded = {}
    prior = (run / "results.jsonl").read_text(encoding="utf-8") if (run / "results.jsonl").exists() else ""
    for line in prior.splitlines():
        if line.strip():
            r = json.loads(line)
            recorded[(r["case"], r["qi"])] = r["answer"]
    online_f = run / "online_results.jsonl"
    if online_f.exists():  # resume: live answers from an earlier online pass
        for line in online_f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                recorded[(r["case"], r["qi"])] = r["answer"]
    div, base, n = ps.load()
    state = {"calls": 0, "tokens": 0, "blocked": 0, "asked": 0}
    call_llm = None
    if a.live:
        if a.max_calls <= 0:
            sys.exit("--live requires --max-calls > 0")
        sys.path.insert(0, str(PROJ))
        from llm_client import call_llm  # noqa: E402,F811

    def judge_fn(q: dict, p: float, rng: random.Random) -> str:
        key = (q["_case"], q["_qi"])
        state["asked"] += 1
        if key in recorded:
            return to_policy_answer(recorded[key], q)
        if not a.live or state["calls"] >= a.max_calls or state["tokens"] >= a.max_tokens:
            state["blocked"] += 1
            return "ABSTAIN"
        perm = list(range(len(q["options"])))
        random.Random(f"{key[0]}:{key[1]}").shuffle(perm)
        text, back = build_prompt(key[0], q, q["_iface"], perm, "min")
        state["calls"] += 1
        parsed: dict = {}
        try:
            reply, meta = call_llm(SYSTEM, text, case_id=key[0], reasoning_effort="high",
                                   return_metadata=True, log_dir=str(run / "api_logs_online"))
            parsed = parse_answer(reply)
            raw = parsed["answer"]
            state["tokens"] += (meta.get("usage") or {}).get("total_tokens", 0)
        except Exception as e:  # noqa: BLE001 - truncation etc. = abstention
            raw, reply = "API_ERROR", str(e)
            state["tokens"] += 33_000  # a length-capped call still costs the full budget
        ans = back.get(raw, raw)
        recorded[key] = ans
        with online_f.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"case": key[0], "qi": key[1], "answer": ans, "label": q["label"],
                                 "confidence": parsed.get("confidence"), "spec_gap": parsed.get("spec_gap"),
                                 "reply": reply}, ensure_ascii=False) + "\n")
        print(f"  live: {key[0]} q{key[1]} label={q['label']} -> {ans}", flush=True)
        return to_policy_answer(ans, q)

    for d in div:
        for qi, q in enumerate(d["queries"]):
            q["_case"], q["_qi"], q["_iface"] = d["case"], qi, d["iface"]
    orig_cs, orig_lh = ps.consistent, ps.likelihood

    def consistent(opt: str, ans: str) -> bool:
        return False if ans == "ABSTAIN" else orig_cs(opt, ans)

    def likelihood(opt: str, ans: str, p: float, n_ans: int) -> float:
        return 1.0 if ans == "ABSTAIN" else orig_lh(opt, ans, p, n_ans)  # abstention carries no information
    ps.consistent, ps.likelihood, ps.judge = consistent, likelihood, judge_fn
    rng = random.Random(0)
    per = []
    for d in div:
        s, k = ps.run_problem(d, "bayes", a.p, a.budget, a.tau, "configs", rng)
        per.append((d["case"], s, k))
    acc = (sum(s for _, s, _ in per) + base) / n
    ps.judge = lambda *_: "NONE"
    maj_per = [ps.run_problem(d, "majority", a.p, 0, a.tau, "votes", rng)[0] for d in div]
    cfg_per = [ps.run_problem(d, "majority", a.p, 0, a.tau, "configs", rng)[0] for d in div]
    maj = (sum(maj_per) + base) / n
    cfg = (sum(cfg_per) + base) / n
    (run / "per_task.json").write_text(json.dumps(
        [{"case": c, "askrtl": s, "questions": k, "majority_votes": m, "majority_configs": g}
         for (c, s, k), m, g in zip(per, maj_per, cfg_per)], indent=1), encoding="utf-8")
    print(f"\nbenchmark accuracy over {n} problems:")
    print(f"  majority vote (per sample)       {maj:.3f}")
    print(f"  majority vote (per config)       {cfg:.3f}")
    print(f"  AskRTL online (B={a.budget}, p={a.p})      {acc:.3f}   "
          f"questions asked={state['asked']} ({state['asked'] / len(div):.2f}/divergent problem)")
    print(f"  live calls={state['calls']} tokens~{state['tokens']} blocked-by-guard={state['blocked']}")
    wrong = [c for c, s, _ in per if s < 1]
    print(f"  divergent problems not solved: {wrong}")


if __name__ == "__main__":
    main()
