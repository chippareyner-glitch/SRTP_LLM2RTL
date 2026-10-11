# Phase 1 report: reference-free disambiguation infrastructure

Date: 2026-10-08 · API spend: **0** · Code: [askrtl/](askrtl/) · Plan: [RESEARCH_PLAN.md](RESEARCH_PLAN.md)

## TL;DR

1. **The search clears its gate by a wide margin.** Gate: find ≥80% of the divergences that matter, using only the candidates (no spec, no reference, no official testbench). Result:
   - 99.1% of (correct, incorrect) candidate pairs are separated (523/528);
   - 46 of 48 problems are fully separated;
   - one of the two misses is a race in the official testbench, where our method is the one that's right.
2. **Disagreements are local.** Distinguishing traces are short: median 1 cycle after the reset cycle, at most 23 cycles. The one exception is a deep-state bug in Prob141 (clock rollover at about 4,255 cycles), handled with windowed rendering.
3. **Whole-trace comparison asks the wrong question a third of the time.** In 33% of trace pairs (SpecLens-style, 32 cycles) *neither* trace is correct. For minimal local questions the figure is 2%.
4. **Voting counts duplicates as independent evidence.** Per-configuration voting gains +2.2 points on the benchmark with no questions asked (88.5% → 90.7%).
5. **The simulated noisy judge sets a clear Phase 2 target:**
   - with a judge that is right 70% of the time, Bayesian asking reaches 92.2%;
   - at 80%, it reaches 92.8–93.0%;
   - the ceiling (pass@any) is 94.9%.
6. **Benchmark defects found as a by-product:** 1 testbench race, 2 grading artifacts from the reference's own timeout, and 1 broken testbench interface (details below).

## 1. What was built

| File | Role |
|---|---|
| `askrtl/diffsim.py` | Ports from Icarus `.vvp`; clock/reset inferred by name; four stimulus profiles (uniform, sparse, dense, sticky) plus a 60K-cycle long run; one harness co-simulating all candidates with 4-state output traces; partitioning; delta-debugging minimiser (shortest prefix, fewest toggles). Never reads the reference or the official testbench |
| `askrtl/phase1_eval.py` | Runs the search per problem and scores it against hidden ground truth |
| `askrtl/queries.py` | Turns each cluster pair into a question:<br>• minimal trace + output history + options (A/B/C…)<br>• a SpecLens-style long-trace variant<br>• a hidden label from simulating the reference (letter / ANY = don't-care / NONE) |
| `askrtl/policy_sim.py` | Selection policies under a synthetic noisy judge: majority, per-config majority, top-2 (single arbitration), Bayesian with expected information gain |
| `askrtl/judge.py` | Phase 2 harness. **Dry-run by default**; live calls need `--live --max-calls N`. Option letters are shuffled to control position bias |
| `askrtl/replay.py` | Phase 2 analysis: feeds recorded judge replies into the policies |

Timing convention:
- inputs change while the clock is low;
- outputs are sampled just before (`pre`) and just after (`post`) each rising edge;
- the sample before the first edge of a reset cycle is ignored, since no spec constrains it.

## 2. Search quality (156 VerilogEval problems, about 9.5 DeepSeek samples each)

| Metric | Value |
|---|---|
| (correct, incorrect) pair separation | **523/528 = 99.1%** |
| Problems fully separated | 46/48 (comb 9/9, seq 12/12, FSM 20/21, black-box 5/6) |
| Pairs split by official stimuli that we also split | 715/880 = 81.2%. All the misses are same-correctness pairs; they don't affect selection |
| Splits we find that the official testbench doesn't | 25. 15 of them involve X; these are don't-cares, which the judge can answer with ANY |
| Minimal distinguishing trace length (correct vs incorrect) | Median **1** cycle after reset; 79% are ≤ 3 cycles; max 23. Plus Prob141 at 4,255 cycles, windowed |
| Simulator calls per minimisation | Median 4 |

**Misses.**
- **Prob139** (FSM): the official testbench drives `resetn = 1` with a *blocking* assignment at `@(posedge clk)`. That's a race. Candidates c4 and c6 are graded wrong because of it, yet with `<=` they pass with 0 mismatches. Our search correctly finds c1 ≡ c4 ≡ c6.
- **Prob145** (latch-like `circuit8`): divergence needs inputs that change while the clock is high, and our harness only changes inputs while it's low. This is a known limitation, fixable with dual-phase stimulus.

## 3. Questions

- 220 questions from 54 divergent problems; all rendered and labelled.
- Minimal-trace labels: 194 single option · 19 ANY (don't-care) · 4 NONE · 3 multi-option.
- Long-trace labels: 140 A/B · 7 ANY · **73 NONE (33%)**.

Two example questions:

- **Prob137 (serial receiver).** After start bit and 7 data zeros, `in=1` on the 8th data bit: may `done` rise now?
  - Label: B (no; the stop bit hasn't arrived yet).
  - The majority cluster says yes, which is the counting bug.
- **Prob141 (12-hour clock).** At 12:59:59 AM with `ena=1`, does `pm` flip as the hour rolls to 01?
  - Label: A (no; it flips at 11→12).
  - This needs the 60K-cycle long run and windowed rendering.

## 4. Selection with a simulated noisy judge (benchmark accuracy, 156 problems)

A judge with accuracy *p* returns the true label with probability *p*; otherwise a random wrong answer.

| Policy | p=0.6 | 0.7 | 0.8 | 0.9 | 1.0 |
|---|---|---|---|---|---|
| Majority vote (per sample) | .885 | .885 | .885 | .885 | .885 |
| Majority vote (per configuration) | .907 | .907 | .907 | .907 | .907 |
| Top-2 single question (VClare/SpecLens-style) | .901 | .903 | .909 | .926 | .944 |
| Bayesian EIG, sample-vote prior, ≤3 questions | .905 | .909 | .916 | .931 | .949 |
| **Bayesian EIG, per-config prior, ≤3 questions** | **.920** | **.923** | **.930** | **.936** | **.949** |
| Bayesian, uniform prior, ≤3 questions | .841 | .869 | .897 | .923 | .949 |

Ceiling = pass@any = 94.9%.

**Caveat:** synthetic judge errors are independent. A real LLM judge may share the generator's misreading, so its errors would be correlated. That is exactly what Phase 2 measures; `replay.py` re-runs this table with real replies.

## 5. Updated pilot numbers (after fixing timeout grading for 082/141)

| | |
|---|---|
| Mean per-sample accuracy | 79.1% |
| Best single source: json_ir / v4-pro single shot | 91.0% / 88.1% |
| Majority with official stimuli, don't-care merged | 87.8% |
| pass@any | **94.9%** |

## 6. Benchmark errata found so far (VerilogEval spec-to-rtl, Icarus 12)

| Problem | Issue | Evidence |
|---|---|---|
| 034, 053, 104 | Initial values the spec never states; every candidate "fails" the same way | Unanimous, wrong pools |
| 062, 093, 149 | The spec text contradicts the reference | Earlier manual audit |
| 099 | The testbench connects ports `Y2`/`Y4` that don't exist in the spec | Compile error for every design |
| 139 | Testbench race: blocking `resetn = 1` at a clock edge | With `<=`, the "failing" designs pass with 0 mismatches |
| 082, 141 | The reference itself hits the testbench `TIMEOUT` under Icarus 12; 0 mismatches is the best possible | Reference vs reference run |

## 7. Phase 2 protocol (needs your go-ahead: paid)

Judge model: DS 4.1 Flash. Set its exact API ID in `.env` as `DEEPSEEK_MODEL`, or pass `--model`. Reasoning effort: high.

| Run | Command | Calls | Est. tokens (input + reasoning/output) | Tests |
|---|---|---|---|---|
| 2a | `python -I judge.py --live --max-calls 220` | 220 | ~0.2M + ~0.5–0.9M | Judge accuracy p̂; H1 against the p thresholds in Section 4; ANY/NONE handling |
| 2b | `python -I judge.py --variant long --live --max-calls 220` | 220 | ~0.4M + ~0.5–0.9M | H2: minimal vs long traces |
| 2c (optional) | 2a with `--samples 3` | +440 | ~0.4M + ~1–1.8M | Answer stability, self-consistency, confidence calibration |

Then run `python -I replay.py out_judge/<run>` for the end-to-end benchmark accuracy with real replies.

**Go/no-go after 2a.**
- **Go:** replayed Bayesian-per-config accuracy beats per-config majority (90.7%), and judge accuracy on the 10 voting-failure problems is ≥0.7.
- **Otherwise:** pivot to the human-in-the-loop question-efficiency study.

**Comparability caveat.** The pool was generated by older DeepSeek models (flash / v4-pro), and the judge is DS 4.1 Flash. So Phase 2 tests *judge usefulness*. The strict *generation–verification gap* (same model generating and judging) is Phase 3, which needs fresh DS 4.1 Flash samples.

## 8. Next zero-cost items (if Phase 2 is delayed)

- Dual-phase stimulus, for latch-style and dual-edge designs (Prob145).
- A controlled-sampling harness for Phase 3: N samples × prompts × models, with per-config bookkeeping.
- An FSM scaling-set generator (random FSM → spec → reference), as the harder benchmark.
- RTLLM v2 adapter for the search (the reference-free part needs only candidates).
