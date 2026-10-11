# config.py
"""
config.py
================================================================================
SystemVerilog测试自动化配置和工具模块
================================================================================

该模块提供了用于自动化SystemVerilog测试工作流程的核心配置设置和实用函数。
它专为处理Verilog/SystemVerilog问题数据集而设计，并与大型语言模型接口以生成代码解决方案。

主要功能:
---------
1. 路径配置管理
   - 数据集目录设置
   - 输出目录和文件路径配置
   - 仿真工具路径配置(Icarus Verilog)

2. 大语言模型集成
   - Doubao/Ark模型的API配置
   - 请求/响应处理工具
   - API调用错误管理

3. 测试自动化工具
   - 带超时处理的命令执行
   - 文件分组和组织
   - 测试结果数据结构

4. 验证支持
   - 参考模块检测
   - 语法和功能检查辅助工具

工作流程概述:
------------
1. 从数据集目录加载问题规格说明
2. 在基于接口或基于提示的规范之间进行选择
3. 调用大语言模型生成SystemVerilog实现
4. 使用Icarus Verilog运行仿真测试
5. 评估结果并记录输出
6. 生成CSV/JSON格式的性能报告

作者: 
日期: 2025.12.16
"""

# ... existing code ...

from pathlib import Path
import subprocess
import json
import re  # 导入 re 模块

# 获取当前脚本所在目录的绝对路径
SCRIPT_DIR = Path(__file__).parent.resolve()

# =========================
# 路径配置
# =========================

# 数据集根目录（包含各题目文件夹）
DATASET_DIR = SCRIPT_DIR.parent / "testbench" / "testbench" / "verilog-eval-main" / "verilog-eval-main" / "dataset_spec-to-rtl"

# 生成结果目录（gen.sv、log 等）
RUNS_DIR = SCRIPT_DIR / "runs_onlymodule"

# 闭环优化系统输出目录（新版模块化系统）
CASES_DIR = SCRIPT_DIR / "runs_closed_loop"

# 增强版闭环优化系统输出目录（与 modular 版本隔离）
from datetime import datetime
CASES_DIR_ENHANCED = SCRIPT_DIR / "experiments" / datetime.now().strftime("legacy_v2_%Y%m%d_%H%M%S_%f")

# =========================
# 工具路径配置
# =========================

# 仿真工具路径
IVERILOG = r"D:\iverilog\bin\iverilog.exe"
VVP = r"D:\iverilog\bin\vvp.exe"
# 测试平台顶层模块名
TB_TOP = "tb"

# =========================
# 输出文件配置
# =========================

# 结果 CSV 文件路径
RESULTS_CSV = RUNS_DIR / "results_gcc.csv"
# 汇总 JSON 文件路径
SUMMARY_JSON = RUNS_DIR / "summary_gcc.json"

# =========================
# Spec 选择策略
# =========================

# True  -> 使用 *_ifc.txt
# False -> 使用 *_prompt.txt
USE_IFC = False

# =========================
# Ark LLM 配置
# =========================

# ⚠️ 必填：你的 API Key
from llm_client import ARK_API_KEY, ARK_MODEL, REVIEWER_ARK_API_KEY, REVIEWER_ARK_MODEL

# 推荐模型（主生成模型）


# =========================
# Reviewer LLM 配置 (第二套模型)
# =========================

# ⚠️ 必填：Reviewer 模型的 API Key

# Reviewer 模型名称


# =========================
# Prompt 组装公共策略
# =========================

# 统一硬件约束：所有生成/修复请求都通过公共组装函数注入一次
DEFAULT_HARDWARE_CONSTRAINTS_TEXT = """1. Bit-widths: Ensure strict matching of bit-widths across all assignments and module instantiations. Implicit truncations or extensions are strictly forbidden.
2. Initialization: Explicitly initialize all registers and state variables using proper asynchronous or synchronous reset logic."""

# 无 Reviewer 链路或 Reviewer 失败时的默认指导占位文本
DEFAULT_REVIEW_GUIDANCE = """Ambiguity Analysis:
- Reviewer guidance is unavailable; use conservative and explicit design assumptions.

Missing Critical Details:
- Confirm reset strategy, timing requirements, and boundary behavior expectations from available spec context.

Edge Cases & Risks:
- Verify overflow/underflow conditions, zero-value paths, and illegal control combinations.

Functional Correctness Prediction:
- Functional risk remains medium unless ambiguous behaviors are explicitly constrained.

Actionable Guidance for RTL/TB Generation:
- Keep reset behavior deterministic and make all expected checks explicit in testbench.
"""


def build_generation_user_prompt(spec: str, review_guidance: str, task_text: str) -> str:
    """
    统一组装"生成类"用户提示词，确保约束只注入一次且分块清晰。
    """
    guidance = (review_guidance or "").strip() or DEFAULT_REVIEW_GUIDANCE
    return f"""[ORIGINAL SPEC]
{spec}

[EXPERT REVIEW GUIDANCE]
{guidance}

[CRITICAL HARDWARE CONSTRAINTS]
{DEFAULT_HARDWARE_CONSTRAINTS_TEXT}

[TASK]
{task_text}"""


def build_syntax_fix_user_prompt(
    spec: str,
    original_code: str,
    error_log: str,
    code_type: str = "module",
) -> str:
    """
    统一组装"语法修复类"用户提示词，避免各文件重复硬编码约束文本。
    """
    return f"""[ORIGINAL SPEC]
{spec}

[EXPERT REVIEW GUIDANCE]
{DEFAULT_REVIEW_GUIDANCE}

[CRITICAL HARDWARE CONSTRAINTS]
{DEFAULT_HARDWARE_CONSTRAINTS_TEXT}

[TASK]
Fix syntax errors for this code type: {code_type}

[ORIGINAL CODE WITH SYNTAX ERRORS]
{original_code}

[SYNTAX ERROR LOG]
{error_log}

Output ONLY the corrected SystemVerilog code without any additional explanations."""


# =========================
# 数据结构定义
# =========================

from dataclasses import dataclass

@dataclass
class CaseResult:
    case_id: str
    used_spec: str
    syntax_pass: bool
    func_pass: bool
    func_note: str
    error_stage: str
    generation_time_sec: float


# =========================
# 工具函数
# =========================

def run_cmd(cmd, cwd=None, timeout=60):
    """
    运行系统命令并捕获执行结果
    
    功能:
    - 执行指定的系统命令并等待完成
    - 自动处理带空格的可执行文件路径
    - 支持设置工作目录和超时时间
    - 捕获并分类处理各种异常情况
    
    Args:
        cmd (list): 要执行的命令列表，每个参数作为单独的元素
        cwd (str, optional): 命令执行的工作目录，默认为 None 表示使用当前目录
        timeout (int): 命令执行超时时间（秒），默认 60 秒
        
    Returns:
        tuple: 包含四个元素的元组 (returncode, stdout, stderr, timed_out)
            - returncode (int): 命令返回码，0 表示成功，非 0 表示失败
            - stdout (str): 命令的标准输出内容
            - stderr (str): 命令的错误输出内容
            - timed_out (bool): 是否超时标志，True 表示超时
            
    Raises:
        subprocess.TimeoutExpired: 命令执行超时
        PermissionError: 权限不足无法执行命令
        FileNotFoundError: 命令或文件未找到
        Exception: 其他未预期的异常
    """
    try:
        # 预处理命令参数，确保带空格的路径被正确引用
        processed_cmd = []
        for item in cmd:
            if isinstance(item, str):
                # 如果是可执行文件路径且包含空格，则加上引号
                if ' ' in item and ('.exe' in item.lower()):
                    processed_cmd.append(f'"{item}"')
                else:
                    processed_cmd.append(item)
            else:
                processed_cmd.append(item)
        
        # 打印将要执行的命令（用于调试）
        print(f"Executing command: {' '.join(processed_cmd)}")
        if cwd:
            print(f"In directory: {cwd}")
        
        result = subprocess.run(
            processed_cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr, False
    except subprocess.TimeoutExpired:
        print("Command timed out")
        return -1, "", "TIMEOUT", True
    except PermissionError as e:
        print(f"Permission denied: {e}")
        return -1, "", f"PERMISSION_DENIED: {str(e)}", False
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return -1, "", f"FILE_NOT_FOUND: {str(e)}", False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return -1, "", str(e), False

def group_cases(dataset_dir: Path):
    """
    将数据集目录下的测试用例按题目编号分组
    
    功能:
    - 扫描指定的数据集目录
    - 识别并组织同一题目的不同类型文件（提示、接口、测试平台、参考实现）
    - 构建便于访问的文件分组字典结构
    - 处理缺失目录的情况
    
    Args:
        dataset_dir (Path): 数据集目录的 Path 对象
        
    Returns:
        dict: 以基础名称为键，包含不同类型文件路径的字典为值的字典
              例如: {
                      "Prob001_zero": {
                          "prompt": Path("Prob001_zero_prompt.txt"),
                          "test": Path("Prob001_zero_test.sv"),
                          "ref": Path("Prob001_zero_ref.sv")
                      }
                    }
              
    Note:
        期望的文件命名格式:
        - *_prompt.txt: 用户提示文件
        - *_ifc.txt: 接口定义文件
        - *_test.sv: 测试平台文件
        - *_ref.sv: 参考实现文件
    """
    cases = {}

    if not dataset_dir.exists():
        print(f"Warning: Dataset directory {dataset_dir} does not exist")
        return cases

    # 收集所有相关文件
    files = {}
    for f in dataset_dir.iterdir():
        if f.is_file():
            # 提取基础名称（去掉后缀）
            if f.name.endswith("_prompt.txt"):
                base_name = f.name[:-11]  # Remove "_prompt.txt"
                if base_name not in files:
                    files[base_name] = {}
                files[base_name]["prompt"] = f
            elif f.name.endswith("_ifc.txt"):
                base_name = f.name[:-8]   # Remove "_ifc.txt"
                if base_name not in files:
                    files[base_name] = {}
                files[base_name]["ifc"] = f
            elif f.name.endswith("_test.sv"):
                base_name = f.name[:-8]   # Remove "_test.sv"
                if base_name not in files:
                    files[base_name] = {}
                files[base_name]["test"] = f
            elif f.name.endswith("_ref.sv"):
                base_name = f.name[:-7]   # Remove "_ref.sv"
                if base_name not in files:
                    files[base_name] = {}
                files[base_name]["ref"] = f

    # 构建 cases 字典
    for base_name, file_dict in files.items():
        cases[base_name] = file_dict

    return cases

def contains_refmodule_definition(test_content: str) -> bool:
    """
    检查测试内容中是否包含参考模块 (RefModule) 的定义
    
    功能:
    - 在测试平台文件内容中搜索 RefModule 模块定义
    - 使用正则表达式精确匹配模块声明
    - 判断测试平台是否已内嵌参考实现
    
    Args:
        test_content (str): 测试平台文件的内容字符串
        
    Returns:
        bool: 如果包含 RefModule 定义返回 True，否则返回 False
    """
    # 使用正则表达式更准确地查找 RefModule 定义
    pattern = r'module\s+RefModule\b'
    return bool(re.search(pattern, test_content))

from llm_client import call_llm, call_reviewer_llm
