"""Strict schema for category-independent executable behavior contracts."""

from __future__ import annotations

import re
from typing import Any


IDENTIFIER = re.compile(r"^[A-Za-z_]\w*$")
EXPRESSION = re.compile(r"^[A-Za-z0-9_'bBoOdDhHxXzZ\s\[\]():?~!&|^+\-*/%<>=.,{}]+$")
IDENTIFIER_TOKEN = re.compile(r"(?<!['\d])\b[A-Za-z_]\w*\b")
RESERVED = {"signed", "unsigned", "true", "false"}


class ContractSchemaError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractSchemaError(message)


def _exact(value: Any, required: set[str], optional: set[str], path: str) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{path}: expected object")
    missing = required - set(value)
    extra = set(value) - required - optional
    _require(not missing and not extra, f"{path}: missing={sorted(missing)}, extra={sorted(extra)}")
    return value


def _identifier(value: Any, path: str) -> str:
    _require(isinstance(value, str) and bool(IDENTIFIER.fullmatch(value)), f"{path}: invalid identifier")
    return value


def _positive_int(value: Any, path: str) -> int:
    _require(isinstance(value, int) and not isinstance(value, bool) and value > 0, f"{path}: expected positive integer")
    return value


def _refs(value: Any, allowed: set[str], path: str) -> list[str]:
    _require(isinstance(value, list) and value and all(isinstance(item, str) for item in value), f"{path}: invalid source_refs")
    unknown = set(value) - allowed
    _require(not unknown, f"{path}: unknown source refs {sorted(unknown)}")
    return value


def _expression(value: Any, known: set[str], path: str) -> str:
    _require(isinstance(value, str) and value.strip(), f"{path}: expression must be non-empty")
    text = value.strip()
    _require(len(text) <= 1000 and bool(EXPRESSION.fullmatch(text)), f"{path}: unsupported expression")
    lowered = text.lower()
    _require(not any(item in lowered for item in (";", "`", "$")), f"{path}: statement injection forbidden")
    _require(not re.search(r"\b(?:module|endmodule|always|initial|assign|task|function)\b", lowered), f"{path}: statement injection forbidden")
    unknown = {
        token for token in IDENTIFIER_TOKEN.findall(text)
        if token not in known and token.lower() not in RESERVED
    }
    _require(not unknown, f"{path}: unknown identifiers {sorted(unknown)}")
    for opening, closing in (("(", ")"), ("[", "]"), ("{", "}")):
        _require(text.count(opening) == text.count(closing), f"{path}: unbalanced {opening}{closing}")
    return text


def _values(value: Any, targets: set[str], expression_names: set[str], path: str) -> dict[str, str]:
    _require(isinstance(value, dict) and value, f"{path}: expected non-empty object")
    for name, expression in value.items():
        _identifier(name, f"{path} key")
        _require(name in targets, f"{path}: invalid target {name}")
        _expression(expression, expression_names, f"{path}.{name}")
    return value


def _validate_steps(
    steps: Any,
    inputs: set[str],
    outputs: set[str],
    clocks: set[str],
    models: set[str],
    path: str,
) -> None:
    _require(isinstance(steps, list) and steps, f"{path}: steps must be non-empty")
    # Oracle and stimulus must never depend on DUT outputs, including indirectly.
    expression_names = inputs | models
    for index, raw_step in enumerate(steps):
        step_path = f"{path}[{index}]"
        _require(isinstance(raw_step, dict), f"{step_path}: expected object")
        op = raw_step.get("op")
        _require(op in {"drive", "wait_edge", "delay", "expect", "set_model", "update_model", "repeat"}, f"{step_path}: unsupported op {op!r}")
        if op == "drive":
            _exact(raw_step, {"op", "values"}, set(), step_path)
            _values(raw_step["values"], inputs - clocks, expression_names, f"{step_path}.values")
        elif op == "wait_edge":
            _exact(raw_step, {"op", "signal", "edge"}, set(), step_path)
            _require(raw_step["signal"] in clocks, f"{step_path}.signal: not a declared clock")
            _require(raw_step["edge"] in {"posedge", "negedge"}, f"{step_path}.edge: invalid")
        elif op == "delay":
            _exact(raw_step, {"op", "ticks"}, set(), step_path)
            _positive_int(raw_step["ticks"], f"{step_path}.ticks")
        elif op == "expect":
            _exact(raw_step, {"op", "values", "label"}, set(), step_path)
            _require(isinstance(raw_step["label"], str) and raw_step["label"], f"{step_path}.label: required")
            _values(raw_step["values"], outputs, expression_names, f"{step_path}.values")
        elif op in {"set_model", "update_model"}:
            _exact(raw_step, {"op", "values"}, set(), step_path)
            _values(raw_step["values"], models, expression_names, f"{step_path}.values")
        elif op == "repeat":
            _exact(raw_step, {"op", "count", "steps"}, set(), step_path)
            _positive_int(raw_step["count"], f"{step_path}.count")
            _validate_steps(raw_step["steps"], inputs, outputs, clocks, models, f"{step_path}.steps")


def validate_contract(bundle: dict[str, Any], registry: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate a contract and guarantee every declared requirement has a scenario."""
    _exact(
        bundle,
        {"schema_version", "case_id", "module", "clocks", "initial", "models", "requirements", "scenarios", "timeout_ticks"},
        set(),
        "contract",
    )
    _require(bundle["schema_version"] == 1, "contract.schema_version must be 1")
    _require(isinstance(bundle["case_id"], str) and bundle["case_id"], "contract.case_id: invalid")
    _positive_int(bundle["timeout_ticks"], "contract.timeout_ticks")
    allowed_refs = {item["id"] for item in registry if isinstance(item, dict) and isinstance(item.get("id"), str)}

    module = _exact(bundle["module"], {"name", "ports"}, set(), "contract.module")
    _require(module["name"] == "TopModule", "contract.module.name must be TopModule")
    _require(isinstance(module["ports"], list) and module["ports"], "contract.module.ports: invalid")
    inputs: set[str] = set()
    outputs: set[str] = set()
    names: set[str] = set()
    for index, raw_port in enumerate(module["ports"]):
        port = _exact(raw_port, {"name", "direction", "width", "source_refs"}, set(), f"port[{index}]")
        name = _identifier(port["name"], f"port[{index}].name")
        _require(name not in names, f"duplicate port {name}")
        names.add(name)
        _require(port["direction"] in {"input", "output"}, f"port[{index}].direction: invalid")
        _positive_int(port["width"], f"port[{index}].width")
        _refs(port["source_refs"], allowed_refs, f"port[{index}].source_refs")
        (inputs if port["direction"] == "input" else outputs).add(name)

    _require(isinstance(bundle["clocks"], list), "contract.clocks: expected array")
    clocks: set[str] = set()
    for index, raw_clock in enumerate(bundle["clocks"]):
        clock = _exact(raw_clock, {"signal", "initial", "half_period", "source_refs"}, set(), f"clock[{index}]")
        _require(clock["signal"] in inputs, f"clock[{index}].signal: must be input")
        _require(clock["signal"] not in clocks, f"duplicate clock {clock['signal']}")
        clocks.add(clock["signal"])
        _require(clock["initial"] in {0, 1}, f"clock[{index}].initial: expected 0 or 1")
        _positive_int(clock["half_period"], f"clock[{index}].half_period")
        _refs(clock["source_refs"], allowed_refs, f"clock[{index}].source_refs")

    _require(isinstance(bundle["models"], list), "contract.models: expected array")
    models: set[str] = set()
    for index, raw_model in enumerate(bundle["models"]):
        model = _exact(raw_model, {"name", "width", "signed", "initial"}, set(), f"model[{index}]")
        name = _identifier(model["name"], f"model[{index}].name")
        _require(name not in names and name not in models, f"model[{index}]: duplicate/conflicting name")
        models.add(name)
        _positive_int(model["width"], f"model[{index}].width")
        _require(isinstance(model["signed"], bool), f"model[{index}].signed: expected boolean")
    expression_names = inputs | models
    for index, model in enumerate(bundle["models"]):
        _expression(model["initial"], expression_names, f"model[{index}].initial")

    _require(isinstance(bundle["initial"], dict), "contract.initial: expected object")
    expected_initial = inputs - clocks
    _require(set(bundle["initial"]) == expected_initial, f"contract.initial must initialize inputs {sorted(expected_initial)}")
    for name, expression in bundle["initial"].items():
        _expression(expression, expression_names, f"contract.initial.{name}")

    _require(isinstance(bundle["requirements"], list) and bundle["requirements"], "contract.requirements: invalid")
    requirement_ids: set[str] = set()
    for index, raw_requirement in enumerate(bundle["requirements"]):
        requirement = _exact(raw_requirement, {"id", "text", "source_refs"}, set(), f"requirement[{index}]")
        requirement_id = _identifier(requirement["id"], f"requirement[{index}].id")
        _require(requirement_id not in requirement_ids, f"duplicate requirement {requirement_id}")
        requirement_ids.add(requirement_id)
        _require(isinstance(requirement["text"], str) and requirement["text"], f"requirement[{index}].text: invalid")
        _refs(requirement["source_refs"], allowed_refs, f"requirement[{index}].source_refs")

    _require(isinstance(bundle["scenarios"], list) and bundle["scenarios"], "contract.scenarios: invalid")
    covered: set[str] = set()
    scenario_ids: set[str] = set()
    for index, raw_scenario in enumerate(bundle["scenarios"]):
        scenario = _exact(raw_scenario, {"id", "verifies", "source_refs", "steps"}, set(), f"scenario[{index}]")
        scenario_id = _identifier(scenario["id"], f"scenario[{index}].id")
        _require(scenario_id not in scenario_ids, f"duplicate scenario {scenario_id}")
        scenario_ids.add(scenario_id)
        _require(isinstance(scenario["verifies"], list) and scenario["verifies"], f"scenario[{index}].verifies: invalid")
        _require(set(scenario["verifies"]) <= requirement_ids, f"scenario[{index}].verifies: unknown requirement")
        covered.update(scenario["verifies"])
        _refs(scenario["source_refs"], allowed_refs, f"scenario[{index}].source_refs")
        _validate_steps(scenario["steps"], inputs, outputs, clocks, models, f"scenario[{index}].steps")
    missing = requirement_ids - covered
    _require(not missing, f"requirements without executable scenarios: {sorted(missing)}")
    return bundle


def coverage_map(bundle: dict[str, Any]) -> dict[str, list[str]]:
    return {
        requirement["id"]: [
            scenario["id"] for scenario in bundle["scenarios"]
            if requirement["id"] in scenario["verifies"]
        ]
        for requirement in bundle["requirements"]
    }
