# PPA 接入验证（2026-10-11）

本机后端安装在 `tools/ppa/.venv312`，独立于原项目环境和系统 Python。
Yosys 0.69，YoWASP 包 `0.69.0.0.post1233`；完整版本记录见 `requirements-installed.txt`。
依赖一致性检查 `pip check` 通过。安装与检测均保持 TLS 验证，没有调用模型 API。

新增 14 项 PPA 测试全部通过（`ppa-tests.log`）：覆盖真实门电路、触发器、常量零单元、
辅助模块展开与自动顶层、无效 RTL、未定义子模块、超时、工具缺失、日志缺失、禁止复用旧目录，
以及 JSON 主入口的功能结论与 PPA 状态独立性。

四份历史生成 RTL 的新综合报告位于 `experiments/ppa_validation_20261011_final`。
综合前后原始 RTL SHA-256 全部一致，没有更新历史实验结果。

| 生成代码 | 综合 | 通用单元 | 触发器 | 组合逻辑深度 |
|---|---|---:|---:|---:|
| Prob034_dff8 | 成功 | 8 | 8 | 0 |
| Prob062_bugs_mux2 | 成功 | 8 | 0 | 1 |
| Prob153_gshare | 成功 | 2056 | 263 | 16 |
| Prob154_fsm_ps2data | 成功 | 50 | 44 | 2 |

这些数据仅为通用综合代理；实际物理面积、关键路径时延、Fmax 和功耗均未评估。

现有全项目回归在测试进程显式设置本机数据集、UTF-8 输出和 JSON_REASONING_EFFORT=low 后，
63 项中 62 项通过，1 项报错（`regression-configured.log`）。报错为既有
`test_targeted_repair.TargetedRepairTests.test_only_functional_failures`：旧修复索引引用另一台机器的
历史实验路径，读取不到 `summary.json`。该索引、测试和 `run_targeted_repair.py` 均未改动。
没有为本次 PPA 改动调整系统编码、默认数据集、模型推理配置或旧实验路径。

YoWASP 的 ABC 阶段可能截断所捕获的标准输出，因此使用 Yosys 的独立 `-l` 日志及
`tee` 路径报告作为依据；展开层次时关闭 `$scopeinfo`，避免把调试元数据计入面积代理。
