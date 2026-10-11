#!/usr/bin/env python3
"""Minimal A/B experiment for direct RTL vs. Spec Card assisted RTL.

The official testbench is used only after generation/compile repair. Functional
simulation feedback is never sent to the model. API credentials are read only
from DEEPSEEK_API_KEY and are never written to experiment artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT
from candidate_runtime import DEFAULT_DATASET, DEFAULT_IVERILOG, DEFAULT_VVP, call_api, as_text, ARK_MODEL
DEFAULT_EXPERIMENT_ROOT = ROOT / "experiments" / "prompt_understanding"
SPEC_CARD_VERSION = "v3_observable_timing"
ROUTER_VERSION = "v3_flag_only_and_risk_route"

DIRECT_SYSTEM = """You are an expert RTL designer. Implement exactly the supplied hardware specification in synthesizable SystemVerilog. Preserve the requested module name, port names, directions, and widths. Pay special attention to clock edge, reset polarity and timing, priority, state-update timing, output latency, signedness, and boundary behavior. Do not invent unspecified behavior unless required for a legal implementation. Return exactly one SystemVerilog code block and no explanation."""

SUFFICIENCY_SYSTEM = """You assess whether a natural-language RTL specification is sufficient for implementation. Do not design RTL and do not propose internal hardware. Return exactly one compact JSON object with:
- readiness: one of complete, ambiguous, contradictory, interface_incomplete
- complexity: one of simple, complex
- risk_tags: zero or more of interface, combinational, edge, reset, priority, latency, exact_duration, sequence, serial_protocol, fsm, signedness, width
- reason: one concise sentence
- evidence: short fragments from the specification supporting the decision

Mark complex only when correct behavior requires multi-phase control, an FSM, serial sequence/history, interacting priorities, or exact multi-cycle duration accounting. Ordinary Boolean logic, muxes, arithmetic, and a single bank of flip-flops are simple. Mark ambiguous when two materially different externally visible behaviors are consistent with the text, especially when asked to fix buggy code without being told the intended truth table, waveform, or invariant. Do not use conventional assumptions to hide missing behavior.
Mark incomplete only when a signal required at the TopModule boundary is actually missing. Signals explicitly belonging to surrounding circuitry are not missing TopModule ports. Relative cycle language such as \"the following cycle\" or \"within two cycles\" is implementable timing, not ambiguity. A behavior may require state memory without being ambiguous. Standard digital-design numbering is sufficient when the specification itself explains the convention."""

SPEC_CARD_SYSTEM = """You are a hardware timing analyst, not an RTL architect. Convert the supplied natural-language RTL specification into one compact observable-behavior Spec Card. Do not write RTL, invent internal registers, choose state encodings, or prescribe a datapath. Return exactly one JSON object with schema_version \"v3_observable_timing\" and only these fields:

- interface: exact module and ports.
- clock_reset: active edge, reset polarity, synchronous/asynchronous behavior, and externally visible post-reset behavior.
- ordered_behaviors: concise ordered conditions and required externally visible effects.
- edge_contracts: for each externally visible phase change, state the triggering input/history before edge E, outputs immediately after E, outputs during following intervals, and outputs immediately after the terminal edge. State whether the post-E interval is interval 1 of a stated duration.
- duration_accounting: for each exact duration, define interval 1, the last interval, the edge that ends it, and verify the minimum/example case arithmetically. Express requirements using ports and abstract values only, never proposed register names.
- priorities: ordered simultaneous conditions.
- ambiguities: genuinely unspecified behavior only.
- final_checks: at most five externally observable checks most likely to catch reset, latency, priority, stale-value, and off-by-one errors.

Every rule must include a short evidence fragment and confidence = explicit, inferred, or unspecified. If an edge captures the last bit of a field, distinguish the old partial value from the completed abstract value, but do not propose how it is stored. For an asserted status lasting N cycles, explicitly decide whether the assertion edge begins interval 1 and therefore must not be followed by N additional asserted edges. Keep the entire card short, non-repetitive, and independent of any particular RTL implementation."""

CARD_RTL_SYSTEM = """You are an expert RTL designer. Implement the original hardware specification in synthesizable SystemVerilog, using the supplied observable-behavior Spec Card only as a semantic checklist. The original specification is authoritative if there is any conflict. Preserve the exact requested interface. Choose the simplest conventional architecture yourself; do not infer internal registers, state encodings, or datapath structure from names used in the card.

Before emitting code, enforce these rules:
1. Implement every edge contract so outputs visible immediately after a transition edge agree with the new phase.
2. Remember that nonblocking-assignment RHS expressions read pre-edge values. When the current input completes a field, compute the completed value directly from the old partial register and current input.
3. For every exact duration, count the assertion edge's post-edge interval as interval 1 when the card says so. Verify algebraically that the terminal edge does not add or remove an active interval.
4. Do not drive an output from a shadow register one cycle late. Prefer one canonical registered value or a clearly aligned combinational assignment.
5. On a terminal edge, update state, status outputs, and visible count consistently; do not leave an extra active cycle.
6. Reset and same-edge control priorities must match the card and original specification.

Return exactly one complete synthesizable SystemVerilog code block and no explanation."""

REPAIR_SYSTEM = """You repair SystemVerilog compilation errors. Preserve the behavior and exact requested interface of the supplied design. Change only what is needed to make it compile; do not redesign from compiler messages. Return exactly one complete SystemVerilog code block and no explanation."""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    p.add_argument("--output", type=Path)
    p.add_argument("--model", default=ARK_MODEL)
    p.add_argument("--reasoning-effort", default="none")
    p.add_argument("--max-tokens", type=int, default=8192)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--max-repairs", type=int, default=2)
    p.add_argument(
        "--arm",
        choices=("both", "direct", "spec_card", "adaptive", "direct_adaptive", "all"),
        default="both",
    )
    p.add_argument("--case", action="append", default=[])
    p.add_argument("--limit", type=int)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--direct-prompt", choices=("baseline", "g3"), default="baseline")
    from ppa import add_ppa_arguments
    add_ppa_arguments(p)
    return p.parse_args()


def direct_prompt(args) -> str:
    variant = getattr(args, "direct_prompt", "baseline")
    if variant not in {"baseline", "g3"}:
        raise ValueError("Unknown direct prompt variant")
    return (ROOT / "prompts" / "direct" / f"{variant}.system.txt").read_text(encoding="utf-8").strip()


def atomic_json(path: Path, value: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)



def extract_sv(text: str) -> str:
    blocks = re.findall(r"```(?:systemverilog|verilog|sv)?\s*\n(.*?)```", text, flags=re.I | re.S)
    candidate = max(blocks, key=len) if blocks else text
    start = re.search(r"\bmodule\s+TopModule\b", candidate)
    if start:
        candidate = candidate[start.start():]
    end_positions = [m.end() for m in re.finditer(r"\bendmodule\b", candidate)]
    if end_positions:
        candidate = candidate[:end_positions[-1]]
    return candidate.strip() + "\n"


def extract_json_object(text: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("model response contains no JSON object")
        value = json.loads(cleaned[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response JSON is not an object")
    return value


def should_use_spec_card(spec: str, assessment: dict[str, Any]) -> bool:
    """Route only timing-sensitive designs through the expensive Spec Card."""
    tags = {str(tag).lower() for tag in assessment.get("risk_tags", [])}
    if tags.intersection({"exact_duration", "latency", "serial_protocol"}):
        return True
    lowered = spec.lower()
    timing_phrases = (
        "serial", "start bit", "stop bit", "clock cycles",
        "following clock cycle", "complete cycle beginning",
        "successive clock cycles",
    )
    return "sequence" in tags and any(phrase in lowered for phrase in timing_phrases)


def run_process(cmd: list[str], cwd: Path, timeout: int) -> tuple[int, str, str, bool]:
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        return 124, as_text(exc.stdout), as_text(exc.stderr), True


def syntax_check(sv_path: Path, log_path: Path) -> tuple[bool, str]:
    cmd = [str(DEFAULT_IVERILOG), "-g2012", "-s", "TopModule", "-t", "null", str(sv_path)]
    rc, out, err, timed_out = run_process(cmd, sv_path.parent, 60)
    text = out + "\n" + err
    log_path.write_text(text, encoding="utf-8")
    return rc == 0 and not timed_out, text[-6000:]


def official_eval(case_id: str, candidate: Path, test: Path, ref: Path, out_dir: Path) -> dict[str, Any]:
    sim = out_dir / "official_sim.vvp"
    cmd = [str(DEFAULT_IVERILOG), "-g2012", "-s", "tb", "-o", str(sim), str(test), str(ref), str(candidate)]
    rc, out, err, timed_out = run_process(cmd, out_dir, 60)
    (out_dir / "official_compile.log").write_text(out + "\n" + err, encoding="utf-8")
    if rc != 0 or timed_out or not sim.exists():
        return {"status": "compile_failed", "pass": False, "mismatches": None, "samples": None}
    rc, out, err, timed_out = run_process([str(DEFAULT_VVP), str(sim)], out_dir, 60)
    full = out + "\n" + err
    (out_dir / "official_sim.log").write_text(full, encoding="utf-8")
    match = re.search(r"Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples", full, flags=re.I)
    if timed_out:
        status, mismatches, samples = "timeout", None, None
    elif match and rc == 0 and int(match.group(2)) > 0:
        mismatches, samples = int(match.group(1)), int(match.group(2))
        status = "pass" if mismatches == 0 else "mismatch"
    else:
        status, mismatches, samples = "unknown_sim_fail", None, None
    return {"status": status, "pass": status == "pass", "mismatches": mismatches, "samples": samples, "returncode": rc}


def save_api_call(
    directory: Path,
    name: str,
    response: str,
    metadata: dict[str, Any],
    system: str,
    user: str,
) -> None:
    atomic_json(directory / f"{name}_prompt.json", {"system": system, "user": user})
    (directory / f"{name}_response.txt").write_text(response, encoding="utf-8")
    atomic_json(directory / f"{name}_api.json", metadata)


def generate_arm(
    args: argparse.Namespace,
    case_id: str,
    spec: str,
    arm: str,
    case_out: Path,
    reuse_direct_candidate: Path | None = None,
) -> dict[str, Any]:
    arm_out = case_out / arm
    arm_out.mkdir(parents=True, exist_ok=True)
    calls: list[dict[str, Any]] = []
    spec_card = None
    assessment = None
    effective_strategy = arm
    if arm == "adaptive":
        assessment_user = f"SPECIFICATION:\n{spec}"
        response, meta = call_api(args, SUFFICIENCY_SYSTEM, assessment_user)
        save_api_call(
            arm_out, "assessment", response, meta,
            SUFFICIENCY_SYSTEM, assessment_user,
        )
        calls.append(meta)
        assessment = extract_json_object(response)
        atomic_json(arm_out / "assessment.json", assessment)
        readiness = str(assessment.get("readiness", "")).lower()
        if readiness != "complete":
            effective_strategy = "direct_flagged"
        else:
            effective_strategy = "spec_card" if should_use_spec_card(spec, assessment) else "direct"

    if effective_strategy == "spec_card":
        response, meta = call_api(args, SPEC_CARD_SYSTEM, f"SPECIFICATION:\n{spec}")
        save_api_call(arm_out, "spec_card", response, meta, SPEC_CARD_SYSTEM, f"SPECIFICATION:\n{spec}")
        calls.append(meta)
        spec_card = response.strip()
        user = f"ORIGINAL SPECIFICATION:\n{spec}\n\nSPEC CARD (analysis aid):\n{spec_card}"
        system = CARD_RTL_SYSTEM
    else:
        user = f"SPECIFICATION:\n{spec}"
        system = direct_prompt(args)

    reused_direct = bool(
        arm == "adaptive"
        and effective_strategy in {"direct", "direct_flagged"}
        and reuse_direct_candidate is not None
        and reuse_direct_candidate.exists()
    )
    if reused_direct:
        code = reuse_direct_candidate.read_text(encoding="utf-8")
        (arm_out / "reused_from_direct.txt").write_text(str(reuse_direct_candidate), encoding="utf-8")
    else:
        response, meta = call_api(args, system, user)
        save_api_call(arm_out, "initial", response, meta, system, user)
        calls.append(meta)
        code = extract_sv(response)
    first_syntax_pass = False
    final_path = arm_out / "attempt_00.sv"

    for attempt in range(args.max_repairs + 1):
        if attempt:
            repair_user = (
                f"ORIGINAL SPECIFICATION:\n{spec}\n\nCURRENT RTL:\n```systemverilog\n{code}```"
                f"\n\nCOMPILER ERRORS:\n{compiler_error}"
            )
            response, meta = call_api(args, REPAIR_SYSTEM, repair_user)
            save_api_call(arm_out, f"repair_{attempt:02d}", response, meta, REPAIR_SYSTEM, repair_user)
            calls.append(meta)
            code = extract_sv(response)
            final_path = arm_out / f"attempt_{attempt:02d}.sv"
        final_path.write_text(code, encoding="utf-8")
        syntax_pass, compiler_error = syntax_check(final_path, arm_out / f"attempt_{attempt:02d}_syntax.log")
        if attempt == 0:
            first_syntax_pass = syntax_pass
        if syntax_pass:
            break

    if syntax_pass:
        shutil.copy2(final_path, arm_out / "module_final.sv")
    result = {
        "arm": arm,
        "effective_strategy": effective_strategy,
        "assessment": assessment,
        "reused_direct_candidate": reused_direct,
        "first_syntax_pass": first_syntax_pass,
        "final_syntax_pass": syntax_pass,
        "attempts": attempt + 1,
        "api_calls": len(calls),
        "api_usage": [m.get("usage", {}) for m in calls],
        "official": None,
    }
    return result


def discover_cases(dataset: Path, requested: list[str], limit: int | None) -> list[str]:
    cases = sorted(p.name[:-11] for p in dataset.glob("*_prompt.txt"))
    if requested:
        selected = []
        for query in requested:
            matches = [c for c in cases if c == query or c.startswith(query)]
            if len(matches) != 1:
                raise ValueError(f"case selector {query!r} matched {len(matches)} cases")
            selected.append(matches[0])
        cases = selected
    if not cases:
        raise ValueError(f"No specification files in {dataset}")
    return cases[:limit] if limit is not None else cases


def aggregate(results: list[dict[str, Any]], args: argparse.Namespace, cases: list[str]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "temperature": args.temperature,
        "max_repairs": args.max_repairs,
        "direct_prompt": getattr(args, "direct_prompt", "baseline"),
        "direct_prompt_sha256": hashlib.sha256(direct_prompt(args).encode()).hexdigest(),
        "official_feedback_used_for_generation": False,
        "spec_card_version": SPEC_CARD_VERSION,
        "router_version": ROUTER_VERSION,
        "selected_cases": cases,
        "completed_cases": len(results),
        "arms": {},
        "results": results,
    }
    for arm in ("direct", "spec_card", "adaptive"):
        rows = [r[arm] for r in results if arm in r]
        summary["arms"][arm] = {
            "completed": len(rows),
            "generated": sum(int(r.get("attempts", 0)) > 0 for r in rows),
            "abstained": sum(r.get("effective_strategy") == "stop_underspecified" for r in rows),
            "flagged_best_effort": sum(r.get("effective_strategy") == "direct_flagged" for r in rows),
            "first_syntax_pass": sum(bool(r["first_syntax_pass"]) for r in rows),
            "final_syntax_pass": sum(bool(r["final_syntax_pass"]) for r in rows),
            "official_pass": sum(bool((r.get("official") or {}).get("pass")) for r in rows),
            "api_calls": sum(int(r["api_calls"]) for r in rows),
            "total_tokens": sum(int(u.get("total_tokens", 0) or 0) for r in rows for u in r["api_usage"]),
        }
    paired = [r for r in results if "direct" in r and "adaptive" in r]
    if paired:
        def passed(row: dict[str, Any], arm: str) -> bool:
            return bool((row[arm].get("official") or {}).get("pass"))

        summary["paired_direct_adaptive"] = {
            "completed": len(paired),
            "both_pass": sum(passed(r, "direct") and passed(r, "adaptive") for r in paired),
            "direct_only_pass": sum(passed(r, "direct") and not passed(r, "adaptive") for r in paired),
            "adaptive_only_pass": sum(not passed(r, "direct") and passed(r, "adaptive") for r in paired),
            "neither_pass": sum(not passed(r, "direct") and not passed(r, "adaptive") for r in paired),
            "oracle_any_pass": sum(passed(r, "direct") or passed(r, "adaptive") for r in paired),
        }
        by_strategy: dict[str, dict[str, int]] = {}
        for row in paired:
            strategy = str(row["adaptive"].get("effective_strategy", "unknown"))
            bucket = by_strategy.setdefault(
                strategy,
                {"completed": 0, "both_pass": 0, "direct_only_pass": 0,
                 "adaptive_only_pass": 0, "neither_pass": 0},
            )
            direct_pass, adaptive_pass = passed(row, "direct"), passed(row, "adaptive")
            bucket["completed"] += 1
            if direct_pass and adaptive_pass:
                bucket["both_pass"] += 1
            elif direct_pass:
                bucket["direct_only_pass"] += 1
            elif adaptive_pass:
                bucket["adaptive_only_pass"] += 1
            else:
                bucket["neither_pass"] += 1
        summary["paired_by_adaptive_strategy"] = by_strategy
    return summary


def main() -> int:
    from ppa import final_ppa, write_summary_ppa_csv
    args = parse_args()
    if args.max_repairs < 0 or (args.limit is not None and args.limit < 1):
        raise ValueError("max-repairs must be nonnegative and limit positive")
    if not DEFAULT_IVERILOG.exists() or not DEFAULT_VVP.exists():
        raise RuntimeError("Icarus Verilog tools were not found")
    cases = discover_cases(args.dataset, args.case, args.limit)
    if args.output:
        output = args.output.resolve()
    else:
        output = DEFAULT_EXPERIMENT_ROOT / f"spec_card_ab_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if output.exists() and not args.resume:
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True, exist_ok=True)
    args.api_log_root = output / "api_requests"
    summary_path = output / "summary.json"
    results: list[dict[str, Any]] = []
    if args.resume and summary_path.exists():
        previous = json.loads(summary_path.read_text(encoding="utf-8"))
        if previous.get("direct_prompt", "baseline") != args.direct_prompt:
            raise ValueError("Resume direct prompt differs from saved experiment")
        saved_hash = previous.get("direct_prompt_sha256")
        if saved_hash and saved_hash != hashlib.sha256(direct_prompt(args).encode()).hexdigest():
            raise ValueError("Resume prompt content differs from saved experiment")
        results = previous.get("results", [])
    completed = {r["case_id"] for r in results}

    for index, case_id in enumerate(cases, 1):
        if case_id in completed:
            continue
        print(f"[{index}/{len(cases)}] {case_id}", flush=True)
        spec_path = args.dataset / f"{case_id}_prompt.txt"
        test_path = args.dataset / f"{case_id}_test.sv"
        ref_path = args.dataset / f"{case_id}_ref.sv"
        spec = spec_path.read_text(encoding="utf-8")
        case_out = output / case_id
        case_out.mkdir(parents=True, exist_ok=True)
        (case_out / "original_spec.txt").write_text(spec, encoding="utf-8")
        row: dict[str, Any] = {"case_id": case_id}
        try:
            arm_sets = {
                "both": ("direct", "spec_card"),
                "direct_adaptive": ("direct", "adaptive"),
                "all": ("direct", "spec_card", "adaptive"),
            }
            selected_arms = arm_sets.get(args.arm, (args.arm,))
            for arm in selected_arms:
                reuse_path = None
                if arm == "adaptive" and "direct" in row:
                    candidate = case_out / "direct" / "module_final.sv"
                    if candidate.exists():
                        reuse_path = candidate
                arm_result = generate_arm(
                    args, case_id, spec, arm, case_out,
                    reuse_direct_candidate=reuse_path,
                )
                if arm_result["final_syntax_pass"]:
                    final_sv = case_out / arm / "module_final.sv"
                    arm_result["official"] = official_eval(case_id, final_sv, test_path, ref_path, case_out / arm)
                final_sv = case_out / arm / 'module_final.sv'
                arm_result['ppa'] = final_ppa(args, final_sv if final_sv.is_file() else None,
                                              case_out / arm / 'ppa',
                                              functional_passed=(arm_result.get('official') or {}).get('pass'))
                row[arm] = arm_result
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            results.append(row)
            atomic_json(summary_path, aggregate(results, args, cases))
            raise
        results.append(row)
        atomic_json(case_out / "result.json", row)
        atomic_json(summary_path, aggregate(results, args, cases))
        write_summary_ppa_csv(output / 'ppa_results.csv', results)
        statuses = []
        for arm in selected_arms:
            official = row[arm]["official"]
            fallback = row[arm].get("generation_status", "syntax")
            statuses.append(f"{arm}={official['status'] if official else fallback}")
        print("  " + "; ".join(statuses), flush=True)
    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
