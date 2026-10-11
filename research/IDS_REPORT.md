# Interpretation-diverse sampling (IDS)

Date: 2026-10-10 · Model: `deepseek-flash` (DS 4.1 Flash) · Spend: ≈5.1M tokens

| Step | Calls | Tokens |
|---|---|---|
| Listing | 198 | 1.50M |
| Generation | 436 | 2.70M |
| Online judge | 140 | 0.93M |

Code: `research/ids/ids.py`, `ids_eval.py`; pipeline reuse via `ASKRTL_TAG=*_ids`.

## Motivation

Divergence-based defect detection (Phase 3) is blind when every sample misreads the spec the same way. RTL-BenchMT's 034, 053, 131, 136 and 148 got no question at all. IDS tries to *create* the missing disagreement:
1. One call per problem lists what the spec leaves ambiguous, contradictory or silent, each with two concrete readings.
2. For the top-2 ambiguities, one design is generated per reading, with that reading stated explicitly.
3. These designs join the existing 5-sample pool as a separate sampling configuration (`ids`).

## Results

### Coverage and selection

| Pool | pass@any | Majority vote | AskRTL, judge only | Hybrid (escalate confidence < 0.95) | User answers everything |
|---|---|---|---|---|---|
| VerilogEval base (5 samples) | 142/156 (91.0%) | 87.2% | 87.5% | 90.1% (0.04 user q/problem) | 91.0% |
| **VerilogEval + IDS** | **145/156 (92.9%)** | 87.8% | **90.1%** | **91.0%** (0.08 user q/problem) | 92.9% |
| RTLLM base | 37/42 (88.1%) | 84.1% | 85.7% | 85.7% | 85.7% |
| **RTLLM + IDS** | **39/42 (92.9%)** | 88.0% | 87.3% | 87.3% | 89.3% |

- **IDS adds correct candidates** where all 5 samples were wrong: VerilogEval 034, 146 and 151; RTLLM `fsm` and `sequence_detector`.
- **On VerilogEval, IDS + AskRTL reaches 90.1% with no human**, +2.6 over AskRTL on the base pool. That equals what the base pool needed a human for. With ≈12 user questions in total it reaches 91.0%.
- **On RTLLM, majority vote over the IDS-augmented pool is already 88.0%**, and the judge does not improve on it. The remaining errors are spec defects (`alu`, `fixed_point_adder`) and one Mealy-timing judge error (`fsm`).

### Sample-matched control (added 2026-10-11, `ids/ids_matched.py`, no API)

The table above compares 5 base samples with 5 base samples plus up to 4 IDS designs, so pool size is confounded with diversity. Here the pool size is held at 5: k base samples are swapped for IDS designs, with the expectation taken over all subsets. Only problems with a full 5-sample base pool are counted.

| Benchmark | Problems | Base, n=5 | IDS swapped in, n=5 | Unmatched (table above) |
|---|---|---|---|---|
| VerilogEval | 156 | 142.0 | **141.8** | 145 |
| RTLLM | 40 | 35.0 | **37.0** | 37 |
| CVDP | 67 | 49.0 | **49.4** | 50 |

- **At equal pool size, IDS designs give no coverage advantage on VerilogEval or CVDP.** On RTLLM they add 2 problems.
- **Individual IDS designs are worse**: pass@1 is 49.6% vs 70.6% for base samples on VerilogEval, and 46.6% vs 56.5% on CVDP. Forcing a reading often forces the wrong one.
- **The "90.1% with no human" result is unmatched too.** It needs a 9-sample base pool as a control, which requires paid generation.

### As a specification-defect detector: negative

Precision and recall are against the "all verified" ground truth: RTL-BenchMT plus defects verified in this project.

| Detector | VerilogEval flagged / P / R | RTLLM flagged / P / R |
|---|---|---|
| Text ambiguity listing | 92 / 0.13 / 0.86 | 27 / 0.19 / 0.83 |
| Base-pool divergence (Phase 3 signal) | 21 / **0.33** / 0.50 | 11 / **0.36** / 0.67 |
| IDS behavioural divergence | 75 / 0.09 / 0.50 | 24 / 0.21 / 0.83 |
| IDS + judge filter | 9 / 0.33 / 0.21 | 6 / 0.17 / 0.17 |

- **Telling a model to resolve an ambiguity a certain way almost always changes behaviour, even for harmless ambiguities.** So behavioural divergence induced by IDS does not separate real defects from benign gaps.
- The *text* listing has the highest recall: it names 034 and 053 ("initial value of q not specified") as RTL-BenchMT does. But it flags ~60% of all problems.
- Precision here is a **lower bound**, because the ground truth lists only known defects. Hand checks of the IDS + judge flags found more real issues, below.

### New findings from hand-adjudicating the IDS + judge flags

| Problem | Verdict |
|---|---|
| **RTLLM `instr_reg`** | **Spec vs reference contradiction (new).** Spec: "On the rising edge of the clock, if the reset (rst) signal is low, both registers are initialized to zero" (synchronous). Reference: `always @(posedge clk or negedge rst)` (asynchronous). The judge followed the spec |
| RTLLM `sequence_detector` | Real underspecification: whether overlapping `1001` occurrences are detected. The judge answered UNCLEAR and named it |
| VerilogEval 153 gshare | Real underspecification: PHT reset value. The judge answered UNCLEAR. **Correction:** Phase 3 listed 153 as a judge error; it is underspecified. An earlier project note (`repair_prompts_20261008`) records the reference resetting the PHT to `01` without the spec saying so |
| VerilogEval 104 | Known underspecified initial value (see errata) |
| VerilogEval 091, RTLLM `adder_bcd` | Our stimulus violated a stated input domain (one-hot / BCD). The judge's "don't care" is correct |
| RTLLM `fsm` | **Judge error.** The question's post-edge sample of a Mealy output reflects the new state *and* the still-held input; the judge reasoned bit by bit. Trace presentation for Mealy outputs should be clarified |

**Tooling limitation found.** Reset polarity is inferred from port names, so `rst` was assumed active-high, but `instr_reg` specifies active-low. Reading the polarity from the spec text would fix this.

## Conclusions

1. IDS is **not a better defect detector**; base-pool divergence plus the judge remains the best signal. It does surface a few hidden defects (034, 148) and new ones (`instr_reg`) at the cost of many flags.
2. IDS **is a useful generation strategy**: +3 / +2 problems of coverage, and on VerilogEval, AskRTL over the IDS pool matches the human-in-the-loop accuracy of the base pool without any human.
3. Updated defect tally across Phases 3 and IDS:
   - 10 genuine spec defects or contradictions, 5 of them new: 135, `fixed_point_adder`, `fixed_point_substractor`, `alu`, `instr_reg`;
   - 7 real underspecifications;
   - 5 tooling/stimulus artifacts;
   - **1 judge error** (`fsm`).
