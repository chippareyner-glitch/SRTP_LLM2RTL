"""Benchmark abstraction shared by the research scripts.

verilogeval : dataset_spec-to-rtl_gcc (<case>_prompt.txt / _ref.sv (RefModule) / _test.sv, top = TopModule)
rtllm       : research/benchmarks/rtllm_local/<case>/ (spec.txt, ref.sv, testbench.v + data files, meta.json)
              rebuilt from the RTLLM reference-check run of 2026-10-08 (build_rtllm_local.py)

All research tooling works on a *normalised* top module called TopModule; `to_top` renames a
candidate's (or reference's) top module accordingly.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RESEARCH = Path(__file__).resolve().parent
PROJ = RESEARCH.parent
VE_DIR = PROJ / "dataset_spec-to-rtl_gcc"
RTLLM_DIR = RESEARCH / "benchmarks" / "rtllm_local"

RTLLM_SUFFIX = ("\nUse the module names and interfaces from the specification. Include all required RTL "
                "submodules. Return all RTL in one code block. Do not emit testbenches, simulation system "
                "tasks, file I/O, or external includes.")


CVDP_JSONL = (PROJ.parent / "benchmarks" / "cvdp" / "data" / "v1.1.0" /
              "cvdp_v1.1.0_nonagentic_code_generation_no_commercial.jsonl")
_CVDP: dict[str, dict] = {}


def cvdp_tasks() -> dict[str, dict]:
    """cid003 (spec-to-RTL) tasks of NVIDIA CVDP v1.1.0, keyed by task id."""
    if not _CVDP:
        for line in CVDP_JSONL.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if "cid003" in r["categories"]:
                env = r["harness"]["files"].get("src/.env", "")
                top = re.search(r"^\s*TOPLEVEL\s*=\s*(\S+)", env, flags=re.M)
                r["_top"] = top.group(1) if top else None
                _CVDP[r["id"]] = r
    return _CVDP


class Bench:
    def __init__(self, name: str) -> None:
        if name not in ("verilogeval", "rtllm", "cvdp"):
            raise ValueError(name)
        self.name = name

    # ---- problems
    def cases(self) -> list[str]:
        if self.name == "verilogeval":
            return sorted(p.name[: -len("_prompt.txt")] for p in VE_DIR.glob("Prob*_prompt.txt"))
        if self.name == "cvdp":
            return sorted(k for k, v in cvdp_tasks().items() if v["_top"])
        return sorted(d.name for d in RTLLM_DIR.iterdir() if (d / "meta.json").exists())

    def spec(self, case: str) -> str:
        if self.name == "verilogeval":
            return (VE_DIR / f"{case}_prompt.txt").read_text(encoding="utf-8")
        if self.name == "cvdp":
            return cvdp_tasks()[case]["input"]["prompt"] + f"\n\nWrite the complete RTL for `{self.target(case)}`."
        return (RTLLM_DIR / case / "spec.txt").read_text(encoding="utf-8")

    def top(self, case: str) -> str:
        if self.name == "verilogeval":
            return "TopModule"
        if self.name == "cvdp":
            return cvdp_tasks()[case]["_top"]
        return json.loads((RTLLM_DIR / case / "meta.json").read_text(encoding="utf-8"))["top"]

    def target(self, case: str) -> str:
        """CVDP output file path, e.g. rtl/16qam_mapper.sv."""
        return next(iter(cvdp_tasks()[case]["output"]["context"]))

    def has_reference(self) -> bool:
        return self.name != "cvdp"  # CVDP withholds reference RTL (contamination control)

    def system_prompt(self) -> str:
        base = (PROJ / "prompts" / "direct" / "baseline.system.txt").read_text(encoding="utf-8").strip()
        return base + (RTLLM_SUFFIX if self.name in ("rtllm", "cvdp") else "")

    def params(self, case: str) -> dict[str, str]:
        """Parameter values the official testbench instantiates the top module with (RTLLM)."""
        if self.name in ("verilogeval", "cvdp"):  # CVDP: designs use their own defaults (runner may sweep)
            return {}
        meta = json.loads((RTLLM_DIR / case / "meta.json").read_text(encoding="utf-8"))
        tb = "\n".join((RTLLM_DIR / case / t).read_text(encoding="utf-8", errors="replace")
                       for t in meta["testbenches"])
        tb = re.sub(r"/\*.*?\*/|//[^\n]*", "", tb, flags=re.S)
        m = re.search(rf"\b{re.escape(meta['top'])}\s*#\s*\((.*?)\)\s*\w+\s*\(", tb, flags=re.S)
        if not m:
            return {}
        local = dict(re.findall(r"\b(?:parameter|localparam)\s+(?:integer\s+)?(\w+)\s*=\s*([^;,]+)", tb))
        out = {}
        for name, val in re.findall(r"\.(\w+)\s*\(\s*([^()]+?)\s*\)", m.group(1)):
            out[name] = local.get(val, val).strip()
        return out

    def reset_active_low(self, case: str, port: str | None) -> bool | None:
        """Reset polarity stated in the spec text near the port name (None if not stated)."""
        if not port:
            return None
        text = self.spec(case)
        for m in re.finditer(rf"\b{re.escape(port)}\b", text):
            window = text[max(0, m.start() - 80): m.end() + 120].lower()
            # explicit statements only: "if rst is low, the register updates" describes the *inactive* state
            if re.search(r"active[- _]?low|low[- _]active|asserted low", window):
                return True
            if re.search(r"active[- _]?high|high[- _]active|asserted high", window):
                return False
        return None

    # ---- normalisation to TopModule
    def to_top(self, code: str, case: str) -> str:
        top = self.top(case)
        if top == "TopModule":
            return code
        return re.sub(rf"\bmodule\s+{re.escape(top)}\b", "module TopModule", code, count=1)

    def ref_as_top(self, case: str) -> str | None:
        if self.name == "cvdp":
            return None
        if self.name == "verilogeval":
            ref = (VE_DIR / f"{case}_ref.sv").read_text(encoding="utf-8")
            return re.sub(r"\bmodule\s+RefModule\b", "module TopModule", ref, count=1)
        return self.to_top((RTLLM_DIR / case / "ref.sv").read_text(encoding="utf-8"), case)
