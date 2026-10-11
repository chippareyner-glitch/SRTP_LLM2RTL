"""Offline simulation of query policies with a *synthetic* noisy judge (no API).

Ground-truth query labels come from queries.py (reference simulation).  A judge with
accuracy p returns the labelled answer with probability p, otherwise a uniformly random
wrong answer.  We compare final selection accuracy over the whole benchmark for:
  majority  - pick the cluster with most votes (no questions)
  top2      - one question between the two highest-vote clusters (VClare/SpecLens-style)
  bayes     - noisy-oracle Bayesian posterior, expected-information-gain query choice,
              stop at posterior >= tau or after `budget` questions
This yields the judge accuracy p* above which asking beats voting.
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
import sys  # noqa: E402

sys.path.insert(0, str(HERE))
from paths import P1, POOL, QDIR, case_files  # noqa: E402


def consistent(opt: str, ans: str) -> bool:
    if ans == "NONE":
        return opt == "other"
    if ans.startswith("ANY:"):
        return opt in ans[4:]
    return opt == ans


def answer_space(q: dict) -> list[str]:
    letters = sorted(set(v for v in q["cluster_option"].values() if v != "other"))
    sp = letters + ["NONE"]
    if q["label"].startswith("ANY:") and q["label"] not in sp:
        sp.append(q["label"])
    return sp


def likelihood(opt: str, ans: str, p: float, n_ans: int) -> float:
    return p if consistent(opt, ans) else (1 - p) / max(n_ans - 1, 1)


def judge(q: dict, p: float, rng: random.Random) -> str:
    sp = answer_space(q)
    if rng.random() < p:
        return q["label"]
    wrong = [a for a in sp if a != q["label"]]
    return rng.choice(wrong) if wrong else q["label"]


def entropy(ps: list[float]) -> float:
    return -sum(x * math.log(x) for x in ps if x > 0)


def posterior_update(post: list[float], cids: list[str], q: dict, ans: str, p: float) -> list[float]:
    n = len(answer_space(q))
    new = [w * likelihood(q["cluster_option"].get(c, "other"), ans, p, n) for w, c in zip(post, cids)]
    s = sum(new)
    return [x / s for x in new] if s > 0 else post


def eig(post: list[float], cids: list[str], q: dict, p: float) -> float:
    sp = answer_space(q)
    h0, exp_h = entropy(post), 0.0
    for a in sp:
        pa = sum(w * likelihood(q["cluster_option"].get(c, "other"), a, p, len(sp)) for w, c in zip(post, cids))
        if pa <= 0:
            continue
        exp_h += pa * entropy(posterior_update(post, cids, q, a, p))
    return h0 - exp_h


def config_of(source: str) -> str:
    """Sampling configuration family: the six three-candidate runs share model + setup."""
    return "tri" if source.startswith("tri") else source.split(":")[0]


_CW: dict[str, list[float]] = {}


def config_weights(d: dict) -> list[float]:
    if d["case"] not in _CW:
        _CW[d["case"]] = _config_weights(d)
    return _CW[d["case"]]


def _config_weights(d: dict) -> list[float]:
    """Each configuration casts one unit of vote, split over its samples."""
    pool = json.loads((POOL / f"{d['case']}.json").read_text(encoding="utf-8"))
    srcs = {c["id"]: c["sources"] for c in pool["candidates"]}
    per_cfg: dict[str, int] = {}
    for cl in d["clusters"]:
        for m in cl["members"]:
            for s in srcs[m]:
                per_cfg[config_of(s)] = per_cfg.get(config_of(s), 0) + 1
    w = []
    for cl in d["clusters"]:
        w.append(sum(1 / per_cfg[config_of(s)] for m in cl["members"] for s in srcs[m]))
    return w


def run_problem(d: dict, policy: str, p: float, budget: int, tau: float, prior: str,
                rng: random.Random) -> tuple[float, int]:
    cl = d["clusters"]
    cids = [c["rep"] for c in cl]
    good = [c["correct"][0] for c in cl]
    votes = config_weights(d) if prior == "configs" else [c["votes"] for c in cl]
    if prior in ("votes", "configs"):
        post = [v / sum(votes) for v in votes]
    else:
        post = [1 / len(cl)] * len(cl)

    def pick(ps: list[float]) -> float:  # expected correctness under random tie-breaking
        m = max(ps)
        tied = [i for i, x in enumerate(ps) if abs(x - m) < 1e-12]
        return sum(good[i] for i in tied) / len(tied)

    qs = [q for q in d["queries"]]
    if policy == "majority" or not qs:
        return pick([v / sum(votes) for v in votes]), 0
    if policy == "top2":
        order = sorted(range(len(cl)), key=lambda i: -votes[i])
        a, b = cids[order[0]], cids[order[1]]
        q = next((q for q in qs if set(q["pair"]) == {a, b}), None)
        if q is None:
            return pick([v / sum(votes) for v in votes]), 0
        ans = judge(q, p, rng)
        post = posterior_update([v / sum(votes) for v in votes], cids, q, ans, p)
        return pick(post), 1
    asked = 0
    used: set[int] = set()
    while asked < budget and max(post) < tau:
        cand = [(eig(post, cids, q, p), i) for i, q in enumerate(qs) if i not in used]
        if not cand:
            break
        g, i = max(cand)
        if g <= 1e-9:
            break
        used.add(i)
        post = posterior_update(post, cids, qs[i], judge(qs[i], p, rng), p)
        asked += 1
    return pick(post), asked


def load() -> tuple[list[dict], float, int]:
    """Return divergent problems, plus correctness credit from non-divergent ones."""
    div, base, n = [], 0.0, 0
    for f in case_files(P1):
        n += 1
        qf = QDIR / f.name
        q = json.loads(qf.read_text(encoding="utf-8")) if qf.exists() else {"status": "missing"}
        if q.get("status") == "ok":
            div.append(q)
        else:
            pool = json.loads((POOL / f.name).read_text(encoding="utf-8"))
            cl = pool["clusters"]
            # no divergence found by our search -> every candidate looks identical; credit if top is correct
            if cl:  # official clusters available (VerilogEval)
                base += float(cl[0]["correct"])
            else:  # RTLLM: the most-voted compiling candidate stands for the (single) behaviour
                live = [c for c in pool["candidates"] if c.get("compiles")]
                if live:
                    base += float(max(live, key=lambda c: len(c["sources"]))["correct"])
    return div, base, n


def main() -> None:
    div, base, n = load()
    print(f"problems={n} divergent={len(div)} non-divergent credit={base:.0f}")
    reps = 300
    print(f"{'policy':<28}" + "".join(f"p={p:<6}" for p in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)))
    rows = [("majority", "majority", 0, "votes"), ("majority per-config", "majority", 0, "configs"),
            ("top2 (1 q)", "top2", 1, "votes")]
    for prior in ("votes", "configs", "uniform"):
        for b in (1, 2, 3, 5):
            rows.append((f"bayes {prior} B={b}", "bayes", b, prior))
    results = {}
    for name, pol, b, prior in rows:
        line = f"{name:<28}"
        for p in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
            rng = random.Random(0)
            tot, qn = 0.0, 0
            for _ in range(reps if pol != "majority" else 1):
                for d in div:
                    s, k = run_problem(d, pol, p, b, 0.95, prior, rng)
                    tot += s
                    qn += k
            r_ = reps if pol != "majority" else 1
            acc = (tot / r_ + base) / n
            results[f"{name}|{p}"] = {"acc": acc, "q_per_div_problem": qn / r_ / len(div)}
            line += f"{acc:.3f} "
        print(line)
    (HERE / "out_queries" / "policy_sim.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
