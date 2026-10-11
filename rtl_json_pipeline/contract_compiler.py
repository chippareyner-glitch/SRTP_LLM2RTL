"""Deterministically compile behavior primitives into a self-checking SV testbench."""

from __future__ import annotations

from typing import Any


def _logic_range(width: int) -> str:
    return "" if width == 1 else f"[{width - 1}:0] "


def _escaped(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('%', '%%')


def _compile_steps(steps: list[dict[str, Any]], lines: list[str], indent: str) -> None:
    for step in steps:
        op = step["op"]
        if op == "drive":
            for name, expression in step["values"].items():
                lines.append(f"{indent}{name} = {expression};")
        elif op == "wait_edge":
            lines.append(f"{indent}@({step['edge']} {step['signal']});")
            # Move past the active/NBA regions before the next contract step.
            # This makes an immediately following expect observe registered state
            # instead of racing a DUT nonblocking assignment on the same edge.
            lines.append(f"{indent}#1;")
            lines.append(f'{indent}record_trace();')
        elif op == "delay":
            lines.append(f"{indent}#{step['ticks']};")
        elif op == "update_model":
            # Snapshot all RHS expressions before changing any model variable.
            targets = ", ".join(step['values'])
            values = ", ".join(step['values'].values())
            # Width-cast each RHS so concatenation preserves individual widths.
            values = ", ".join(f"$bits({name})'({expr})" for name, expr in step['values'].items())
            lines.append(f"{indent}{{{targets}}} = {{{values}}};")
        elif op == "set_model":
            for name, expression in step["values"].items():
                lines.append(f"{indent}{name} = {expression};")
        elif op == "expect":
            label = _escaped(step["label"])
            for actual, expected in step["values"].items():
                lines.append(f"{indent}checks = checks + 1;")
                lines.append(f"{indent}if ({actual} !== ({expected})) begin")
                lines.append(f'{indent}    dump_trace();')
                lines.append(f'{indent}    $display("CHECKS_EXECUTED=%0d", checks);')
                lines.append(f'{indent}    $fatal(1, "CHECK_FAIL scenario=%s label={label} signal={actual} expected=%0h actual=%0h", current_scenario, ({expected}), {actual});')
                lines.append(f"{indent}end")
        elif op == "repeat":
            lines.append(f"{indent}repeat ({step['count']}) begin")
            _compile_steps(step["steps"], lines, indent + "    ")
            lines.append(f"{indent}end")


def compile_testbench(bundle: dict[str, Any]) -> str:
    """Compile an already validated contract. No design-category dispatch exists here."""
    ports = bundle["module"]["ports"]
    lines = ["`timescale 1ns/1ps", "module behavior_contract_tb;"]
    for port in ports:
        lines.append(f"    logic {_logic_range(port['width'])}{port['name']};")
    for model in bundle["models"]:
        signed = "signed " if model["signed"] else ""
        lines.append(f"    logic {signed}{_logic_range(model['width'])}{model['name']};")
    lines.extend(["    integer checks = 0;", "    string current_scenario;", ""])
    fmt=' '.join(f"{p['name']}=%0h" for p in ports)
    args=', '.join(p['name'] for p in ports)
    lines.extend([
        '    string trace_ring [0:15];', '    integer trace_count = 0;',
        '    task record_trace;', '      begin',
        f'        trace_ring[trace_count % 16] = $sformatf("TRACE time=%0t scenario=%s {fmt}", $time, current_scenario, {args});',
        '        trace_count = trace_count + 1;', '      end', '    endtask',
        '    task dump_trace;', '      integer j;', '      begin',
        '        for (j = (trace_count > 16 ? trace_count - 16 : 0); j < trace_count; j = j + 1)',
        '          $display("%s", trace_ring[j % 16]);',
        '        record_trace();',
        '        $display("%s", trace_ring[(trace_count - 1) % 16]);',
        '      end', '    endtask',
    ])
    connections = ", ".join(f".{port['name']}({port['name']})" for port in ports)
    lines.extend([f"    TopModule dut ({connections});", ""])
    for clock in bundle["clocks"]:
        lines.append(f"    always #{clock['half_period']} {clock['signal']} = ~{clock['signal']};")
    lines.extend(["", "    initial begin"])
    for clock in bundle["clocks"]:
        lines.append(f"        {clock['signal']} = 1'b{clock['initial']};")
    for name, expression in bundle["initial"].items():
        lines.append(f"        {name} = {expression};")
    for model in bundle["models"]:
        lines.append(f"        {model['name']} = {model['initial']};")
    lines.append("        #1;")
    for scenario in bundle["scenarios"]:
        lines.append(f'        current_scenario = "{_escaped(scenario["id"])}";')
        lines.append(f'        $display("SCENARIO_START %s", current_scenario);')
        _compile_steps(scenario["steps"], lines, "        ")
        lines.append(f'        $display("SCENARIO_PASS %s", current_scenario);')
    lines.extend([
        '        $display("BEHAVIOR_CONTRACT_PASS checks=%0d", checks);',
        "        $finish;",
        "    end",
        "",
        "    initial begin",
        f"        #{bundle['timeout_ticks']};",
        '        $fatal(1, "BEHAVIOR_CONTRACT_TIMEOUT");',
        "    end",
        "endmodule",
        "",
    ])
    return "\n".join(lines)
