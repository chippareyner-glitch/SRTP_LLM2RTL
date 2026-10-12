# DeepSeek V4 Pro 实验操作细则

更新日期：2026-09-19。已将你提供的新密钥配置到项目 `.env`，源码不包含新密钥；`.gitignore` 已忽略该文件。主生成、Reviewer 和修复调用均经 `llm_client.py` 访问 DeepSeek 官方接口。

## 1. 已经完成与实际验证

- API 地址：`https://api.deepseek.com/chat/completions`。
- 模型：`deepseek-v4-pro`。官方目前将其列为 DeepSeek-V4-Pro-0813；响应返回的模型字段是别名 `deepseek-v4-pro`，不能据此宣称锁定了不可变权重。
- 一次极小 API 连通性请求成功。
- Prob001_zero 已使用新 API 生成，并通过编译及仿真：0/20 失配。该次生成使用 320 tokens，其中输出 104、推理 75；这是单道简单题，不代表完整基准的成本或正确率。
- 已执行 4 项评测回归测试及解析器、候选排序、代码围栏回归检查。
- 尚未执行 156 题的 DeepSeek 全量实验。保留了旧 `v2`，不会把旧生成结果混入新统计。

官方依据：[模型列表](https://api-docs.deepseek.com/quick_start/pricing/)、[Chat Completions 参数](https://api-docs.deepseek.com/api/create-chat-completion/)。旧的 `deepseek-v4-flash` 当前会路由到 V4.1 Flash，不能用该别名声称复现早期 V4 Flash。

## 2. 打开项目并检查环境

在 PowerShell 中运行：

```powershell
Set-Location -LiteralPath 'C:\Users\USER\OneDrive\文档\srtp\SRTP_LLM2RTL'
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --check
```

预期输出包含 `key_configured: true`、`iverilog: true`、`vvp: true`、`cases: 156`、模型名 `deepseek-v4-pro`。这个操作不调用 API，不产生模型费用。

本机普通 `python` 指向 `D:\Scripts\python.exe`，审计时其标准库与解释器不匹配，出现 `context_aware_warnings` 错误。`run.ps1` 已使用本机可工作的 Codex 附带 Python，不需要先修复系统 Python，也不需要额外安装 requests。新入口仅使用 Python 标准库和已有的 Icarus Verilog。

迁移到别的电脑时，安装可工作的 Python 3.11+ 与 Icarus Verilog，并在 `config.py` 调整 `IVERILOG`、`VVP` 路径。之后直接运行 `python run_experiment.py --check`。上游建议 Icarus v12；本机显示 12.0 devel，正式发表实验建议固定完整工具版本。

## 3. 密钥和模型怎么改

用本地编辑器打开项目 `.env`，其配置项如下；不要把真实密钥替换进报告或分享给别人。

```dotenv
DEEPSEEK_API_KEY=你的有效密钥
DEEPSEEK_MODEL=deepseek-v4-pro
DEEPSEEK_REVIEWER_MODEL=deepseek-v4-pro
DEEPSEEK_REASONING_EFFORT=high
DEEPSEEK_MAX_TOKENS=32768
```

已经为你填好实际密钥，无需再次填写。以后更换密钥，在 [DeepSeek 开放平台](https://platform.deepseek.com/) 登录、管理 API Keys、创建新密钥后，只改 `.env` 第一行。API 账户需要有可用余额；充值金额自行决定。

程序优先使用当前进程的同名环境变量，然后加载 `.env`。如果改文件后仍用旧配置，检查 PowerShell 是否手动设置过这些环境变量，重新打开终端再运行。`high` 是本次试跑使用的思考强度，`none` 用于关闭思考的对照实验。各实验应固定参数并分别记录。

## 4. 先验证 API，再跑一道题

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --smoke
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --case Prob001 --max-repairs 0
```

`--smoke` 会产生一次很小的 API 请求，临时关闭思考、将输出上限设为 1024；它不会改变下一次运行的 `.env`。单题命令接受 `Prob001` 或完整的 `Prob001_zero`。

看到 `Prob001_zero: pass (1/1)` 表示该候选通过当前测试平台。末尾的 `Results:` 是本次输出路径。API 调用成功不等于 RTL 正确；必须查看仿真评价。

## 5. 运行首轮生成基线

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --all --max-repairs 0
```

该命令对 156 道题逐题生成，每题最多一次调用，无反馈修复，适合记录单样本首轮通过率。普通仿真失败、输出截断或空回答会记录为失败并继续下一题；认证、余额、网络或文件异常会保存已完成结果并停止。重新执行默认新建目录；要继续已有实验，使用 `--resume --output 已有实验目录`，并保持相同的 dataset、模型和 max-repairs 设置。续跑保留已记录的失败题，不会偷偷重试或修改首轮分数。单独补生成应另建输出目录。

原始数据集已有已知缺陷，见审计报告。不要把未经数据清洗的分数直接称为模型能力。先记录原始基准分数，再对经审核的修正版单独实验。

## 6. 运行带修复的实验

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --case Prob104 --max-repairs 2
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --all --max-repairs 2
```

`--max-repairs 2` 表示每题初次生成加最多两次修复，最多三个候选；156 题最多 468 次生成调用，实际通过后会提前结束。新入口把原题、上次代码及仿真错误交给同一模型修复，不发送参考答案源码。它是可控的生成—仿真—修复基线，不等同于原先多 Reviewer/VCD 诊断消融设置；论文中应标明流程差别。

反馈来自同一个测试平台，因此修复后的通过率应称为“反馈修复后通过率”，不应冒充不使用测试反馈的标准 pass@1。正式评估可把开发测试和最终保留测试分开。

## 7. 输出文件怎么读

每次自动新建 `experiments/deepseek_日期_时间/`。也可以用 `--output 新目录` 指定路径；目录必须不存在。

| 文件 | 用途 |
|---|---|
| `summary.json` | 总题数、完成题数、初次通过题数 initial_pass、最终通过题数 final_pass、逐题状态 |
| `api_logs/*.json` | 请求和返回模型名、token 用量、思考强度、结束原因、耗时；不保存密钥 |
| `题号/inputs.json` | 原始题目、参考答案、测试平台的路径和 SHA-256，便于追踪版本 |
| `题号/original_spec.txt` | 本次使用的原题 |
| `题号/attempt_00/prompt.txt` | 实际发给模型的用户提示词 |
| `题号/attempt_00/response.txt` | 模型的最终文本输出，不含 reasoning_content |
| `题号/attempt_00/module.sv` | 提取后的 RTL |
| `题号/attempt_00/evaluation.json` | 编译、仿真状态，样本数、失配数 |
| `题号/attempt_00/eval_syntax.log`、`eval_sim.log` | 详细编译与仿真日志 |
| `题号/module_final.sv` | 仅在某个候选通过后保存的最终代码 |

完整运行的首轮通过率是 `initial_pass / total`；反馈修复后通过率是 `final_pass / total`。若 `completed < total`，这是中断的实验，应同时报告覆盖数，不能当作完整分数。

## 8. 更新数据集

官方快照已保存在上级 `audit_20260919/upstream/verilog-eval-c498220d0a52248f8e3fdffe279075215bde2da6/`。使用其中原始 spec-to-rtl 数据：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1 experiment --case Prob001 --max-repairs 0 --dataset '..\audit_20260919\upstream\verilog-eval-c498220d0a52248f8e3fdffe279075215bde2da6\dataset_spec-to-rtl'
```

新增数据集应按每题三个文件组织：`题号_prompt.txt`、`题号_ref.sv`、`题号_test.sv`；本入口默认 DUT 为 TopModule、参考模块为 RefModule、测试顶层为 tb，测试输出为 `Mismatches: X in Y samples`。其他格式需要适配器，不能只改文件夹名。先用参考答案改名为 TopModule 做基线控制，确保测试平台自身正常。

## 9. 报错时看哪里

| 报错或状态 | 操作 |
|---|---|
| HTTP 401 | 检查 `.env` 的密钥是否完整、是否被撤销 |
| HTTP 402 | 检查开放平台 API 余额 |
| HTTP 400 | 检查模型名和参数；火山的 ep-… 不能用于 DeepSeek |
| HTTP 429 / 500 / 503 | 保留结果，稍后重试；代码没有自动重试收费请求 |
| Incomplete completion / length | 输出截断；提高 token 上限后开新实验，不能把残缺代码当成功 |
| syntax | 看 eval_syntax.log；可能是 RTL 错误，也可能是测试端口不一致 |
| sim | 看失配数和具体信号、首个失配时刻 |
| timeout | 区分模拟时间保护触发和进程运行超时；先测参考答案，不要一律归因模型 |
| unknown_sim_fail | 日志缺少可识别成功证据，按未通过处理 |

## 10. 本次修改边界

已接通共享 API、修复返回值误用和语法布尔判断、支持 verilog 代码围栏、统一功能评测、修正失配日志解析及候选排序。新入口隔离每题每次尝试的仿真目录，保存版本证据。

历史高级入口 `legacy/closed_loop_enhanced_v2.py` 已接入新 API 并修复关键接口错误，但它的旧 Reviewer/VCD 支路仍有缺失依赖和策略问题，未完成全链路验证。现在优先运行本文的 `run.ps1 experiment` / `run_experiment.py`；不要直接依据 MODULE_README（已移至 docs/history/MODULE_README_旧闭环架构.md）中旧有的成功率预测、命令行示例开展正式实验。
