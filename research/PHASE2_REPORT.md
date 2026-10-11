# Phase 2 report: does asking beat voting?

Date: 2026-10-09 · Judge model: `deepseek-flash` (DS 4.1 Flash), reasoning effort high · Benchmark: VerilogEval spec-to-rtl (156 problems).

Candidate pools: the existing older-DeepSeek pools from the pilot, about 9.5 samples per problem. Questions: the 220 minimal-trace questions from Phase 1. Labels come from simulating the reference.

Runs:
- `askrtl/out_judge/20261009_152757_min_live`: 2a, minimal traces, 156 answered, plus 18 online answers.
- `askrtl/out_judge/20261009_152757_long_live`: 2b, long traces, 93 answered (stopped early by agreement, to save budget).

**API spend for this phase:** about 2.15M tokens (2a ≈1.15M incl. 2 truncated calls, 2b ≈0.85M, online 0.17M). Project total so far ≈2.5M, including the counterfactual pilot.

## 1. Headline: end-to-end benchmark accuracy

| Selection method on the same candidate pools | Accuracy (156 problems) |
|---|---|
| Majority vote over behaviour clusters (per sample) | 88.5% |
| Majority vote, one vote per sampling configuration | 90.7% |
| **AskRTL online**: Bayesian policy, per-configuration prior, ≤3 questions, assumed judge accuracy 0.8 | **92.9%** |
| Ceiling: at least one candidate correct (pass@any) | 94.9% |

- AskRTL asked **1.37 questions per divergent problem** (74 in total over 54 problems; 0 for the 102 problems where all candidates agree).
- It recovers **4.4 of the 6.4 points** between per-sample voting and the ceiling.
- Remaining misses:
  - 062, 093, 149: the spec contradicts the reference. No spec-faithful method can pass these.
  - 156: no correct candidate exists.
  - 150, 153, 154: real misses. In 154 the judge answered "don't care" three times; see Section 3.

## 2. Judge accuracy

| Metric | Minimal traces (2a) | Long traces (2b) |
|---|---|---|
| Questions that separate a correct from an incorrect cluster | 77 | 48 |
| Judge points to the correct cluster | **70** | **46** |
| Judge points to the incorrect cluster | 3 | 1 |
| Abstains | 4 | 1 |
| **Decision accuracy** | **95.9%** | **97.9%** |
| Agreement with labels, all questions | 84.8% (158 incl. 2 truncations) | 75.5% |
| Agreement with labels, excluding known-defect problems | **94.5%** (127) | — |
| On the 10 problems where voting fails | 24/24 answered correctly | — |
| Mean tokens per question (same 93 questions) | **5.6K** | 9.1K |

**Where the 22 label disagreements in 2a come from:**

| Cause | Count |
|---|---|
| Known benchmark-defect problems (062, 093, 149, 145) | 15 |
| Don't-care labels: the judge picked one of several acceptable outputs | 4 |
| The judge said "don't care" where the reference has a value (070: "input combination 8 is stated to never occur", which is defensible) | 1 |
| Genuine misses: Prob116 (bit-order ambiguity, flagged by the judge itself) and Prob141 | 2 |

## 3. Hypotheses

| Hypothesis | Result |
|---|---|
| **H1 (asking beats voting)** | **Supported** on this benchmark: 92.9% vs 88.5% / 90.7%. Caveat: the judge (DS 4.1 Flash) is a newer model than the generators. The strict same-model generation-vs-verification test is still open |
| **H2 (minimal traces beat long traces)** | **Not supported on accuracy:** decision accuracy 95.9% vs 97.9%. **Supported on cost:** 39% fewer tokens for the same decisions. Also, 33% of long-trace comparisons have "neither" as ground truth, but the judge still picks the better trace |
| H3 (question efficiency) | 1.37 questions per divergent problem reach 92.9%. The synthetic simulation suggested the information-gain policy and a single top-2 question perform alike. A clean comparison needs repeated judge samples |
| H4 (ambiguity / defect detection) | **Promising:** 15 of 22 label disagreements fall on known defective problems, and the judge's explanation names the gap (Prob116 bit order, Prob149 invalid sensor patterns, Prob070 impossible input) |
| Labelling limitation | Prob154's testbench masks `out_bytes` while `done=0`, but our labels compare it anyway. The judge's three "don't care" answers there are probably *right* and our labels too strict |

## 4. Also tested and rejected

These came from the broader direction search; see [DIRECTIONS_V2.md](DIRECTIONS_V2.md).
- **Recitation of canonical designs:** 0 of 12 counterfactual failures reverted to the original circuit.
- **Errors are mostly unstated conventions:** only 8% of correct-vs-incorrect differences are latency, reset or initial-value conventions.

## 5. Honest assessment of novelty

AskRTL's working core, an LLM arbitrating behavioural divergences between candidates, overlaps with SpecLens and VClare. What this project adds:
1. **Quantitative evidence** that a cheap open-weight judge resolves divergences with ~96% decision accuracy, end-to-end, at ~1.4 questions and ~5K tokens per divergent problem. SpecLens reports ~145K tokens per task with o3-mini.
2. **Evidence that judge disagreements are a benchmark-defect detector** (H4).
3. **Several clean negative results:** no recitation; conventions are a minor share of errors; minimal traces aren't more accurate, only cheaper.
4. **Benchmark errata** found and verified: testbench race (139), reference timeouts (082/141), broken testbench ports (099), spec-vs-reference contradictions (062/093/149).

This makes a solid **empirical study and SRTP report**. As a top-venue *method* paper it is incremental unless results hold on harder, uncontaminated benchmarks.

## 6. Recommended next steps

| Option | Cost | Value |
|---|---|---|
| **A. Same-model test.** DS 4.1 Flash generates the pools (≈5 samples × 54 divergent problems), then judges them | ≈0.6–1.0M tokens | Turns H1 into a clean generation-vs-verification claim |
| **B. Harder benchmark.** RTLLM v2 (harness exists) or the CVDP code-generation subset; generate pools, rerun Phases 1–2 | ≈1.5–3M tokens | Tests whether the gain holds outside saturated, contaminated VerilogEval |
| **C. Write-up.** Empirical report: findings 1–4 + errata | 0 | A deliverable now |
| D. Defect detection as its own study. Judge "don't care" / "unclear" answers vs a hand-verified errata list, across VerilogEval + RTLLM | ≈0.3M | Turns H4 into a measured claim |
