# Phase 3 report: same-model pools (A), RTLLM (B), defect detection (D)

Date: 2026-10-09 · Model: `deepseek-flash` (DS 4.1 Flash) for **both** generation and judging · Spend: ≈4.8M tokens

| Item | Calls | Tokens |
|---|---|---|
| VerilogEval generation | 781 | 2.61M |
| RTLLM generation | 218 | 1.70M |
| Online judge | 44 | 0.45M |

## 1. Setup

- **Pools:** 5 i.i.d. samples per problem from one configuration (baseline prompt, reasoning effort high).
  - VerilogEval: all 156 problems.
  - RTLLM: the 42 of 50 v2 problems whose reference passes its own testbench under local Icarus. They were rebuilt from the 2026-10-08 reference-check run; no download.
- **Failed generations:** two RTLLM problems (`float_multi`, `freq_divbyfrac`) repeatedly ran into the 32K output cap. Those samples are missing and count as generation failures.
- **Pipeline:** unchanged from Phases 1–2 (`research/askrtl`, `ASKRTL_TAG` / `ASKRTL_BENCH`). The online policy uses a per-configuration prior, judge accuracy p=0.8, ≤3 questions, and τ=0.95.
- **Bug found and fixed during this phase:** parameterised RTLLM designs were simulated with each design's *own* parameter defaults, so candidates with `N=16` were compared against a reference with `N=32`. Simulation now uses the testbench's parameter values (`Bench.params`, Icarus `-P`, `#(...)` overrides). The two affected problems were re-run.

## 2. Results (A, B)

| Pool | Per-sample pass@1 | Majority vote | **AskRTL online** | Ceiling (pass@any) | Questions asked |
|---|---|---|---|---|---|
| VerilogEval, DS 4.1 Flash × 5 | 82.1% | 87.2% | **87.5%** | 91.0% | 26 (1.24 per divergent problem) |
| RTLLM (42), DS 4.1 Flash × 5 | 83.8% | 84.1% | **85.7%** | 88.1% | 16 (1.45 per divergent problem) |
| *Pilot for comparison: VerilogEval, older DeepSeek pools, DS 4.1 Flash judge* | 79.1% | 88.5% | 92.9% | 94.9% | 74 (1.37) |

**With the same model generating and judging, asking barely beats voting.** The reason shows up in *where* its own samples disagree.

**VerilogEval, 7 problems between majority vote and the ceiling:**

| Problem | What it is | AskRTL |
|---|---|---|
| 066 | RTL-BenchMT defect | solved |
| 098 | Waveform shows `q = x` at the first edge (benign initial value) | lost |
| 116 | RTL-BenchMT defect | lost |
| 135 | Bit-index ambiguity (**new**) | lost |
| 137 | Genuine FSM disagreement | **solved** |
| 150 | RTL-BenchMT defect | lost |
| 154 | Testbench masks the output (our label artifact) | lost |

That's 6 of 7 spec defects, ambiguities or artifacts.

**VerilogEval, 5 divergent problems with no correct cluster:** 062, 093 and 149 (spec contradicts reference), 146 and 156.

**RTLLM gap problems:**
- `fixed_point_adder`: spec defect;
- `traffic_light`: genuine; **solved by AskRTL**.

**Interpretation:**
- A weaker model's samples disagree on genuine functional points, and a judge resolves those well (pilot: +4.4 points).
- A strong model's samples disagree mostly *where the specification itself is defective or silent*.
- So the generation-vs-verification gap exists on clean questions (137, 066, `traffic_light` all solved), but on current benchmarks it is small. The disagreements that remain are better treated as **spec-defect reports** than as selection problems.

## 3. D: judge disagreement as a specification-defect detector

**Rule, fixed before adjudication.** A problem is *flagged* if, on any question the judge was asked, it:
- picks an option that contradicts the reference with confidence ≥0.9, or
- answers ANY/UNCLEAR where the reference has a single required value.

**Flagged:** 16 problems across the pilot and DS 4.1 runs. Two more problems were adjudicated from their spec-gap notes (`alu`, `LIFObuffer`). Each flag was **checked by hand** against the spec, the question trace and the reference.

| Problem | Bench | Adjudication | Evidence |
|---|---|---|---|
| Prob062 bugs_mux2 | VE | **Spec defect** (spec vs reference) | Earlier manual audit |
| Prob093 ece241_2014_q3 | VE | **Spec defect** (K-map vs reference) | Earlier manual audit |
| Prob149 ece241_2013_q4 | VE | **Spec defect**: spec vs reference; invalid sensor states | The judge names the undefined sensor patterns |
| Prob150 review2015_fsmonehot | VE | **Spec defect** | In RTL-BenchMT's independent list |
| Prob116 m2014_q3 | VE | **Spec defect** (bit order) | In RTL-BenchMT's list; the judge flagged "bit ordering of x is not explicitly stated" |
| Prob135 m2014_q6b | VE | **Spec ambiguity (new)**: is `y[1]` the LSB of a 3-bit `y` port taken from an original `y[3:1]`? | Same family as Prob099's port bug and RTL-BenchMT's Prob136 |
| fixed_point_adder | RTLLM | **Spec defect (new)**: "if a is larger, set the result MSB to 0" is wrong when a is negative; the reference sets it to 1 | The judge followed the literal text and wrote "spec's sign handling… possibly incorrect" |
| fixed_point_substractor | RTLLM | **Spec defect (new)**: "same-sign subtraction keeps the sign of the inputs" gives a positive result for 0 − b; the reference implements this literally | The judge noted the contradiction |
| alu | RTLLM | **Spec contradiction (new)**: the overview says `flag` is the slt/sltu *result*; the implementation section says `flag=1` whenever the op is SLT/SLTU | The judge quoted both passages |
| Prob070 ece241_2013_q2 | VE | Underspecified: the spec says this input "never occurs", but the reference defines an output | Judge answer "don't care" is defensible |
| Prob098 circuit7 | VE | Underspecified initial value: the spec waveform shows `x` at the first edge | Benign |
| div_16bit | RTLLM | Underspecified: division by zero | Spec silent |
| square_wave | RTLLM | Underspecified: no reset or initial value | Spec silent |
| LIFObuffer | RTLLM | Underspecified: `dataOut` during reset | Spec silent |
| Prob154 fsm_ps2data | VE | **Our artifact:** the testbench masks `out_bytes` while `done=0`; our labels did not | The judge's "don't care" is correct |
| Prob145 circuit8 | VE | **Our artifact:** latch-style stimulus limitation | — |
| adder_bcd | RTLLM | **Our artifact:** random stimulus produced non-BCD inputs, which the spec excludes | The judge's "don't care" is correct |
| Prob153 gshare | VE | ~~Judge error~~ **Corrected (IDS round): underspecified.** The spec never gives the PHT reset value, and the reference uses `01` | The judge later answered UNCLEAR and named the gap; an earlier project note records the same |

**Summary of the 18 adjudicated problems:**

| Verdict | Count | Problems |
|---|---|---|
| Genuine spec defects / contradictions | **9** | 062, 093, 149, 150, 116, 135, `fixed_point_adder`, `fixed_point_substractor`, `alu` |
| Of these, not in RTL-BenchMT's list or our prior audit | **4** | 135, `fixed_point_adder`, `fixed_point_substractor`, `alu` |
| Real underspecification (benign; the reference picks one reading) | 6 | 070, 098, `div_16bit`, `square_wave`, `LIFObuffer`, 153 (corrected) |
| Our tooling / label artifacts | 3 | 154, 145, `adder_bcd` |
| Judge errors | ~~1~~ **0** | (153 re-adjudicated as underspecified, see [IDS_REPORT.md](IDS_REPORT.md)) |

So **15 of 18 flags (83%) point at a real issue in the specification**, and there are no judge mistakes. The IDS round later found one judge error (`fsm`).

**Recall limits.** RTL-BenchMT's flawed problems where *all* samples agreed never trigger a question: 034, 053, 131, 136, 148, `serial2parallel`. Those that triggered questions where the judge agreed with the reference: 066, `parallel2serial`. Disagreement-triggered detection only sees defects that split the model's own samples. Unanimous misreadings need another signal, such as interpretation-diverse sampling (see DIRECTIONS_V2).

**Version check (done).** All three new RTLLM defects are still present in the current RTLLM main branch (v2.1, released 15 Aug 2026, "corrected several design descriptions"). Verified by reading `design_description.txt` on GitHub:

| Problem | Text still in v2.1 |
|---|---|
| `fixed_point_adder` | "If `a` is greater than `b`, the result is `a - b` and the MSB of the result is set to 0 (positive)." |
| `fixed_point_substractor` | "The sign of the result will be the same as the inputs." |
| `alu` | Both "the 'flag' is the result of 'slt' and 'sltu' instructions" and "set to '1' when the operation is SLT or SLTU" |

None of the three is in RTL-BenchMT's list.

## 3b. Human-in-the-loop variant (no API)

The judge answers when it is decisive and confident. Everything else goes to the user, simulated by the reference's behaviour at 98% reliability (`askrtl/hybrid.py`).

| Pool | Majority | Judge only | Hybrid (escalate if confidence < 0.95) | User answers everything |
|---|---|---|---|---|
| Pilot (older pools) | 88.5% | 92.9% | **94.2%**, 0.06 user questions per problem | 94.9%, 0.46 per problem |
| VerilogEval, DS 4.1 Flash | 87.2% | 87.5% | **90.1%**, 0.04 per problem (6 in total) | 91.0%, 0.16 per problem |
| RTLLM, DS 4.1 Flash | 84.1% | 85.7% | 85.7% | 85.7% |

With the same strong model, a handful of user questions (6 for the whole of VerilogEval) recovers ~75% of the remaining gap. The judge absorbs the other questions. That supports the design: judge first, and escalate only the uncertain questions to the user.

## 4. Conclusions

1. **Weaker generator + stronger judge:** asking clearly beats voting (+4.4 points on VerilogEval).
2. **Same strong model:** asking adds little (+0.3 / +1.6 points). Its own disagreements are dominated by spec defects (6/7 VerilogEval gap problems).
3. **Defect detection:** a judge asked about minimal disagreements works as a spec-defect detector. 78% of flags are real spec issues, it found 4 defects not in prior lists, and it made 1 judge error in 18. (Corrected 2026-10-11: SpecLens already lists `fixed_point_substractor` and a different `alu` issue; see NOVELTY_REVIEW.md.)
4. **Practical consequence for the project goal** (plain NL spec → RTL): when a strong model's samples disagree and the judge says ANY/UNCLEAR or contradicts the obvious reading, **ask the user** a concrete question, rendered as the minimal trace. Silently picking by vote or by judge is the wrong action.
