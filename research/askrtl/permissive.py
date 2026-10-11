"""E1: permissibility questions against judge overconfidence.

The original judge asks "which option does the spec require?" and almost never answers ANY/UNCLEAR when
the spec is silent (NOVELTY_REVIEW.md section 7). Here the same scenario is asked per option: is this value
ALLOWED or FORBIDDEN by the spec, where FORBIDDEN needs quoted spec evidence. Derived answer: one allowed
option -> that letter, several -> ANY, none -> NONE.

Item sets
  eval    - hand-adjudicated questions (adjudication_n1.json) with a ground truth:
            decided(letter) for genuine test gaps (and Prob154, judge error),
            silent for valid-gated / protocol / spec-silent / ambiguous / OVER-genuine / attribution questions;
            Prob091/150 are decided but debatable and reported separately.
  control - informative questions whose reference label is a single option on problems without known spec
            defects (VerilogEval / RTLLM DS4.1 pools): the spec usually decides these.
Variants
  conv  - permissibility + a short list of situations specs usually leave open
  plain - permissibility only (eval set only; isolates the question format from the hints)

Usage:
  python -I -X utf8 permissive.py run --variant conv --sets eval control [--live --max-calls N --max-tokens T]
  python -I -X utf8 permissive.py report
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import random
import re
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from bench import Bench  # noqa: E402
from defects import OURS, RTLBENCHMT  # noqa: E402
from queries import LETTERS, render  # noqa: E402

PROJ = HERE.parents[1]
OUT = HERE / "out_perm"
LOCK = threading.Lock()
BENCH_OF = {"ve": "verilogeval", "rtllm": "rtllm", "cvdp": "cvdp"}
SILENT = {"valid_gated", "protocol_dontcare", "spec_silent", "ambiguous", "attribution"}

BASE = """You are a meticulous digital-hardware verification engineer.
You will be given a natural-language specification of a Verilog module and ONE concrete input scenario
(a table of input values per clock cycle and the output values observed so far). Several candidate
implementations agree on everything shown, but produce different values at the cell marked "?".

For EACH listed option, decide independently whether the SPECIFICATION permits that value at that cell:
  - FORBIDDEN: the specification rules this value out. Use FORBIDDEN only if you can quote the spec text
    (or an explicit rule or example in it) from which the exclusion follows by direct reasoning or
    computation.
  - ALLOWED: some implementation that satisfies every explicit requirement of the specification would
    produce this value here. Behaviour the specification does not state is not a requirement; the absence
    of a rule means ALLOWED.
More than one option may be ALLOWED, and possibly none.
"""

HINTS = """
Specifications often leave the following open; treat them as ALLOWED unless the text explicitly pins them
down: data outputs while their valid / done / ready / start flag is low; output values during or right after
reset that the spec does not state; synchronous versus asynchronous reset when not stated; one-cycle latency
choices (registered versus combinational outputs) when not stated; input combinations or protocol situations
the spec says cannot occur; edge- versus level-sensitive handling of an input when not stated; overflow
behaviour when not stated.
"""

TAIL = """
Method: quote the spec statements relevant to the marked cell, simulate the specified behaviour step by step
through the table where needed (respect reset and clock-edge timing as described in the scenario), then judge
each option.

End your reply with a single line of JSON:
{"verdicts": {"A": "ALLOWED or FORBIDDEN", "B": "..."}, "evidence": "<quoted spec text for each FORBIDDEN>", "confidence": <0..1>}"""

SYSTEMS = {"conv": BASE + HINTS + TAIL, "plain": BASE + TAIL}


def online_rows(tag: str) -> list[dict]:
    p = HERE / f"out_judge_{tag}" / "online" / "online_results.jsonl"
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def items() -> list[dict]:
    adj = json.loads((HERE / "adjudication_n1.json").read_text(encoding="utf-8"))["items"]
    out = []
    for i in adj:
        truth = None
        if i["cell"] == "UNDER" and i["verdict"] == "genuine":
            truth = {"kind": "decided", "letter": i["expected"]}
        elif i["verdict"] in SILENT or (i["cell"] == "OVER" and i["verdict"] == "genuine"):
            truth = {"kind": "silent"}
        elif i["verdict"] == "judge_wrong":
            qf = json.loads((HERE / f"out_queries_{i['tag']}" / f"{i['case']}.json").read_text(encoding="utf-8"))
            truth = {"kind": "decided", "letter": qf["queries"][i["qi"]]["label"],
                     "debatable": i["case"] != "Prob154_fsm_ps2data"}
        if truth:
            out.append({"id": f"eval:{i['tag']}:{i['case']}:{i['qi']}", "set": "eval", "tag": i["tag"],
                        "case": i["case"], "qi": i["qi"], "truth": truth, "verdict": i["verdict"]})
    excl = {i["case"] for i in adj}
    for tag in ("ve_ds41", "ve_ds41_ids", "rtllm_ds41", "rtllm_ds41_ids"):
        b = BENCH_OF[tag.split("_")[0]]
        bad = OURS.get(b, set()) | RTLBENCHMT.get(b, set()) | excl
        for r in online_rows(tag):
            if len(r["label"]) == 1 and r["label"] in LETTERS and r["case"] not in bad:
                out.append({"id": f"control:{tag}:{r['case']}:{r['qi']}", "set": "control", "tag": tag,
                            "case": r["case"], "qi": r["qi"], "truth": {"kind": "decided", "letter": r["label"]}})
    return out


def prompt(it: dict) -> tuple[str, dict, int]:
    qf = json.loads((HERE / f"out_queries_{it['tag']}" / f"{it['case']}.json").read_text(encoding="utf-8"))
    q = qf["queries"][it["qi"]]
    iface = qf["iface"]
    perm = list(range(len(q["options"])))
    random.Random(f"perm:{it['id']}").shuffle(perm)
    shown = [q["options"][i] for i in perm]
    per = 2 if iface["sequential"] else 1
    text = render(Bench(BENCH_OF[it["tag"].split("_")[0]]).spec(it["case"]), iface,
                  q["stim"][: q["k"] // per + 1], q["hist"], q["k"], shown)
    return text, {LETTERS[d]: LETTERS[o] for d, o in enumerate(perm)}, len(q["options"])


def parse(reply: str) -> dict:
    end = reply.rfind("}")
    for m in reversed(list(re.finditer(r"\{", reply))):
        try:
            obj = json.loads(reply[m.start(): end + 1])
        except ValueError:
            continue
        if isinstance(obj, dict) and "verdicts" in obj:
            return obj
    raise ValueError("no verdict JSON")


def derive(verdicts: dict, back: dict) -> tuple[str, list[str]]:
    allowed = sorted(back[k] for k, v in verdicts.items() if k in back and str(v).upper().startswith("ALLOW"))
    return (allowed[0] if len(allowed) == 1 else "ANY" if allowed else "NONE"), allowed


def control_sample(its: list[dict], n: int) -> set[str]:
    """Fixed random subset of the control items (calls cost ~16K tokens each)."""
    ids = sorted(it["id"] for it in its if it["set"] == "control")
    return set(random.Random(0).sample(ids, min(n, len(ids))))


def run(a: argparse.Namespace) -> None:
    its = items()
    keep = control_sample(its, a.control_n)
    todo_all = [it for it in its if it["set"] in a.sets and (it["set"] != "control" or it["id"] in keep)]
    out = OUT / f"{a.variant}.jsonl"
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    todo = [it for it in todo_all if it["id"] not in done][: a.max_calls or None]
    print(f"variant={a.variant} sets={a.sets}: {len(todo_all)} items, {len(done)} done, {len(todo)} to call")
    if not a.live:
        print("dry run (add --live --max-calls N)")
        return
    sys.path.insert(0, str(PROJ))
    from llm_client import call_llm  # noqa: E402
    OUT.mkdir(exist_ok=True)
    state = {"tokens": 0}

    def one(it: dict) -> None:
        with LOCK:
            if state["tokens"] >= a.max_tokens:
                return
        text, back, n_opt = prompt(it)
        rec = {k: it[k] for k in ("id", "set", "tag", "case", "qi")}
        try:
            reply, meta = call_llm(SYSTEMS[a.variant], text, case_id=it["case"], reasoning_effort="high",
                                   return_metadata=True, log_dir=str(OUT / f"api_logs_{a.variant}"))
            tok = (meta.get("usage") or {}).get("total_tokens", 0)
            obj = parse(reply)
            ans, allowed = derive(obj.get("verdicts", {}), back)
            rec.update(answer=ans, allowed=allowed, confidence=obj.get("confidence"),
                       evidence=obj.get("evidence"), tokens=tok, reply=reply)
        except Exception as e:  # noqa: BLE001 - truncation / parse failure = abstention
            tok = 0
            rec.update(answer="ERROR", allowed=[], error=str(e)[:300], tokens=tok)
        with LOCK:
            state["tokens"] += tok
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            print(f"  {it['id']:70} -> {rec['answer']:5} ({tok} tok, total {state['tokens']})", flush=True)
    with cf.ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(one, todo))
    print(f"done; tokens this run: {state['tokens']}")


def report(_: argparse.Namespace) -> None:
    its = {it["id"]: it for it in items()}
    base = {}
    for tag in {it["tag"] for it in its.values()}:
        for r in online_rows(tag):
            base[(tag, r["case"], r["qi"])] = r["answer"]

    def score(ans: str, truth: dict) -> bool:
        return ans in ("ANY", "UNCLEAR") if truth["kind"] == "silent" else ans == truth["letter"]

    runs = {"baseline": {i: base.get((it["tag"], it["case"], it["qi"]), "MISSING") for i, it in its.items()}}
    for f in sorted(OUT.glob("*.jsonl")):
        runs[f.stem] = {json.loads(l)["id"]: json.loads(l)["answer"]
                        for l in f.read_text(encoding="utf-8").splitlines() if l.strip()}
    groups = {
        "eval silent (should be ANY)": lambda it: it["set"] == "eval" and it["truth"]["kind"] == "silent",
        "eval decided (genuine gaps + 154)": lambda it: it["set"] == "eval" and it["truth"]["kind"] == "decided"
        and not it["truth"].get("debatable"),
        "eval decided, debatable (091/150)": lambda it: it["set"] == "eval" and it["truth"].get("debatable"),
        "control decided (reference label)": lambda it: it["set"] == "control",
    }
    for gname, pred in groups.items():
        ids = [i for i, it in its.items() if pred(it)]
        asked = set.union(set(), *(set(ans) for r, ans in runs.items() if r != "baseline"))
        ids = [i for i in ids if i in asked] or ids  # compare every run on the same questions
        line = f"{gname:38} n={len(ids):3} |"
        for rname, ans in runs.items():
            got = [i for i in ids if i in ans]
            if got:
                line += f" {rname}: {sum(score(ans[i], its[i]['truth']) for i in got)}/{len(got)}"
        print(line)
    for rname, ans in runs.items():
        if rname == "baseline":
            continue
        flips = [i for i, it in its.items() if it["set"] == "control" and i in ans and ans[i] in ("ANY", "NONE")]
        print(f"control items answered ANY/NONE by {rname}: {len(flips)}")
        for i in flips:
            print("   ", i, ans[i])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run", "report"))
    ap.add_argument("--variant", choices=tuple(SYSTEMS), default="conv")
    ap.add_argument("--sets", nargs="+", default=["eval"], choices=("eval", "control"))
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--max-calls", type=int, default=0)
    ap.add_argument("--max-tokens", type=int, default=1_500_000)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--control-n", type=int, default=40)
    a = ap.parse_args()
    {"run": run, "report": report}[a.cmd](a)


if __name__ == "__main__":
    main()
