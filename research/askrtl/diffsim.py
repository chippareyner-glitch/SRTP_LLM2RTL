"""Reference-free differential simulation of RTL candidates (AskRTL, Phase 1).

Given candidate TopModule sources for one problem, this module
  * extracts the port interface from Icarus' compiled .vvp (.port_info lines),
  * infers clock / reset ports by name,
  * generates stimulus from several input "profiles" (no spec, no reference),
  * co-simulates all candidates in one harness and records 4-state output traces,
  * partitions candidates by trace and finds the first divergence for each pair,
  * minimises a distinguishing trace for a pair (shortest prefix, fewest toggles).

Nothing here reads the reference model or the official testbench.
"""
from __future__ import annotations

import hashlib
import os
import random
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

IVERILOG = r"D:\iverilog\bin\iverilog.exe"
VVP = r"D:\iverilog\bin\vvp.exe"
TIMEOUT = 60

# prefixes: APB `p`, AXI `axi_a`/`a`, `s`, `sys_`; suffixes `_in`/`_i` mean "input", not polarity
CLOCK_RE = re.compile(r"^(i_|in_)?(p|s|a|axi_a|sys_)?(clk|clock)(_in|_?i)?$", re.I)
RESET_RE = re.compile(r"^(i_|in_)?(p|s|a|axi_a|sys_)?(reset|rst)(_async|_sync)?(_?n|_?b|_?ni|_bar)?(_in|_?i)?$",
                      re.I)
ACTIVE_LOW_RE = re.compile(r"(_?n|_?b|_?ni|_bar)$", re.I)


def reset_is_active_low(name: str) -> bool:
    stem = re.sub(r"^(i_|in_)", "", name, flags=re.I)
    stem = re.sub(r"(_in|_i)$", "", stem, flags=re.I)
    return bool(ACTIVE_LOW_RE.search(stem))


@dataclass(frozen=True)
class Port:
    name: str
    direction: str  # INPUT / OUTPUT
    width: int


@dataclass
class Interface:
    ports: tuple[Port, ...]
    clock: str | None = None
    reset: str | None = None
    reset_active_low: bool = False

    @property
    def inputs(self) -> list[Port]:
        return [p for p in self.ports if p.direction == "INPUT" and p.name != self.clock]

    @property
    def outputs(self) -> list[Port]:
        return [p for p in self.ports if p.direction == "OUTPUT"]

    @property
    def sequential(self) -> bool:
        return self.clock is not None


@dataclass
class Candidate:
    cid: str
    code: str
    meta: dict = field(default_factory=dict)
    iface: Interface | None = None
    error: str | None = None


def _run(cmd: list[str], cwd: Path, timeout: int = TIMEOUT) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def declared_params(code: str, names: dict[str, str]) -> dict[str, str]:
    """Subset of `names` that the TopModule in `code` actually declares as parameters."""
    m = re.search(r"\bmodule\s+TopModule\b(.*?)\bendmodule\b", strip_comments(code), flags=re.S)
    body = m.group(1) if m else ""
    return {k: v for k, v in names.items() if re.search(rf"\bparameter\b[^;]*?\b{re.escape(k)}\b", body, flags=re.S)}


def extract_interface(code: str, work: Path, params: dict[str, str] | None = None) -> Interface:
    work.mkdir(parents=True, exist_ok=True)
    (work / "m.sv").write_text(code, encoding="utf-8")
    pflags = [f"-PTopModule.{k}={v}" for k, v in declared_params(code, params or {}).items()]
    r = _run([IVERILOG, "-g2012", "-s", "TopModule", *pflags, "-o", "m.vvp", "m.sv"], work)
    if r.returncode != 0:
        raise RuntimeError("compile: " + (r.stdout + r.stderr)[-400:])
    text = (work / "m.vvp").read_text(encoding="utf-8", errors="replace")
    ports = []
    for m in re.finditer(r'\.port_info \d+ /(INPUT|OUTPUT|INOUT) (\d+) "([^"]+)"', text):
        ports.append(Port(m.group(3), m.group(1), int(m.group(2))))
    if not ports:
        raise RuntimeError("no ports found")
    iface = Interface(tuple(ports))
    for p in ports:
        if p.direction == "INPUT" and p.width == 1 and CLOCK_RE.match(p.name):
            iface.clock = p.name
    for p in ports:
        if p.direction == "INPUT" and p.width == 1 and RESET_RE.match(p.name):
            iface.reset = p.name
            iface.reset_active_low = reset_is_active_low(p.name)
    return iface


# --------------------------------------------------------------------------- stimulus

PROFILES = ("uniform", "sparse", "dense", "sticky")


def gen_stimulus(iface: Interface, profile: str, cycles: int, seed: int) -> list[list[int]]:
    """Return cycles x len(iface.inputs) integer matrix."""
    rng = random.Random(seed)
    ins = iface.inputs
    prev = [0] * len(ins)
    rows = []
    for t in range(cycles):
        row = []
        for j, p in enumerate(ins):
            if iface.sequential and p.name == iface.reset:
                active = t < 2 or (profile == "uniform" and rng.random() < 0.03)
                v = int(active) ^ int(iface.reset_active_low)
            elif profile == "uniform":
                v = rng.getrandbits(p.width)
            elif profile == "sticky":
                v = rng.getrandbits(p.width) if (t == 0 or rng.random() < 0.12) else prev[j]
            elif p.width == 1:
                v = int(rng.random() < (0.15 if profile == "sparse" else 0.85))
            else:  # wide inputs in sparse/dense: mostly held, occasionally new random
                v = rng.getrandbits(p.width) if (t == 0 or rng.random() < 0.3) else prev[j]
            row.append(v)
        prev = row
        rows.append(row)
    return rows


def exhaustive_comb(iface: Interface, limit_bits: int = 12) -> list[list[int]] | None:
    ins = iface.inputs
    total = sum(p.width for p in ins)
    if iface.sequential or total > limit_bits:
        return None
    rows = []
    for v in range(1 << total):
        row, shift = [], 0
        for p in ins:
            row.append((v >> shift) & ((1 << p.width) - 1))
            shift += p.width
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- harness

def strip_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.S)
    return re.sub(r"//[^\n]*", "", code)


def _rename_modules(code: str, suffix: str) -> str:
    code = strip_comments(code)
    names = re.findall(r"^\s*(?:module|macromodule)\s+(\w+)", code, flags=re.M)
    for n in sorted(set(names), key=len, reverse=True):
        code = re.sub(rf"\b{re.escape(n)}\b", f"{n}_{suffix}", code)
    return code


def build_harness(cands: list[Candidate], iface: Interface, work: Path,
                  params: dict[str, str] | None = None) -> Path:
    """Compile one harness containing all candidates; return path to .vvp."""
    work.mkdir(parents=True, exist_ok=True)
    srcs = []
    for c in cands:
        f = work / f"{c.cid}.sv"
        f.write_text(_rename_modules(c.code, c.cid), encoding="utf-8")
        srcs.append(f.name)
    ins, outs = iface.inputs, iface.outputs
    stim_w = sum(p.width for p in ins) or 1
    L = ["`timescale 1ns/1ps", "module harness;"]
    if iface.sequential:
        L.append(f"  reg {iface.clock} = 0;")
        L.append(f"  always #5 {iface.clock} = ~{iface.clock};")
    for p in ins:
        L.append(f"  reg [{p.width - 1}:0] {p.name};")
    for c in cands:
        for p in outs:
            L.append(f"  wire [{p.width - 1}:0] {p.name}__{c.cid};")
        conns = [f".{p.name}({p.name})" for p in iface.ports if p.direction == "INPUT"]
        conns += [f".{p.name}({p.name}__{c.cid})" for p in outs]
        ov = declared_params(c.code, params or {})
        pov = (" #(" + ", ".join(f".{k}({v})" for k, v in ov.items()) + ")") if ov else ""
        L.append(f"  TopModule_{c.cid}{pov} u_{c.cid} ({', '.join(conns)});")
    L.append(f"  reg [{stim_w - 1}:0] mem [0:65535];")
    L.append("  integer fd, n, t, hi; reg [1023:0] fin, fout;")
    # concatenation of outputs per candidate
    def sample(tag: str) -> str:
        fmt = " ".join(["%b"] * len(cands))
        args = ", ".join("{" + ", ".join(f"{p.name}__{c.cid}" for p in outs) + "}" for c in cands)
        return f'      $fdisplay(fd, "%0d {tag} {fmt}", t, {args});'
    L.append("  initial begin")
    L.append('    if (!$value$plusargs("in=%s", fin)) $finish;')
    L.append('    if (!$value$plusargs("out=%s", fout)) $finish;')
    L.append('    if (!$value$plusargs("n=%d", n)) $finish;')
    L.append('    if (!$value$plusargs("hi=%d", hi)) hi = 0;')
    L.append("    $readmemb(fin, mem);")
    L.append("    fd = $fopen(fout, \"w\");")
    L.append("    for (t = 0; t < n; t = t + 1) begin")
    shift = stim_w
    assigns = []
    for p in ins:
        hi = shift - 1
        lo = shift - p.width
        assigns.append(f"{p.name} = mem[t][{hi}:{lo}];")
        shift = lo
    if iface.sequential:
        # normal mode: inputs change while the clock is low (t+0); posedge at +5
        # hi mode (+hi=1): inputs change while the clock is HIGH (t+7), for latch / dual-edge designs
        L.append("      if (hi == 0) begin")
        L.append("        " + " ".join(assigns))
        L.append("        #4;")
        L.append("  " + sample("a"))
        L.append("        #5;")  # sample at +9
        L.append("  " + sample("b"))
        L.append("        #1;")
        L.append("      end else begin")
        L.append("        #4;")
        L.append("  " + sample("a"))
        L.append("        #3;")
        L.append("        " + " ".join(assigns))
        L.append("        #2;")
        L.append("  " + sample("b"))
        L.append("        #1;")
        L.append("      end")
    else:
        L.append("      " + " ".join(assigns))
        L.append("      #1;")
        L.append(sample("c"))
    L.append("    end")
    L.append("    $fclose(fd); $finish;")
    L.append("  end")
    L.append("endmodule")
    (work / "harness.sv").write_text("\n".join(L) + "\n", encoding="utf-8")
    r = _run([IVERILOG, "-g2012", "-s", "harness", "-o", "h.vvp", "harness.sv", *srcs], work)
    if r.returncode != 0:
        raise RuntimeError("harness compile: " + (r.stdout + r.stderr)[-600:])
    return work / "h.vvp"


def _stim_lines(iface: Interface, rows: list[list[int]]) -> str:
    out = []
    for row in rows:
        bits = "".join(format(v, f"0{p.width}b") for p, v in zip(iface.inputs, row)) or "0"
        out.append(bits)
    return "\n".join(out) + "\n"


def simulate(vvp: Path, iface: Interface, rows: list[list[int]], tag: str,
             hi: bool = False) -> list[list[str]] | None:
    """Return per-sample list of candidate output strings: samples[k][i] for candidate i.

    hi=True changes inputs while the clock is high (search only; questions assume low-phase changes).
    """
    work = vvp.parent
    fin, fout = work / f"s_{tag}.txt", work / f"o_{tag}.txt"
    fin.write_text(_stim_lines(iface, rows), encoding="ascii")
    try:
        _run([VVP, "-n", vvp.name, f"+in={fin.name}", f"+out={fout.name}", f"+n={len(rows)}",
              f"+hi={int(hi)}"], work, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return None
    if not fout.exists():
        return None
    samples = []
    for line in fout.read_text(encoding="ascii", errors="replace").splitlines():
        parts = line.split()
        samples.append(parts[2:])
    fin.unlink(missing_ok=True)
    fout.unlink(missing_ok=True)
    return samples


# --------------------------------------------------------------------------- analysis

def start_index(iface: Interface) -> int:
    """Samples before the first clock edge of a reset cycle are unconstrained by any spec."""
    return 1 if (iface.sequential and iface.reset) else 0


def first_divergence(samples: list[list[str]], i: int, j: int, start: int = 0) -> int | None:
    for k in range(start, len(samples)):
        if samples[k][i] != samples[k][j]:
            return k
    return None


def x_involved(a: str, b: str) -> bool:
    return any(ch in "xz" for ch in a + b)


def partition(traces: dict[str, str]) -> list[list[str]]:
    groups: dict[str, list[str]] = {}
    for cid, h in traces.items():
        groups.setdefault(h, []).append(cid)
    return sorted(groups.values(), key=len, reverse=True)


def sample_index_to_cycle(k: int, iface: Interface) -> tuple[int, str]:
    if iface.sequential:
        return k // 2, ("a" if k % 2 == 0 else "b")
    return k, "c"


def minimise(vvp: Path, iface: Interface, rows: list[list[int]], i: int, j: int,
             budget: int = 300) -> tuple[list[list[int]], dict]:
    """Shrink a distinguishing stimulus for candidates i, j (indices into harness order).

    Keeps the first cycle (reset) fixed for sequential designs.  Returns the
    shortest stimulus found and stats.
    """
    calls = 0

    def div(stim: list[list[int]]) -> int | None:
        nonlocal calls
        calls += 1
        s = simulate(vvp, iface, stim, f"min{calls}")
        if s is None:
            return None
        return first_divergence(s, i, j, start_index(iface))

    def cut(stim: list[list[int]]) -> list[list[int]] | None:
        k = div(stim)
        if k is None:
            return None
        cyc, _ = sample_index_to_cycle(k, iface)
        return stim[: cyc + 1]

    cur = cut(rows)
    if cur is None:
        return rows, {"ok": False, "calls": calls}
    orig_len = len(cur)
    keep = 1 if (iface.sequential and iface.reset) else 0
    # 1) ddmin-style chunk removal over cycles (after the fixed prefix)
    chunk = max(1, (len(cur) - keep) // 2)
    while chunk >= 1 and calls < budget:
        changed = False
        start = keep
        while start < len(cur) - 1 and calls < budget:  # never drop the divergence cycle itself
            trial = cur[:start] + cur[start + chunk:]
            if len(trial) > keep:
                res = cut(trial)
                if res is not None and len(res) <= len(cur) - 1:
                    cur, changed = res, True
                    continue
            start += chunk
        if not changed:
            chunk //= 2
    # 2) value simplification: hold previous value (fewer toggles), then zero
    t = keep
    while t < len(cur):
        for q, p in enumerate(iface.inputs):
            if calls >= budget or t >= len(cur):
                break
            if iface.sequential and p.name == iface.reset:
                continue
            for cand_v in ([cur[t - 1][q]] if t > 0 else []) + [0]:
                if cur[t][q] == cand_v:
                    break
                trial = [r[:] for r in cur]
                trial[t][q] = cand_v
                res = cut(trial)
                if res is not None and len(res) <= len(cur):
                    cur = res
                    break
        t += 1
    toggles = sum(1 for t in range(1, len(cur)) for q in range(len(iface.inputs))
                  if cur[t][q] != cur[t - 1][q])
    return cur, {"ok": True, "calls": calls, "orig_len": orig_len, "min_len": len(cur),
                 "toggles": toggles}


def trace_hash(samples: list[list[str]], i: int, start: int = 0) -> str:
    return hashlib.sha1("|".join(s[i] for s in samples[start:]).encode()).hexdigest()


def clean(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def scratch_root() -> Path:
    return Path(os.environ.get("ASKRTL_SCRATCH", os.environ.get("TEMP", "."))) / "askrtl"
