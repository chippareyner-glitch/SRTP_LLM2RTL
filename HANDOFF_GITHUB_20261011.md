# 交接说明：把 2026-10-08 ~ 10-11 的新工作上传到 GitHub

> 写给 Codex。写于 2026-10-11，作者是 Claude（Claude Code 会话）。
> 研究内容的说明见 `research/README.md` 和 `research/工作总结_接手前后_20261011.md`。本文件只讲**上传哪些、不传哪些、怎么分提交**。

## 0. 现状

- `E:\SRTP\SRTP_LLM2RTL` **目前不是 git 仓库**（没有 `.git`），而且这台机器的 PATH 里找不到 `git`。如果已有远程仓库，请先 clone 或 `git init` 后再关联 remote，然后再按下面的步骤处理。
- 现有 `.gitignore` 只有：`.env`、`.env.*`、`!.env.example`、`__pycache__/`、`.venv/`、`experiments/`、`.deps/`。

## 1. 必须先做：安全检查

1. **`.env` 里有真实的 DeepSeek API key**，绝对不能提交。`.gitignore` 已经排除了它，提交前用 `git status` 再确认一遍。
2. 我用正则（`sk-...`、`Bearer ...`、`api_key = "..."`）扫过整个项目（不含 `.venv`/`.deps`/`experiments`），只有 `.env` 一个文件命中。`research/` 下的日志和 prompt 存档里没有 key，也没有 `C:\Users\<用户名>` 这类路径。
3. **CVDP 数据许可，请人工确认后再决定是否公开。** 我们用的是 NVIDIA CVDP v1.1.0 的 `..._no_commercial.jsonl`。下面这些文件里包含 CVDP 题面原文、生成的设计或测试：
   - `research/pools/cvdp_ds41*/`
   - `research/askrtl/out_*cvdp*`
   - `research/askrtl/supp_tests/cvdp.json`

   CVDP 有防训练污染的要求。**建议：仓库设为私有；如果要公开，先把这些 CVDP 产物排除掉。**
   VerilogEval（`dataset_spec-to-rtl_gcc/`）和 RTLLM（`research/benchmarks/rtllm_local/`）是开源基准副本，一般没问题，但也请顺手确认一下许可证。

## 2. 建议追加到 `.gitignore`

```gitignore
# PPA 工具的本地环境与缓存（约 316 MB，不该进仓库）
tools/ppa/.venv312/
tools/ppa/cache/

# 本地杂项
.vscode/
_nul
*.pyc
```

`research/` 总共约 42 MB、约 1.1 万个文件。单个文件最大 5.2 MB（`research/askrtl/out_queries/Prob141_count_clock.json`），低于 GitHub 的限制，**不需要 LFS**。如果想让仓库更轻，可以只提交代码和报告，把 `research/**/out_*/` 与 `research/pools/*/` 打包成 Release 附件。但报告里的数字都能追溯到这些输出，**默认建议一起提交**。

## 3. 文件清单与建议的提交拆分

### 提交 A：研究代码与报告（Claude 做的主要工作）

- `research/` 整个目录（`__pycache__` 除外）
  - 报告：`README.md`（新写的索引）、`工作总结_接手前后_20261011.md`、`SRTP研究报告_20261010.md`、`RESEARCH_REPORT.md`、`NOVELTY_REVIEW.md`、`EXP_20261011.md`、`BENCHMARK_ERRATA.md`、`VERILOGEVAL_AUDIT_20261011.md`、`PHASE1/2/3_REPORT.md`、`IDS_REPORT.md`、`CVDP_REPORT.md`、`RESEARCH_PLAN.md`、`DIRECTIONS_V2.md`
  - 代码：`bench.py`、`grade.py`、`cvdp_*.py`、`adaptive.py`、`check_balance.py`、`list_models.py`、`build_rtllm_local.py`、`askrtl/*.py`、`pools/*.py`、`ids/*.py`、`repair/*.py`、`cfrtl/*.py`
  - 数据与日志：`askrtl/out_*`、`pools/*/`、`cfrtl/out_cf`、`cfrtl/variants`、`benchmarks/rtllm_local`、`pilot_pool/`、各 `*.log`、`askrtl/adjudication_n1.json`、`askrtl/supp_tests/`
- `HANDOFF_GITHUB_20261011.md`（本文件）

建议的提交信息：

```
research: AskRTL disagreement-probe study (VerilogEval/RTLLM/CVDP), benchmark errata, reports
```

### 提交 B：原流程中 Claude 改过的两个文件（"提示词长度优化"会话，10-11 下午）

- `llm_client.py`：报错信息里区分"输出长度上限"和"服务器返回的错误"。
- `candidate_repair.py`：pyslang 诊断最多只放 12 条进提示词；模型只回了文字、没回代码时，不再把这段文字当代码回传。

建议的提交信息：

```
fix(repair): cap pyslang diagnostics in repair prompt; clearer LLM length errors
```

### 提交 C：PPA 相关 —— **不是 Claude 做的，请 Codex 自己确认**

下面这些文件在 10-11 16:17–16:31 之间被改过或新建，但不是两个 Claude 会话产生的，推测是你（Codex）或用户做的 PPA 工作：

- `ppa.py`、`run_ppa.py`、`PPA使用说明.md`、`tests/test_ppa.py`
- `tools/ppa/`：`requirements*.txt`、`VALIDATION.md`、`*.log` 可以提交；`.venv312/`、`cache/` 要排除
- 同一时间段修改时间有变化的文件：`run.py`、`run_experiment.py`、`run_json_pipeline.py`、`run_rtllm.py`、`run_spec_card_ab.py`、`run_three_candidate_select.py`、`select_candidates_with_contract.py`、`reselect_existing_candidates.py`、`MODULE_README.md`、`JSON流程使用说明.md`

如果是你做的，按你自己的理解提交即可。如果不是，请问一下用户。

### 不提交

- `.env`、`.venv/`、`.deps/`、`experiments/`（已在 `.gitignore` 中；`experiments/ppa_*` 同理）
- `tools/ppa/.venv312/`、`tools/ppa/cache/`、`__pycache__/`、`_nul`

## 4. 外部依赖（仓库里没有，README 里已经说明）

| 依赖 | 位置 / 说明 |
|---|---|
| Python | 项目自带的 `.venv` 指向别人机器上的解释器，已经坏了。实际使用的是 `%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`（3.12），配合 `PYTHONPATH=E:\SRTP\SRTP_LLM2RTL\.deps\json_pipeline`（提供 pyslang） |
| Icarus Verilog 12 | 仿真 |
| CVDP | `E:\SRTP\benchmarks\cvdp`（数据 + cocotb venv）。硬编码在 `research/bench.py:26`、`research/grade.py:92`、`research/cvdp_check.py:21-22`，后两处可用 `CVDP_PYTHON`、`GRADE_SCRATCH` 环境变量覆盖 |
| `research/pilot_pool/pool_analysis.py:28` | 硬编码了 `E:\SRTP`。只是一次性分析脚本，不影响主流程 |

这些路径**不需要**为了上传而修改。如果想让别人也能直接跑，后续可以把它们统一改成读环境变量。

## 5. 提交前的快速自检（可选，零 API 花费）

```bash
python -I -X utf8 research/repair/repair.py selftest --judge <某个 askrtl/out_judge_* 下的 run 目录>
```

单元测试：`python -m unittest discover -s tests -t tests`。截至 10-11，49 个里有 3 个因为环境问题失败（`config.py` 硬编码了 `D:\iverilog`；`test_targeted_repair` 读 `C:\Users\USER\...`；`test_length_fallback_recorded` 需要设置 `JSON_REASONING_EFFORT`），这 3 个**不是本轮改动引入的**。

## 6. 给 README 或提交说明用的成果摘要

- **AskRTL**：不需要参考答案的差分仿真，找出候选之间的最短分歧输入，交给 LLM 评审或用户裁决。在 VerilogEval 旧候选池上，多数投票 88.5% → 92.9%（上限 94.9%）。同一模型既生成又评审时，收益很小（VE +0.3，RTLLM +1.6，CVDP +0.5）。
- **基准勘误**：新发现的缺陷（扣除 SpecLens 已报告的）有 VerilogEval Prob135、Prob131、Prob156，RTLLM `fixed_point_adder`、`instr_reg`、`pulse_detect` 以及 `alu` 的一处新问题，CVDP 有 4 道题的接口名缺陷。VerilogEval 全量审计：156 题中 33 题有问题。详见 `research/BENCHMARK_ERRATA.md`。
- **补充测试**：9 处测试漏洞做成了可执行的测试。参考设计都能通过，但有 10 个原本通过官方测试的设计不能通过。
- **否定结果**（同样写进了报告）：
  - CF-RTL 的"模型回退到教科书设计"不成立；
  - IDS 的收益在等样本数对照下消失；
  - 在 DeepSeek 模型家族内造不出"弱生成器"（E3）。
- **花费**：项目累计约 31M token；当前账户余额不公开。
- **需要说明的局限**：所有人工裁定都由 AI 完成，投稿前需要人工复核。
