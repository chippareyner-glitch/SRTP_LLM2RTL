# NVIDIA CVDP v1.1.0 (cid003, spec-to-RTL): status and results

Date: 2026-10-10 · Model: `deepseek-flash` (DS 4.1 Flash) · Tasks: 78 cid003 (non-agentic code generation, no commercial tools; 41 easy / 37 medium)

## 1. Environment (set up by Codex, reviewed and independently verified)

- `E:\SRTP\benchmarks\cvdp\.venv` (Python 3.10.11): cocotb 2.0.1, pytest 8.3.2, PyYAML, python-dotenv, aes. Python runtime DLLs copied so Icarus can load cocotb (hashes in `validation_20261010/integrity.json`).
- `scripts/cvdp_local.py` runs each task's own docker-compose pytest command locally:
  - container paths remapped;
  - per-run work folders kept;
  - **pass** requires pytest exit code 0, a compiled simulation, and every JUnit and cocotb test passed with none skipped.
- `research/grade.py`: only the CVDP branch changed; it calls `cvdp_local.py` through the venv. The VerilogEval and RTLLM grading code is identical to the previous version.

**Independent check** (`research/cvdp_check.py`, official solved example `cvdp_copilot_lfsr_0001`):

| Design | Result |
|---|---|
| Official solution | **pass** |
| Wrong tap | functional_failed (2/3 cocotb tests failed) |
| Stuck register | functional_failed (3/3 failed) |
| Syntax error | compile_error |

A first mutation, an inverted seed on reset, passed. Inspection showed the example's testbench cannot detect it: it checks only next-state consistency and maximal length. That is a test weakness, not a grader bug.

**Caveat.** Local Icarus is 12.0-devel; the official image uses Icarus 13.0. The compile errors inspected so far are genuine model errors (e.g. `3'sd -3`, which is illegal SystemVerilog). Version-specific failures cannot be excluded without the official container.

## 2. Results so far (no judge yet)

**Pool:** 5 samples per task requested.
- 352/390 generated: 67 tasks complete, 6 partial, 5 with no sample.
- Missing samples: 17 length-cap truncations, 27 rate-limit (HTTP 429) or empty replies, 36 "insufficient balance" (HTTP 402) when the API credit ran out.
- Missing samples count as failures.

| Metric (78 tasks) | Value |
|---|---|
| Per-sample pass@1 | **54.7%** (VerilogEval 82.1%, RTLLM 83.8% for the same model) |
| pass@any (≤5 samples) | 65.4% |
| Majority vote over behaviour clusters | 60.2% |
| Reference-free search: correct/incorrect pairs separated | 47/50 (94%) |
| Tasks with divergence / questions built | 34 / 122. Unlabelled: CVDP withholds reference RTL, so judge accuracy cannot be scored per question; end-to-end accuracy is still graded by the official harness |
| Phase 1 status | 63 ok, 4 single-candidate, 9 ungradable (no compiling candidate), 2 harness errors |

**Partial IDS pool.** With only 67/274 interpretation-specific designs present, pass@any rises from 65.4% to **67.9%** (+2 tasks). The full IDS run needs API credit.

**Headroom for asking:** 60.2% → 65.4% (+5.2 points). That's more than on VerilogEval (+3.8) and RTLLM (+4.0).

## 2b. Failure analysis (offline)

Scripts: `research/cvdp_analysis.py`, `cvdp_analysis2.py`, `cvdp_analysis3.py`, `cvdp_toplevel_audit.py`.

### Corrected headline numbers

5 tasks got no sample only because of API rate-limit/balance errors at the end of the run (`ttc_lite`, `unpacker_one_hot`, `vending_machine`, `vga_controller`, `wb2ahb`). Excluding them (73 tasks):

| Metric | Value |
|---|---|
| pass@1 | 58.4% |
| Majority vote | 64.3% |
| pass@any | 69.9% |
| Excluding also the 4 interface-defect tasks (below), 69 tasks: pass@any | 73.9% |

### Where samples fail (of 390 requested)

| Outcome | Count | Share |
|---|---|---|
| pass | 211 | 54% |
| Functional failure | 105 | 27% |
| Compile error | 31 | 8% |
| Timeout | 5 | 1% (`perf_counters`, `axil_precision_counter`: the simulation never terminates) |
| Not generated: rate/balance | 26 | — |
| Not generated: **output-length truncation** | 12 | All on the longest specs (8–26K chars): `microcode_sequencer`, `static_branch_predict`, `perceptron`, `apb_dsp_unit`, `sync_serial_communication` |

Compile errors (re-run through Icarus to get the messages):

| Cause | Samples |
|---|---|
| **Module name differs from the harness TOPLEVEL** | **17** |
| `enum` assignment without a cast | 5 |
| Syntax error (e.g. `3'sd -3`) | 4 |
| Icarus-12 "sorry, not supported" | 3 |
| Other | 2 |

Only the 3 "not supported" cases could plausibly behave differently under the official Icarus 13.

### Difficulty

| Split | pass@1 | pass@any |
|---|---|---|
| easy (41) | 68.3% | 78.0% |
| medium (37) | 38.4% | 51.4% |

| Spec length quartile | pass@1 |
|---|---|
| Q1 (1.0–2.3K chars) | 76.8% |
| Q2 | 60.0% |
| Q3 | 47.4% |
| Q4 (5.4–26K chars) | 33.0% |

The number of ambiguities the model lists for a spec predicts failure even after controlling for length: partial r = −0.32 (length given ambiguities: −0.27). It's a cheap, reference-free difficulty signal.

### Benchmark issues found

1. **Interface-name defects (4 tasks, 5%).** The harness instantiates a top module whose name the prompt never gives, or contradicts:

   | Task | Harness expects | Output file / prompt says |
   |---|---|---|
   | `ethernet_packet_parser_0001` | `field_extract` | file `ethernet_parser.v` |
   | `sync_serial_communication_0001` | `..._tx_rx` | file `..._top.sv` |
   | `hebbian_rule_0017` | `hebb_gates` | prompt names `hebbian_rule` |
   | `sequencial_binary_to_one_hot_decoder_0001` | `..._sequential` | prompt spells it `sequencial` |

   Every sample fails to compile on these. 10 more prompts omit the name, but the output file name supplies it, and the model inferred it.
2. **Under-constrained tests.** In **15 of the 48** tasks with a passing design, ≥2 behaviourally different designs all pass the official tests. `clock_divider_0003`, `restoring_division_0001` and `thermostat_0001` each have 4. Part of this may come from our random stimuli leaving the valid input protocol, but "passes CVDP" clearly does not pin down one behaviour.

### Behavioural situation per task (78)

| Situation | Tasks |
|---|---|
| Unanimous correct | 25 |
| Divergent, majority correct | 13 |
| Divergent, correct in minority or tie | 10 (in 5 of these, all tied clusters are correct, so selection is harmless) |
| **Divergent, no correct candidate** | **11** |
| Unanimous wrong | 4 |
| Single behaviour / unanalysable | 6 |
| Nothing compiles | 4 (= the interface defects) |
| No sample | 5 |

The pools are **much more diverse** than on VerilogEval: 10 tasks show 4–5 distinct behaviours from 5 samples. Votes are mostly 1 each, so majority voting carries little information.

### Parameter generalisation

- 33/78 runners sweep design parameters. 15 candidates pass some parameter instances and fail others. Examples:
  - `prbs_gen_0003` passes `[8-1-7-0]` and fails `[8-3-7-0]`; all 5 samples fail the same 36/54 instances.
  - `matrix_multiplier_0001` fails at width 4, not 8.
  - `restoring_division_0001` fails at width 4.
- These are hard-coded-assumption bugs. Our reference-free search simulates only default parameters, so it cannot see them.

### Partial IDS

The 67 IDS designs that exist (of 274 planned) already add correct candidates for `apb_dsp_unit_0001` and `axi_stream_upscale_0001`.

### Adaptive sampling (all benchmarks, offline simulation, `research/adaptive.py`)

Rule: draw samples one at a time and stop as soon as two behave identically under the reference-free clustering. Averaged over 50 random sample orders:

| Benchmark | Fixed 5 + vote | Stop at 2 agreeing | Samples saved |
|---|---|---|---|
| VerilogEval | 86.9% | 87.2% | 53% |
| RTLLM | 84.7% | 84.7% | 43% |
| CVDP | 59.8% | 59.5% | 36% |

This is Adaptive-Consistency-style stopping (known in LLM reasoning) applied with behavioural equivalence. Here it is an engineering result: same accuracy for roughly half the generation cost, with the savings largest where disagreement is rare.

## 2c. Judge and full IDS results (2026-10-10/11, after API top-up)

Spend: 19.3 CNY. That covers 207 IDS generations, 70 judge calls on the base pool (~0.83M tokens) and 124 judge calls on the IDS pool (~1.56M tokens). 10 IDS designs were lost to output-length truncation.

### End-to-end accuracy (78 tasks, graded by the official cocotb harness)

| Pool | pass@1 | pass@any | Majority (per config) | AskRTL online (B=3, p=0.8) | Questions/divergent task |
|---|---|---|---|---|---|
| Base `cvdp_ds41` (5 samples) | 54.7% | 65.4% | 60.2% | **60.7%** | 2.06 |
| `cvdp_ds41_ids` (base + interpretation-specific designs) | 53.7% | **70.5%** | **64.5%** | 64.3% → **65.6%** after the clock-detection fix (below) | 2.21 |

**IDS helps on CVDP; asking does not (yet).**
- Interpretation-diverse sampling adds 5.1 points of pass@any.
- It also raises plain majority vote by 4.3 points, unlike VerilogEval and RTLLM, where IDS added little to the majority.
- On top of that, the judge-based selection is neutral: +0.4 tasks on the base pool, −0.1 on the IDS pool.

> **Correction (2026-10-11): the IDS gain is mostly a missing-data artifact.**
> - **pass@any:** of the 4 extra tasks solved, 2 (`unpacker_one_hot`, `vga_controller`) had **zero** base samples because the API ran out of balance, and 1 (`apb_dsp_unit`) had only 3.
> - **Majority vote:** the same 2 zero-sample tasks also account for 2 of its ~3.4 extra tasks.
> - **At a matched pool size:** over the 67 tasks with a full base pool, with n=5 fixed, IDS reaches 49.4 tasks against 49.0 for the base pool (`ids/ids_matched.py`).
>
> "IDS helps on CVDP" is not supported.

### Why asking is neutral here (`askrtl/cvdp_judge_analysis.py`, `askrtl/headroom.py`, `per_task.json`)

1. **Tiny selection headroom.** Of the divergent tasks, only those with a passing cluster that majority voting misses can gain:

   | Pool | Divergent tasks | With a passing cluster | Expected tasks majority voting misses |
   |---|---|---|---|
   | Base | 34 | 23 | 4.1 (over 6 tasks) |
   | IDS | 56 | 38 | 5.3 (over 8 tasks) |

   Most failing divergent tasks have no correct candidate at all (11 on base, 18 on IDS). On CVDP, generation is the bottleneck.

2. **Most questions cannot move the score.** Each question was classified using official pass/fail per cluster:

   | Question kind | Base | IDS |
   |---|---|---|
   | Informative (a passing and a failing option) | 17 | 33 |
   | All options fail | 23 | 39 |
   | All options pass (tests cannot tell them apart) | 19 | 25 |
   | Mixed clusters | 11 | 27 |

3. **On informative questions the judge is mostly right**, but the remaining errors land exactly on the few headroom tasks.

   | Outcome on informative questions | Base | IDS |
   |---|---|---|
   | Picked the passing option | 10 | 21 |
   | Picked a failing option | 3 | 3 |
   | Picked a mixed option | 1 | 2 |
   | ANY | 3 | 5 |
   | Error | 0 | 2 |

   Decisive accuracy is about 77% on the base pool and 81–88% on the IDS pool, against 96–98% on labelled VerilogEval questions.

   | Pool | AskRTL wins | AskRTL losses |
   |---|---|---|
   | Base | `hill_cipher` (+0.8), `restoring_division` (+0.2) | `axil_precision_counter` (−0.4), `axis_joiner` (−0.2) |
   | IDS | `hill_cipher` (+0.5), `axis_joiner` (+0.25), `thermostat` (+0.12) | `events_to_apb` (−1.0) |

4. **The losses are not clear judge errors.**
   - `axil_precision_counter`: the questions ask about AXI ready outputs during reset. The judge's "0 during reset" reading is reasonable. The matching cluster fails the official tests, but a per-cluster pass/fail cannot attribute the failure to this behaviour; the cluster probably fails for another bug.
   - `events_to_apb`: an off-by-one in when the "15-cycle" APB timeout fires (count from entering ACCESS or from the first ACCESS cycle). The spec does not pin it down, and the judge chose the other reading from the test (confidence 0.85).

   Both are the "single answered behaviour ≠ whole correct design" limitation: answering one question right does not make the chosen cluster correct elsewhere.

### Implications

- On realistic, long specs (CVDP) the bottleneck is **generation**. IDS's apparent +5.1 pass@any / +4.3 majority does not survive the matched control above. The next lever would be **question-guided repair** (`repair/repair.py`): turning answered questions into constraints for regeneration, instead of only selecting among existing candidates.
- AskRTL's selection gains did not transfer to CVDP:
  - Pilot pool: 88.5% → 92.9%.
  - Same-model VerilogEval: 87.2% → 87.5%.
  - RTLLM: 84.1% → 85.7%.

  CVDP pools rarely contain a minority correct design.

### Tool fix: clock/reset name detection (2026-10-11)

`diffsim.py` recognised clocks and resets by name, and missed the APB/AXI spellings `pclk`, `axi_aclk`, `presetn`, `preset_n` and `axi_aresetn`, plus `rst_in` and `rst_n_i`.
- **Effect:** on 8 CVDP tasks the clock was driven as a random data input.
- **Fix:** widened patterns. Polarity is now decided after stripping `_in`/`_i`, so `rst_in` is active-high and `rst_n_i` is active-low.
- **Regression check:** detection is unchanged on every VerilogEval and RTLLM interface.
- **Re-run:** phase 1 and queries for the 8 tasks in both pools. Stale answers were moved aside (`askrtl/archive_answers.py`, `*.stale_clkfix`) and 23 questions were re-asked (~0.22M tokens).

| Pool | AskRTL before fix | AskRTL after fix | Majority (per config) |
|---|---|---|---|
| Base | 60.7% | 60.7% | 60.2% |
| IDS | 64.3% | **65.6%** | 64.5% |

On the IDS pool `axil_precision_counter` flips from a loss to a win, so part of that "loss" in item 4 above was our tool bug.

## 2d. Question-guided repair pilot (2026-10-11, `repair/repair.py`, `repair/repair_report.py`)

**Method.** Decisive judge answers become executable constraints: under this input trace, cycle k must output V. These go into the prompt in two arms:
- **fresh:** generate a new design;
- **edit:** fix the cluster representative most consistent with the constraints.

New designs are filtered reference-free by simulating the constraints. Official tests are used only for scoring.

**Results**

| | VerilogEval (`ve_ds41`) | CVDP (`cvdp_ds41_ids`) |
|---|---|---|
| Tasks | all 15 divergent tasks with constraints | the 19 divergent tasks AskRTL fails (**selected with ground truth**) |
| Designs per arm | 3 | 2 |
| Generated / requested | 68/90 (22 length-truncated) | 54/76 (22 truncated) |
| fresh: correct / constraint-consistent correct | 22/43, 19/38 | 5/33, 4/28 |
| edit: correct / constraint-consistent correct | 13/25, 12/20 | 1/21, 1/19 |
| Newly solved (no correct candidate before) | `Prob146_fsm_serialdata` | `secure_read_write_register_bank_0001` |
| AskRTL selection on these tasks | 6.5 tasks | 0.5 tasks |
| Random pick among constraint-consistent repaired designs | 7.0 tasks; 7.5 with fallback to AskRTL when no repaired design is consistent (`Prob135`) | **2.25 tasks** (`hill_cipher` 1.0, `secure_rw_register_bank` 1.0, `apb_dsp_unit` 0.25) |
| Benchmark-level effect | 87.5% → ~88.1% | ~+2.2 points, an upper-bound estimate because of task selection |

**Reading the results**
- Repair produces correct designs on tasks where **no candidate was correct**, which no selection method can do. That is the generation bottleneck identified in §2c.
- VerilogEval spec-defect tasks (062, 093, 149, …) stay "wrong": repaired designs follow the spec, which disagrees with the flawed reference.
- On CVDP the edit arm is poor (1/21). Long-spec designs that already fail are probably wrong in several places at once.
  - **Correction (2026-10-11, prompt bug):** the edit prompt always said the starting design "disagrees with at least one example", but the starting design was chosen as the one most consistent with the answers and already met every example on 13/15 VerilogEval tasks and 16/19 CVDP tasks. With this false premise, 36/71 edit calls hit the 32K output cap, compared with 1/12 where the premise was true (fresh arm on the same tasks: 5/71). So the edit arm's weak numbers are partly a prompt artefact. `repair.py` now tells the model which examples, if any, the starting design fails.
- **Cost:** 3.54M tokens (VerilogEval 1.63M, CVDP 1.92M), 2.4× the estimate. Every length-truncated call is billed at the full budget, and the truncation rate is 27%.

**Missing for a fair CVDP number:** repair on the ~34 divergent tasks AskRTL already solves, to measure regressions (~3.5M tokens).

## 3. Remaining optional work

| Step | Calls | Est. tokens |
|---|---|---|
| Fair CVDP repair control (tasks AskRTL already solves) | ~136 | ~3.5M |
| Reduce truncation (raise max_tokens, or ask for the changed module only) | — | code only |
| Refill missing base samples (5 tasks have none) | ~38 | ~0.4M |

The IDS ambiguity listing finished for all 78 tasks: 70/78 list at least one ambiguity.
