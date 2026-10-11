#!/usr/bin/env python3
"""Generate three RTL candidates, select one without oracle feedback, then evaluate.

The selector sees only the natural-language specification and syntax-clean RTL.
Official reference/testbench files are opened only after the selection is frozen.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from ppa import add_ppa_arguments, final_ppa, write_summary_ppa_csv

from run_spec_card_ab import (
    DEFAULT_DATASET,
    DEFAULT_IVERILOG,
    DEFAULT_VVP,
    REPAIR_SYSTEM,
    atomic_json,
    call_api,
    discover_cases,
    extract_json_object,
    extract_sv,
    official_eval,
    save_api_call,
    syntax_check,
)


from candidate_runtime import ARK_MODEL

ROOT = Path(__file__).resolve().parent
DEFAULT_EXPERIMENT_ROOT = ROOT / "experiments" / "candidate_selection"
SELECTOR_VERSION = "v2_mandatory_edge_trace"

CANDIDATE_SYSTEMS = (
    (
        "literal",
        """You are an expert RTL designer. Implement the specification literally in synthesizable SystemVerilog. Preserve the exact TopModule interface. Resolve timing from externally observable clock-edge behavior, respect reset and priority, and avoid adding unspecified behavior. Return exactly one complete SystemVerilog code block.""",
    ),
    (
        "contract",
        """You are an expert RTL designer using a verification-first method. Before coding, silently derive the interface, reset contract, ordered behaviors, boundary cases, and cycle-by-cycle output timing. Then implement the smallest synthesizable SystemVerilog TopModule satisfying those observations. Check nonblocking-assignment timing and exact durations. Return only one complete SystemVerilog code block.""",
    ),
    (
        "counterexample",
        """You are an expert RTL designer. Independently implement the supplied specification in synthesizable SystemVerilog. Silently challenge the most likely wrong interpretation using counterexamples involving simultaneous controls, first/last cycles, terminal counts, signed widths, and current-edge inputs. Preserve the exact TopModule interface. Return only one complete SystemVerilog code block.""",
    ),
)

SELECTOR_SYSTEM = """You are selecting among syntax-clean RTL implementations using only the specification. You have no reference design or hidden testbench. Do not perform a qualitative code review first. For every candidate, symbolically trace externally observable behavior using pre-edge values for all nonblocking-assignment right-hand sides.

Mandatory checks, when applicable:
1. exact ports, widths, combinational truth table, signedness, and complete assignment;
2. reset assertion edge and first edge after reset;
3. the edge on which a sequence or field's final input bit arrives, including outputs immediately after that same edge;
4. simultaneous controls in stated priority order;
5. the first, penultimate, and terminal intervals of every exact duration; for N cycles, explicitly number interval 1 and interval N;
6. the terminal edge and outputs immediately after it;
7. one minimum/boundary example such as delay=0, count=0, or maximum width.

Reject reasoning such as "looks cleaner" or "likely equivalent" when a concrete edge trace can decide it. Do not prefer longer code or the first listing. Return exactly one JSON object with fields selector_version, candidate_checks, selected_label, ranking, confidence, and reason. selector_version must be v2_mandatory_edge_trace. candidate_checks must contain one concise entry per supplied label describing its first concrete divergence or "no divergence found". selected_label must be one supplied label; ranking must contain every supplied label exactly once."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default=ARK_MODEL)
    parser.add_argument("--reasoning-effort", default="none")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16384)
    parser.add_argument("--max-functional-repairs", type=int, default=3)
    parser.add_argument("--no-contract-review", dest="contract_review", action="store_false")
    parser.add_argument("--prompt-dir", type=Path, default=ROOT / "prompts" / "candidate")
    parser.add_argument("--max-repairs", type=int, default=1)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--case", "--cases", action="extend", nargs="+", default=[])
    selector.add_argument("--all", action="store_true")
    parser.add_argument("--selection", choices=["contract", "llm"], default="contract")
    parser.add_argument("--contract-dir", type=Path, help="Use curated saved contracts instead of generating them")
    parser.add_argument("--skip-official", action="store_true", help="Do not access official ref/testbench files")
    parser.add_argument("--limit", type=int)
    add_ppa_arguments(parser)
    args = parser.parse_args()
    if args.max_repairs < 0 or args.max_functional_repairs < 0 or (args.limit is not None and args.limit < 1):
        parser.error("max-repairs must be nonnegative and limit positive")
    return args


def usage_tokens(calls: list[dict[str, Any]]) -> int:
    return sum(int((call.get("usage") or {}).get("total_tokens", 0) or 0) for call in calls)


def generate_candidate(
    args: argparse.Namespace,
    case_out: Path,
    spec: str,
    candidate_id: int,
    strategy: str,
    system: str,
) -> dict[str, Any]:
    out = case_out / f"candidate_{candidate_id}_{strategy}"
    out.mkdir(parents=True)
    calls: list[dict[str, Any]] = []
    user = f"SPECIFICATION:\n{spec}"
    response, metadata = call_api(args, system, user)
    save_api_call(out, "initial", response, metadata, system, user)
    calls.append(metadata)
    code = extract_sv(response)
    first_syntax_pass = False
    syntax_pass = False
    compiler_error = ""
    final_path = out / "attempt_00.sv"

    for attempt in range(args.max_repairs + 1):
        if attempt:
            repair_user = (
                f"ORIGINAL SPECIFICATION:\n{spec}\n\nCURRENT RTL:\n```systemverilog\n{code}```"
                f"\n\nCOMPILER ERRORS:\n{compiler_error}"
            )
            response, metadata = call_api(args, REPAIR_SYSTEM, repair_user)
            save_api_call(out, f"repair_{attempt:02d}", response, metadata, REPAIR_SYSTEM, repair_user)
            calls.append(metadata)
            code = extract_sv(response)
            final_path = out / f"attempt_{attempt:02d}.sv"
        final_path.write_text(code, encoding="utf-8")
        syntax_pass, compiler_error = syntax_check(final_path, out / f"attempt_{attempt:02d}_syntax.log")
        if attempt == 0:
            first_syntax_pass = syntax_pass
        if syntax_pass:
            break

    module_path = None
    if syntax_pass:
        module_path = out / "module_final.sv"
        shutil.copy2(final_path, module_path)
    return {
        "candidate_id": candidate_id,
        "strategy": strategy,
        "first_syntax_pass": first_syntax_pass,
        "final_syntax_pass": syntax_pass,
        "compile_error": compiler_error if not syntax_pass else "",
        "attempts": attempt + 1,
        "syntax_repairs": attempt, "functional_repairs": 0,
        "initial_module_path": str(final_path) if module_path else None,
        "module_path": str(module_path) if module_path else None,
        "api_calls": len(calls),
        "total_tokens": usage_tokens(calls),
        "official": None,
    }


def blinded_order(case_id: str, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Use a stable case-dependent order so the judge cannot learn strategy position."""
    return sorted(
        candidates,
        key=lambda row: hashlib.sha256(f"{case_id}:{row['candidate_id']}".encode()).hexdigest(),
    )


def select_candidate_llm(
    args: argparse.Namespace,
    case_id: str,
    case_out: Path,
    spec: str,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    eligible = [row for row in candidates if row["final_syntax_pass"]]
    if not eligible:
        return {"status": "no_syntax_clean_candidate", "selected_id": None, "api_calls": 0, "total_tokens": 0}
    if len(eligible) == 1:
        return {"status": "single_eligible", "selected_id": eligible[0]["candidate_id"], "api_calls": 0, "total_tokens": 0}

    ordered = blinded_order(case_id, eligible)
    label_to_id: dict[str, int] = {}
    sections: list[str] = [f"SPECIFICATION:\n{spec}"]
    for index, row in enumerate(ordered, 1):
        label = f"R{index}"
        label_to_id[label] = row["candidate_id"]
        code = Path(row["module_path"]).read_text(encoding="utf-8")
        sections.append(f"{label}:\n```systemverilog\n{code}```")
    user = "\n\n".join(sections)
    selector_out = case_out / "selector"
    selector_out.mkdir()
    response, metadata = call_api(args, SELECTOR_SYSTEM, user)
    save_api_call(selector_out, "selection", response, metadata, SELECTOR_SYSTEM, user)

    status = "selected"
    parsed: dict[str, Any] | None = None
    try:
        parsed = extract_json_object(response)
        label = str(parsed.get("selected_label", ""))
        if label not in label_to_id:
            raise ValueError(f"unknown selected_label: {label}")
        ranking = parsed.get("ranking")
        if not isinstance(ranking, list) or len(ranking) != len(label_to_id) or set(ranking) != set(label_to_id):
            raise ValueError("ranking must contain every supplied label exactly once")
        checks = parsed.get("candidate_checks")
        if not isinstance(checks, dict) or set(checks) != set(label_to_id):
            raise ValueError("candidate_checks must contain every supplied label exactly once")
        selected_id = label_to_id[label]
    except (ValueError, json.JSONDecodeError) as exc:
        status = "selector_parse_error"
        selected_id = None
        (selector_out / "parse_error.txt").write_text(str(exc), encoding="utf-8")
    frozen = {
        "status": status,
        "selected_id": selected_id,
        "label_to_candidate_id": label_to_id,
        "decision": parsed,
        "api_calls": 1,
        "total_tokens": usage_tokens([metadata]),
        "official_feedback_seen": False,
        "selector_version": SELECTOR_VERSION,
    }
    atomic_json(selector_out / "frozen_selection.json", frozen)
    return frozen


def select_candidate(args, case_id, case_out, spec, candidates):
    from candidate_verification import select_with_generated_contract, select_with_saved_contract
    method = getattr(args, 'selection', 'llm')
    if method == 'llm':
        selection = select_candidate_llm(args, case_id, case_out, spec, candidates)
        selection['selection_method'] = 'llm_only_comparison'
    elif getattr(args, 'contract_dir', None):
        selection = select_with_saved_contract(args, case_id, case_out, candidates)
    else:
        selection = select_with_generated_contract(args, case_id, case_out, spec, candidates)
    atomic_json(case_out / 'frozen_selection.json', selection)
    return selection


def aggregate(rows: list[dict[str, Any]], args: argparse.Namespace, cases: list[str]) -> dict[str, Any]:
    completed = len(rows)
    first_candidates = [next((c for c in row['candidates'] if c['candidate_id'] == 1), {}) for row in rows]
    pass1 = sum(bool((candidate.get('initial_official', candidate.get('official')) or {}).get('pass')) for candidate in first_candidates)
    pass3 = sum(any(bool((candidate.get("initial_official", candidate.get('official')) or {}).get("pass")) for candidate in row["candidates"]) for row in rows)
    select3 = sum(bool((row.get("selected_official") or {}).get("pass")) for row in rows)
    syntax1 = sum(bool(candidate.get('first_syntax_pass')) for candidate in first_candidates)
    syntax3 = sum(len(row['candidates']) == 3 and all(bool(candidate["final_syntax_pass"]) for candidate in row["candidates"]) for row in rows)
    result = {
        "evaluation": "three_candidate_" + getattr(args, "selection", "llm"),
        "official_evaluation_enabled": not getattr(args, "skip_official", False),
        "metric_note": "pass@1 and oracle pass@3 are BEFORE functional repairs (after allowed syntax repairs); selected@3 is AFTER functional repairs",
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "max_functional_repairs": getattr(args, "max_functional_repairs", 0),
        "temperature": args.temperature,
        "official_feedback_used_for_generation_or_selection": False,
        "selector_version": SELECTOR_VERSION,
        "selected_cases": cases,
        "completed_cases": completed,
        "metrics": {
            "syntax_at_1_count": syntax1,
            "all_three_final_syntax_count": syntax3,
            "pass_at_1_count": pass1,
            "oracle_pass_at_3_count": pass3,
            "blind_select_at_3_count": select3,
            "pass_at_1_rate": pass1 / completed if completed else None,
            "oracle_pass_at_3_rate": pass3 / completed if completed else None,
            "blind_select_at_3_rate": select3 / completed if completed else None,
        },
        "api_calls": sum(
            sum(candidate["api_calls"] for candidate in row["candidates"])
            + int(row["selection"]["api_calls"])
            for row in rows
        ),
        "total_tokens": sum(
            sum(candidate["total_tokens"] for candidate in row["candidates"])
            + int(row["selection"]["total_tokens"])
            for row in rows
        ),
        "results": rows,
    }
    if getattr(args, 'skip_official', False):
        for key in result['metrics']:
            if 'syntax' not in key:
                result['metrics'][key] = None
    result['metrics']['contract_selected_count'] = sum(row['selection'].get('selected_id') is not None and row['selection'].get('selection_method') != 'llm_only_comparison' for row in rows)
    result['metrics']['selected_at_3_count'] = result['metrics']['blind_select_at_3_count']
    result['metrics']['selected_at_3_rate'] = result['metrics']['blind_select_at_3_rate']
    result['metrics']['oracle_after_repair_count'] = sum(any((c.get('official') or {}).get('pass') for c in r['candidates']) for r in rows) if not getattr(args, 'skip_official', False) else None
    result['usage_note'] = 'api_calls/total_tokens aggregate completed logical stages; failed/interrupted stages may have unknown usage. Inspect api_requests for all recorded transport attempts.'
    return result


def write_csv(path, rows):
    import csv
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        writer.writerow(['题号', '类别', '迭代次数', '语法是否通过', '功能是否通过', '报错原因', '候选编号', '规格测试通过', '选择状态', '语法修复次数', '功能修复次数'])
        for row in rows:
            for candidate in row['candidates']:
                official = candidate.get('official')
                failure = (candidate.get('directed') or {}).get('first_failure')
                history = candidate.get('functional_history') or []
                reason = candidate.get('generation_error') or candidate.get('compile_error') or row['selection'].get('error')
                if not reason and failure:
                    reason = json.dumps(failure, ensure_ascii=False)
                if not reason and history and history[-1].get('status') in {'no_progress', 'repair_error', 'verifier_suspect'}:
                    reason = history[-1].get('error') or history[-1]['status']
                if not reason and official and not official.get('pass'):
                    reason = f"{official.get('status')}; mismatches={official.get('mismatches')}; samples={official.get('samples')}"
                writer.writerow([row['case_id'], candidate['strategy'], max(0, candidate['attempts']-1) + candidate.get('functional_repairs', 0),
                    candidate['final_syntax_pass'], official['pass'] if official else '未评测',
                    str(reason or '')[:2000], candidate['candidate_id'],
                    (candidate.get('directed') or {}).get('passed', '未评测'), row['selection']['status'], max(0, candidate['attempts']-1), candidate.get('functional_repairs', 0)])
    with path.with_name('case_results.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.writer(stream)
        writer.writerow(['题号', '选择状态', '选中候选', '选中代码官方通过', '修复前候选至少一个通过', '修复后候选至少一个通过', '功能修复调用次数'])
        for row in rows:
            evaluated = any(c.get('official') is not None for c in row['candidates'])
            writer.writerow([row['case_id'], row['selection']['status'], row['selection'].get('selected_id'),
                (row.get('selected_official') or {}).get('pass', '未选出' if evaluated else '未评测'),
                any((c.get('initial_official', c.get('official')) or {}).get('pass') for c in row['candidates']) if evaluated else '未评测',
                any((c.get('official') or {}).get('pass') for c in row['candidates']) if evaluated else '未评测',
                sum(c.get('functional_repairs', 0) for c in row['candidates'])])


def main() -> int:
    args = parse_args()
    if not DEFAULT_IVERILOG.exists() or not DEFAULT_VVP.exists():
        raise RuntimeError("Icarus Verilog tools were not found")
    cases = discover_cases(args.dataset, args.case, args.limit)
    output = (args.output or DEFAULT_EXPERIMENT_ROOT / f"three_candidate_select_{datetime.now():%Y%m%d_%H%M%S}").resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    args.api_log_root = output / "api_requests"
    from rtl_json_pipeline.validation import environment_check
    check = environment_check(output / 'tool_check', DEFAULT_IVERILOG, DEFAULT_VVP)
    if not check['passed']:
        atomic_json(output / 'summary.json', {'status': 'environment_failed', 'check': check})
        return 1
    systems = CANDIDATE_SYSTEMS
    prompt_dir = getattr(args, 'prompt_dir', None)
    if prompt_dir:
        systems = tuple((name, (prompt_dir / f'candidate_{name}_system.txt').read_text(encoding='utf-8')) for name, _ in CANDIDATE_SYSTEMS)
        snapshot = output / 'prompts'
        snapshot.mkdir()
        for name, content in systems:
            (snapshot / f'candidate_{name}_system.txt').write_text(content, encoding='utf-8')
    rows: list[dict[str, Any]] = []
    consecutive_api_errors = 0

    for index, case_id in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] {case_id}", flush=True)
        spec = (args.dataset / f"{case_id}_prompt.txt").read_text(encoding="utf-8")
        case_out = output / case_id
        case_out.mkdir()
        (case_out / "original_spec.txt").write_text(spec, encoding="utf-8")
        candidates = []
        try:
            for candidate_id, (strategy, system) in enumerate(systems, 1):
                try:
                    candidate = generate_candidate(args, case_out, spec, candidate_id, strategy, system)
                except Exception as exc:
                    candidate = {'candidate_id': candidate_id, 'strategy': strategy, 'first_syntax_pass': False,
                                 'final_syntax_pass': False, 'attempts': 0, 'module_path': None, 'api_calls': 0,
                                 'total_tokens': 0, 'official': None, 'generation_error': str(exc)}
                candidates.append(candidate)
                atomic_json(case_out / 'candidates.json', candidates)
            if any(c['final_syntax_pass'] for c in candidates):
                selection = select_candidate(args, case_id, case_out, spec, candidates)
            else:
                selection = {'status': 'generation_failed', 'selected_id': None, 'api_calls': 0, 'total_tokens': 0}
                atomic_json(case_out / 'frozen_selection.json', selection)
        except Exception as exc:
            selection = {'status': 'case_error', 'error': str(exc), 'selected_id': None,
                         'api_calls': 0, 'total_tokens': 0}
            atomic_json(case_out / 'frozen_selection.json', selection)
        # Always preserve all attempted cases, including failures before candidate 1.
        while len(candidates) < 3:
            candidates.append({'candidate_id': len(candidates)+1, 'strategy': 'not_completed',
                               'first_syntax_pass': False, 'final_syntax_pass': False,
                               'attempts': 0, 'module_path': None, 'api_calls': 0, 'total_tokens': 0, 'official': None})
        selected_id = selection["selected_id"]
        test = args.dataset / f"{case_id}_test.sv"
        ref = args.dataset / f"{case_id}_ref.sv"
        for candidate in candidates:
            if candidate["final_syntax_pass"] and not args.skip_official:
                candidate_dir = case_out / f"candidate_{candidate['candidate_id']}_{candidate['strategy']}"
                candidate["official"] = official_eval(
                    case_id, Path(candidate["module_path"]), test, ref, candidate_dir
                )
                initial_path = candidate.get('initial_module_path')
                if initial_path and candidate.get('functional_repairs', 0):
                    initial_out = candidate_dir / 'initial_official'
                    initial_out.mkdir()
                    candidate['initial_official'] = official_eval(case_id, Path(initial_path), test, ref, initial_out)
                else:
                    candidate['initial_official'] = candidate['official']
        selected = next((candidate for candidate in candidates if candidate["candidate_id"] == selected_id), None)
        if selected and selected["module_path"]:
            shutil.copy2(selected["module_path"], case_out / "selected.sv")
        row = {
            "case_id": case_id,
            "candidates": candidates,
            "selection": selection,
            "selected_official": selected.get("official") if selected else None,
        }
        row['ppa'] = final_ppa(args, case_out / 'selected.sv' if selected and selected['module_path'] else None,
                               case_out / 'ppa',
                               functional_passed=(row['selected_official'] or {}).get('pass'))
        rows.append(row)
        atomic_json(case_out / "result.json", row)
        summary = aggregate(rows, args, cases)
        consecutive_api_errors = consecutive_api_errors + 1 if selection['status'] in {'case_error', 'contract_api_error', 'generation_failed'} else 0
        summary['not_attempted'] = cases[index:]
        summary['batch_status'] = 'completed' if index == len(cases) else ('stopped_errors' if consecutive_api_errors >= 3 else 'running')
        atomic_json(output / "summary.json", summary)
        write_csv(output / 'results.csv', rows)
        write_summary_ppa_csv(output / 'ppa_results.csv', rows)
        if consecutive_api_errors >= 3 and index < len(cases):
            print('连续三题异常，已停止并保存结果。', flush=True)
            return 1
        statuses = [str((candidate.get("official") or {}).get("status", "not_evaluated" if candidate["final_syntax_pass"] else "syntax_failed")) for candidate in candidates]
        chosen_status = (row["selected_official"] or {}).get("status", "none")
        print(f"  selection={selection['status']}; candidates={statuses}; selected={selected_id}:{chosen_status}", flush=True)

    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
