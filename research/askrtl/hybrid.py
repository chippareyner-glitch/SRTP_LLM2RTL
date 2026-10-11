"""Human-in-the-loop AskRTL (no API): the LLM judge answers what it can, the *user* answers the rest.

Replays the online Bayesian policy.  For each question the policy asks:
  * a recorded judge answer is used if it is decisive (a single option) and its confidence >= --theta;
  * otherwise the question is escalated to a simulated user, who answers with the reference's
    behaviour (the question label: an option, ANY, or NONE) and is right with probability --p-user;
  * questions the judge was never asked go straight to the user (an upper bound on user effort).
Reports benchmark accuracy against user questions per problem, for several thresholds.

Usage: python -I -X utf8 hybrid.py <judge_run_dir> [<judge_run_dir> ...]   (ASKRTL_TAG / ASKRTL_BENCH set)
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import policy_sim as ps  # noqa: E402


def load_answers(runs: list[str]) -> dict:
    rec = {}
    for run in runs:
        for name in ("results.jsonl", "online_results.jsonl"):
            f = Path(run) / name
            if f.exists():
                for line in f.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        r = json.loads(line)
                        rec[(r["case"], r["qi"])] = r
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--p-user", type=float, default=0.98)
    ap.add_argument("--p", type=float, default=0.8)
    a = ap.parse_args()
    rec = load_answers(a.runs)
    div, base, n = ps.load()
    for d in div:
        for qi, q in enumerate(d["queries"]):
            q["_case"], q["_qi"] = d["case"], qi
    orig_cs, orig_lh = ps.consistent, ps.likelihood
    print(f"{'policy':<34}{'accuracy':>9}{'user q / problem':>18}{'judge q':>9}{'user q':>8}")
    for theta in (None, 0.95, 0.9, 0.0, "user-only"):
        stats = {"user": 0, "judge": 0}

        def judge_fn(q: dict, p: float, rng: random.Random, theta=theta) -> str:
            r = rec.get((q["_case"], q["_qi"]))
            if theta != "user-only" and r is not None:
                ans = r["answer"]
                try:
                    conf = float(r.get("confidence"))
                except (TypeError, ValueError):
                    conf = 1.0
                decisive = len(ans) == 1 and ans.isalpha()
                if theta is None or (decisive and conf >= theta):
                    stats["judge"] += 1
                    if ans == "ANY":
                        return "ANY:" + "".join(sorted(set(v for v in q["cluster_option"].values() if v != "other")))
                    return ans if decisive or ans == "NONE" else "ABSTAIN"
            if theta is None:  # judge-only policy and the judge never answered: no information
                return "ABSTAIN"
            stats["user"] += 1  # escalate to the (simulated) user
            return q["label"] if rng.random() < a.p_user else "ABSTAIN"

        def consistent(opt: str, ans: str) -> bool:
            return False if ans == "ABSTAIN" else orig_cs(opt, ans)

        def likelihood(opt: str, ans: str, p: float, n_ans: int) -> float:
            return 1.0 if ans == "ABSTAIN" else orig_lh(opt, ans, p, n_ans)
        ps.consistent, ps.likelihood, ps.judge = consistent, likelihood, judge_fn
        rng = random.Random(0)
        tot = sum(ps.run_problem(d, "bayes", a.p, 3, 0.95, "configs", rng)[0] for d in div)
        acc = (tot + base) / n
        name = {None: "judge only (online)", "user-only": "user only (every question)"}.get(
            theta, f"hybrid: escalate if conf < {theta}" if theta else "hybrid: escalate ANY/NONE/UNCLEAR")
        print(f"{name:<34}{acc:>9.3f}{stats['user'] / n:>18.3f}{stats['judge']:>9}{stats['user']:>8}")
    ps.judge = lambda *_: "NONE"
    maj = (sum(ps.run_problem(d, "majority", a.p, 0, 0.95, "votes", random.Random(0))[0] for d in div) + base) / n
    print(f"{'majority vote (no questions)':<34}{maj:>9.3f}")


if __name__ == "__main__":
    main()
