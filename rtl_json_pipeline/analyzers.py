"""Source-level parser/elaborator and compiler adapters."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

from .models import Diagnostic, StageResult


class PyslangAnalyzer:
    name = "pyslang"

    def analyze(self, source_path: Path, top: str) -> StageResult:
        del top  # pyslang elaborates compilation roots; retained for the common interface.
        try:
            from pyslang.ast import Compilation
            from pyslang.syntax import SyntaxTree
        except ImportError as exc:
            return StageResult(
                stage="pyslang_analysis",
                available=False,
                passed=False,
                diagnostics=[Diagnostic(
                    stage="pyslang_analysis",
                    tool=self.name,
                    severity="unavailable",
                    code="dependency_missing",
                    message=str(exc),
                )],
            )

        # Python handles Windows Unicode/OneDrive paths; native fromFile may not.
        tree = SyntaxTree.fromText(source_path.read_text(encoding='utf-8-sig'))
        compilation = Compilation()
        compilation.addSyntaxTree(tree)
        compilation.getRoot()
        engine = __import__("pyslang").DiagnosticEngine(compilation.sourceManager)
        diagnostics: list[Diagnostic] = []
        has_error = False
        for item in compilation.getAllDiagnostics():
            severity_value = engine.getSeverity(item.code, item.location).value
            severity = {0: "ignored", 1: "note", 2: "warning", 3: "error", 4: "fatal"}.get(
                severity_value, "unknown"
            )
            has_error |= severity in {"error", "fatal"}
            code_match = re.search(r"\(([^)]+)\)", str(item.code))
            diagnostics.append(Diagnostic(
                stage="pyslang_analysis",
                tool=self.name,
                severity=severity,
                code=code_match.group(1) if code_match else str(item.code),
                message=engine.formatMessage(item),
                file=str(source_path),
                line=compilation.sourceManager.getLineNumber(item.location),
                column=compilation.sourceManager.getColumnNumber(item.location),
            ))
        return StageResult(
            stage="pyslang_analysis",
            passed=not has_error,
            diagnostics=diagnostics,
            details={"diagnostic_count": len(diagnostics)},
        )


class IcarusCompiler:
    name = "iverilog"

    def __init__(self, executable: Path):
        self.executable = executable

    def analyze(self, source_path: Path, top: str) -> StageResult:
        stage = "iverilog_compile"
        if not self.executable.exists():
            return StageResult(
                stage=stage,
                available=False,
                passed=False,
                diagnostics=[Diagnostic(
                    stage=stage,
                    tool=self.name,
                    severity="unavailable",
                    code="executable_missing",
                    message=f"Icarus executable not found: {self.executable}",
                )],
            )
        command = [str(self.executable), "-g2012", "-s", top, "-t", "null", source_path.name]
        completed = subprocess.run(
            command,
            cwd=source_path.parent,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        diagnostics = self._parse_diagnostics(completed.stderr, source_path, stage)
        if completed.returncode and not diagnostics:
            diagnostics.append(Diagnostic(
                stage=stage,
                tool=self.name,
                severity="error",
                code="compile_failed",
                message=completed.stderr.strip() or completed.stdout.strip() or "Icarus compilation failed",
                file=str(source_path),
            ))
        return StageResult(
            stage=stage,
            passed=completed.returncode == 0,
            diagnostics=diagnostics,
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )

    def _parse_diagnostics(self, stderr: str, source_path: Path, stage: str) -> list[Diagnostic]:
        results: list[Diagnostic] = []
        pattern = re.compile(r"^(.*?):(\d+)(?::(\d+))?:\s*(.*)$")
        for line in stderr.splitlines():
            match = pattern.match(line.strip())
            if match:
                message = match.group(4)
                severity = "warning" if "warning" in message.lower() else "error"
                results.append(Diagnostic(
                    stage=stage,
                    tool=self.name,
                    severity=severity,
                    code="compiler_diagnostic",
                    message=message,
                    file=match.group(1),
                    line=int(match.group(2)),
                    column=int(match.group(3)) if match.group(3) else None,
                ))
            elif line.strip():
                results.append(Diagnostic(
                    stage=stage,
                    tool=self.name,
                    severity="error",
                    code="compiler_diagnostic",
                    message=line.strip(),
                    file=str(source_path),
                ))
        return results
