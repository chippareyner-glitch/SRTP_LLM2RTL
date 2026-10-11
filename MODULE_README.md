# SPEC-to-RTL GCC 项目 - Python 模块功能详解

## 📋 项目概述

本项目是一个 **SPEC-to-RTL 自动化流水线（GCC 版本）**，旨在将自然语言描述的硬件规格（SPEC）自动转换为 SystemVerilog RTL 代码。系统通过引入 LLM（大语言模型）实现硬件设计的自动化生成，并配套语法纠错与仿真验证机制，大幅降低手动编写 RTL 的门槛和错误率。

### 核心价值
- 🚀 **自动化生成**: 自然语言规格到 SystemVerilog 代码的自动转换
- 🔧 **智能纠错**: 语法错误自动检测与 LLM 迭代修复
- ✅ **闭环验证**: 完整的"生成→检查→修复→验证"工作流
- 📊 **波形分析**: VCD 波形解析与错误追踪定位
- 最终 RTL 默认追加通用综合评估，保存资源和逻辑深度代理指标，使用与边界见 [PPA使用说明.md](PPA使用说明.md)。

---

## 🏗️ 核心架构模块

### 1. **配置与基础设施工具**

#### [`config.py`](config.py)
**功能**: 全局配置中心和工具函数库  
**主要职责**:
- 路径配置管理（数据集目录、输出目录、仿真工具路径）
- LLM API 集成配置（Doubou/Ark 模型）
- 测试自动化工具（命令执行、超时处理、文件分组）
- Prompt 模板组装（统一的提示词构建函数）
- 数据结构定义（CaseResult 等）

**关键函数**:
- `run_cmd()`: 带超时处理的命令执行
- `group_cases()`: 测试用例分组
- `call_llm()`: LLM API 调用封装
- `call_reviewer_llm()`: Reviewer 模型专用调用
- `contains_refmodule_definition()`: 参考模块检测

---

### 2. **代码生成与验证核心模块**

#### [`spec_pre.py`](spec_pre.py)
**功能**: 规格说明预处理器  
**输入**: 原始提示词文件（如 `Prob001_prompt.txt`）  
**输出**: 优化后的提示词文件（`原文件名_review.txt`）  
**工作流程**:
1. 读取原始自然语言规格
2. 调用 Reviewer 模型进行结构化审查
3. 识别歧义、缺失细节及潜在风险
4. 生成增强版规格说明

**使用示例**:
```python
from spec_pre import spec_pre
optimized_spec = spec_pre("Prob001_prompt.txt")
```

---

#### [`code_gen.py`](code_gen.py)
**功能**: RTL 代码生成器  
**输入**: Review 后的提示词文件（如 `Prob001_review.txt`）  
**输出**: `module.sv` SystemVerilog 模块代码  
**特性**:
- 多策略代码提取（优先匹配 ```systemverilog```，降级到通用 ```）
- Module 到 endmodule 自动截取
- 错误处理（失败时写入 `_error.txt`）

**使用示例**:
```python
from code_gen import code_gen
result = code_gen("Prob001_review.txt")
```

---

#### [`code_syntax.py`](code_syntax.py)
**功能**: 语法验证器  
**输入**: SystemVerilog 代码文件（如 `module.sv`）  
**输出**: `syntax_report.txt` 语法检查报告  
**返回**: 
- `0`: 语法通过
- `1`: 语法失败

**工具链**: Icarus Verilog (`iverilog`)

**使用示例**:
```python
from code_syntax import code_syntax
result = code_syntax("module.sv")
if result == 0:
    print("✅ Syntax check passed")
```

---

#### [`code_val.py`](code_val.py)
**功能**: 功能验证器  
**输入**: 
- 待验证代码（`module.sv`）
- 测试平台（`Prob001_test.sv`）
- 参考代码（`Prob001_ref.sv`）

**输出**: `func_report.txt` 功能验证报告  
**返回**: 
- `True`: 功能通过
- `False`: 功能失败

**工作流程**:
1. 使用 `iverilog` 编译 DUT + Testbench + Reference
2. 调用 `vvp` 运行仿真
3. 比对 DUT 和 REF 的输出
4. 统计 Mismatch 数量

**使用示例**:
```python
from code_val import code_val
result = code_val("module.sv", "Prob001_test.sv", "Prob001_ref.sv")
```

---

### 3. **错误诊断与修复模块**

#### [`code_judge.py`](code_judge.py)
**功能**: 错误判定与波形分析器  
**输入**: VCD 波形文件（如 `wave.vcd`）  
**输出**: `error_trace_report.txt` 详细错误报告  

**核心能力**:
- VCD 波形快速解析（支持流式读取大文件）
- 错误点上下文提取（前后各 2 个时钟周期）
- 完整状态信息呈现（输入、预期输出、实际输出）
- Mismatch 高亮标记（使用 `>>>` 和 `*** ERROR ***`）

**数据结构**:
```python
error_traces = [
    {
        'time': '10ns',
        'inputs': {...},
        'expected': {...},
        'actual': {...},
        'context_states': [...]
    }
]
```

**使用示例**:
```python
from code_judge import code_judge
errors = code_judge("wave.vcd")
```

---

#### [`code_diag.py`](code_diag.py)
**功能**: 代码诊断师  
**输入**: 
- 失败的代码文件
- 规格说明文件
- 评估结果字典
- 题目 ID

**输出**: `repair_diagnosis.txt` 诊断报告  

**诊断维度**:
- 语法错误类型分析
- 功能失配模式识别
- 端口连接问题检测
- 时序逻辑缺陷定位
- Testbench 端口信息提取

**使用示例**:
```python
from code_diag import code_diag
eval_result = {
    'syntax_pass': True,
    'func_pass': False,
    'status': 'sim',
    'mismatches': 5,
    'samples': 100,
    'error_text': '...'
}
diagnosis = code_diag("module.sv", "Prob001_prompt.txt", eval_result, "Prob001")
```

---

#### [`code_fix.py`](code_fix.py)
**功能**: 代码修复器  
**输入**: 
- 失败代码
- 规格说明
- 评估结果

**输出**: 
- `repaired_code.sv` 或 `best_gen.sv`
- `repair_diagnosis.txt` 修复诊断

**修复策略** (基于 v678 分层分桶):
1. **小补丁修复**: 最小化修改（初值、首拍等）
2. **局部修复**: 针对特定错误类型的定向修复
3. **全面修复**: 重新生成整个模块

**候选生成**:
- 并行生成多个候选变体（Cand_A, Cand_B, Cand_C）
- 分层评估排序
- 选择最优方案

**使用示例**:
```python
from code_fix import code_fix
result = code_fix("module.sv", "Prob001_prompt.txt", eval_result)
if result['success']:
    print(f"✅ 修复成功，采用候选：{result['accepted_variant']}")
```

---

#### [`code_eval.py`](code_eval.py)
**功能**: 代码评估器  
**输入**: 
- 候选代码文件
- 测试平台
- 参考代码
- 题目 ID

**输出**: `{tag}_eval.json` 评估结果  

**评估流程**:
1. 语法检查（`iverilog`）
2. 功能仿真（`vvp`）
3. Mismatch 统计
4. 质量评分与排序

**解析能力**:
- 从日志中提取失配数量和样本总数
- 区分语法错误、仿真错误、超时等状态

**使用示例**:
```python
from code_eval import code_eval
result = code_eval("cand_a.sv", "Prob001_test.sv", "Prob001_ref.sv", "Prob001")
if result['func_pass']:
    print("✅ Functional verification passed")
```

---

#### [`code_repair_loop.py`](code_repair_loop.py)
**功能**: 闭环修复循环控制器  
**输入**: 
- 失败代码
- 规格说明
- 测试平台
- 参考代码
- 最大修复轮次（默认 3）

**输出**: 完整过程文件和最终修复结果  

**工作流**:
```
失败代码 → 语法检查 → 功能验证 → 诊断分析 → 修复生成 → 评估验证
     ↑                                                                  |
     └────────────────────── 循环直到通过或达最大轮次 ──────────────────┘
```

**单轮修复流程**:
```python
def run_single_repair_round(
    round_num, failed_code_path, spec_path, 
    testbench_path, ref_path, prev_diagnosis=None
):
    # 1. 诊断
    diagnosis = code_diag(...)
    # 2. 修复
    fix_result = code_fix(...)
    # 3. 评估候选
    for candidate in candidates:
        eval_result = code_eval(...)
    # 4. 选择最优
    best_candidate = select_best(...)
```

**使用示例**:
```python
from code_repair_loop import run_repair_loop
report = run_repair_loop("module.sv", "Prob001_prompt.txt", 
                         "Prob001_test.sv", "Prob001_ref.sv", max_rounds=3)
```

---

### 4. **综合验证与报告模块**

#### [`validator.py`](validator.py)
**功能**: 全功能验证器与报告生成器  
**验证模式**:
- `runs`: 原始生成结果验证
- `run_syntax`: 语法纠错后结果验证

**验证阶段**:
1. **语法验证**: 使用 `iverilog` 检查语法
2. **功能验证**: 运行仿真比对 DUT vs REF
3. **结果统计**: CSV/JSON格式汇总
4. **错误分析**: 详细错误报告（类型、规格长度等）
5. **报告生成**: Excel 格式详细测试报告

**输出文件**:
- `syntax_results.csv`: 语法验证结果
- `func_results.csv`: 功能验证结果
- `validation_summary.xlsx`: Excel 汇总报告

**使用方式**:
```bash
python validator.py
# 交互式选择验证目标目录（0: runs, 1: run_syntax）
```

---

### 5. **完整闭环系统**

#### [`closed_loop_modular.py`](closed_loop_modular.py)
**功能**: 模块化闭环优化系统  
**整合模块**: 8 个核心模块（spec_pre, code_gen, code_syntax, code_val, code_judge, code_diag, code_fix, code_eval）

**特性**:
- ✅ 全周期双重验证（每次迭代都执行语法 + 功能检查）
- ✅ Reviewer 输入增强（VCD 波形、语法日志、Mismatch 报告）
- ✅ 分层修复策略（v678 分桶策略，多候选并行）
- ✅ 智能迭代（自动诊断→修复→评估，直到收敛）

**输出目录**: `runs_closed_loop_modular/`

**运行方式**:
```bash
python closed_loop_modular.py --case Prob001 --max-iterations 5
```

---

#### [`closed_loop_enhanced.py`](closed_loop_enhanced.py)
**功能**: 增强版闭环系统（第一代增强）  
**改进点**:
- 基于 modular 版本的功能增强
- 更详细的错误报告
- 改进的波形分析

**输出目录**: `runs_closed_loop_enhanced/`

---

#### [`closed_loop_enhanced_v2.py`](closed_loop_enhanced_v2.py)
**功能**: 增强版闭环系统 V2.0（最新修复版）  
**核心改进**:
1. ✅ **VCD 解析降级策略**: VCD 解析失败时从传统报告提取统计信息
2. ✅ **一致性保证**: Quick Summary 必须采信 Traditional Report 的错误计数
3. ✅ **冲突检测**: 自动识别并报告摘要与详细报告的矛盾
4. ✅ **友好提示**: 数据不可用时显示明确提示而非空表
5. ✅ **移除 Code Diff**: 不再依赖参考代码对比，符合生产场景

**新增功能**:
- 强制波形生成（即使验证通过也执行仿真）
- VCD 文件存在性显式校验
- 错误上下文窗口策略（仅提取错误点前后 2 个时刻）
- 大文件性能优化（VCD 超过 40MB 自动切换流式读取）

**输出目录**: `v2/`

**运行方式**:
```bash
python closed_loop_enhanced_v2.py --case Prob001 --max-iterations 5
```

---



## 🔄 典型工作流程

### 完整闭环流程（推荐）

```
1. 规格预审
   spec_pre("Prob001_prompt.txt") 
   → "Prob001_review.txt"

2. 代码生成
   code_gen("Prob001_review.txt") 
   → "module.sv"

3. 语法检查
   code_syntax("module.sv") 
   → "syntax_report.txt" (return: 0/1)

4. 功能验证
   code_val("module.sv", "Prob001_test.sv", "Prob001_ref.sv") 
   → "func_report.txt" (return: True/False)

5. 错误判定（若失败）
   code_judge("wave.vcd") 
   → "error_trace_report.txt"

6. 诊断分析
   code_diag("module.sv", "Prob001_prompt.txt", eval_result, "Prob001") 
   → "repair_diagnosis.txt"

7. 代码修复
   code_fix("module.sv", "Prob001_prompt.txt", eval_result) 
   → "repaired_code.sv" + 多个候选

8. 候选评估
   code_eval("cand_a.sv", "Prob001_test.sv", "Prob001_ref.sv", "Prob001") 
   → "{tag}_eval.json"

9. 循环迭代
   重复步骤 3-8 直到通过或达到最大轮次
```

### 一键式自动化（使用 V2）

```bash
python closed_loop_enhanced_v2.py --case Prob001 --max-iterations 5
```

**自动执行**:
- ✅ 规格预审与优化
- ✅ 代码生成与语法检查
- ✅ 功能验证与波形生成
- ✅ 错误诊断与智能修复
- ✅ 多轮迭代优化
- ✅ 最终报告生成

---

## 📁 输出目录结构

```
script_gcc_test/
├── runs_gcc/                    # 基础生成结果
│   └── Prob001/
│       ├── module.sv           # 生成的 RTL 代码
│       ├── syntax_report.txt   # 语法检查报告
│       └── ...
│
├── run_syntax/                  # 语法纠错结果
│   └── Prob001/
│       ├── repaired_code.sv    # 修复后的代码
│       └── ...
│
├── runs_closed_loop_modular/    # 模块化闭环结果
│   └── Prob001/
│       ├── pre_phase/          # 预审阶段文件
│       ├── iteration_1/        # 第 1 轮迭代文件
│       ├── iteration_2/        # 第 2 轮迭代文件
│       └── final/              # 最终结果
│
├── runs_closed_loop_enhanced/   # 增强版闭环结果
│   └── ...
│
└── v2/                          # V2.0 最新结果
    └── Prob001/
        ├── enhanced_summary.json    # 总结报告
        ├── func_results.csv         # 功能验证结果
        └── wave.vcd                 # 波形文件
```

---

## 🛠️ 环境要求

### 必需工具
- **Python**: 3.10+
- **Icarus Verilog**: `iverilog` (编译器) + `vvp` (仿真器)

### Python 依赖
```bash
pip install requests pandas openpyxl
```

### 配置文件
编辑 [`config.py`](config.py):
```python
# ARK API 配置
ARK_API_KEY = "your_api_key_here"
ARK_MODEL = "model_name"

# Icarus Verilog 路径（Windows）
IVERILOG = r"D:\Verilog_Related\Icarus\bin\iverilog.exe"
VVP = r"D:\Verilog_Related\Icarus\bin\vvp.exe"

# 数据集路径
DATASET_DIR = Path("dataset_spec-to-rtl_gcc")
```

---

## 🚀 快速开始

### 方式 1: 完整自动化（推荐新手）
```bash
# 单个案例
python closed_loop_enhanced_v2.py --case Prob001

# 批量处理
python closed_loop_enhanced_v2.py --all
```

### 方式 2: 分步执行（适合调试）
```python
from spec_pre import spec_pre
from code_gen import code_gen
from code_syntax import code_syntax
from code_val import code_val

# 1. 规格优化
reviewed = spec_pre("Prob001_prompt.txt")

# 2. 代码生成
code_gen("Prob001_review.txt")

# 3. 语法检查
if code_syntax("module.sv") == 0:
    print("✅ Syntax passed")
    
# 4. 功能验证
if code_val("module.sv", "Prob001_test.sv", "Prob001_ref.sv"):
    print("✅ Function verified")
```

### 方式 3: 独立验证
```bash
# 验证已有生成结果
python validator.py
# 选择 0 (runs) 或 1 (run_syntax)
```

---

## 📊 性能指标

### 典型处理时间
- **规格预审**: ~5-10 秒
- **代码生成**: ~10-20 秒
- **语法检查**: <1 秒
- **功能验证**: ~5-10 秒
- **错误诊断**: ~10-15 秒
- **代码修复**: ~15-30 秒（含多候选生成）

### 成功率（参考）
- **初始生成通过率**: ~40-60%
- **一轮修复后**: ~70-80%
- **三轮修复后**: ~85-95%

---

## 🔍 常见问题

### Q1: VCD 文件未生成？
**A**: 使用手动仿真工具补生成：
```bash
python manual_sim_prob082.py
```

### Q2: 语法检查陷入死循环？
**A**: 检查 [`code_repair_loop.py`](code_repair_loop.py) 中的 `max_rounds` 参数，建议设置为 3-5。

### Q3: Reviewer 调用失败？
**A**: 系统会自动降级到 `DEFAULT_REVIEW_GUIDANCE`，仍可继续流程。

### Q4: 文件权限错误（WinError 5/32）？
**A**: 关闭占用文件的进程（如文本编辑器、仿真器），或使用管理员权限运行。

---

## 📝 开发规范

### 代码风格
- 变量名使用 camelCase
- 函数名使用 snake_case
- 类名使用 PascalCase
- 所有公开函数必须有 docstring

### 文件命名
- 模块文件：`snake_case.py`
- 输出文件：`{case_id}_{type}.{ext}`
- 迭代文件：`iteration_{N}/`

### 错误处理
- 使用 try-except 捕获异常
- 提供友好的错误提示
- 记录详细日志到文件

---

## 🔮 未来规划

- [ ] 支持更多 LLM 后端（除了 ARK）
- [ ] 添加 Web UI 界面
- [ ] 支持分布式并行处理
- [ ] 集成更多仿真器（ModelSim、Vivado）
- [ ] 机器学习驱动的错误预测

---

## 👥 贡献者

- 核心开发团队
- Spec-to-RTL GCC 项目组

---

## 📄 许可证

本项目为内部研究使用，暂未开放开源许可。

---

## 📞 联系方式

如有问题请提交 Issue 或联系开发团队。

---

**最后更新**: 2026-03-30  
**版本**: v2.0
