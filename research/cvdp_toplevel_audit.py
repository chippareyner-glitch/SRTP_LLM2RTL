"""Audit: does each CVDP cid003 prompt tell the model the module name the harness instantiates?

For every task: harness TOPLEVEL (src/.env), output file path, and whether TOPLEVEL appears in
the prompt.  Tasks where it does not are unsolvable from the prompt unless the name is guessed.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bench import Bench, cvdp_tasks  # noqa: E402

MOD_RE = re.compile(r"\bmodule\s*(?:name)?\s*[:\-]?\s*[`'\"*]*([A-Za-z_]\w+)", re.I)


def main() -> None:
    T, b = cvdp_tasks(), Bench("cvdp")
    missing = []
    for tid in b.cases():
        t = T[tid]
        spec, top = t["input"]["prompt"], t["_top"]
        if not re.search(rf"\b{re.escape(top)}\b", spec):
            named = sorted({m for m in MOD_RE.findall(spec) if len(m) > 3 and m.lower() not in ("name", "that", "should")})
            missing.append((tid, top, b.target(tid), named[:5]))
    print(f"{len(missing)}/{len(b.cases())} cid003 prompts never mention the harness TOPLEVEL module name:")
    for tid, top, target, named in missing:
        print(f"  {tid.replace('cvdp_copilot_', ''):<44} TOPLEVEL={top:<38} file={target:<40} prompt names: {named}")


if __name__ == "__main__":
    main()
