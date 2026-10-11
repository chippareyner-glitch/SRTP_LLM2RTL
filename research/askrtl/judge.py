"""Phase 2 harness: ask an LLM judge the disambiguation queries and score it.

DRY-RUN BY DEFAULT: renders every prompt, writes them to out_judge/<run>/prompts.jsonl and
prints a token estimate.  Real API calls require BOTH --live and --max-calls N.

Each query is shown with a random permutation of option letters (position-bias control);
answers are mapped back before scoring against the hidden reference label.

Usage:
  python -I judge.py                                  # dry run over all queries
  python -I judge.py --live --max-calls 150 --samples 1 --effort high
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from queries import LETTERS, render, render_long  # noqa: E402

from paths import BENCH, JUDGE_OUT as OUT, QDIR, case_files  # noqa: E402

PROJ = HERE.parents[1]

SYSTEM = """You are a meticulous digital-hardware verification engineer.
You will be given a natural-language specification of a Verilog module and ONE concrete
input scenario (a table of input values per clock cycle and the output values observed so
far). Several candidate implementations agree on everything shown, but disagree at the cell
marked "?". Your job is to decide, from the SPECIFICATION ALONE, what the output must be at
that cell.

Method: restate the relevant rules of the spec, then simulate the specified behaviour step by
step through the table (track internal state explicitly, cycle by cycle, respecting reset and
clock-edge timing as described in the scenario), and compare with the options.

Answer with exactly one of:
  - a single option letter, if the spec requires that option and rules out the others;
  - ANY   if the spec does not constrain the output here (e.g. explicit don't-care,
          undefined/unused input combination) so more than one listed option is acceptable;
  - NONE  if none of the listed options (or the outputs shown earlier in the table) are
          consistent with the spec;
  - UNCLEAR if the spec is genuinely ambiguous about this situation (state the gap).

End your reply with a single line of JSON:
{"answer": "<letter|ANY|NONE|UNCLEAR>", "confidence": <0..1>, "spec_gap": "<short note or empty>"}"""


SYSTEM_LONG = SYSTEM.split("Answer with exactly one of:")[0].replace(
    'disagree at the cell\nmarked "?"', "disagree somewhere in the shown traces").replace(
    "what the output must be at\nthat cell", "which output trace the specification allows") + \
    """Answer with exactly one of: A, B, ANY (both traces acceptable), NONE (neither), UNCLEAR.
End your reply with a single line of JSON:
{"answer": "<A|B|ANY|NONE|UNCLEAR>", "confidence": <0..1>, "spec_gap": "<short note or empty>"}"""


def build_prompt(case: str, q: dict, iface: dict, perm: list[int], variant: str = "min") -> tuple[str, dict]:
    """perm[i] = index of original option shown at display position i."""
    spec = BENCH.spec(case)
    if variant == "long":
        lg = q["long"]
        outs = [lg["outs"][i] for i in perm[:2]]
        text = render_long(spec, iface, lg["stim"], outs[0], outs[1], lg["st0"],
                           lg.get("first_cycle", 0) if iface["sequential"] else 0)
        return text, {LETTERS[d]: LETTERS[o] for d, o in enumerate(perm[:2])}
    shown = [q["options"][i] for i in perm]
    per = 2 if iface["sequential"] else 1
    stim = q["stim"][: q["k"] // per + 1]
    text = render(spec, iface, stim, q["hist"], q["k"], shown)
    back = {LETTERS[d]: LETTERS[o] for d, o in enumerate(perm)}
    return text, back


def parse_answer(reply: str) -> dict:
    m = re.findall(r"\{[^{}]*\"answer\"[^{}]*\}", reply)
    if not m:
        return {"answer": "PARSE_ERROR"}
    try:
        d = json.loads(m[-1])
    except json.JSONDecodeError:
        return {"answer": "PARSE_ERROR"}
    d["answer"] = str(d.get("answer", "")).strip().upper()
    return d


def score(ans: str, label: str) -> bool:
    if label.startswith("ANY:"):
        return ans == "ANY"
    return ans == label


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--effort", default="high")
    ap.add_argument("--model", default=None, help="defaults to DEEPSEEK_MODEL from .env")
    ap.add_argument("--cases", nargs="*")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--variant", choices=("min", "long"), default="min")
    ap.add_argument("--resume", help="existing out_judge/<run> directory to continue")
    a = ap.parse_args()
    system = SYSTEM_LONG if a.variant == "long" else SYSTEM
    rng = random.Random(a.seed)
    items = []
    for f in case_files(QDIR):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("status") != "ok" or (a.cases and not any(d["case"].startswith(c) for c in a.cases)):
            continue
        for qi, q in enumerate(d["queries"]):
            if a.variant == "long" and not q.get("long"):
                continue
            for s in range(a.samples):
                perm = list(range(2 if a.variant == "long" else len(q["options"])))
                rng.shuffle(perm)
                text, back = build_prompt(d["case"], q, d["iface"], perm, a.variant)
                label = q["long"]["label"] if a.variant == "long" else q["label"]
                items.append({"case": d["case"], "qi": qi, "sample": s, "perm": perm, "back": back,
                              "label": label, "len": q["len"], "variant": a.variant, "user": text})
    if a.resume:  # continue an interrupted run in place; perms are seeded, so items are identical
        run = Path(a.resume)
        done = set()
        if (run / "results.jsonl").exists():
            for line in (run / "results.jsonl").read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    if r["answer"] != "API_ERROR":
                        done.add((r["case"], r["qi"], r["sample"]))
        items = [it for it in items if (it["case"], it["qi"], it["sample"]) not in done]
        print(f"resuming {run.name}: {len(done)} done, {len(items)} remaining")
    else:
        run = OUT / (datetime.now().strftime("%Y%m%d_%H%M%S") + f"_{a.variant}" + ("_live" if a.live else "_dry"))
    run.mkdir(parents=True, exist_ok=True)
    with (run / ("prompts_resume.jsonl" if a.resume else "prompts.jsonl")).open("w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    chars = sum(len(it["user"]) + len(system) for it in items)
    print(f"{len(items)} judge prompts from {len({i['case'] for i in items})} problems; "
          f"~{chars / 3.5 / 1e3:.0f}K input tokens (+ reasoning/output). Saved to {run}")
    if not a.live:
        print("dry run: no API calls made (use --live --max-calls N)")
        return
    if a.max_calls <= 0:
        sys.exit("--live requires --max-calls > 0")
    sys.path.insert(0, str(PROJ))
    from llm_client import call_llm  # noqa: E402
    results, calls = [], 0
    for it in items:
        if calls >= a.max_calls:
            break
        calls += 1
        t0 = time.time()
        try:
            reply, meta = call_llm(system, it["user"], model=a.model, case_id=it["case"],
                                   reasoning_effort=a.effort, return_metadata=True,
                                   log_dir=str(run / "api_logs"))
            ans = parse_answer(reply)
        except Exception as e:  # noqa: BLE001
            reply, meta, ans = "", {"error": str(e)}, {"answer": "API_ERROR"}
        raw = ans["answer"]
        mapped = it["back"].get(raw, raw)
        res = {k: it[k] for k in ("case", "qi", "sample", "perm", "label", "len")}
        res.update({"raw": raw, "answer": mapped, "correct": score(mapped, it["label"]),
                    "confidence": ans.get("confidence"), "spec_gap": ans.get("spec_gap"),
                    "usage": meta.get("usage"), "secs": round(time.time() - t0, 1), "reply": reply})
        results.append(res)
        with (run / "results.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(res, ensure_ascii=False) + "\n")
        print(it["case"], it["qi"], it["label"], "->", mapped, "OK" if res["correct"] else "x", flush=True)
    acc = sum(r["correct"] for r in results) / max(len(results), 1)
    print(f"judge accuracy {acc:.3f} over {len(results)} calls")


if __name__ == "__main__":
    main()
