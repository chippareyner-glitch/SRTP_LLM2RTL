"""Experiment selection for the AskRTL scripts.

  ASKRTL_TAG   pool tag under research/pools/<tag>/out  (default: the original pilot pool)
  ASKRTL_BENCH verilogeval | rtllm                        (default: verilogeval)

Each tag gets its own Phase 1 / query / judge output folders, so runs never mix.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bench import Bench  # noqa: E402

TAG = os.environ.get("ASKRTL_TAG", "")
BENCH = Bench(os.environ.get("ASKRTL_BENCH", "verilogeval"))
SUFFIX = f"_{TAG}" if TAG else ""
POOL = (HERE.parent / "pools" / TAG / "out") if TAG else (HERE.parent / "pilot_pool" / "out")
HI = os.environ.get("ASKRTL_HI", "0") == "1"  # opt-in: extra search run with inputs changing while clk is high
P1 = HERE / f"out_phase1{SUFFIX}{'_hi' if HI else ''}"
QDIR = HERE / f"out_queries{SUFFIX}"
JUDGE_OUT = HERE / f"out_judge{SUFFIX}"
NON_CASE = {"summary", "divtypes", "policy_sim"}


def case_files(d: Path) -> list[Path]:
    """Per-problem JSON files in an output folder (skips aggregate files)."""
    return sorted(f for f in d.glob("*.json") if f.stem not in NON_CASE)
