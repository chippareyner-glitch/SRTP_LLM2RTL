# SRTP LLM-to-RTL / AskRTL

自然语言硬件规格到 RTL 的实验项目，包含原有生成、验证与修复流程，AskRTL 候选分歧研究，以及最终 RTL 的通用综合评估。

## 从哪里开始

- [研究目录与报告索引](research/README.md)
- [接手前后工作总结](research/工作总结_接手前后_20261011.md)
- [中文研究报告](research/SRTP研究报告_20261010.md)
- [2026-10-11 实验记录](research/EXP_20261011.md)
- [基准勘误](research/BENCHMARK_ERRATA.md)
- [VerilogEval 全量审计](research/VERILOGEVAL_AUDIT_20261011.md)
- [原流程说明](MODULE_README.md)
- [JSON / DesignIR 流程](JSON流程使用说明.md)
- [通用综合评估说明](PPA使用说明.md)
- [本次公开版本的范围](PUBLICATION_NOTES.md)

## 研究内容

AskRTL 对多个候选 RTL 进行差分仿真，把候选之间的短分歧输入序列转成具体行为问题，由 LLM 评审或用户回答，再选择候选或指导重新生成。

旧 VerilogEval 候选池的官方测试得分从普通多数投票的 88.5% 提升至 AskRTL 的 92.9%。同一强模型生成并评审时，收益较小。IDS 的等样本数对照、评审答案指导的修复试点和负面结果均有记录；这些结果不代表完整规格证明或硬件验证。

报告中的“人工裁定”由 AI 完成，需由人独立复核。人机混合实验中的用户答案由参考设计模拟。报告数字若有差异，请以最新修正说明为准。

## 运行与外部依赖

- Python 3.12、pyslang，以及 Icarus Verilog / VVP。使用自己创建的虚拟环境；本机虚拟环境不随仓库分发。
- 项目配置见 [`.env.example`](.env.example)。密钥仅保存在本地 `.env`，不提交到 Git。
- 原流程启动前显式指定数据集，例如 `python run_experiment.py --check --dataset ./dataset_spec-to-rtl_gcc`。
- 研究入口支持 `ASKRTL_TAG`、`ASKRTL_BENCH`；付费研究脚本默认 dry-run，使用 `--live` 才调用模型。
- PPA 后端及固定依赖见 [`tools/ppa/requirements.txt`](tools/ppa/requirements.txt)，验证记录见 [`tools/ppa/VALIDATION.md`](tools/ppa/VALIDATION.md)。当前提供通用单元数和逻辑深度代理，不提供实际面积、Fmax 或功耗。
- CVDP 数据、官方 harness、适配器和 cocotb 环境需要独立获取和配置。公开仓库保留相关方法代码与汇总报告，排除了其题面、候选 RTL、逐题测试与评审产物；部分 CVDP 分析无法仅凭此公开副本复现。

部分历史脚本仍使用原实验的绝对目录，需要按自己的环境配置；本次发布仅整理上传范围，没有重新运行全量模型实验。

## 第三方基准

- [NVIDIA VerilogEval](https://github.com/NVlabs/verilog-eval)：本地 `dataset_spec-to-rtl_gcc/` 为既有编译兼容版本。上游许可证见 [VerilogEval-LICENSE.txt](third_party/VerilogEval-LICENSE.txt)。
- [RTLLM](https://github.com/hkust-zhiyao/RTLLM)：`research/benchmarks/rtllm_local/` 为既有 42 题重建副本。上游许可证见 [RTLLM-LICENSE.txt](third_party/RTLLM-LICENSE.txt)。
- [NVIDIA CVDP](https://github.com/NVlabs/cvdp_benchmark)：数据及实验原始产物未包含在此公开版本中。

第三方文件遵循各自许可证；此仓库未为原创部分另行声明许可。
