# Research plan: Ask, Don't Vote

*Query-efficient behavioural disambiguation for spec-to-RTL generation with open-weight LLMs*

Date: 2026-10-08 · Status: **Phase 1 complete (gate passed, see [PHASE1_REPORT.md](PHASE1_REPORT.md)); Phase 2 awaiting approval** · No paid API used yet · Working name: **AskRTL**

> **Correction (after Phase 1):** two problems (082, 141) were graded wrong in the pilot because the reference itself hits the testbench timeout. Corrected numbers: per-sample 79.1%, majority 87.8%, pass@any **94.9%**. The figures in Section 3 below are the original pilot values.

---

## 1. Summary

The literature from 2024–2026 has already covered the obvious next steps for our pipeline:

| Line of work | Covered by |
|---|---|
| Candidate clustering and voting | VRank, VFocus |
| Turning divergence into constraints | SpecLens (ASP-DAC 2027) |
| Spec repair with human arbitration | VClare (Jul 2026) |
| Formal cross-model consensus for triage | NoTB (MLCAD 2026) |
| LLM testbench generation | AutoBench, CorrectBench, PRO-V |

A zero-cost pilot on our existing DeepSeek candidates (Section 3) shows where the remaining headroom is:

- **Voting fails because errors are correlated.** That is true even when every disagreement is visible, because the official stimuli are used.
  - Majority vote reaches 87.2%, while at least one correct candidate exists for 93.6% of problems.
  - Most of the gap is in FSMs and protocols.
  - With perfect answers to the questions, 1–3 binary questions per problem would close the gap.
- **Most problems with no correct candidate are spec defects, not model weakness.** Six of the ten are unstated initial values or contradictions between the spec and the benchmark.

**Proposed direction.** Treat the candidate pool as a set of hypotheses about the intended behaviour. Do not vote among them. Instead:

1. find a **minimal input sequence that separates two behaviour clusters**;
2. **ask** a judge about that one concrete situation: what does the spec require the output to be here? The judge is an LLM, or a human when the LLM is unsure;
3. update the cluster probabilities with a noisy-oracle Bayesian rule, then choose the next most informative question.

"The spec doesn't say" is an allowed answer. It turns spec ambiguity into a concrete, answerable question instead of a silent failure.

**The central bet is falsifiable.** It is a *generation–verification gap*: an LLM judging a short, concrete trace is more accurate than the majority of its own full generations, especially on FSMs. Phase 2 tests this cheaply, using only judge calls on existing pools, before any large spend.

---

## 2. Literature map (2024–2026) and what remains open

| Line of work | Representative papers | What they do | Open gap we target |
|---|---|---|---|
| Self-consistency selection | VRank (ISQED'25), VFocus (Nov'25) | Cluster candidates by outputs on an LLM-written testbench; pick the largest / most consistent cluster | Assumes the majority is right. Our pilot shows correlated errors defeat this on FSMs |
| Divergence → constraints | **SpecLens** (Sep'26, ASP-DAC'27) | LLM-generated stimuli. An LLM picks the better of the **top-2** clusters' traces and derives textual constraints. 89.4% on VerilogEval v2 with o3-mini | ~145K tokens/task. Fails when the correct cluster is not in the top 2 (15.8% of rounds for o3-mini-high). Stimulus refinement rarely helps (3.8%). Traces are long, and LLMs read waveforms poorly (ChipBench). Closed models only |
| Spec imperfection | **VClare** (Jul'26), SpecFix (ASE'25, software), 2508.05266 | Mine inconsistencies in the spec text. A human confirms the first divergent test between the top-2 clusters | Evaluated only on **injected** defects. Single arbitration point. No query-efficiency analysis. No LLM-as-oracle accuracy study |
| Formal consensus | **NoTB** (MLCAD'26) | Pairwise sequential equivalence checking (JasperGold) across 4 model families; accept if ≥k families agree | **Triage only**: defers on disagreement, no pass@1 gain, no ambiguity handling. Commercial tool |
| Testbench generation | AutoBench, CorrectBench, PRO-V(-R1) | Generate and self-correct testbenches from the spec | Crowded. The testbench itself is the error-prone oracle (our Prob018/041/043/063 contract errors; NoTB: 43–84% precision depending on testbench author) |
| Multi-agent / formal repair | MAGE, VerilogCoder, HDLFORGE (BMC traces → micro-tests), 2607.28877 | Generate → test → debug loops; HDLFORGE runs bounded model checking (BMC) against LLM-written properties | Properties and tests come from the same LLM that misreads the spec |
| Interactive synthesis (software) | TiCoder (TSE'24), Test-Time Transduction (NeurIPS'25) | Ask the user or an LLM about distinguishing tests; maximin query selection | Not applied to **sequential hardware**, where traces are temporal, reset protocols matter and don't-cares are common |
| Benchmark quality | RTL-BenchMT (May'26), GateTruth (Aug'26), 2508.05266 | Flawed specs and weak testbenches in VerilogEval and RTLLM | We treat these as evaluation hygiene, not as the main contribution |
| FSM difficulty | LLM-FSM (Feb'26) | 1,000 generated FSM tasks; accuracy drops sharply with complexity | A natural scaling testbed for our method |

**Novelty claim, scoped honestly.** Divergence analysis and human arbitration both exist. What does not, as far as we found, is the combination of:

- (a) *minimal* distinguishing traces for sequential RTL as the unit of questioning,
- (b) choosing questions over *all* clusters with a noisy-oracle model, so a minority-correct cluster can win,
- (c) an explicit "spec doesn't constrain this" / "spec unclear" answer that flags real (not injected) ambiguity,
- (d) an empirical study of the **generation–verification gap on traces** for RTL,
- (e) open-weight models and an open-source toolchain, with token cost reported.

We must re-check arXiv before writing. The area moves monthly: SpecLens appeared 3 weeks ago.

---

## 3. Pilot evidence (zero API cost)

Code: [pilot_pool/pool_analysis.py](pilot_pool/pool_analysis.py), [pilot_pool/summarise.py](pilot_pool/summarise.py). Output: `pilot_pool/out/summary.json`.

**Setup.**

- For each VerilogEval spec-to-rtl problem, we took every *initial* (pre-repair) candidate from six earlier runs:
  - deepseek_full (v4-pro)
  - legacy_v2
  - direct_batch
  - json_ir
  - two three-candidate runs (deepseek-flash)
- That gives ~9.5 samples per problem. Identical code (after normalisation) was deduplicated, and duplicates count as votes.
- Each candidate was graded against the official reference.
- Each pair was compared by renaming one candidate to `RefModule` inside the official testbench. Two candidates agree only if there are 0 mismatches in both directions.
- Clusters are the connected components of that agreement graph.
- All 156 problems are done.

| Metric | Value |
|---|---|
| Mean per-sample accuracy (pass@1 estimate) | 78.4% |
| Best single source (json_ir / v4-pro single shot) | 89.5% / 86.8% |
| Majority vote, official stimuli, clusters that all pass the reference merged (don't-cares) | **87.2%** |
| Pool coverage: at least one candidate correct (pass@any) | **93.6%** |
| Covered but voting fails | **10 problems**: 066, 071, 112, 128, 133, 137, 139, 140, 142, 155. Seven are FSM or protocol tasks |
| Questions a perfect oracle needs to isolate the correct cluster (divergent problems) | 1 question: 26 · 2: 20 · 3: 11 |
| Unanimous but wrong | 034, 053, 104: all **initial values the spec never states** |
| Divergent, but no candidate correct | 062, 093, 149 (**spec contradicts the reference**), 082 and 141 (hit the testbench time limit; possibly a harness issue), 156 (genuinely hard) |
| FSM category (35 problems) | 10 have a correct candidate that is in the minority or tied |

**Reading of the pilot.**

1. Voting barely beats the best single configuration. Even with the official stimuli, which no real method has, it leaves 6.4 points on the table. Those points sit in sequential and FSM tasks.
2. The wrong majorities are mostly near-identical samples from one configuration: deepseek-flash, reasoning off, same prompt family. Errors within a configuration are strongly correlated, so more samples from the same source do not help.
3. Several "splits" between correct candidates are don't-care noise: they differ only where the reference output is X. A disambiguation method needs an "unconstrained" answer.
4. Of the 10 problems with no correct candidate, 6 are spec defects and 2 are testbench time-limit problems. Evaluation must report these separately (errata list) or the method will be blamed or credited wrongly.

**Caveats.** The pool is not i.i.d. (mixed prompts and two DeepSeek models). The stimuli are the benchmark's own, so the 87.6% voting figure is an upper bound for voting. It is a single model family. VerilogEval is close to saturated for strong models, so harder sets are needed (Section 5).

---

## 4. Directions considered

| Direction | Novelty | Feasibility (API, no GPU, Windows) | Expected impact | Verdict |
|---|---|---|---|---|
| **A. Ask-don't-vote disambiguation** (this plan) | Medium-high (see Section 2) | High: iverilog now; yosys/SBY optional | Targets the measured gap. Gives clean, falsifiable hypotheses | **Pursue** |
| B. Better LLM testbench / contract generation | Low (CorrectBench, PRO-V, AutoBench) | High | Incremental | Drop. Reuse our contract code only as a baseline |
| C. Automatic spec repair / ambiguity | Low-medium (VClare, SpecFix) | High | Partly covered | Fold into A as the "spec unclear" answer, evaluated on *natural* defects |
| D. Formal consensus triage | Low (NoTB) | Medium (needs open-source sequential equivalence checking) | Selective prediction only | Use as a component and a baseline |
| E. Fine-tuning / RL of small models | Low (CodeV-R1, VeriReason, …) | Low (no GPU budget; off-goal) | — | Drop |
| F. Cost-aware model routing | Low (HDLFORGE) | High | Engineering | Report cost as a metric only |
| G. FSM intermediate representation + deterministic codegen | Medium-low (LLM-FSM uses YAML; our json_ir is already the best source at 90%) | High | Solid but narrower | Keep json_ir as a strong, diverse **candidate source** inside A |

---

## 5. Method sketch: AskRTL

1. **Diverse hypothesis pool.**
   - Draw N≈8–12 candidates from at least two open-weight families (e.g., DeepSeek-V4, Qwen3-Coder, GLM) and different prompt styles, including our json_ir route.
   - Add *interpretation-diverse sampling*: an LLM lists unstated aspects (reset and initial values, edge vs level, timing of outputs) and we generate one variant per reading. This targets unanimous-wrong cases like 034/053/104.
2. **Behaviour partition and minimal distinguishing traces.**
   - Compile everything, then search for distinguishing inputs between cluster representatives. Three ways, cheapest first:
     - random simulation that respects the reset protocol inferred from the ports;
     - directed search;
     - optional formal BMC on a miter (yosys/SBY), which also proves equivalence so clusters can be merged.
   - Minimise each trace (shortest prefix, fewest input changes; delta debugging).
   - Render it as a small cycle table.
3. **Question.** Show the spec, the minimal trace and the alternative output values. Never show the code. The judge answers one of:
   - **A / B / …**: this output is the one the spec requires;
   - **unconstrained**: both outputs are acceptable (don't-care or invalid input);
   - **unclear**: the spec is ambiguous here.

   Sample the judge k times, with paraphrases, to get a confidence estimate.
4. **Noisy-oracle update and question selection.**
   - Bayesian weights over clusters. The prior comes from votes, discounted for duplicates from the same configuration. The likelihood comes from judge accuracy.
   - Choose the next question by expected information gain (or maximin).
   - Stop when one cluster's posterior exceeds τ or the budget runs out.
5. **Escalation and outputs.**
   - "Unclear" answers go to a human (we count them) or become flagged assumptions.
   - Output: the selected RTL, a confidence score, the questions that were answered as spec addenda, and regression tests built from those answers.

**Hypotheses.**

- **H1 (generation–verification gap).** On problems where candidates diverge, the LLM judge's answer on a minimal trace is right more often than majority vote is, *with the same model*. The prediction is strongest for FSMs.
- **H2 (minimality matters).** Judge accuracy falls with trace length and number of input changes. Minimal traces beat SpecLens-style full traces.
- **H3 (query efficiency).** At most ~2 questions per problem on average recover most of the pass@any − vote gap. Information-gain ordering beats top-2-only arbitration, which is what VClare and SpecLens do.
- **H4 (natural ambiguity).** "Unclear" and "unconstrained" answers, plus disagreement between judge samples, flag real spec defects (034, 053, 104, 062, 093, 149, …) with useful precision.
- **H5 (diversity for correlated errors).** Interpretation-diverse sampling raises pool coverage on unanimous-wrong problems. Adding more i.i.d. samples does not.

---

## 6. Experimental plan with go/no-go gates

**Benchmarks.**

- VerilogEval v2 spec-to-rtl, with our errata column reported separately.
- RTLLM v2: the harness already exists (`run.py rtllm`).
- An FSM scaling set: LLM-FSM if it has been released; otherwise our own generator (random FSM → YAML → NL spec → reference), which is also contamination-free.
- Optional: a CVDP code-generation subset (cocotb/Docker cost).

**Models (open-weight, via API).** DeepSeek-V4 flash and pro (already integrated) plus one or two of Qwen3-Coder, GLM-4.x, Kimi. Each must be tried with ≥2 sampling configurations, because configuration sensitivity is large (2604.17102).

**Baselines.**

- single-shot
- best-of-N with our contract tests
- majority / self-consistency (VRank-style, LLM testbench)
- SpecLens-style top-2 trace judging with full traces (re-implemented)
- NoTB-style agreement triage
- VClare-style single human arbitration (simulated)

**Metrics.**

- pass@1 after selection
- coverage vs precision (risk–coverage curve)
- questions per problem (LLM and human counted separately)
- tokens and cost per problem
- ambiguity-flag precision and recall against the hand-verified errata

| Phase | Work | Spend | Gate |
|---|---|---|---|
| 0 ✅ | Literature, pool pilot | 0 | — |
| 1 (wk 1–2) | Local distinguishing-input search and minimiser on existing pools. Check that it finds the divergences the official stimuli reveal. Build the trace renderer and judge prompt | 0 | Search recall ≥ 80% of official-stimulus divergences, or add formal BMC |
| 2 (wk 2–3) | **H1/H2 test**: judge calls only, on the ~55 divergent pilot problems × ≤3 questions, with minimal vs full traces, DeepSeek flash and pro | ~0.3–0.6M tokens | **Go if** judge accuracy > majority on divergent FSM problems. Otherwise pivot to human-in-the-loop query efficiency + ambiguity audit (still publishable) |
| 3 (wk 3–6) | Controlled i.i.d. sampling, 2–3 models × 3 benchmarks; full AskRTL vs baselines | ~10–15M tokens per model (≈400 problems × 10 samples × 3K, plus questions) | — |
| 4 (wk 6–8) | Ablations (minimality, question policy, diversity sampling, oracle noise), simulated human-query study, errata release, writing | small | — |

Target venues: a workshop (MLCAD / LAD / ICCAD-W), or the DATE/ASP-DAC tier if H1–H3 hold on two or more benchmarks.

---

## 7. Risks

| Risk | Mitigation |
|---|---|
| H1 fails: the judge shares the generator's misreading | Cheap to learn in Phase 2. Fall back to human questions (the query-efficiency result still holds) and report the negative result |
| Scooped (fast-moving area) | Move fast. Our unique angles are the minimal-trace and oracle-accuracy study, minority-correct recovery, and natural ambiguity |
| VerilogEval saturated | FSM scaling set + RTLLM v2, where both headroom and divergence are larger |
| Random stimuli violate input protocols (false divergences) | "Unconstrained" answer; reset/valid-protocol inference; formal BMC with assumptions |
| Formal tools on Windows | Start simulation-only. OSS CAD Suite (yosys/SBY/eqy) is optional, or run it in WSL |
| Reviewer fairness (official stimuli, leakage) | Methods never see the reference or the official testbench. Benchmark-assisted runs (e.g., the 10-08 targeted repair) stay out of the headline tables |

---

## 8. What I need from you

1. **API access** for at least two open-weight model families. DeepSeek is set up; add one of Qwen3-Coder, GLM or Kimi. Also a **spending cap per phase**; Phase 2 is under 1M tokens.
2. Permission to **download and install OSS CAD Suite** (yosys/SBY/eqy, ~1–2 GB) or to use WSL. This is optional and only needed if Phase 1 search recall is too low.
3. Agreement that experiment code lives under `research/` and the existing pipeline stays untouched except for reuse.

## References (verified 2026-10-08)

- SpecLens — https://arxiv.org/abs/2609.16729
- VClare — https://arxiv.org/abs/2607.24854
- NoTB — https://arxiv.org/abs/2608.21962
- VRank — https://arxiv.org/abs/2502.00028
- VFocus — https://arxiv.org/abs/2511.02285
- MAGE — https://arxiv.org/abs/2412.07822
- PRO-V — https://arxiv.org/abs/2506.12200
- CorrectBench — https://arxiv.org/abs/2411.08510
- HDLFORGE — https://arxiv.org/abs/2603.04646
- SpecFix — https://arxiv.org/abs/2505.07270
- TiCoder — https://arxiv.org/abs/2208.05950
- Test-Time Transduction — https://arxiv.org/abs/2509.17393
- RTL-BenchMT — https://arxiv.org/abs/2605.15537
- GateTruth — https://arxiv.org/abs/2608.12635
- Errors of LLM RTL — https://arxiv.org/abs/2508.05266
- LLM-FSM — https://arxiv.org/abs/2602.07032
- Configuration over Selection — https://arxiv.org/abs/2604.17102
- Front-end EDA challenges — https://arxiv.org/abs/2607.09616
- Verilog LLM survey — https://arxiv.org/abs/2512.00020
- CVDP — https://arxiv.org/abs/2506.14074
