"""Adaptive sampling by behavioural agreement, simulated on existing pools (no API).

Policy "stop-at-agreement(k)": draw samples s0, s1, ... in order; a sample votes for its
behaviour cluster (Phase 1, reference-free) if it compiles.  Stop as soon as some behaviour has
k votes, or after 5 samples; answer = the behaviour with most votes (ties -> earliest).
Compared with always drawing 5 and voting, and with drawing 1.
Accuracy is graded with the official tests (evaluation only).

Usage: python -I -X utf8 adaptive.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
TAGS = [("ve_ds41", "VerilogEval"), ("rtllm_ds41", "RTLLM"), ("cvdp_ds41", "CVDP")]


def load(tag: str) -> list[dict]:
    """Per task: list of (sample index, behaviour id or None, correct) for s0..s4."""
    pool = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in (RESEARCH / "pools" / tag / "out").glob("*.json")}
    out = []
    for task, r in pool.items():
        f = RESEARCH / "askrtl" / f"out_phase1_{tag}" / f"{task}.json"
        p1 = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        cl_of = {}
        if p1.get("status") == "ok":
            for i, cl in enumerate(p1["clusters"]):
                for m in cl:
                    cl_of[m] = i
        samples = []
        for c in r["candidates"]:
            for s in c["sources"]:
                k = int(s.split(":s")[-1]) if ":s" in s else 0
                beh = cl_of.get(c["id"], f"solo_{c['id']}" if c.get("compiles") else None)
                samples.append((k, beh, c["correct"]))
        samples.sort()
        out.append({"task": task, "samples": samples})
    return out


def run(tasks: list[dict], k: int | None, max_n: int = 5, order_seed: int | None = None) -> tuple[float, float]:
    acc = drawn = 0.0
    rng = random.Random(order_seed)
    for t in tasks:
        s = list(t["samples"])
        if order_seed is not None:
            rng.shuffle(s)
        votes, first, correct_of, n = {}, {}, {}, 0
        for i, (_, beh, ok) in enumerate(s[:max_n]):
            n += 1
            if beh is None:
                continue
            votes[beh] = votes.get(beh, 0) + 1
            first.setdefault(beh, i)
            correct_of[beh] = ok
            if k is not None and votes[beh] >= k:
                break
        drawn += n
        if votes:
            best = max(votes, key=lambda b: (votes[b], -first[b]))
            acc += correct_of[best]
    return acc / len(tasks), drawn / len(tasks)


def main() -> None:
    print(f"{'benchmark':<12}{'policy':<26}{'accuracy':>9}{'samples/task':>14}{'saving vs 5':>13}")
    for tag, name in TAGS:
        tasks = load(tag)
        res = {}
        for label, k, n in (("1 sample", None, 1), ("fixed 5 + vote", None, 5),
                            ("stop at 2 agreeing", 2, 5), ("stop at 3 agreeing", 3, 5)):
            # average over random sample orders to remove order effects
            vals = [run(tasks, k, n, seed) for seed in range(50)]
            a = sum(v[0] for v in vals) / len(vals)
            d = sum(v[1] for v in vals) / len(vals)
            res[label] = (a, d)
        full = res["fixed 5 + vote"][1]
        for label, (a, d) in res.items():
            print(f"{name:<12}{label:<26}{a:>9.3f}{d:>14.2f}{1 - d / full:>12.0%}")


if __name__ == "__main__":
    main()
