# Asking Instead of Voting: Behavioural Disambiguation for LLM Spec-to-RTL Generation, and What Doesn't Work

*SRTP research report (draft).*

- Date: 2026-10-09
- Code: `research/`
- Models: DeepSeek (API) only; `deepseek-flash` = DS 4.1 Flash
- Detailed logs:
  - [PHASE1_REPORT.md](PHASE1_REPORT.md)
  - [PHASE2_REPORT.md](PHASE2_REPORT.md)
  - [DIRECTIONS_V2.md](DIRECTIONS_V2.md)
  - [RESEARCH_PLAN.md](RESEARCH_PLAN.md)

## Abstract

Large language models (LLMs) can write register-transfer-level (RTL) hardware code from natural-language specifications. When several candidate designs are sampled, the usual way to choose one is to vote over their behaviour or to test them against an LLM-written testbench.

We study a different strategy: find the *minimal input sequence* on which two candidate designs disagree, then ask an LLM judge which output the specification requires at that point.

On VerilogEval spec-to-RTL (156 problems), with pools of older DeepSeek samples:
- **reference-free differential simulation** separates 99.1% of correct/incorrect candidate pairs;
- **asking** lifts selection accuracy from 88.5% (majority vote) and 90.7% (per-configuration vote) to **92.9%**, against a 94.9% ceiling;
- it needs only **1.37 questions per problem where candidates disagree**;
- a DS 4.1 Flash judge picks the correct candidate in **96–98%** of the decisive questions.

We also report three hypotheses we tested and **rejected**:
1. LLMs recite canonical designs when a spec deviates from them: 0 of 12 counterfactual failures reverted.
2. Residual errors are mostly unstated conventions: 8%.
3. Minimal traces make the judge more accurate than long traces: they don't. They are only 39% cheaper.

Finally, we found that **where the judge disagrees with a benchmark reference is a useful signal for finding benchmark defects**, and we report several previously undocumented VerilogEval defects.

**Same-model generalisation.** When the same model (DS 4.1 Flash) both generates and judges, asking adds only +0.3 points on VerilogEval and +1.6 on RTLLM. The reason: 6 of the 7 VerilogEval problems where its own samples disagree, and where voting fails, are **specification defects or ambiguities**.

**Specification-defect detection.** Turned around, this is our main finding. Of 18 problems the judge flagged, by hand adjudication:
- **14 (78%)** point at real specification issues;
- **4** of those are defects not in prior lists (corrected 2026-10-11: SpecLens had already listed `fixed_point_substractor` and a different `alu` issue; see [NOVELTY_REVIEW.md](NOVELTY_REVIEW.md) §1);
- only **1** is a judge error.

## 1. Motivation and related work

**Project goal.** Generate RTL automatically from plain natural-language requirements, using general-purpose open-weight LLM APIs.

**State of the art (2024–2026).**
- **Candidate selection by behavioural agreement:**
  - VRank and VFocus vote over candidates by behaviour.
  - SpecLens (ASP-DAC'27) turns divergences between candidates into spec constraints, judged by an LLM; it uses ~145K tokens per task with o3-mini.
  - VClare (2026) asks a human to arbitrate the first divergent test.
  - NoTB (MLCAD'26) uses formal cross-model consensus for triage.
- **Testbench generation:** CorrectBench, PRO-V.
- **Benchmark problems:**
  - VerilogEval is close to saturated (98.1% reported) and heavily contaminated (VeriContaminated).
  - RTL-BenchMT and GateTruth document flawed test cases.

**Our position.** The divergence-then-judge idea is shared with SpecLens and VClare. Our contributions are:
1. an end-to-end, open-weight, low-cost instantiation with careful measurement;
2. negative results that constrain the design space;
3. judge-vs-reference disagreement as a benchmark-audit signal.

## 2. Setup

- **Benchmark:** VerilogEval v2 spec-to-RTL (156 problems), graded by the official Icarus testbenches.
- **Grading fixes:**
  - Prob082 and Prob141: the reference itself hits the testbench timeout, so "0 mismatches + timeout" counts as a pass.
  - Prob099: the testbench is broken, so it is ungradable.
- **Pools:** about 9.5 candidates per problem from earlier project runs (deepseek-v4-pro / deepseek-flash, six prompt configurations).
- **Rule:** methods never see the reference design or the official testbench. Those are used only for grading and for labelling questions.

## 3. Reference-free differential simulation (Phase 1)

**Method.**
- All candidates of a problem are co-simulated in one Icarus harness.
- Ports come from the compiled `.vvp`; clock and reset are inferred from port names.
- Stimulus: four random profiles plus one 60K-cycle long run.
- Candidates are partitioned by their 4-state output traces.
- For each pair of clusters, the distinguishing trace is shrunk by delta debugging: shortest prefix, fewest input changes.

**Results.**

| Metric | Value |
|---|---|
| (correct, incorrect) pairs separated | 523/528 (99.1%) |
| Problems fully separated | 46 of 48 |
| Minimal trace length | median **1 cycle** after reset (max 23, plus one 4,255-cycle deep-state bug shown as a window) |

The two misses:
- **Prob139:** a testbench race. Our method is right and the benchmark is wrong.
- **Prob145:** a latch-style design that needs inputs to change while the clock is high (a known limitation).

## 4. Asking vs voting (Phase 2)

**Questions.** A question shows the spec, the minimal trace and the conflicting outputs, never the code. Allowed answers:
- an option letter;
- ANY (don't care);
- NONE;
- UNCLEAR.

**Policy.** A Bayesian posterior over clusters. The prior comes from votes, with one unit per sampling configuration. Each next question is chosen by expected information gain; the policy stops at posterior ≥0.95 or after 3 questions.

| Selection method | Accuracy (156 problems) |
|---|---|
| Majority vote (per sample) | 88.5% |
| Majority vote (per configuration) | 90.7% |
| **AskRTL** (DS 4.1 Flash judge, online) | **92.9%** |
| Ceiling: pass@any | 94.9% |

**Judge accuracy** (decision accuracy on questions that separate a correct from an incorrect cluster):
- minimal traces: 95.9%;
- long traces: 97.9%;
- on the 10 problems where voting fails: 24/24.

**Cost.** Median 3.7K tokens per question (mean 5.6–7K). The long tail is hard FSM questions; two of them hit the 32K output cap.

## 5. Negative results

| Hypothesis | Test | Outcome |
|---|---|---|
| Recitation: LLMs implement the canonical design when the spec is a small deviation from it | 16 verified counterfactual variants × 5 samples, plus base problems as controls, with exact reversion grading | **Rejected.** 0/12 failures reverted; pass-rate drop 3.7 points (CI 0–7.5). Failures were Icarus `enum`-cast errors (13/17), unspecified reset behaviour, and timing |
| Residual errors are mostly unstated conventions (latency, reset, initial value) | Divergence typing with a causal reset test, over 101 correct/incorrect pairs | **Rejected.** 8% conventions, 91% genuine value differences |
| Minimal traces improve judge accuracy over long traces | Same questions, both formats | **Rejected on accuracy** (95.9% vs 97.9%); **supported on cost** (5.6K vs 9.1K tokens) |
| Plain voting is a strong baseline | Pilot pools | Weakened. Near-duplicate samples from one configuration create wrong majorities. Counting one vote per configuration gains +2.2 points for free |

## 6. Benchmark errata (VerilogEval spec-to-RTL, Icarus 12)

| Problem | Defect | Evidence |
|---|---|---|
| 139 | Testbench race: blocking `resetn = 1` at `@(posedge clk)` | With `<=`, the "failing" designs pass with 0 mismatches |
| 082, 141 | The reference hits the testbench `TIMEOUT` | Reference vs reference run |
| 099 | Testbench connects ports `Y2`/`Y4`, which don't exist in the interface | Compile error for every design |
| 062, 093, 149 | The spec text contradicts the reference | Manual audit; the judge also follows the spec and flags them (Section 8) |
| 034, 053, 104 | Initial values the spec never states | Unanimously wrong pools. 034 and 053 are also in RTL-BenchMT's independent list |
| 154 | The testbench masks `out_bytes` while `done=0` | The judge answers "don't care"; our labels were too strict |

## 7. Generalisation: same-model pools and RTLLM

Details: [PHASE3_REPORT.md](PHASE3_REPORT.md).

| Pool | pass@1 | Majority vote | AskRTL | Ceiling |
|---|---|---|---|---|
| VerilogEval, DS 4.1 Flash × 5 | 82.1% | 87.2% | 87.5% | 91.0% |
| RTLLM (42), DS 4.1 Flash × 5 | 83.8% | 84.1% | 85.7% | 88.1% |

When generator and judge are the same strong model, asking barely beats voting.

- **Clean disagreements are solved.** Prob137, Prob066 and `traffic_light` are all resolved by asking.
- **But they are rare.** 6 of the 7 VerilogEval gap problems are spec defects or ambiguities, or label artifacts (066, 098, 116, 135, 150, 154). Only 137 is a clean functional disagreement.
- **So the pilot's large gain came mostly from a newer judge correcting an older generator.**

## 8. Judge disagreement as a specification-defect detector

**Ground truth.**
- Independent: RTL-BenchMT's per-case analysis (8 VerilogEval v2 problems, 5 RTLLM v2.1).
- Plus hand adjudication of every flag.

| Verdict on 18 flagged / spec-gap problems | Count |
|---|---|
| Genuine spec defects or contradictions | **9**: 062, 093, 149, 150, 116, 135, `fixed_point_adder`, `fixed_point_substractor`, `alu` |
| … of these, new (not in RTL-BenchMT or our earlier audit) | **4**: 135, `fixed_point_adder`, `fixed_point_substractor`, `alu`. *Corrected 2026-10-11:* SpecLens (2609.16729) already lists `fixed_point_substractor` (no details) and reports a different `alu` issue (LUI). Strictly new: 135 and `fixed_point_adder`, plus a new issue in `alu` |
| Real underspecification | 5: 070, 098, `div_16bit`, `square_wave`, `LIFObuffer` |
| Our tooling / label artifacts | 3: 154, 145, `adder_bcd` |
| Judge errors | **1**: 153 |

- **Precision:** 78% of flags point at a real spec issue.
- **Recall limit:** defects on which all samples agree never trigger a question (RTL-BenchMT's 034, 053, 131, 136, 148, `serial2parallel`).
- **The judge's `spec_gap` notes typically name the problem.** For example, `alu`: "The top-level description says flag is the comparison result, but the detailed implementation says flag=1 for SLT/SLTU regardless of result".

**The new RTLLM defects are confirmed unfixed in the current release.** All three are still present in RTLLM v2.1 (checked on GitHub, 2026-10-09).

**Human-in-the-loop.** The judge answers confident questions and the user answers the rest. On the same-model VerilogEval pool this reaches **90.1% with 6 user questions across all 156 problems**, against 87.5% for the judge alone and 91.0% for the ceiling ([PHASE3_REPORT.md](PHASE3_REPORT.md) §3b).

**Interpretation-diverse sampling** ([IDS_REPORT.md](IDS_REPORT.md)). We generated one design per explicit reading of each listed ambiguity.

- **As a generation strategy it helps.** pass@any rises from 91.0% to 92.9% on VerilogEval and from 88.1% to 92.9% on RTLLM. AskRTL over the IDS pool reaches **90.1% on VerilogEval with no human** (base pool: 87.5%), or 91.0% with ~12 user questions in total.
- **As a defect detector it is negative.** Induced divergence flags ~half of all problems, because even harmless ambiguities change behaviour once resolved explicitly. Base-pool divergence remains the best signal.
- **Hand checks still found:**
  - a fifth new defect, RTLLM `instr_reg`: the spec says synchronous reset, the reference is asynchronous;
  - a re-adjudication: Prob153 is underspecified (PHT reset value), not a judge error.

**Updated tally:** 10 genuine defects (5 new), 7 underspecifications, 5 tooling artifacts, 1 judge error.

*Corrected 2026-10-11* ([NOVELTY_REVIEW.md](NOVELTY_REVIEW.md)):
- **Defects:** 3 new problems (135, `fixed_point_adder`, `instr_reg`), plus 1 new issue in a known problem (`alu`). `fixed_point_substractor` was already listed by SpecLens; we add the concrete diagnosis.
- **IDS:** its pass@any gain vanishes at a matched pool size on VerilogEval (141.8 vs 142.0 problems at n=5) and CVDP (49.4 vs 49.0). It remains +2 problems on RTLLM.

**Implication for the project goal.** For plain-language specs and strong models, disagreement between samples should trigger a **clarifying question to the user**, rendered as a minimal concrete trace, rather than silent selection.

## 9. Limitations

- One model family (DeepSeek).
- VerilogEval is contaminated.
- Labels come from a reference that is itself sometimes wrong.
- Phase 1 stimulus can't reach latch-style behaviour.
- Single judge sample per question.
- The prior and the assumed judge accuracy p=0.8 were fixed in advance, not tuned.

## 10. Reproducibility

Every step has a dry-run mode. Paid runs log the prompt, reply and token usage under `research/**/api_logs`.

Total API spend: **≈7.3M tokens**.

| Item | Tokens |
|---|---|
| Counterfactual pilot | 0.33M |
| Phase 2 judge | 2.15M |
| Phase 3 generation (VerilogEval 2.61M + RTLLM 1.70M) | 4.31M |
| Phase 3 judge | 0.45M |

Phase 3 bug fix: parameterised designs are now simulated with the testbench's parameter values.
