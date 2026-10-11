#!/usr/bin/env python3
"""Run specification-derived directed tests without a reference oracle.

The RTL under test may be a dataset reference implementation while validating
this prototype, but expected values are stored explicitly in a contract that
was derived from the natural-language specification.  No second implementation
is compiled and no source-code comparison is performed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import shutil
import subprocess
from typing import Any, Dict, Iterable, List
from candidate_runtime import DEFAULT_DATASET, DEFAULT_IVERILOG, DEFAULT_VVP, as_text


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONTRACT_DIR = SCRIPT_DIR / "verification_contracts"
DEFAULT_RTL_ROOT = DEFAULT_DATASET
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "experiments" / "spec_directed_results"


def validate_contract(contract):
    """This small saved-contract format permits literal expectations only."""
    identifier = re.compile(r'^[A-Za-z_][A-Za-z0-9_$]*$')
    literal = re.compile(r"^(?:[0-9]+|[0-9]+'[sS]?[bBoOdDhH][0-9a-fA-F_]+|'[01])$")
    ports = contract.get('ports', [])
    names = [p.get('name', '') for p in ports]
    if len(set(names)) != len(names) or not all(identifier.fullmatch(n) for n in names):
        raise ValueError('Invalid or duplicate port names')
    if any(p.get('direction') not in {'input', 'output'} or not 1 <= int(p.get('width', 1)) <= 65536 for p in ports):
        raise ValueError('Invalid port direction/width')
    inputs = {p['name'] for p in ports if p['direction'] == 'input'}
    outputs = set(names) - inputs
    clock = contract.get('clock')
    if clock and (clock['name'] not in inputs or int(clock.get('half_period', 5)) < 1):
        raise ValueError('Invalid clock')
    def values(group, allowed):
        if set(group) - allowed or not all(literal.fullmatch(str(v)) for v in group.values()):
            raise ValueError('Signal direction mismatch or nonliteral value in saved contract')
    values(contract.get('initial', {}), inputs)
    tests = contract.get('tests', [])
    if not tests or not outputs:
        raise ValueError('Contract needs outputs and nonempty tests')
    checked = set()
    for test in tests:
        count = 0
        for step in test['steps']:
            if set(step) - {'set', 'expect', 'delay', 'posedge', 'clock'}:
                raise ValueError('Unknown test step field')
            values(step.get('set', {}), inputs)
            values(step.get('expect', {}), outputs)
            count += len(step.get('expect', {}))
            checked.update(step.get('expect', {}))
            if 'delay' in step and int(step['delay']) < 1:
                raise ValueError('delay must be positive')
            if 'posedge' in step and (not clock or int(step['posedge']) < 1 or step.get('clock', clock['name']) != clock['name']):
                raise ValueError('Invalid clock wait')
        if not count:
            raise ValueError('Every test requires an output check')
    if checked != outputs:
        raise ValueError('Every output requires a check')


def _sv_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _port_width(port: Dict[str, Any]) -> str:
    width = int(port.get("width", 1))
    return "" if width == 1 else f"[{width - 1}:0] "


def build_testbench(contract: Dict[str, Any], dut_module: str | None = None) -> str:
    """Translate a declarative directed-test contract into a self-checking TB."""
    validate_contract(contract)
    module_name = dut_module or contract.get("dut_module", "TopModule")
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_$]*', module_name):
        raise ValueError('Invalid DUT module name')
    ports = contract["ports"]
    inputs = [port for port in ports if port["direction"] == "input"]
    outputs = [port for port in ports if port["direction"] == "output"]
    known_names = {port["name"] for port in ports}

    if not outputs:
        raise ValueError("contract must define at least one output")
    for test in contract["tests"]:
        for step in test["steps"]:
            for group in ("set", "expect"):
                unknown = set(step.get(group, {})) - known_names
                if unknown:
                    raise ValueError(f"unknown signals in {test['id']}/{group}: {sorted(unknown)}")

    lines: List[str] = [
        "`timescale 1ns/1ps",
        "module spec_directed_tb;",
        "  integer checks = 0;",
        "  integer failures = 0;",
    ]
    for port in inputs:
        lines.append(f"  logic {_port_width(port)}{port['name']};")
    for port in outputs:
        lines.append(f"  wire {_port_width(port)}{port['name']};")

    lines.extend(["", f"  {module_name} dut ("])
    lines.extend(
        f"    .{port['name']}({port['name']}){',' if index < len(ports) - 1 else ''}"
        for index, port in enumerate(ports)
    )
    lines.append("  );")

    clock = contract.get("clock")
    if clock:
        clock_name = clock["name"]
        half_period = int(clock.get("half_period", 5))
        lines.extend([
            "",
            f"  initial {clock_name} = 1'b0;",
            f"  always #{half_period} {clock_name} = ~{clock_name};",
        ])

    lines.extend(["", "  initial begin"])
    for name, value in contract.get("initial", {}).items():
        if name not in known_names:
            raise ValueError(f"unknown initial signal: {name}")
        lines.append(f"    {name} = {value};")
    lines.append("    #1;")

    for test in contract["tests"]:
        test_id = _sv_string(test["id"])
        requirement = _sv_string(test.get("requirement", ""))
        lines.append(f'    $display("DIRECTED_TEST|{test_id}");')
        for step in test["steps"]:
            for name, value in step.get("set", {}).items():
                lines.append(f"    {name} = {value};")
            if "delay" in step:
                lines.append(f"    #{int(step['delay'])};")
            if "posedge" in step:
                count = int(step["posedge"])
                lines.append(f"    repeat ({count}) @(posedge {step.get('clock', clock['name'])});")
                lines.append("    #1;")
            if step.get('set') and 'delay' not in step and 'posedge' not in step:
                lines.append('    #1;')
            for name, expected in step.get("expect", {}).items():
                lines.extend([
                    "    checks = checks + 1;",
                    f"    if ({name} !== {expected}) begin",
                    "      failures = failures + 1;",
                    (
                        f'      $display("DIRECTED_FAIL|test={test_id}|signal={name}'
                        f'|expected=%0h|actual=%0h|requirement={requirement}", '
                        f"{expected}, {name});"
                    ),
                    "    end",
                ])

    lines.extend([
        '    $display("DIRECTED_SUMMARY|checks=%0d|failures=%0d", checks, failures);',
        "    if (failures == 0) $finish(0);",
        "    else $fatal(1, \"directed functional checks failed\");",
        "  end",
        "endmodule",
        "",
    ])
    return "\n".join(lines)


def _resolve_executable(explicit: str | None, name: str, windows_default: str) -> str:
    if explicit:
        return explicit
    found = shutil.which(name)
    if found:
        return found
    if Path(windows_default).exists():
        return windows_default
    raise FileNotFoundError(f"cannot find {name}; pass its path explicitly")


def run_contract(
    contract_path: Path,
    rtl_root: Path,
    output_root: Path,
    iverilog: str,
    vvp: str,
    dut_module: str | None = None,
    rtl_path_override: Path | None = None,
) -> Dict[str, Any]:
    contract_path = contract_path.resolve()
    rtl_root = rtl_root.resolve()
    output_root = output_root.resolve()
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    case_id = contract["case_id"]
    rtl_path = rtl_path_override.resolve() if rtl_path_override else rtl_root / contract["rtl_file"]
    case_output = output_root / case_id
    case_output.mkdir(parents=True, exist_ok=True)
    tb_path = case_output / "generated_directed_tb.sv"
    simulation_path = case_output / "directed_sim.vvp"
    report_path = case_output / "result.json"
    tb_path.write_text(build_testbench(contract, dut_module), encoding="utf-8")

    result: Dict[str, Any] = {
        "case_id": case_id,
        "contract": str(contract_path),
        "rtl": str(rtl_path),
        "uses_reference_oracle": False,
        "test_count": len(contract["tests"]),
        "status": "infrastructure_error",
        "passed": False,
    }
    if not rtl_path.exists():
        result["reason"] = "RTL file does not exist"
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    try:
        return _execute_contract(result, contract, report_path, case_output, rtl_path, tb_path, simulation_path, iverilog, vvp)
    except (OSError, subprocess.TimeoutExpired) as exc:
        result.update(status='infrastructure_error', reason=str(exc))
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
        return result


def _execute_contract(result, contract, report_path, case_output, rtl_path, tb_path, simulation_path, iverilog, vvp):
    compile_process = subprocess.run(
        [iverilog, "-g2012", "-s", "spec_directed_tb", "-o", str(simulation_path), str(rtl_path), str(tb_path)],
        cwd=case_output,
        capture_output=True,
        text=True, encoding="utf-8", errors="replace",
        timeout=60,
    )
    result["compile_returncode"] = compile_process.returncode
    result["compile_stdout"] = compile_process.stdout
    result["compile_stderr"] = compile_process.stderr
    if compile_process.returncode != 0:
        result.update(status="compile_error", reason="RTL and generated testbench did not compile")
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    try:
        simulation_process = subprocess.run(
            [vvp, str(simulation_path)],
            cwd=case_output,
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=int(contract.get("timeout_seconds", 30)),
        )
    except subprocess.TimeoutExpired as exc:
        result.update(
            status="timeout",
            reason="directed testbench timed out",
            simulation_stdout=as_text(exc.stdout),
            simulation_stderr=as_text(exc.stderr),
        )
        report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        return result

    stdout = simulation_process.stdout
    summary = re.search(r'^DIRECTED_SUMMARY\|checks=(\d+)\|failures=(\d+)\s*$', stdout, re.M)
    summary_seen = summary is not None and int(summary[1]) > 0 and int(summary[2]) == 0
    failure_seen = "DIRECTED_FAIL|" in stdout
    passed = simulation_process.returncode == 0 and summary_seen and not failure_seen
    result.update(
        status="pass" if passed else "functional_failure",
        passed=passed,
        reason=(
            "all specification-derived directed checks passed"
            if passed
            else "one or more specification-derived directed checks failed"
        ),
        simulation_returncode=simulation_process.returncode,
        simulation_stdout=stdout,
        simulation_stderr=simulation_process.stderr,
    )
    report_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def _contract_paths(contract_dir: Path, selected_cases: Iterable[str]) -> List[Path]:
    selected = set(selected_cases)
    paths = sorted(contract_dir.glob("*.json"))
    if selected:
        paths = [path for path in paths if path.stem in selected]
        missing = selected - {path.stem for path in paths}
        if missing:
            raise FileNotFoundError(f"contracts not found: {sorted(missing)}")
    return paths


def _latest_verified_legacy_rtl(legacy_case_dir: Path) -> Path | None:
    """Select the exact candidate associated with the latest validator report."""
    grouped = []
    for iteration_dir in legacy_case_dir.glob("iteration_*"):
        try:
            iteration = int(iteration_dir.name.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        rtl = iteration_dir / "module_for_verification.sv"
        report = iteration_dir / "func_report.txt"
        if rtl.exists() and report.exists():
            grouped.append((iteration, rtl))
    if grouped:
        return max(grouped, key=lambda item: item[0])[1]

    flat = []
    for rtl in legacy_case_dir.glob("module_for_verification_iteration_*.sv"):
        try:
            iteration = int(rtl.stem.rsplit("_", 1)[1])
        except (IndexError, ValueError):
            continue
        if (legacy_case_dir / f"func_report_iteration_{iteration}.txt").exists():
            flat.append((iteration, rtl))
    if flat:
        return max(flat, key=lambda item: item[0])[1]

    for name in ("module_final.sv", "module_failed_final.sv", "module.sv"):
        candidate = legacy_case_dir / name
        if candidate.exists():
            return candidate
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts", type=Path, default=DEFAULT_CONTRACT_DIR)
    parser.add_argument("--rtl-root", type=Path, default=DEFAULT_RTL_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--legacy-root",
        type=Path,
        help="validate the latest actually-verified candidate in each legacy case directory",
    )
    parser.add_argument("--case", action="append", default=[], help="case id; repeat for multiple cases")
    parser.add_argument("--dut-module", help="override module name, e.g. TopModule for generated RTL")
    parser.add_argument("--iverilog")
    parser.add_argument("--vvp")
    args = parser.parse_args()

    iverilog = _resolve_executable(args.iverilog, "iverilog", str(DEFAULT_IVERILOG))
    vvp = _resolve_executable(args.vvp, "vvp", str(DEFAULT_VVP))
    args.output.mkdir(parents=True, exist_ok=True)

    results = []
    for path in _contract_paths(args.contracts, args.case):
        contract = json.loads(path.read_text(encoding="utf-8"))
        rtl_override = None
        if args.legacy_root:
            legacy_case_dir = args.legacy_root.resolve() / contract["case_id"]
            rtl_override = _latest_verified_legacy_rtl(legacy_case_dir)
            if rtl_override is None:
                # Keep a missing legacy candidate missing; never silently fall
                # back to the dataset reference implementation.
                rtl_override = legacy_case_dir / "__missing_verified_candidate__.sv"
        results.append(
            run_contract(
                path,
                args.rtl_root,
                args.output,
                iverilog,
                vvp,
                args.dut_module,
                rtl_override,
            )
        )
    summary = {
        "uses_reference_oracle": False,
        "total": len(results),
        "passed": sum(item["passed"] for item in results),
        "failed": sum(not item["passed"] for item in results),
        "results": results,
    }
    (args.output / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    for item in results:
        marker = "PASS" if item["passed"] else "FAIL"
        print(f"[{marker}] {item['case_id']}: {item['status']} - {item['reason']}")
    print(f"Summary: {summary['passed']}/{summary['total']} passed")
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
