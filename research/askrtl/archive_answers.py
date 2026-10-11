"""Move recorded judge answers for given cases out of a run (their questions were rebuilt).

Answers are keyed by (case, question index); after re-running phase1/queries for a case the
indices can point at different questions, so stale answers must not be reused.
Usage: python -I archive_answers.py <run_dir> <tag-for-archive> case [case ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    run, tag, cases = Path(sys.argv[1]), sys.argv[2], set(sys.argv[3:])
    for name in ("results.jsonl", "online_results.jsonl"):
        f = run / name
        if not f.exists():
            continue
        keep, moved = [], []
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                (moved if json.loads(line)["case"] in cases else keep).append(line)
        if moved:
            with (run / f"{name}.stale_{tag}").open("a", encoding="utf-8") as fh:
                fh.write("\n".join(moved) + "\n")
            f.write_text("\n".join(keep) + ("\n" if keep else ""), encoding="utf-8")
        print(f"{f}: kept {len(keep)}, archived {len(moved)}")


if __name__ == "__main__":
    main()
