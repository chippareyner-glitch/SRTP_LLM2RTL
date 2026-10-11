#!/usr/bin/env python3
"""Validate a constrained DesignIR and render deterministic SystemVerilog.

DesignIR deliberately describes behavior rather than accepting arbitrary HDL
fragments.  The first version supports continuous combinational assignments and
priority-ordered sequential state transitions, which are enough to represent a
large fraction of the current benchmark while keeping generation auditable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Set


IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")
EXPRESSION_RE = re.compile(r"^[A-Za-z0-9_'bBoOdDhHxXzZ\s\[\]():?~!&|^+\-*/%<>=.,{}]+$")
IDENTIFIER_TOKEN_RE = re.compile(r"(?<!['\d])\b[A-Za-z_]\w*\b")
RESERVED_EXPRESSION_WORDS = {
    "otherwise", "signed", "unsigned", "true", "false",
}


class DesignIRError(ValueError):
    """Raised when DesignIR is incomplete, unsafe, or internally inconsistent."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DesignIRError(message)


def _identifier(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(IDENTIFIER_RE.fullmatch(value)), f"{path}: invalid identifier")
    return value


def _width(value: Any, path: str) -> int:
    _require(isinstance(value, int) and value > 0, f"{path}: width must be a positive integer")
    return value


def _range(width: int) -> str:
    return "" if width == 1 else f"[{width - 1}:0] "


def _validate_expression(expression: Any, known_names: Set[str], path: str) -> str:
    _require(isinstance(expression, str) and expression.strip(), f"{path}: expression must be non-empty")
    expression = expression.strip()
    _require(len(expression) <= 1000, f"{path}: expression is too long")
    _require(bool(EXPRESSION_RE.fullmatch(expression)), f"{path}: unsupported characters in expression")
    forbidden = (";", "`", "$")
    lowered = expression.lower()
    _require(not any(token in lowered for token in forbidden), f"{path}: HDL statement/code injection is forbidden")
    _require(
        not re.search(r"\b(?:module|endmodule|always|initial|assign|function|task)\b", lowered),
        f"{path}: HDL statement/code injection is forbidden",
    )
    unknown = {
        token for token in IDENTIFIER_TOKEN_RE.findall(expression)
        if token not in known_names and token.lower() not in RESERVED_EXPRESSION_WORDS
    }
    _require(not unknown, f"{path}: unknown identifiers {sorted(unknown)}")
    _require(expression.count("(") == expression.count(")"), f"{path}: unbalanced parentheses")
    _require(expression.count("[") == expression.count("]"), f"{path}: unbalanced brackets")
    _require(expression.count("{") == expression.count("}"), f"{path}: unbalanced braces")
    return expression


def validate_design_ir(ir: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and return the same IR for fluent use by callers."""
    _require(isinstance(ir, dict), "root must be an object")
    _require(ir.get("schema_version") == 1, "schema_version must be 1")
    module = ir.get("module")
    _require(isinstance(module, dict), "module must be an object")
    module_name = _identifier(module.get("name"), "module.name")
    _require(module_name == "TopModule", "module.name must be TopModule")
    ports = module.get("ports")
    _require(isinstance(ports, list) and ports, "module.ports must be a non-empty list")

    known: Set[str] = set()
    output_names: Set[str] = set()
    port_by_name: Dict[str, Dict[str, Any]] = {}
    for index, port in enumerate(ports):
        _require(isinstance(port, dict), f"module.ports[{index}] must be an object")
        name = _identifier(port.get("name"), f"module.ports[{index}].name")
        _require(name not in known, f"duplicate port {name}")
        direction = port.get("direction")
        _require(direction in {"input", "output"}, f"port {name}: direction must be input or output")
        width = _width(port.get("width", 1), f"port {name}.width")
        port["width"] = width
        known.add(name)
        port_by_name[name] = port
        if direction == "output":
            output_names.add(name)

    design = ir.get("design")
    _require(isinstance(design, dict), "design must be an object")
    kind = design.get("kind")
    _require(kind in {"combinational", "sequential"}, "design.kind must be combinational or sequential")

    signals = design.get("signals", [])
    _require(isinstance(signals, list), "design.signals must be a list")
    for index, signal in enumerate(signals):
        name = _identifier(signal.get("name"), f"design.signals[{index}].name")
        _require(name not in known, f"duplicate signal {name}")
        signal["width"] = _width(signal.get("width", 1), f"signal {name}.width")
        known.add(name)

    assignments = design.get("outputs", [])
    _require(isinstance(assignments, list), "design.outputs must be a list")
    assigned_targets: Set[str] = set()
    for index, assignment in enumerate(assignments):
        target = _identifier(assignment.get("target"), f"design.outputs[{index}].target")
        _require(target in output_names, f"output assignment target {target} is not an output port")
        _require(target not in assigned_targets, f"output {target} is assigned more than once")
        assigned_targets.add(target)

    if kind == "combinational":
        for index, signal in enumerate(signals):
            _validate_expression(signal.get('expr'), known, f'design.signals[{index}].expr')
        for index, assignment in enumerate(assignments):
            assignment["expr"] = _validate_expression(
                assignment.get("expr"), known, f"design.outputs[{index}].expr"
            )
        _require(not design.get("registers"), "combinational design cannot declare registers")
        _require(assigned_targets == output_names, f"undriven outputs: {sorted(output_names - assigned_targets)}")
        return ir

    clock = design.get("clock")
    _require(isinstance(clock, dict), "sequential design requires clock")
    clock_signal = _identifier(clock.get("signal"), "design.clock.signal")
    _require(clock_signal in port_by_name and port_by_name[clock_signal]["direction"] == "input", "clock must be an input port")
    _require(clock.get("edge") in {"posedge", "negedge"}, "clock.edge must be posedge or negedge")

    registers = design.get("registers")
    _require(isinstance(registers, list) and registers, "sequential design requires registers")
    register_names: Set[str] = set()
    for index, register in enumerate(registers):
        name = _identifier(register.get("name"), f"design.registers[{index}].name")
        _require(name not in register_names, f"duplicate register {name}")
        _require(name not in known or name in output_names, f"register {name} conflicts with an existing signal")
        register["width"] = _width(register.get("width", 1), f"register {name}.width")
        if name in port_by_name:
            _require(port_by_name[name]["direction"] == "output", f"register port {name} must be an output")
            _require(port_by_name[name]["width"] == register["width"], f"register {name} width differs from port width")
        else:
            known.add(name)
        register_names.add(name)

    for index, assignment in enumerate(assignments):
        assignment["expr"] = _validate_expression(
            assignment.get("expr"), known, f"design.outputs[{index}].expr"
        )

    _require(not (assigned_targets & register_names), 'output cannot have both continuous and register drivers')
    for index, signal in enumerate(signals):
        _validate_expression(signal.get('expr'), known, f'design.signals[{index}].expr')

    reset = design.get("reset")
    if reset is not None:
        _require(isinstance(reset, dict), "design.reset must be an object")
        reset_signal = _identifier(reset.get("signal"), "design.reset.signal")
        _require(reset_signal in port_by_name and port_by_name[reset_signal]["direction"] == "input", "reset must be an input port")
        _require(reset.get("type") in {"synchronous", "asynchronous"}, "reset.type is invalid")
        _require(reset.get("level") in {"high", "low"}, "reset.level is invalid")
        values = reset.get("values")
        _require(isinstance(values, dict), "reset.values must be an object")
        _require(set(values) == register_names, "reset.values must initialize every register exactly once")
        for name, value in values.items():
            values[name] = _validate_expression(value, known, f"reset.values.{name}")

    transitions = design.get("transitions")
    _require(isinstance(transitions, list) and transitions, "sequential design requires transitions")
    priorities = []
    otherwise_seen = False
    for index, transition in enumerate(transitions):
        priority = transition.get("priority")
        _require(isinstance(priority, int) and priority >= 0, f"transition {index}: priority must be a non-negative integer")
        priorities.append(priority)
        condition = transition.get("when")
        _require(isinstance(condition, str), f"transition {index}: when must be a string")
        if condition == "otherwise":
            _require(not otherwise_seen, "only one otherwise transition is allowed")
            otherwise_seen = True
        else:
            _require(not otherwise_seen, "otherwise transition must be last by priority")
            transition["when"] = _validate_expression(condition, known, f"transition {index}.when")
        updates = transition.get("updates")
        _require(isinstance(updates, dict) and updates, f"transition {index}: updates must be non-empty")
        _require(set(updates) <= register_names, f"transition {index}: update targets must be registers")
        for name, value in updates.items():
            updates[name] = _validate_expression(value, known, f"transition {index}.updates.{name}")
    _require(len(priorities) == len(set(priorities)), "transition priorities must be unique")
    _require(priorities == sorted(priorities), "transitions must be sorted by ascending priority")

    driven_by_register = output_names & register_names
    _require(
        assigned_targets | driven_by_register == output_names,
        f"undriven outputs: {sorted(output_names - assigned_targets - driven_by_register)}",
    )
    return ir


def render_systemverilog(ir: Dict[str, Any]) -> str:
    ir = validate_design_ir(ir)
    module = ir["module"]
    design = ir["design"]
    ports = module["ports"]
    lines: List[str] = [f"module {module['name']} ("]
    for index, port in enumerate(ports):
        comma = "," if index < len(ports) - 1 else ""
        lines.append(
            f"    {port['direction']} logic {_range(port['width'])}{port['name']}{comma}"
        )
    lines.extend([(");"), ""])

    port_names = {port["name"] for port in ports}
    for signal in design.get("signals", []):
        lines.append(f"    logic {_range(signal['width'])}{signal['name']};")
    if design["kind"] == "sequential":
        for register in design["registers"]:
            if register["name"] not in port_names:
                lines.append(f"    logic {_range(register['width'])}{register['name']};")
    if design.get("signals") or (
        design["kind"] == "sequential"
        and any(register["name"] not in port_names for register in design["registers"])
    ):
        lines.append("")

    for signal in design.get("signals", []):
        lines.append(f"    assign {signal['name']} = {signal['expr']};")
    if design.get("signals") and design.get("outputs"):
        lines.append("")

    for assignment in design.get("outputs", []):
        lines.append(f"    assign {assignment['target']} = {assignment['expr']};")

    if design["kind"] == "sequential":
        if design.get("outputs"):
            lines.append("")
        clock = design["clock"]
        reset = design.get("reset")
        sensitivity = f"{clock['edge']} {clock['signal']}"
        if reset and reset["type"] == "asynchronous":
            reset_edge = "posedge" if reset["level"] == "high" else "negedge"
            sensitivity += f" or {reset_edge} {reset['signal']}"
        lines.append(f"    always_ff @({sensitivity}) begin")
        indent = "        "
        if reset:
            reset_condition = reset["signal"] if reset["level"] == "high" else f"!{reset['signal']}"
            lines.append(f"{indent}if ({reset_condition}) begin")
            for register in design["registers"]:
                lines.append(f"{indent}    {register['name']} <= {reset['values'][register['name']]};")
            lines.append(f"{indent}end else begin")
            indent += "    "

        for index, transition in enumerate(design["transitions"]):
            condition = transition["when"]
            if condition == "otherwise":
                opener = "else begin" if index else "begin"
            else:
                opener = f"if ({condition}) begin" if index == 0 else f"else if ({condition}) begin"
            lines.append(f"{indent}{opener}")
            for name, value in transition["updates"].items():
                lines.append(f"{indent}    {name} <= {value};")
            lines.append(f"{indent}end")
        if reset:
            lines.append("        end")
        lines.append("    end")

    lines.extend(["", "endmodule", ""])
    return "\n".join(lines)


def load_ir(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ir", type=Path)
    parser.add_argument("--output", "-o", type=Path, required=True)
    args = parser.parse_args()
    rendered = render_systemverilog(load_ir(args.ir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Generated {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
