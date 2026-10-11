# RTL 生成研究项目交接说明

更新时间：2026-09-26  
工作区：`C:\Users\USER\Desktop\script_gcc_test_modular_9.25`

本文描述当前真实代码、已经运行的实验、能够成立的结论，以及下一阶段应做和不应做的事情。2026-09-25 的旧交接文档保存在 `docs/archive/PROJECT_HANDOFF_20260925.md`，仅用于追溯，不再代表推荐路线。

## 1. 一句话结论

当前项目已经观察到：**三个候选中可以出现首个候选没有覆盖的正确 RTL，但纯 LLM 代码审查不一定能把它选出来；下一阶段的关键不是继续增加 JSON 层级或候选数量，而是从自然语言规格生成少量可靠、可执行的定向测试，用实际仿真筛选候选。**

必须区分三个目标：

1. 数据集得分：是否能在这 156 道题中找到通过官方测试的代码。
2. 首次生成能力：只给规格时，第一个候选是否正确，即 `pass@1`。
3. 可部署选择能力：生成多个候选后，不读取官方答案，能否选中正确候选，即 `select@k`。

现有候选池在修正一处基准错误后达到 156/156，但这是历史候选的官方测试筛选结果，**不是模型单次生成正确率，也不是当前无答案选择器的正确率**。

## 2. 当前研究边界

本阶段只研究两件事：

- 提升模型理解自然语言规格的能力；
- 在不读取参考 RTL 和官方测试反馈的前提下，验证并选择生成候选。

当前明确不研究：

- 综合结果；
- 面积、功耗、时序等 PPA；
- 网表级优化；
- 为 156 道题分别编写专用规则；
- 用官方 mismatch 反复修代码并把结果称为泛化能力。

默认在线模型使用 `deepseek-flash`，默认 `reasoning_effort=none`。密钥只能通过 `DEEPSEEK_API_KEY` 环境变量提供，不能写入源码、提示词记录或交接文档。曾在对话中明文出现过的密钥应轮换。

## 3. 整理后的目录

```text
workspace/
├─ README.md
├─ main/                         # 唯一公共主流程
│  ├─ run.py                     # 唯一支持的入口
│  ├─ prompts/                   # 外置的公共提示词
│  ├─ contracts/
│  └─ tests/
├─ members/
│  └─ gcc/
│     ├─ .env
│     ├─ envs/
│     ├─ prompts/
│     ├─ sandbox/
│     ├─ artifacts/
│     └─ experiments/
├─ shared/
│  └─ datasets/dataset_spec-to-rtl_gcc/
├─ archive/
│  └─ trace_only/script_gcc_test_legacy_20260926/
├─ docs/
│  ├─ PROJECT_HANDOFF.md
│  ├─ archive/PROJECT_HANDOFF_20260925.md
│  ├─ diagrams/
│  └─ references/
```

多人隔离重构详见 `docs/RESTRUCTURE_20260926.md`。历史 JSON 中的绝对路径没有重写，它们是运行时溯源记录，移动后可能不再是有效访问路径。

### 3.1 多人协作边界

- `main/` 是唯一公共主流程，默认只读，维护者记录在 `main/OWNERS.md`。
- 每位贡献者只能把实验、虚拟环境、自定义提示词和临时代码写入自己的 `members/<name>/`。
- 主流程要求 `--member`，并在运行时拒绝落到成员目录之外的输出路径。
- 已存在的输出目录始终报错，不允许静默覆盖。
- `main/` 不得导入 `members/` 或 `archive/` 中的代码和数据。
- 个人成果提升到主流程前，必须提供复现命令、同一批题的前后指标、相关测试和升级记录，详见 `main/PROMOTION.md`。
- 当前 Windows 环境无法根据协作者身份设置不同 ACL，因此使用目录政策和只读文件属性实现“默认只读”；这不是强安全边界。

## 4. 工作演进与关键结论

### 4.1 原 JSON pipeline

历史 JSON pipeline 位于：

```text
members/gcc/experiments/baselines/json_pipeline_20260926_004134_869935/
```

历史统计中，内部结果约为 133/156，最近一次官方口径约为 132/156。它包含结构化中间表示、验证和修复等多层流程，但没有证据说明复杂 JSON 本身能稳定改善规格理解。主要问题是：

- 中间表示容易把模型第一次的误解固化；
- JSON 字段完整不等于行为正确；
- 内部状态、寄存器和 FSM 结构被过早规定，限制了 RTL 生成；
- 流程复杂度增加，但无法证明对应的功能收益。

因此 DesignIR 和早期行为契约实现被保留作历史参考，不再作为当前主路径。

### 4.2 Spec Card 实验

归档脚本 `archive/trace_only/script_gcc_test_legacy_20260926/run_spec_card_ab.py` 比较直接生成与 Spec Card 辅助生成。Spec Card v3 只描述端口可观察行为、关键边沿、持续周期和优先级，不规定内部寄存器或状态编码。该脚本用于历史复现，不是当前公共入口。

Prob156 的代表性结果：

| 方法 | 官方 mismatch |
|---|---:|
| 直接生成 | 14 / 200000 |
| Spec Card v1 | 244 / 200000 |
| 过度详细的 v2 | 198303 / 200000 |
| observable-timing v3 | 0 / 200000 |

这说明 Spec Card 对“精确周期、串行字段、终止边沿”类题目可能有价值，但内容越多不一定越好。v2 的失败尤其说明：更复杂的结构化描述可能放大误解。

其他观察：

- Prob046 简单触发器：直接生成与 Spec Card 均通过。
- Prob062 mux 修错题：两者均未匹配官方参考，原因主要是题面不足与参考语义冲突。
- 20 题 adaptive 实验中，直接生成 13/20，adaptive 12/20，说明过度路由会伤害简单题。
- 12 题 holdout 中，直接生成 8/12，adaptive 10/12；其中一题提升来自重新采样而不是语义方法。排除采样混淆后，明确的 Spec Card 独有增益主要体现在 Prob154。

因此当前路由原则是：

- 简单组合逻辑、普通寄存器和常规算术直接生成；
- 只对精确持续时间、输出延迟、串行协议等高风险题使用 observable-timing Spec Card；
- adaptive 的简单分支复用同一份直接候选，避免把重新采样误算成方法提升。

### 4.3 候选池审计

归档脚本 `archive/trace_only/script_gcc_test_legacy_20260926/audit_candidate_pool.py` 从历史运行目录中收集每题已有的 `TopModule`，按源码哈希去重，再使用官方测试逐个验证，找到第一个通过候选并复制为 `selected.sv`。

结果目录：

```text
members/gcc/experiments/candidate_pool/candidate_pool_20260926/
```

结果：

- 未修改官方基准：155/156；
- 唯一异常：`Prob099_m2014_q6c`；
- 修正基准副本后：156/156；
- 当前目录中共有 156 个 `selected.sv`。

Prob099 的问题不是 RTL 功能失败：题面接口和参考模块输出为 `Y1、Y3`，官方 testbench 却用不存在的命名端口 `Y2、Y4` 实例化参考模块和候选模块。项目没有修改原始数据，而是在：

```text
members/gcc/experiments/candidate_pool/candidate_pool_20260926/benchmark_fixes/Prob099_m2014_q6c/
```

保存独立修正版。修正后候选为 0/200 mismatches。

候选池结论只能表述为：

> 历史生成结果中，每道题至少出现过一份正确 RTL。

不能表述为：

- `pass@1=100%`；
- 当前生成器单次运行全对；
- 系统在没有官方答案时能选出全部正确候选。

### 4.4 三候选生成与盲选

主流程模块 `main/run_three_candidate_select.py` 实现三种固定候选，并由唯一入口 `main/run.py generate` 调用：

1. `literal`：按题面字面直接实现；
2. `contract`：生成前静默推导可观察行为、边界和周期；
3. `counterexample`：重点检查优先级、最后一位、终止计数和边界反例。

每份代码先用 Icarus Verilog 做语法检查，语法失败时只允许最小编译修复。随后候选匿名打乱，LLM 只根据原始规格与代码进行盲选。选择先写入 `frozen_selection.json`，之后才允许运行官方测试。

三题 smoke 结果位于：

```text
members/gcc/experiments/candidate_selection/three_candidate_select_smoke_20260926_02/
```

| 题目 | 候选结果 | 盲选结果 |
|---|---|---|
| Prob062 | 三个均不符合官方参考 | 失败 |
| Prob080 | 三个均通过 | 通过 |
| Prob156 | 只有 contract 候选通过 | 选择器选错 |

汇总：

- 三题的三个候选全部首次语法通过；
- `pass@1 = 1/3`；
- `oracle pass@3 = 2/3`；
- `blind select@3 = 1/3`。

这里最重要的不是样本率，而是 Prob156 暴露的机制问题：正确候选已经生成，但 LLM 阅读长 RTL 后错误判断了序列检测和 `counting` 的启动边沿。

### 4.5 纯 LLM 选择器 v2 仍然失败

选择器 v2 强制输出逐候选检查表，并要求推演最后输入位、精确持续区间、终止边沿及非阻塞赋值旧值语义。

相同候选上的重选结果位于：

```text
members/gcc/experiments/candidate_selection/three_candidate_reselect_v2_20260926_01/
```

结果仍是 `select@3=1/3`。模型把正确的“当前输入参与序列检测”判成晚一拍，同时接受了真正晚一拍的实现。

结论：仅通过增加审查提示词，不能可靠完成 RTL 符号执行。不要继续在这条路径上堆更多自然语言检查项。

### 4.6 可执行规格契约筛选

`main/select_candidates_with_contract.py` 使用规格派生的 JSON 验证契约，经 `main/spec_directed_validator.py` 确定性生成自检查 SystemVerilog testbench，然后让三个候选实际运行相同测试。

顺序必须保持为：

```text
读取原始 spec 和候选
→ 运行规格派生测试
→ 冻结 selected_id
→ 才读取官方 testbench/ref 做离线计分
```

Prob156 契约检查复位、序列结束、第四个 delay 位、delay=0 的 1000 周期、终止边沿和 ack。结果位于：

```text
members/gcc/experiments/candidate_selection/three_candidate_contract_select_prob156_20260926_01/
```

只有候选2通过规格定向测试，选择候选2后官方测试也通过，0/200000 mismatches。

Prob062 的有效结果位于：

```text
members/gcc/experiments/candidate_selection/three_candidate_contract_select_prob062_20260926_02/
```

规格契约认为候选2、3正确，因为题面表达式明确对应 `sel=0` 选择 `a`、`sel=1` 选择 `b`，修复点是输出位宽。官方参考却实现 `sel ? a : b`，选择方向相反。因此候选通过规格契约但不通过官方参考。这应标记为“规格/基准冲突”，不能通过扭曲提示词去迎合。

注意：`three_candidate_contract_select_prob062_20260926_01` 是修复 `dut_module` 覆盖参数前的无效试运行；有效结果是 `_02`。`three_candidate_select_smoke_20260926_01` 是网络沙箱拦截后留下的失败现场；有效 smoke 是 `_02`。

## 5. 当前推荐流程

```text
原始自然语言 spec
  │
  ├─ 完整性/风险分类 JSON
  │    ├─ 明确且普通：直接生成
  │    ├─ 精确时序风险：生成 observable-timing Spec Card
  │    └─ 明显冲突/不足：标记风险，但仍可 best-effort 生成
  │
  ├─ 三个固定视角的 RTL 候选
  │    ├─ literal
  │    ├─ contract
  │    └─ counterexample
  │
  ├─ 语法编译与最小修复
  │
  ├─ 规格派生的可执行定向测试
  │    ├─ 无候选通过：生成或验证能力不足
  │    ├─ 一个通过：直接选择
  │    └─ 多个通过：LLM 只做次级排序
  │
  ├─ 冻结选择结果
  │
  └─ 官方 testbench/ref 仅做离线评分
```

纯 LLM 选择器不应再作为唯一功能判据。它可以在多个候选都通过定向测试时充当次级排序器，也可以给出诊断建议，但不能代替执行验证。

## 6. JSON 现在的正确用途

保留四类 JSON：

1. 风险分类：判断规格是否完整、是否存在精确时序风险。
2. observable-timing Spec Card：仅辅助高风险题生成候选。
3. 可执行验证契约：定义端口、激励、关键边沿和预期输出，并生成真实 testbench。
4. 实验记录：保存候选、选择冻结、API 使用量和官方离线结果。

不再推荐：用 JSON 规定内部寄存器、固定 FSM 编码、机械翻译庞大 DesignIR，或把字段完整率当成功能正确率。

## 7. 核心代码索引

| 文件 | 作用 | 状态 |
|---|---|---|
| `main/run.py` | 唯一公共入口，分派三个受支持命令 | 当前入口 |
| `main/run_three_candidate_select.py` | 三候选生成、匿名盲选、三项指标 | 主流程实现模块 |
| `main/select_candidates_with_contract.py` | 用可执行规格契约筛选已有候选 | 主流程实现模块 |
| `main/spec_directed_validator.py` | JSON 契约确定性编译为自检查 testbench | 当前验证核心 |
| `main/pipeline_common.py` | API、编译、官方离线评测和成员输出约束 | 公共基础设施 |
| `main/prompts/` | 全部活跃提示词与用户模板 | 公共只读配置 |
| `main/contracts/` | 13 份已有规格定向契约 | 仅部分题目覆盖，且包含早期契约 |
| `shared/datasets/` | 公共数据集 | 稳定只读输入 |
| `members/gcc/experiments/` | 已运行实验和候选池 | gcc 个人区 |
| `archive/trace_only/` | Spec Card、旧闭环、DesignIR 等历史代码 | 仅供追溯 |

## 8. 指标口径

必须同时报告：

- `syntax@1`：第一个候选首次生成能否编译；
- `pass@1`：第一个候选官方功能通过率；
- `oracle pass@3`：三个候选中至少一个官方通过，仅表示候选上界；
- `select@3`：不读取官方答案的选择器选中通过候选的比例；
- `contract coverage`：可执行契约覆盖了多少关键需求；
- `contract/official disagreement`：规格派生验证与官方评分冲突数；
- API 调用数、令牌数和耗时。

不要混用：候选池覆盖率与 pass@k、pass@3 与 select@3、语法通过率与功能通过率、内部定向测试通过与官方通过。

## 9. 当前测试状态

本轮修改后已运行：

```powershell
python -m py_compile main\pipeline_common.py main\run.py `
  main\run_three_candidate_select.py main\select_candidates_with_contract.py `
  main\spec_directed_validator.py

python -m unittest discover -s main\tests -v
```

结果：相关脚本均可编译；三候选指标测试 2/2 通过；定向验证器测试 2/2 通过。

多人重构后又通过唯一入口完成一次 Prob156 回归：规格契约只接受候选2，冻结选择为候选2，官方离线结果为 `pass`。复现记录位于 `members/gcc/experiments/candidate_selection/contract_select_restructure_smoke_20260926_01/REPRODUCE.md`。

旧交接文档记录过一次 31 项旧模块测试中 29 通过、1 失败、1 跳过。本轮没有重新执行全部旧测试套件，因此不能声称旧模块现已全部通过。旧失败涉及 `pyslang` 提前拒绝一份测试候选，与当前三候选和定向验证路径无直接关系。

## 10. 如何运行

从工作区根目录执行。先安全设置 API 密钥：

```powershell
$env:DEEPSEEK_API_KEY = Read-Host -MaskInput "DeepSeek API key"
```

运行三候选实验：

```powershell
python '.\main\run.py' generate --member gcc `
  --case Prob080 --case Prob156
```

默认结果进入 `members/gcc/experiments/candidate_selection/three_candidate_select_<timestamp>/`。

对已有候选使用当前 LLM 选择器重选：

```powershell
python '.\archive\trace_only\script_gcc_test_legacy_20260926\reselect_existing_candidates.py' `
  --source '.\members\gcc\experiments\candidate_selection\three_candidate_select_smoke_20260926_02'
```

上式仅用于复现实验历史，不是公共主流程入口。

使用可执行规格契约选择 Prob156：

```powershell
python '.\main\run.py' select-contract --member gcc `
  --source-case '.\members\gcc\experiments\candidate_selection\three_candidate_select_smoke_20260926_02\Prob156_review2015_fancytimer' `
  --contract '.\main\contracts\Prob156_review2015_fancytimer.json'
```

审计历史候选池：

```powershell
python '.\archive\trace_only\script_gcc_test_legacy_20260926\audit_candidate_pool.py'
```

候选池审计属于历史数据盘点，不是公共主流程入口。

所有入口默认创建新的时间戳目录；如果显式输出目录已存在，程序会停止，避免覆盖历史结果。

## 11. 下一阶段建议

### 第一优先级：自动生成小而可靠的验证契约

当前 Prob156 契约证明执行筛选有效，但仍是针对代表题手工确认的。下一步应让模型从 spec 生成少量高价值测试，而不是庞大完整行为模型。每题优先生成一条正常路径、最小/最大边界、优先级冲突、首次/末次周期以及复位恢复检查。

### 第二优先级：契约可信度门禁

自动契约进入筛选前至少检查：端口一致、预期可追溯、不用 DUT 输出计算期望、边沿采样明确、最小错误候选能被拒绝，以及不检查 don't-care 输出。

### 第三优先级：新鲜 holdout

Prob156 已参与提示词和契约调试，只能作为开发题。下一次正式结论必须使用未参与修改的新鲜题目，建议 20 至 30 题。运行前冻结模型、参数、三候选提示词、契约生成提示词、选择规则和最大 API 调用数；运行后统一统计 `pass@1`、`pass@3`、`select@3` 与契约/官方冲突。

### 第四优先级：最后才接闭环修复

只有当可执行契约在 holdout 上显示足够可靠后，才把定向测试失败证据送回模型修复 RTL。修复循环中契约必须冻结；多轮在同一检查点失败时，应停止并标记 `verifier_suspect`。

## 12. 交接原则

1. 不把参考 RTL、官方 testbench 输出或 mismatch 数量放进生成、选择或修复提示词。
2. 官方测试只能在候选或选择被冻结后用于离线评分。
3. 不覆盖历史实验；每次创建新目录。
4. 不把候选池 156/156 写成 pass@1 或系统正确率。
5. Prob099 按基准基础设施错误单独报告。
6. Prob062 按规格/参考冲突单独报告，不以迎合参考为提示词优化目标。
7. Prob156 是开发样例，不再用于证明泛化提升。
8. 简单题优先直接生成，高风险精确时序题才使用 Spec Card。
9. 纯 LLM 代码审查不能作为唯一选择器。
10. 当前主问题是规格理解与无答案验证，不是综合或 PPA。
