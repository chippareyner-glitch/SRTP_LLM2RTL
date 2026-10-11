# Benchmark errata found in this project (VerilogEval v2, RTLLM v2/v2.1, NVIDIA CVDP v1.1.0)

Compiled 2026-10-10. Each item states how it was verified. **"New"** means not in RTL-BenchMT's published per-case list (arXiv 2605.15537, checked 2026-10-09) or in the papers we reviewed.

Re-checked 2026-10-11 against SpecLens (2609.16729) and VeriRefine (2607.18519). Two RTLLM labels changed: `fixed_point_substractor` and `alu` (see [NOVELTY_REVIEW.md](NOVELTY_REVIEW.md) §1).

**Not submitted anywhere.** Filing issues upstream needs the team's decision.

Legend:
- **Defect:** no spec-faithful implementation can pass, or the spec contradicts itself or the reference.
- **Underspecified:** the spec is silent and the reference picks one reading.
- **Harness:** a test-infrastructure problem.
- **Note:** not a defect, but relevant to tool builders.

## VerilogEval v2 (spec-to-rtl)

| Problem | Type | Issue | Verification | New? |
|---|---|---|---|---|
| Prob139_2013_q2bfsm | Harness | Testbench race: `resetn = 1` is a *blocking* assignment at `@(posedge clk)`. Two-process FSMs are graded wrong | With `<=` instead, the "failing" designs pass with 0 mismatches (Icarus 12) | **new** |
| Prob099_m2014_q6c | Harness | Testbench connects ports `Y2`/`Y4`; the interface declares `Y1`/`Y3` | Every spec-conforming design fails to compile | earlier project audit |
| Prob082_lfsr32, Prob141_count_clock | Harness (tool-dependent) | The reference itself hits the testbench `TIMEOUT` under Icarus 12 (200,000 samples, 0 mismatches) | Reference vs reference run | **new** (may depend on the Icarus version) |
| Prob062_bugs_mux2 | Defect | Spec vs reference contradiction (mux select direction) | Manual audit; LLM judge sides with the spec | earlier project audit |
| Prob093_ece241_2014_q3 | Defect | K-map in the spec vs reference | Manual audit; judge flagged 5 questions | earlier project audit |
| Prob149_ece241_2013_q4 | Defect | Spec text (fill-valve direction) vs reference; sensor patterns undefined | Manual audit; judge: "s=3'b110 is not a valid sensor pattern" | earlier project audit |
| Prob135_m2014_q6b | Defect (ambiguity) | Bit indexing: is `y[1]` the LSB of the 3-bit port `y` taken from an original `y[3:1]`? | Judge disagreement + manual reading | **new** |
| Prob116_m2014_q3 | Defect | K-map input bit order unstated | Judge: "bit ordering of x is not explicitly stated" | RTL-BenchMT |
| Prob150_review2015_fsmonehot | Defect | — | Judge flagged it independently | RTL-BenchMT |
| Prob066_edgecapture | Underspecified | Does the previous-input register update during reset? | Causal divergence test (inputs zeroed during reset) | RTL-BenchMT |
| Prob034_dff8, Prob053_m2014_q4d | Underspecified | Initial register values unstated; every sample "fails" identically | Unanimously wrong pools | RTL-BenchMT |
| Prob104_mt2015_muxdff | Underspecified | Initial value unstated | Unanimously wrong pool | earlier project audit |
| Prob153_gshare | Underspecified | Reset value of the pattern-history table unstated (reference uses `01`) | Judge answered UNCLEAR and named it | earlier project note |
| Prob070_ece241_2013_q2 | Underspecified | Spec says input 8 "never occurs", but the testbench checks a defined output for it | Judge: don't care | **new** |
| Prob098_circuit7 | Underspecified | The waveform spec shows `q = x` at the first edge | Judge reading | **new** (benign) |
| Prob156_review2015_fancytimer | Harness | The reference itself hits the testbench `TIMEOUT` (100K cycles, 0 mismatches). Our grading treated every design as failing; DS4.1 is actually 4/5 correct | Reference self-check of all 156 problems (only 082, 141, 156 time out; 099 fails to compile). `grade.py` fixed 2026-10-11 | **new** |
| Prob131_mt2015_q4 | Defect | The spec never names the module `TopModule`; samples use other names and fail with "Unknown module type: TopModule" | All DS4.1 samples fail to compile for this reason | **new** (RTL-BenchMT lists 131, reason not checked) |
| Prob136_m2014_q6 | Underspecified | A `reset` port exists, but the spec never states polarity, sync/async, or reset state (the reference uses synchronous, active high, to A) | Full audit | RTL-BenchMT |
| Prob148_2013_q2afsm | Typo | The diagram edge `A --r0=0,r1=0,r2=0--> D` should read r2=1 (it duplicates A's self-loop); the prose is correct | Full audit | RTL-BenchMT |
| Prob031_dff, Prob080_timer, Prob076, Prob132 | Typo | `input q` (should be output); stray sentence "implement a single D flip-flop"; stray `);`; copy-pasted heading "adder-subtractor" | Full audit | **new** (benign) |
| Prob154_fsm_ps2data | Note | Testbench masks `out_bytes` while `done = 0` (a correct don't-care); naive equivalence labels are too strict | Testbench reading | — |

## RTLLM (local v2 copy, 42 problems; items marked v2.1 re-checked on GitHub main)

| Problem | Type | Issue | Verification | New? |
|---|---|---|---|---|
| fixed_point_adder | Defect | "If `a` is greater than `b`, the result is `a - b` and the MSB … is set to 0". Wrong when `a` is negative; the reference sets MSB = 1 | Judge followed the literal text and flagged it; **still in v2.1** | **new** |
| fixed_point_substractor | Defect | "The sign of the result will be the same as the inputs" gives a positive result for 0 − b; the reference implements this literally | Judge flagged it; **still in v2.1** | Known: SpecLens lists the task as a spec–testbench mismatch without details. Our diagnosis is new |
| alu | Defect | `flag` is "the result of slt and sltu" in one place, and "set to '1' when the operation is SLT or SLTU" in another | Judge quoted both; **still in v2.1** | **new issue** in a known task. SpecLens reports a different `alu` problem (LUI uses the upper 16 bits of `a`) |
| instr_reg | Defect | Spec: "on the rising edge of the clock, if rst is low, both registers are initialized" (synchronous). Reference: `always @(posedge clk or negedge rst)` (asynchronous) | Judge followed the spec; **still in v2.1** | **new** |
| sequence_detector | Underspecified | Whether overlapping occurrences of `1001` are detected | Judge UNCLEAR | **new** |
| div_16bit | Underspecified | Division by zero | Judge | **new** (benign) |
| square_wave | Underspecified | No reset or initial value | Judge | **new** (benign) |
| LIFObuffer | Underspecified | `dataOut` during reset | Judge | **new** (benign) |
| adder_pipe_64bit, multi_pipe_4bit, ring_counter, asyn_fifo, freq_divbyeven (compile), radix2_div, clkgenerator (functional), RAM (top ambiguous) | Harness (tool-dependent) | The reference fails its own testbench under local Icarus 12 | Reference self-check | not verified as defects |

## NVIDIA CVDP v1.1.0 (cid003, non-agentic, no commercial)

| Task | Type | Issue | Verification | New? |
|---|---|---|---|---|
| cvdp_copilot_ethernet_packet_parser_0001 | Defect | Harness TOPLEVEL `field_extract` appears nowhere in the prompt; the output file is `rtl/ethernet_parser.v` | `cvdp_toplevel_audit.py`; all 5 samples fail to compile | **new** |
| cvdp_copilot_sync_serial_communication_0001 | Defect | TOPLEVEL `sync_serial_communication_tx_rx`; output file `..._top.sv`; name absent from the prompt | Same | **new** |
| cvdp_copilot_hebbian_rule_0017 | Defect | Prompt names `hebbian_rule`; harness and file use `hebb_gates` | Same | **new** |
| cvdp_copilot_sequencial_binary_to_one_hot_decoder_0001 | Defect | Prompt spells the module "sequencial"; harness expects "sequential" | Same | **new** |
| 15 tasks, e.g. clock_divider_0003, restoring_division_0001, thermostat_0001, car_parking_management_0001, filo_0005 | Note (test adequacy) | ≥2 behaviourally different designs all pass the official tests | Reference-free differential simulation; random stimuli may partly leave valid input protocols | **new** observation |
| Example cvdp_copilot_lfsr_0001 (solved example) | Note (test adequacy) | The test cannot detect a design that loads `~seed` on reset (it checks only next-state consistency and period) | Mutation check | **new** observation |

## Found by consensus-vs-reference questions (E2, 2026-10-11)

| Task | Type | Issue | Verification | New? |
|---|---|---|---|---|
| RTLLM pulse_detect | Defect (spec vs reference) | The spec says `data_out` is produced "inside an always block, sensitive to the positive edge of the clk signal" (registered). The reference's registered block is commented out and replaced by a combinational `always @(*)` (Mealy) output. All 5 DS4.1 samples follow the spec and fail | Both judge prompts flagged it; reference read; **still in v2.1** (GitHub main, `Miscellaneous/Others/pulse_detect`) | **new** (not in RTL-BenchMT or SpecLens lists) |

## Confirmed test gaps: designs that violate an explicit spec statement but pass the official tests (2026-10-11)

These come from hand adjudication of every "all options pass" judge question ([askrtl/adjudication_n1.json](askrtl/adjudication_n1.json)). Each gap ships as an executable supplementary test: minimal stimulus plus the spec-required value ([askrtl/supp_tests/](askrtl/supp_tests/)). Where a reference exists, it passes the test.

| Task | Spec statement the passing design violates | Violating designs |
|---|---|---|
| VerilogEval Prob079_fsm3onehot | Next-state logic "by inspection" on a multi-hot state | 1 |
| VerilogEval Prob143_fsm_onehot (2 checks) | "the input state can be a combination of multiple states" (S0+S7 → out2=1; S0+S1 → next S1\|S2) | 1 each |
| RTLLM JC_counter | Update "on the falling edge of rst_n" (asynchronous reset) | 1 |
| CVDP axi_register_0001 | A write to an undefined address returns SLVERR | 1 |
| CVDP complex_multiplier_0001 | Complex components are signed (implied, not stated) | 2 |
| CVDP dbi_0001 | While reset is active, data_out=0 and dbi_cntrl=00 (the design drives X) | 1 |
| CVDP filo_0005 | Pop when not empty (push and pop together on a non-empty FILO) | 1 |
| CVDP thermostat_0001 | o_fan=1 if i_fan_on=1 (no fault, enabled) | 1 |

## Totals

| Benchmark | Defects (of which new) | Underspecified (of which new) | Harness issues |
|---|---|---|---|
| VerilogEval | 6 (1 new) | 7 (2 new) | 4 (3 new) |
| RTLLM | 4 (2 new tasks + 1 new issue in a known task + 1 known task newly diagnosed; all still in v2.1) | 4 (4 new) | 8 tool-dependent |
| CVDP | 4 interface-name defects (4 new) | — | Test-adequacy notes |
