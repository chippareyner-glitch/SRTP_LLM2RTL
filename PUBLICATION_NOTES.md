# 公开版本范围（2026-10-12）

仓库根目录现对应本地 `SRTP_LLM2RTL_clean` 整理版。此次更新沿用原仓库的公开范围和脱敏规则，并在已有提交之后追加整理提交，保留之前的三个提交。

## 整理内容

- 旧闭环模块移入 `legacy/`，文档移入 `docs/usage/` 和 `docs/history/`。
- PowerShell 入口统一为 `run.ps1`，`run.py` 新增 `experiment` 与 `targeted-repair` 命令。
- 定向修复提示词移入 `prompts/repair_20261008/`，相关脚本和测试同步采用新路径。
- 仓库保留研究代码、汇总报告及可公开的 VerilogEval / RTLLM 结果；上游许可证保留在 `third_party/`。

## 包含与排除

- 排除真实 `.env`、虚拟环境、依赖安装目录、缓存、旧运行输出和 `experiments/`。
- 排除 CVDP 题面、候选设计、逐题仿真、评审、修复与补充测试产物，保留方法代码及汇总报告。
- 混合文件 `research/askrtl/adjudication_n1.json`、`out_perm/*.jsonl`、`supp_tests/results.json` 中的 CVDP 记录已移除；两份混合运行日志未发布。因此这些公开文件是本地完整实验的子集。
- 三份 Word 草稿带有个人作者元数据，保留在本地，未加入公开仓库。
- 个人 Windows / Linux 用户目录替换为 `USER`，历史个人账户标识及账户余额已脱敏。第三方版权归属信息保留。

## 复现与验证边界

本次整理版仍依赖 README 中列出的外部工具与历史实验目录。公开仓库不附带完整历史运行数据，引用这些数据的脚本需要单独提供相应输入。

发布前逐文件检查真实本地密钥、凭据模式、个人路径、Python 语法、JSON / JSONL 可解析性及文件哈希，并核对实际提交和远程文件树。

本次不调用模型 API，不重新运行全量生成实验。现有单元测试使用单独指定的本机 pyslang、Icarus 与 Yosys 环境；整理版和实际公开副本均为 63 项中通过 62 项、1 项因缺失历史实验文件报错，没有跳过测试。具体配置与验证边界见 [发布验证记录](docs/history/PUBLIC_RELEASE_VALIDATION_20261012.md)。通用 PPA 代理的原有验证边界见 `tools/ppa/VALIDATION.md`；物理面积、时序和功耗尚未评估。

报告中的 AI 裁定、模拟用户答案、不等样本量比较和 CVDP 修复选题偏差应在引用结果时保留。
