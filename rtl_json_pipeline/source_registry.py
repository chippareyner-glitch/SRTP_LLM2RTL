"""Create neutral source-span IDs without interpreting hardware behavior."""

from __future__ import annotations

import re
from typing import Any


def build_source_registry(spec: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    pattern = re.compile(r"(?m)^\s*[-*]\s+[^\n]+|[^\n.!?]+(?:[.!?]+|$)")
    for match in pattern.finditer(spec):
        text = match.group(0).strip()
        if not text:
            continue
        start = match.start() + len(match.group(0)) - len(match.group(0).lstrip())
        kind = "interface" if text.startswith(("-", "*")) else "statement"
        spans.append({
            "id": f"SRC{len(spans) + 1:03d}",
            "source_text": text,
            "start": start,
            "end": match.end(),
            "kind": kind,
        })
    return spans


def registry_ids(registry: list[dict[str, Any]]) -> set[str]:
    return {str(item["id"]) for item in registry}
