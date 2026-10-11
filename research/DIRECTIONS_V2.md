# Research directions v2: beyond AskRTL

Date: 2026-10-09 · API spend: **0** · Supersedes the direction choice in [RESEARCH_PLAN.md](RESEARCH_PLAN.md). The Phase 1 tooling is kept: [PHASE1_REPORT.md](PHASE1_REPORT.md).

## 1. Why AskRTL should not be the headline

1. **Overlap.**
   - SpecLens (ASP-DAC'27) already turns sample divergence into spec-derived constraints using an LLM judge.
   - VClare (Jul'26) already asks a human to arbitrate the first divergent test between the top clusters.
   - NoTB (MLCAD'26) already does formal cross-model consensus.

   AskRTL's differences are real (minimal traces, information-gain question choice, ANY/NONE answers, open models) but they are refinements.
2. **Shrinking headroom on the standard benchmark.**
   - VerilogEval has ~100% contamination for most commercial models (VeriContaminated, 2025).
   - It now scores 98.1% with DeepSeek-v3.2 plus correction (2508.05266).
   - Our own pool already covers 94.9%.
3. **A blind spot shared by the whole family.** Every selection and consensus method fails when all samples make the *same* mistake. That includes VRank, VFocus, SpecLens, NoTB, EAHC (Aug'26) and AskRTL. In our pilot:
   - 3 problems were unanimously wrong;
   - the 10 voting failures were driven by near-identical samples from one configuration.

   Nothing in the RTL literature targets **systematic, shared errors**.

## 2. Gaps found in the 2025–26 literature

| Gap | Evidence | Who comes closest |
|---|---|---|
| **G1. Shared errors are invisible to divergence methods** | Our pilot: unanimously wrong pools, correlated majorities. The SpecLens limitation section | None for RTL. NoTB uses model diversity but only for triage |
| **G2. Do models read the spec or recall the canonical design?** | SpecLens notes, in passing, that baselines "still frequently produced the original benchmark-aligned implementation despite explicit local changes to the specification" | Software: *Memorize or Generalize?* (2503.02296) and functional memorization (ICML'26) measure it but don't detect it at inference. RTL: LiveVerilogEval (DATE'26) mutates designs against contamination; CircuitGuard (2510.19676) treats memorization as IP leakage. As far as we found, neither measures **reversion to canonical behaviour** or detects it when generating. We have not read LiveVerilogEval's full text; check it before writing |
| **G3. Real users write deltas from familiar circuits** ("a decade counter but 3–12", "Rule 90 with wrap-around") | This is exactly the regime where training priors compete with the spec. Our project goal is "straightforward NL descriptions" | VClare injects defects (vague / contradictory / incomplete), not *deviations from a canonical design* |

## 3. Directions evaluated

| | Direction | Novelty | Feasibility | Risk | Verdict |
|---|---|---|---|---|---|
| **A** | **CF-RTL: canonical-prior interference.** Benchmark + reversion metric + inference-time *prior-contrastive verification* | **High** in RTL; first study of its kind there; detection side new overall | High. 16 verified variants + grader already built; pilot ≈145 calls | Effect might be small for strong models. The pilot settles it cheaply, and a negative result is still informative | **Recommended** |
| B | AskRTL (minimal-trace questions) | Medium (SpecLens / VClare / NoTB) | Done (Phase 1) | Incremental | Keep as a **component of A** (delta-licensing questions), or as a short paper |
| C | L\*-style active automata learning of FSMs with an LLM as spec oracle | Medium (L\*LM, ICLR-W'25, does DFAs from NL for RL tasks) | Medium-low: hundreds of membership queries per FSM | High cost, oracle noise | Park |
| D | Error-decorrelation portfolios (mix models / IRs / prompts to cover shared errors) | Medium (NoTB cross-family; *Representation Bottleneck* 2604.17097 on IR choice) | High | Incremental | Use as a **baseline / ablation inside A** |
| E | Benchmark hygiene (our errata: testbench race, timeouts, port bug) | Low (RTL-BenchMT, GateTruth) | Done | — | Appendix material |

## 4. Recommended: Direction A, "Spec or Prior?"

### Research questions
- **RQ1 (measurement).** When a spec is a small, natural delta from a canonical design, how often do open-weight LLMs implement the *canonical* behaviour instead?
  - Reversion is measured *exactly*: the design matches the original reference on the official stimulus (exact simulation; formal equivalence later).
  - Which delta types trigger it most? Parameter, rule, or a delta that contradicts a familiar port name (e.g. `pedge` used for falling edges).
- **RQ2 (blind spot).** Are reversion errors *shared* across samples, and so invisible to consensus and divergence methods (majority, VRank-style, SpecLens-style, NoTB-style)?
- **RQ3 (method).** Can **Prior-Contrastive Verification (PCV)** detect and repair reversion without the reference? Steps:
  1. Ask the model for the canonical design C it associates with the spec ("the standard circuit this is based on, without the modifications").
  2. Generate T from the full spec.
  3. Compare T against C behaviourally, with Phase 1 `diffsim` and its minimal traces.
  4. Decide:
     - if T ≡ C while the spec states a delta, flag *recitation* and regenerate with the delta made explicit;
     - if T differs from C, check that each minimal divergence is *licensed by the delta*. This is a local judge question that reuses AskRTL rendering.

  The point: the contrast comes from the spec's delta, not from disagreement between samples. So PCV can catch errors that *every* sample shares.

### Done so far (zero cost)
- [cfrtl/build_seed.py](cfrtl/build_seed.py) holds **16 verified counterfactual variants** across 13 base problems:
  - rule variants: wrap-around and boundaries-one for Rule 90/110, rising capture, left shift, enable priority, down-counter, zero-count, a thermostat fan rule;
  - parameter variants: count 3–12, count 0–499, LFSR taps 5/2 (checked to be maximal length, period 31), reset 0xA5, sequence 1011;
  - pulse vs sticky detection;
  - one **name-conflict** variant: the port is still called `pedge` but the spec asks for falling edges.

  Every delta is a whitespace-insensitive edit of the original spec. Interfaces are unchanged, so the official testbench grades against the counterfactual reference.
- [cfrtl/verify_seed.py](cfrtl/verify_seed.py) gives every variant two checks:
  - the testbench passes the counterfactual reference against itself (0 mismatches);
  - **the testbench separates the counterfactual from the original**, with mismatch rates from 8% to 99% of samples.

  So reversion is measurable for all 16.
- [cfrtl/run_cf.py](cfrtl/run_cf.py) is the generation harness:
  - dry-run by default; live calls need `--live --max-calls N`;
  - unmodified base problems are included as controls;
  - it grades pass / reverted / other failure.

  Its self-test classifies 16/16 counterfactual references as *pass* and 16/16 originals as *reverted*.

### Honest prior evidence against a large effect
On the three natural spec-vs-reference conflicts in VerilogEval (062, 093, 149), *no* DeepSeek candidate reproduced the reference. So DeepSeek may follow spec text over memorised *benchmark* solutions. Canonical *textbook* priors are a different matter and still untested. That's why the pilot comes first.

### Phases and gates

| Phase | Work | Spend | Gate |
|---|---|---|---|
| A0 ✅ | Seed set, verifier, harness, grader self-test | 0 | — |
| A1 | **Pilot:** DS 4.1 Flash, 5 samples × (16 counterfactual + 13 base) = **145 calls**, ≈50K input tokens + reasoning (~0.3–0.6M total) | small | **Go** if counterfactual pass drops ≥10 points below base on ≥4 variants, **or** ≥30% of counterfactual failures are exact reversions. Otherwise publish the negative result as a short note and fall back to AskRTL (B) on harder benchmarks |
| A2 | Scale to 60–100 variants: VerilogEval + RTLLM + a few contamination-free designs, using the same template. Students can write variants; the verifier gates them. 2–3 open model families; reasoning effort as a factor | moderate | — |
| A3 | PCV vs baselines: plain, delta-highlight prompt, self-consistency, SpecLens-style divergence, a cross-family portfolio (D), AskRTL (B) | moderate | — |
| A4 | Analysis: which deltas induce reversion, name conflicts, phrasing ("like X but…"), effect of reasoning | small | — |

**Expected contributions:**
1. The first measurement of canonical-prior interference in RTL generation, with an exact reversion metric.
2. A verified counterfactual benchmark with an auto-verification protocol.
3. Evidence that shared errors defeat consensus methods.
4. PCV, a reference-free detector and repair method that addresses that blind spot.

## 5. Pilot A1 result (2026-10-09): **NO-GO**

Run: `cfrtl/out_cf/20261009_142938`. Model: `deepseek-flash` (DS 4.1 Flash). Reasoning: high. 5 samples × (16 counterfactual + 13 base problems) = 145 calls, 331K tokens.

| Metric | Value |
|---|---|
| Mean pass, base problems | 88.7% |
| Mean pass, counterfactual variants | 85.0% |
| Mean drop | 3.7 points, 95% bootstrap CI [0.0, 7.5] |
| Variants with a drop of 10 points or more | 3 (gate: ≥4) |
| **Exact reversions to the original design** | **0 of 12 counterfactual failures** (gate: ≥30%) |
| Samples where every sample reverted | none |

**What the 17 failures actually are** (base and counterfactual together):

| Cause | Count | Detail |
|---|---|---|
| Tool / dialect | **13 (76%)** | Every Prob096 failure, base *and* counterfactual: SystemVerilog `enum` assignment without a cast, which Icarus rejects. Same family as Prob107/119/127 earlier |
| Cycle-timing convention | 1 | Prob054 negedge: right polarity, but the output is combinational (same cycle) where the spec says "the cycle after" |
| Unspecified state during reset | 3 | Prob066, base and counterfactual: whether the previous-input register updates during reset. Phase 1 flagged the same ambiguity on the original problem |
| API error | 1 | Empty reply |

**Conclusions.**
1. On simple-to-medium deltas, DS 4.1 Flash follows the spec rather than the canonical prior. The recitation hypothesis is not supported. This is a valid negative result.
2. The remaining errors come from **unstated conventions** (latency and registered outputs, reset-time behaviour of auxiliary state) and from **dialect**, not from missing knowledge.
3. This matches Phase 1, where divergences were local (median 1 cycle). The errors that remain are about conventions the spec leaves open, which is what AskRTL's ANY/UNCLEAR questions target.

**Correction (same day): the "unstated conventions" reading does not generalise.** A zero-cost classification over all Phase 1 cluster pairs (`askrtl/divtypes.py`; the reset class uses a causal test, "identical when other inputs are held at 0 during reset") gives:

| Correct-vs-incorrect pairs (older DeepSeek pool) | Count |
|---|---|
| Genuine value difference | 91 |
| Init / X | 5 |
| Latency shift (½ or 1 cycle) | 2 |
| Reset-time behaviour | 1 |
| Not separated (Prob139 race, Prob145 latch) | 2 |

Convention share: **8%**. Only 7 of 89 wrong clusters differ from a correct one *only* by a convention. So most of the pool's remaining errors are real functional errors, not convention gaps. A "convention gap" headline is not supported either.

Per the gate, Direction A is shelved for this model class. Possible revival: much harder canonical attractors (complex FSMs / protocols), or weaker models.

## Sources
- VeriContaminated: https://arxiv.org/abs/2503.13572
- Memorize or Generalize?: https://arxiv.org/abs/2503.02296
- Detecting Functional Memorization in Code LMs: https://arxiv.org/html/2606.12764v1
- CircuitGuard: https://arxiv.org/pdf/2510.19676
- NotSoTiny: https://arxiv.org/abs/2512.20823
- Representation Bottleneck: https://arxiv.org/abs/2604.17097
- L\*LM: https://arxiv.org/abs/2402.07051
- EAHC reranking: https://arxiv.org/abs/2608.22938
- EstRTL: https://arxiv.org/abs/2606.09867
- Errors of LLM RTL / 98.1%: https://arxiv.org/abs/2508.05266
- SVA robustness under transformations: https://arxiv.org/abs/2609.05658
- VerilogCL: https://arxiv.org/html/2604.18162v1
- QiMeng-CRUX: https://arxiv.org/abs/2511.20099
- SpecLens / VClare / NoTB: see RESEARCH_PLAN.md
