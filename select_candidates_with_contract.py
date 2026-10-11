#!/usr/bin/env python3
"""Select saved RTL candidates using executable tests derived from the spec."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from run_spec_card_ab import DEFAULT_DATASET, DEFAULT_IVERILOG, DEFAULT_VVP, atomic_json, official_eval
from spec_directed_validator import run_contract


from candidate_runtime import ARK_MODEL

ROOT = Path(__file__).resolve().parent
DEFAULT_EXPERIMENT_ROOT = ROOT / "experiments" / "candidate_selection"
CANDIDATE_RE = re.compile(r"^candidate_(\d+)_(.+)$")


def parse_args() -> argparse.Namespace:
    from ppa import add_ppa_arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-case", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--skip-official", action="store_true")
    parser.add_argument("--output", type=Path)
    add_ppa_arguments(parser)
    return parser.parse_args()


def main() -> int:
    from ppa import final_ppa, write_summary_ppa_csv
    args = parse_args()
    source = args.source_case.resolve()
    contract_path = args.contract.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    case_id = str(contract["case_id"])
    if source.name != case_id:
        raise ValueError("Source case and contract case_id do not match")
    output = (args.output or DEFAULT_EXPERIMENT_ROOT / f"contract_select_{datetime.now():%Y%m%d_%H%M%S}").resolve()
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.mkdir(parents=True)
    args.api_log_root = output / "api_requests"
    (output / "original_spec.txt").write_text(
        (source / "original_spec.txt").read_text(encoding="utf-8"), encoding="utf-8"
    )
    shutil.copy2(contract_path, output / "verification_contract.json")

    candidates: list[dict[str, Any]] = []
    for candidate_dir in sorted(source.glob("candidate_*")):
        match = CANDIDATE_RE.match(candidate_dir.name)
        module = candidate_dir / "module_final.sv"
        if not match or not module.exists():
            continue
        candidate_id = int(match.group(1))
        copied_dir = output / candidate_dir.name
        copied_dir.mkdir()
        copied_module = copied_dir / "module_final.sv"
        shutil.copy2(module, copied_module)
        directed = run_contract(
            contract_path=output / "verification_contract.json",
            rtl_root=args.dataset,
            output_root=copied_dir / "directed",
            iverilog=str(DEFAULT_IVERILOG),
            vvp=str(DEFAULT_VVP),
            dut_module="TopModule",
            rtl_path_override=copied_module,
        )
        candidates.append({
            "candidate_id": candidate_id,
            "strategy": match.group(2),
            "module_path": str(copied_module),
            "directed": directed,
            "official": None,
        })

    passing = [candidate for candidate in candidates if candidate["directed"]["passed"]]
    selected = min(passing, key=lambda row: row["candidate_id"]) if passing else None
    frozen = {
        "selection_method": "spec_derived_executable_contract",
        "uses_reference_or_official_testbench": False,
        "selected_id": selected["candidate_id"] if selected else None,
        "passing_candidate_ids": [candidate["candidate_id"] for candidate in passing],
        "status": "selected" if selected else "no_candidate_passed",
    }
    atomic_json(output / "frozen_selection.json", frozen)

    # Official files are accessed only after the selection is frozen.
    test = args.dataset / f"{case_id}_test.sv"
    ref = args.dataset / f"{case_id}_ref.sv"
    for candidate in candidates:
        candidate_dir = Path(candidate["module_path"]).parent
        if not args.skip_official:
            candidate["official"] = official_eval(case_id, Path(candidate["module_path"]), test, ref, candidate_dir)
    selected_official = selected["official"] if selected else None
    if selected:
        shutil.copy2(selected["module_path"], output / "selected.sv")
    summary = {
        "case_id": case_id,
        "selection": frozen,
        "selected_official": selected_official,
        "candidates": candidates,
    }
    summary['ppa'] = final_ppa(args, output / 'selected.sv' if selected else None,
                               output / 'ppa', functional_passed=(selected_official or {}).get('pass'))
    atomic_json(output / "summary.json", summary)
    write_summary_ppa_csv(output / 'ppa_results.csv', [summary])
    print(json.dumps({
        "case_id": case_id,
        "directed_pass": frozen["passing_candidate_ids"],
        "selected": frozen["selected_id"],
        "selected_official": (selected_official or {}).get("status"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
