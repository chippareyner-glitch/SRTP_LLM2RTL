# 整理版公开发布验证（2026-10-12）

此更新将 `SRTP_LLM2RTL_clean` 的目录结构与入口调整同步到现有公开仓库。之前的三个提交继续保留，本次更新追加一个整理提交。

## 单元测试

使用同一组本地外部依赖，对整理版与实际公开副本分别运行原有测试套件。

| 项目 | 整理版 | 公开副本 |
|---|---:|---:|
| 测试总数 | 63 | 63 |
| 通过 | 62 | 62 |
| 断言失败 | 0 | 0 |
| 报错 | 1 | 1 |
| 跳过 | 0 | 0 |

两侧唯一报错均为 `test_targeted_repair.TargetedRepairTests.test_only_functional_failures`。历史修复提示词索引引用了未随公开仓库发布的历史实验路径，无法读取 `summary.json`。该问题在之前的 PPA 验证记录中也已存在；本次没有补造历史数据或修改该测试来消除错误。

测试配置仅作用于测试进程：Python 3.12、UTF-8 输出，`config.DATASET_DIR` 指向对应副本的 `dataset_spec-to-rtl_gcc`，`JSON_REASONING_EFFORT=low`，显式引用本机已安装的 pyslang 与 Yosys。Yosys 缓存位于发布目录之外。测试中的模型调用使用原有 mock，测试进程还禁止网络连接，没有付费模型调用。

这些结果说明公开脱敏和文件搬迁没有新增套件失败，不表示完整生成实验或完整历史运行流程已重新验证。

## 入口与格式检查

- `json`、`generate`、`direct`、`rtllm`、`experiment`、`targeted-repair`、`reselect`、`select-contract`、`validate-contract`、`ppa` 的 `run.py <command> --help` 全部成功。
- 108 个 Python 文件通过 AST 解析，5,040 个 JSON 文件及 31 个 JSONL 文件通过解析检查。
- 检查即将提交的全部文件是否包含真实本地密钥、凭据模式、个人用户路径、个人作者标识或被排除的 CVDP 逐题数据。
- 按文件哈希确认整理版源文件保持原样；发布副本仅做公开范围过滤、脱敏和发布说明补充。
- 推送后核对远程 main 的提交与完整文件树，确认所有 blob 哈希与审计副本一致。

公开范围和未发布的输入依赖见 [PUBLICATION_NOTES.md](../../PUBLICATION_NOTES.md)。
