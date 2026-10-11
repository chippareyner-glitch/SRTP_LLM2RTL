# research/ — 候选分歧研究（AskRTL 及后续）

2026-10-08 到 10-11 做的研究代码、数据和报告。原有的"生成 → 验证 → 修复"流程在仓库根目录。本目录不改原流程，只会 import 根目录的 `llm_client.py` 等模块。

**一句话结论**：对强模型（DeepSeek 4.1 Flash）来说，多个候选设计之间的分歧，大多数指向**规格缺陷或测试漏洞**，而不是模型能力不足。"分歧 + LLM 评审"可以当作一个不需要参考答案的规格/测试审计工具。用它来挑选候选的提升空间有限，上限受规格质量约束。

## 先读哪些

| 文件 | 内容 |
|---|---|
| `工作总结_接手前后_20261011.md` | 中文总览：原有流程 vs 接手后做的事，含花费 |
| `SRTP研究报告_20261010.md` | 中文主报告（已按 10-11 的复核结果加注修正） |
| `NOVELTY_REVIEW.md` | 创新点复核、相关工作对比、修正后的主线（§6–§7 是 N1/N2 审计） |
| `EXP_20261011.md` | E1 宽容性提示、E2 共识 vs 参考、E3 弱生成器（未通过门槛） |
| `BENCHMARK_ERRATA.md` | VerilogEval / RTLLM / CVDP 的基准勘误汇总 |
| `VERILOGEVAL_AUDIT_20261011.md` | VerilogEval 156 题全量审计（33 题有问题） |
| `RESEARCH_REPORT.md` | 英文总报告（Phase 1–3） |
| `PHASE1/2/3_REPORT.md`、`IDS_REPORT.md`、`CVDP_REPORT.md` | 各阶段详细报告 |
| `RESEARCH_PLAN.md`、`DIRECTIONS_V2.md` | 早期调研与选方向（CF-RTL 方向已否定） |

> 报告之间若数字不一致，以各报告中**最新的修正说明**为准（IDS 增益、修复试点、CVDP 时钟识别修复后的数字都改过）。

## 目录

| 路径 | 内容 |
|---|---|
| `bench.py` / `grade.py` | 三个基准的统一抽象与评分（VerilogEval、RTLLM 本地 42 题、CVDP cid003） |
| `askrtl/` | 差分仿真 `diffsim.py`、最短分歧轨迹、提问生成 `queries.py`、评审 `judge.py`、在线选择 `online.py`、缺陷统计 `defects.py`、N1 对齐审计 `alignment.py`、E1 `permissive.py`、E2 `consensus_ref.py`、补充测试 `supp_tests.py` + `supp_tests/`；`out_*` 是各次运行的输出 |
| `pools/` | 候选池生成 `gen_pool.py` / 评分 `grade_pool.py`；`ve_ds41`、`rtllm_ds41`、`cvdp_ds41` 及 `_ids`、`_low`、`_repair`、`ve_v4pro` 各池 |
| `ids/` | 按解读多样化采样（IDS）及等样本数对照 `ids_matched.py` |
| `repair/` | 把评审答案转成约束再重新生成（`repair.py plan/gen/check/selftest`） |
| `cfrtl/` | 反事实"规格还是先验"试点（结论：否定） |
| `benchmarks/rtllm_local/` | 从 10-08 参考自检结果重建的 RTLLM 42 题 |
| `pilot_pool/` | Phase 1 用的早期候选池 |

## 运行环境

- Python 3.12 + pyslang（`PYTHONPATH` 指向 `../.deps/json_pipeline`）、Icarus Verilog 12。
- CVDP 需要单独的仓库与 cocotb 环境，默认路径 `E:\SRTP\benchmarks\cvdp`，可用环境变量 `CVDP_PYTHON`、`GRADE_SCRATCH` 覆盖。
- 付费调用的脚本默认 dry-run，加 `--live` 才真正调用 API。API key 放在根目录 `.env`（参考 `.env.example`），不要提交。
- 运行时可用 `ASKRTL_TAG` / `ASKRTL_BENCH` 选择候选池和基准，见 `askrtl/paths.py`。

## 注意

- 这是公开子集：CVDP 的题面、候选设计、测试与逐题输出未提交，混合裁定文件也已移除 CVDP 记录。完整实验仍保存在本地，公开副本不能独立复现这些全量统计。详见 [PUBLICATION_NOTES.md](../PUBLICATION_NOTES.md)。
- 所有"人工裁定"（缺陷判定、N1 的 50 题裁定 `askrtl/adjudication_n1.json`）都由 AI 完成，投稿前需要人工独立复核。
- `*.stale_clkfix` 是时钟/复位识别修复前的旧评审答案，只作存档。
