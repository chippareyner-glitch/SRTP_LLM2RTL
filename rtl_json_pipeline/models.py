"""Shared data structures for front-end stages and diagnostic aggregation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Diagnostic:
    stage: str
    tool: str
    severity: str
    code: str
    message: str
    file: str | None = None
    line: int | None = None
    column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StageResult:
    stage: str
    passed: bool
    available: bool = True
    diagnostics: list[Diagnostic] = field(default_factory=list)
    command: list[str] | None = None
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "available": self.available,
            "passed": self.passed,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "details": self.details,
        }
