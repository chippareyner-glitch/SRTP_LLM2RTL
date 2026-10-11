"""Selection headroom of a pool: divergent tasks where some cluster passes but the top-voted one does not.

Usage: python -I headroom.py   (env ASKRTL_TAG / ASKRTL_BENCH)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from paths import QDIR, case_files  # noqa: E402


def main() -> None:
    n_div, room, solved_by_any = 0, [], 0
    for f in case_files(QDIR):
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("status") != "ok":
            continue
        n_div += 1
        cl = d["clusters"]
        passing = [c for c in cl if all(c["correct"])]
        solved_by_any += bool(passing)
        top = max(c["votes"] for c in cl)
        tops = [c for c in cl if c["votes"] == top]
        exp_maj = sum(all(c["correct"]) for c in tops) / len(tops)
        if passing and exp_maj < 1:
            room.append((d["case"].replace("cvdp_copilot_", ""), round(1 - exp_maj, 2),
                         [(c["votes"], all(c["correct"])) for c in cl]))
    print(f"divergent tasks {n_div}; with a passing cluster {solved_by_any}; "
          f"selection headroom {sum(r[1] for r in room):.2f} tasks over {len(room)} tasks")
    for r in room:
        print(" ", r)


if __name__ == "__main__":
    main()
