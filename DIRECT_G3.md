# B5-G3 接入说明

## 冻结契约闭环

### 契约审查与失败追踪增强

G3 闭环在冻结前增加独立 AI 语义审查，输入仅为规格、来源和契约，不提供 DUT。检查输入位条件、已发送数据与期望值、场景复位、逐边沿采样、don't-care，以及协议的单包、相邻包、无效起始和接收中复位覆盖。审查必须返回证据；revise/uncertain 不能进入 RTL 生成。最多两份契约尝试，分别保存原始回复和审查意见。

仿真失败保存最近 16 个显式 wait_edge 后端口快照及失败现场；这是契约步骤追踪，不是完整波形。组合测试也保存失败现场。失败时保存实际 checks；通过仍要求正常完成标记、正常退出、正检查数和无失配。

重复候选或三个候选在同一检查点失败时，独立审查原规格与冻结契约。疑似错误或不确定标为 verifier_suspect，审查请求失败标为 review_failed；不自动放宽契约，不计为通过。冻结后的可疑契约不自动替换：保留当前运行，下一次新建实验重新生成和预检契约，避免更换验收标准后混计结果。不会把官方参考反馈传给模型。

这些机制增加了审查 API 调用和成本。AI 审查并非形式证明，覆盖要求也不能保证模型执行完全正确；实际正确率提升须在新实验中测量。

```powershell
python run.py direct --closed-loop --cases Prob154 --max-repairs 5
python run.py direct --closed-loop --all --max-repairs 5
python run.py direct --closed-loop --check
```

闭环先从规格生成契约，检查 schema、来源和常量变异测试，允许一次契约补救；通过后保存 frozen_contract.json。G3 生成初始 RTL，经 pyslang 与 Icarus/VVP 验证，失败时把原规格、当前代码、固定契约和诊断反馈给模型。默认最多五次修复（初版加修复版最多六次生成），同源码重复出现即停止。工具不可用或执行超时也停止。每轮保存提示、代码、诊断与 API 信息。

闭环只读取规格，不读取官方参考或测试平台；结果为“契约通过”，不会自动进行官方评分。闭环入口使用 --cases/--all 选择任务，不支持原单次模式的 --resume。原 run.py json 的 DesignIR 路径保持可用。

契约预检不是正确性证明，尤其无法排除缺失复位、错误期望等语义问题。若正确实现反复在相同检查点失败，应审查契约，不应放宽它以迎合 DUT。G3 RTL 请求使用 none/8192/temperature=0；契约请求沿用原 JSON 请求配置及有限重试策略。未自动执行付费全量实验。

在 SRTP_LLM2RTL 目录运行：

```powershell
python run.py direct --case Prob001
python run.py direct
python run.py direct --direct-prompt baseline --case Prob001
```

direct 默认使用 9.27 包中 B5 消融实验的 G3 原文，单候选、默认零修复。第二条运行全部题目，会产生模型调用费用。既有 generate 三候选入口保持原策略。

复用已有 Spec Card 实验实现的生成、记录与离线评测。原 run_spec_card_ab.py 默认仍为 baseline，可用 --direct-prompt g3 显式切换其直接生成分支。不是将 B5-G3 替换三候选中的全部提示。

提示词位于 prompts/direct/g3.system.txt 和 baseline.system.txt，逐次 API 记录保存实际提示，汇总增加版本和 SHA256；续跑拒绝提示版本或已记录内容哈希变化。使用 --max-repairs 显式开启编译修复时，结果不再与原单调用 B5 实验完全同口径。

G3 为探索性优化方案，不保证所有项目提升。此次接入不自动启动付费全量实验。
