#!/usr/bin/env python3
"""Blindly reselect saved candidates with the current selector, then evaluate.

Only original_spec.txt and candidate_*/module_final.sv are read from the source
run before selection. Existing official logs/results are deliberately ignored.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from run_spec_card_ab import (
    DEFAULT_DATASET,
    DEFAULT_IVERILOG,
    DEFAULT_VVP,
    atomic_json,
    official_eval,
    syntax_check,
)
from run_three_candidate_select import aggregate, select_candidate


from candidate_runtime import ARK_MODEL

ROOT = Path(__file__).resolve().parent
DEFAULT_EXPERIMENT_ROOT = ROOT / "experiments" / "candidate_selection"
CANDIDATE_DIR_RE = re.compile(r"^candidate_(\d+)_(.+)$")


def parse_args() -> argparse.Namespace:
    from ppa import add_ppa_arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", choices=["contract", "llm"], default="contract")
    parser.add_argument("--contract-dir", type=Path)
    parser.add_argument("--skip-official", action="store_true")
    parser.add_argument("--max-functional-repairs", type=int, default=3)
    parser.add_argument("--no-contract-review", dest="contract_review", action="store_false")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--model", default=ARK_MODEL)
    parser.add_argument("--reasoning-effort", default="none")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=16384)
    parser.add_argument("--max-repairs", type=int, default=0)
    parser.add_argument("--case", action="append", default=[])
    add_ppa_arguments(parser)
    return parser.parse_args()


def load_candidates(source_case: Path, destination_case: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for source_dir in sorted(source_case.glob("candidate_*")):
        match = CANDIDATE_DIR_RE.match(source_dir.name)
        module = source_dir / "module_final.sv"
        if not match or not module.exists():
            continue
        candidate_id, strategy = int(match.group(1)), match.group(2)
        destination_dir = destination_case / source_dir.name
        destination_dir.mkdir()
        destination_module = destination_dir / "module_final.sv"
        shutil.copy2(module, destination_module)
        initial_module = destination_dir / 'initial.sv'
        shutil.copy2(module, initial_module)
        syntax_pass, _ = syntax_check(destination_module, destination_dir / "syntax.log")
        candidates.append({
            "candidate_id": candidate_id,
            "strategy": strategy,
            "first_syntax_pass": syntax_pass,
            "final_syntax_pass": syntax_pass,
            "attempts": 0,
            "module_path": str(destination_module) if syntax_pass else None,
            "initial_module_path": str(initial_module) if syntax_pass else None,
            "api_calls": 0,
            "total_tokens": 0,
            "official": None,
        })
    return sorted(candidates, key=lambda row: row["candidate_id"])


def main() -> int:
    from ppa import final_ppa, write_summary_ppa_csv
    args = parse_args()
    if not DEFAULT_IVERILOG.exists() or not DEFAULT_VVP.exists():
        raise RuntimeError("Icarus Verilog tools were not found")
    source = args.source.resolve()
    output = (args.output or DEFAULT_EXPERIMENT_ROOT / f"reselect_{datetime.now():%Y%m%d_%H%M%S}").resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    args.api_log_root = output / "api_requests"
    available = sorted(path.name for path in source.iterdir() if path.is_dir() and (path / "original_spec.txt").exists())
    cases = []
    for query in args.case:
        matches = [case for case in available if case == query or case.startswith(query)]
        if len(matches) != 1:
            raise ValueError(f"case selector {query!r} matched {len(matches)} cases")
        cases.append(matches[0])
    if not cases:
        cases = available

    rows: list[dict[str, Any]] = []
    for index, case_id in enumerate(cases, 1):
        print(f"[{index}/{len(cases)}] {case_id}", flush=True)
        source_case = source / case_id
        case_out = output / case_id
        case_out.mkdir()
        spec = (source_case / "original_spec.txt").read_text(encoding="utf-8")
        (case_out / "original_spec.txt").write_text(spec, encoding="utf-8")
        candidates = load_candidates(source_case, case_out)
        if not candidates:
            raise RuntimeError(f"no candidates found for {case_id}")

        # Selection is completed and persisted before official files are used.
        selection = select_candidate(args, case_id, case_out, spec, candidates)
        selected_id = selection["selected_id"]
        test = args.dataset / f"{case_id}_test.sv"
        ref = args.dataset / f"{case_id}_ref.sv"
        for candidate in candidates:
            if candidate["final_syntax_pass"] and not args.skip_official:
                candidate_dir = Path(candidate["module_path"]).parent
                candidate["official"] = official_eval(case_id, Path(candidate["module_path"]), test, ref, candidate_dir)
                if candidate.get('functional_repairs', 0):
                    initial_dir = candidate_dir / 'initial_official'
                    initial_dir.mkdir()
                    candidate['initial_official'] = official_eval(case_id, Path(candidate['initial_module_path']), test, ref, initial_dir)
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
        summary["source_candidates"] = str(source)
        summary["generation_api_calls"] = 0
        atomic_json(output / "summary.json", summary)
        write_summary_ppa_csv(output / 'ppa_results.csv', rows)
        status = (row["selected_official"] or {}).get("status", "none")
        print(f"  selected={selected_id}:{status}", flush=True)
    print(f"Results: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
