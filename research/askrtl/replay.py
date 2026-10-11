"""Phase 2 analysis: plug *recorded* LLM-judge answers into the selection policies.

Reads out_judge/<run>/results.jsonl (from judge.py --live) and reports
  * judge accuracy overall / by label type / by trace length / on the voting-failure problems,
  * end-to-end benchmark accuracy of majority vs top-2 vs Bayesian asking, where each
    question is answered by a recorded judge reply (resampled across --samples replies),
  * how often the judge flags UNCLEAR, and on which problems (ambiguity candidates).

Usage: python -I replay.py out_judge/<run> [--p 0.8]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import policy_sim as ps  # noqa: E402

VOTE_FAIL = {"Prob066", "Prob071", "Prob112", "Prob128", "Prob133", "Prob137", "Prob139", "Prob140",
             "Prob142", "Prob155"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--p", type=float, default=0.8, help="judge accuracy assumed by the Bayesian update")
    ap.add_argument("--reps", type=int, default=200)
    a = ap.parse_args()
    res = [json.loads(l) for l in (Path(a.run) / "results.jsonl").read_text(encoding="utf-8").splitlines()]
    res = [r for r in res if r["answer"] not in ("API_ERROR",)]
    print(f"{len(res)} judged replies")
    acc = lambda rs: f"{sum(r['correct'] for r in rs)}/{len(rs)} = {sum(r['correct'] for r in rs) / max(len(rs), 1):.3f}"  # noqa: E731
    print("overall", acc(res))
    by = defaultdict(list)
    for r in res:
        kind = "ANY" if r["label"].startswith("ANY") else ("NONE" if r["label"] == "NONE" else "letter")
        by[f"label={kind}"].append(r)
        by[f"len={'1' if r['len'] <= 1 else '2-4' if r['len'] <= 4 else '5+'}"].append(r)
        by["vote-fail problems" if r["case"][:7] in VOTE_FAIL else "other problems"].append(r)
    for k in sorted(by):
        print(f"  {k:<22} {acc(by[k])}")
    print("answer distribution", dict(Counter(r["answer"] for r in res)))
    unclear = Counter(r["case"] for r in res if r["answer"] == "UNCLEAR")
    print("UNCLEAR by problem", dict(unclear.most_common(15)))
    # ---- end-to-end replay
    answers: dict[tuple[str, int], list[str]] = defaultdict(list)
    for r in res:
        a_ = r["answer"]
        answers[(r["case"], r["qi"])].append("NONE" if a_ in ("UNCLEAR", "PARSE_ERROR") else a_)
    div, base, n = ps.load()

    def judge_replay(q: dict, p: float, rng: random.Random) -> str:
        pool = answers.get((q["_case"], q["_qi"]))
        if not pool:
            return "NONE"  # unanswered question carries no information under our update
        ans = rng.choice(pool)
        if ans == "ANY":  # map to the concrete ANY:xy label space used by the policy
            letters = sorted(set(v for v in q["cluster_option"].values() if v != "other"))
            return "ANY:" + "".join(letters)
        return ans

    for d in div:
        for qi, q in enumerate(d["queries"]):
            q["_case"], q["_qi"] = d["case"], qi
    ps.judge = judge_replay  # route policy questions to recorded replies
    for name, pol, b, prior in [("majority", "majority", 0, "votes"), ("top2", "top2", 1, "votes"),
                                ("bayes votes B=3", "bayes", 3, "votes"),
                                ("bayes configs B=3", "bayes", 3, "configs")]:
        rng = random.Random(0)
        tot = 0.0
        for _ in range(a.reps):
            for d in div:
                tot += ps.run_problem(d, pol, a.p, b, 0.95, prior, rng)[0]
        print(f"{name:<20} benchmark acc = {(tot / a.reps + base) / n:.3f}")


if __name__ == "__main__":
    main()
