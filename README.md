# SRTP_LLM2RTL：自然语言规格 → RTL

用开源大模型 API（DeepSeek）把自然语言硬件规格生成 SystemVerilog RTL，经过语法检查、仿真验证和修复；之后在此基础上做了候选分歧研究（AskRTL）。

> 本目录是 2026-10-11 从 `E:\SRTP\SRTP_LLM2RTL` 整理出来的精简版，原目录保持原样未改动。整理记录见文末。

## 目录

| 路径 | 内容 |
|---|---|
| `run.py` / `run.ps1` | **统一入口**：`.\run.ps1 <command> [参数]`（或 `python run.py <command> ...`） |
| `run_*.py`、`candidate_*.py`、`spec_directed_validator.py`、`select_candidates_with_contract.py`、`reselect_existing_candidates.py`、`audit_candidate_pool.py` | 各实验流程的实现（见下表） |
| `config.py`、`llm_client.py`、`code_gen.py`、`code_eval.py`、`code_val.py`、`validator.py`、`rtllm_validator.py`、`ppa.py`、`export_results.py` | 共用模块：配置、API 调用、生成、仿真评测、PPA 评估、报表导出 |
| `rtl_json_pipeline/` | JSON DesignIR + 规格契约测试流程 |
| `prompts/` | 提示词（`candidate/`、`direct/`、系统提示词、`repair_20261008/` 定向修复提示） |
| `verification_contracts/` | 手写的规格契约样例 |
| `dataset_spec-to-rtl_gcc/` | VerilogEval spec-to-rtl 数据集副本 |
| `research/` | AskRTL 候选分歧研究：代码、数据、报告，入口见 [research/README.md](research/README.md) |
| `legacy/` | 3 月的旧闭环流程（Reviewer + VCD 诊断 + 修复），已不再作为主流程，保留可运行 |
| `tests/` | 单元测试 |
| `tools/ppa/` | PPA 评估用的 yosys 环境（`.venv312` 不进仓库） |
| `docs/usage/` | 各流程的使用说明 |
| `docs/history/` | 历史记录：集成说明、故障修复记录、GitHub 交接、旧架构说明 |
| `experiments/` | 新运行的输出目录（空；历史结果见下） |

## 统一入口 `run.py` 的命令

| 命令 | 对应脚本 | 说明 | 文档 |
|---|---|---|---|
| `json` | `run_json_pipeline.py` | JSON DesignIR + 契约测试 + 闭环修复（不用参考 RTL） | [JSON流程使用说明](docs/usage/JSON流程使用说明.md) |
| `generate` | `run_three_candidate_select.py` | 三候选生成 + AI 契约测试台选择，之后独立官方评测 | [THREE_CANDIDATE_EXPERIMENT](docs/usage/THREE_CANDIDATE_EXPERIMENT.md) |
| `direct` | `run_direct.py` | 单候选直接生成（G3 提示词） | [DIRECT_G3](docs/usage/DIRECT_G3.md) |
| `rtllm` | `run_rtllm.py` | RTLLM 2.1：G3 生成 + 原配测试台验证 + 修复 | [RTLLM_RUN](docs/usage/RTLLM_RUN.md) |
| `experiment` | `run_experiment.py` | VerilogEval 直接生成 / 标准测试反馈修复，可导出六列报表 | [DeepSeek操作细则](docs/usage/DeepSeek操作细则.md)、[六列报告](docs/usage/六列报告操作说明.md) |
| `targeted-repair` | `run_targeted_repair.py` | 定向修复（使用基准信息，结果不能当独立实验） | — |
| `reselect` / `select-contract` / `validate-contract` | 同名脚本 | 对已有候选重新选择 / 用契约选择 / 契约验证 | — |
| `ppa` | `run_ppa.py` | 对最终 RTL 做综合评估 | [PPA使用说明](docs/usage/PPA使用说明.md) |

大多数流程支持 `--check`（只检查环境，不调用 API）。

## 环境

- **Python**：项目原来的 `.venv` 已损坏（指向其他机器上的解释器），没有复制过来。`run.ps1` 固定使用 `%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`（3.12），并把 `.deps\json_pipeline`（pyslang）加入 `PYTHONPATH`。
- **Icarus Verilog 12**：`config.py` 中写死了 `D:\iverilog\bin\`，换机器时需要修改。
- **API key**：放在 `.env`（参考 `.env.example`），不要提交。
- **CVDP**（只在 research 中用到）：`E:\SRTP\benchmarks\cvdp`。

测试（截至整理时 63 个测试中有 3 个因本机环境失败，整理前后一致）：

```powershell
$env:PYTHONPATH = "$PWD\.deps\json_pipeline"
python -X utf8 -m unittest discover -s tests -t tests
```

## 实验结果在哪里

- **主要结果（已整理）**：`E:\SRTP\experiments\`，按流程分类。每个批次对应什么流程、怎样验证、哪些数字可以引用，见 `E:\SRTP\experiments\实验流程与数据集对应清单.md`。
- **全部原始运行输出**：`E:\SRTP\SRTP_LLM2RTL\experiments\`（包括 RTLLM 参考自检、定向修复、PPA 验证等零散批次）。`research/build_rtllm_local.py` 和 `research/pilot_pool/pool_analysis.py` 读取的就是这里。
- **研究结论**：[research/README.md](research/README.md)、[research/工作总结_接手前后_20261011.md](research/工作总结_接手前后_20261011.md)。

## 整理记录（2026-10-11）

相对原目录 `E:\SRTP\SRTP_LLM2RTL` 的改动：

- **没有复制**：坏掉的 `.venv`、`v2/`（旧闭环流程的输出）、`experiments/`（历史结果，见上）、`tools/ppa/cache`（yosys 编译缓存，首次运行时会重新生成）、`__pycache__`、`_nul`、`.vscode`。
- **移入 `legacy/`**：`closed_loop_enhanced.py`、`closed_loop_enhanced_v2.py`、`closed_loop_modular.py`、`code_diag.py`、`code_fix.py`、`code_judge.py`、`code_repair_loop.py`、`code_syntax.py`、`spec_pre.py`、`generate_specs_batch.py`。主流程不依赖这些文件。每个文件开头加了两行，用来把项目根目录加入 `sys.path`，因此 `python legacy/closed_loop_enhanced_v2.py ...` 仍可运行。
- **文档**：根目录的 12 个 md 移到 `docs/usage/` 和 `docs/history/`。`MODULE_README.md` 描述的是 3 月的旧架构，已改名为 `docs/history/MODULE_README_旧闭环架构.md`。
- **脚本**：4 个 `.ps1` 合并为一个 `run.ps1`；`run.py` 新增 `experiment`、`targeted-repair` 两个命令。文档中的命令已同步更新。
- `repair_prompts_20261008/` → `prompts/repair_20261008/`，`run_targeted_repair.py` 的默认路径和对应测试已一起修改。
- `.gitignore` 补上了 `tools/ppa/.venv312/`、`tools/ppa/cache/`、`.vscode/`、`*.pyc`。

## GitHub 公开版本说明（2026-10-12）

仓库根目录对应整理版内容，使用 `run.ps1` / `run.py` 为统一入口。密钥、本机依赖、历史运行目录、CVDP 逐题数据及含个人作者信息的 Word 草稿未发布；个人用户路径已脱敏。公开范围、外部输入依赖和验证边界见 [PUBLICATION_NOTES.md](PUBLICATION_NOTES.md)。
