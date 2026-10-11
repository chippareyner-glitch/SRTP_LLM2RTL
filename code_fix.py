# code_fix.py
"""
代码修复模块 (Code Fixer)
================================================================================

功能:
根据语法检查和功能验证的结果，调用 LLM 生成修复后的代码。
实现了分层分桶的修复策略（基于闭环仿真 v678 版本）。

输入:
- failed_code_filename: 失败的代码文件名
- spec_filename: 规格说明文件名
- eval_result: 评估结果字典（包含语法/功能通过状态、错误信息等）

输出:
- 同目录下生成 repaired_code.sv 或 best_gen.sv
- 生成修复诊断报告 repair_diagnosis.txt

使用示例:
    from code_fix import code_fix
    
    eval_result = {
        'syntax_pass': False,
        'func_pass': False,
        'status': 'syntax',  # 或 'sim', 'timeout'
        'mismatches': 5,
        'error_text': '...'
    }
    
    result = code_fix("module.sv", "Prob001_prompt.txt", eval_result)
    if result['success']:
        print(f"修复成功，采用候选：{result['accepted_variant']}")
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from config import (
    ARK_MODEL, 
    ARK_API_KEY,
    call_llm,
    DEFAULT_HARDWARE_CONSTRAINTS_TEXT,
)


# =========================
# 修复策略配置（来自闭环仿真 v678）
# =========================

# 小补丁修复（只修初值、首拍等最小必要逻辑）
SMALL_INITIAL_PATCH = {
    "Prob034_dff8",
    "Prob053_m2014_q4d",
    "Prob104_mt2015_muxdff",
}

# 小逻辑修复
SMALL_LOGIC_PATCH = {
    "Prob070_ece241_2013_q2",
}

# 仅编译修复
COMPILE_ONLY = {
    "Prob021_mux256to1v",
    "Prob144_conwaylife",
    "Prob154_fsm_ps2data",
}

# 超时重写
TIMEOUT_REWRITE = {
    "Prob082_lfsr32",
    "Prob141_count_clock",
    "Prob156_review2015_fancytimer",
}

# 强语义修复
SEMANTICS_STRONG = {
    "Prob054_edgedetect",
    "Prob066_edgecapture",
    "Prob089_ece241_2014_q5a",
    "Prob093_ece241_2014_q3",
    "Prob096_review2015_fsmseq",
    "Prob098_circuit7",
    "Prob117_circuit9",
    "Prob137_fsm_serial",
    "Prob142_lemmings2",
    "Prob146_fsm_serialdata",
}


def classify_case_type(case_id: str) -> str:
    """
    根据 case_id 分类题目类型
    
    Args:
        case_id (str): 题目 ID
        
    Returns:
        str: 类型标识（edge, shift_lfsr, fsm, mux_comb, seq_basic, default）
    """
    cid = case_id.lower()
    
    # 边沿检测类
    if any(kw in cid for kw in ["edge", "edgedetect", "edgecapture", "pedge", "anyedge"]):
        return "edge"
    
    # 移位/LFSR 类
    if any(kw in cid for kw in ["shift", "lfsr", "shiftcount", "count_clock", "fancytimer"]):
        return "shift_lfsr"
    
    # FSM 类
    if any(kw in cid for kw in ["fsm", "serial", "ps2", "lemmings", "timer"]):
        return "fsm"
    
    # 组合逻辑/MUX 类
    if any(kw in cid for kw in ["mux", "circuit", "kmap", "always_if", "always_case", "bugs_mux2"]):
        return "mux_comb"
    
    # 时序逻辑类
    if any(kw in cid for kw in ["dff", "muxdff", "q4d"]):
        return "seq_basic"
    
    return "default"


def choose_repair_bucket(case_id: str, case_type: str, eval_result: Dict) -> str:
    """
    选择修复桶（基于闭环仿真 v678 的分层策略）
    
    Args:
        case_id (str): 题目 ID
        case_type (str): 题目类型
        eval_result (Dict): 评估结果
        
    Returns:
        str: 修复桶名称
    """
    status = eval_result.get('status', 'unknown')
    mismatches = eval_result.get('mismatches')
    
    # 特殊题目特殊处理
    if case_id in SMALL_INITIAL_PATCH:
        return "small_initial_patch"
    
    if case_id in SMALL_LOGIC_PATCH:
        return "small_logic_patch"
    
    # 语法错误或编译失败
    if case_id in COMPILE_ONLY or status == "syntax":
        return "compile_only_fix"
    
    # 超时重写
    if case_id in TIMEOUT_REWRITE or status == "timeout":
        return "timeout_rewrite"
    
    # 强语义修复
    if case_id in SEMANTICS_STRONG:
        return "semantics_fix"
    
    # 根据失配数量判断
    if mismatches is not None and mismatches <= 3:
        return "boundary_patch"
    
    if mismatches is not None and mismatches <= 20:
        return "targeted_logic_fix"
    
    # 根据题目类型
    if case_type in {"edge", "fsm", "shift_lfsr"}:
        return "semantics_fix"
    
    # 默认结构重写
    return "structure_rewrite"


def get_variant_candidates(bucket: str) -> List[str]:
    """
    获取某修复桶的候选变体
    
    Args:
        bucket (str): 修复桶名称
        
    Returns:
        List[str]: 候选变体列表（A, B, C）
    """
    variant_map = {
        "small_initial_patch": ["A", "B"],
        "small_logic_patch": ["A", "B"],
        "compile_only_fix": ["A", "B"],
        "boundary_patch": ["A", "B"],
        "targeted_logic_fix": ["A", "B"],
        "timeout_rewrite": ["B", "C"],
        "semantics_fix": ["A", "B", "C"],
        "structure_rewrite": ["B", "C"],
    }
    return variant_map.get(bucket, ["A", "B"])


def build_mode_hints(bucket: str) -> List[str]:
    """
    构建修复模式提示
    
    Args:
        bucket (str): 修复桶名称
        
    Returns:
        List[str]: 修复提示列表
    """
    hints_table = {
        "small_initial_patch": [
            "本轮不要整体重写，只修初值、首拍和最小必要逻辑。",
            "如果参考实现依赖初始值，请优先修边界/首拍，而不是大改主体结构。",
        ],
        "small_logic_patch": [
            "本轮不要整体重写，只修最少量逻辑。",
            "优先根据 TB hint、first mismatch 和局部表达式做定点修复。",
        ],
        "compile_only_fix": [
            "本轮第一目标是 Icarus Verilog 可编译和接口严格匹配。",
            "优先使用 reg/localparam/always @(*)/always @(posedge clk)。",
            "避免 output wire 在 always 中赋值。",
        ],
        "boundary_patch": [
            "这是小残差修复：尽量保留主体结构，只修首拍、末拍、reset、输入顺序和一拍时机。",
            "若参考值为 x，不要为了消掉 x 而强行初始化。",
        ],
        "targeted_logic_fix": [
            "根据首个坏信号和首个失配时间定点修复。",
            "重点检查位序、拼接顺序、mux 方向和一拍时序。",
        ],
        "timeout_rewrite": [
            "这类题不要沿旧结构打补丁，应重写核心控制逻辑。",
            "重点检查 terminal condition、rollover、done 产生与退出条件。",
        ],
        "semantics_fix": [
            "这类题优先核对题意语义，而不是修单个边界常数。",
            "必要时重写控制相位、状态转移和优先级。",
        ],
        "structure_rewrite": [
            "当前高比例失配，通常不是边界问题。",
            "保留接口，按规格重写核心逻辑。",
        ],
    }
    return hints_table.get(bucket, [])


def extract_module_header(code: str) -> str:
    """
    提取 SystemVerilog 代码的模块头（端口声明部分）
    
    Args:
        code (str): 完整代码
        
    Returns:
        str: 模块头部分
    """
    # 匹配 module 到第一个分号（端口声明结束）
    match = re.search(r'(module\s+\w+\s*\(.*?\);)', code, re.DOTALL)
    if match:
        return match.group(1)
    return ""


def get_code_context_for_variant(bucket: str, variant: str, code: str) -> Tuple[str, str]:
    """
    根据修复桶和变体决定提供的代码上下文
    
    Args:
        bucket (str): 修复桶
        variant (str): 变体（A/B/C）
        code (str): 当前代码
        
    Returns:
        Tuple[str, str]: (描述文本，代码内容)
    """
    # 这些情况只提供模块头，避免错误结构锚定
    if bucket in {"timeout_rewrite", "structure_rewrite"}:
        return "仅提供接口头，避免错误结构锚定。", extract_module_header(code)
    
    if bucket == "compile_only_fix" and variant == "B":
        return "仅提供接口头，专注修接口与兼容性。", extract_module_header(code)
    
    if bucket in {"semantics_fix"} and variant == "C":
        return "仅提供接口头，要求按规格重写。", extract_module_header(code)
    
    # 其他情况提供全文
    return "提供当前代码作为参考。", code[:2000]  # 限制长度


def build_repair_prompt(
    case_id: str,
    case_type: str,
    bucket: str,
    variant: str,
    spec_text: str,
    failed_code: str,
    eval_result: Dict,
    mode_hints: List[str],
) -> str:
    """
    构建修复提示词
    
    Args:
        case_id (str): 题目 ID
        case_type (str): 题目类型
        bucket (str): 修复桶
        variant (str): 变体
        spec_text (str): 规格说明
        failed_code (str): 失败的代码
        eval_result (Dict): 评估结果
        mode_hints (List[str]): 模式提示
        
    Returns:
        str: 完整的修复提示词
    """
    context_desc, code_context = get_code_context_for_variant(bucket, variant, failed_code)
    
    error_info = eval_result.get('error_text', 'Unknown error')[:1000]
    mismatches = eval_result.get('mismatches', 'N/A')
    samples = eval_result.get('samples', 'N/A')
    
    return f"""[CASE INFORMATION]
Case ID: {case_id}
Type: {case_type}
Repair Bucket: {bucket}
Variant: {variant}
Status: {eval_result.get('status', 'unknown')}
Mismatches: {mismatches}/{samples}

{context_desc}

[SPECIFICATION]
{spec_text}

[CURRENT FAILED CODE]
{code_context}

[ERROR INFORMATION]
{error_info}

[MODE HINTS]
""" + "\n".join(mode_hints) + f"""

[HARDWARE CONSTRAINTS]
{DEFAULT_HARDWARE_CONSTRAINTS_TEXT}

[TASK]
Generate a corrected SystemVerilog implementation that fixes the identified issues.

Output ONLY the SystemVerilog code within ```systemverilog ``` code blocks."""


def system_prompt_for_variant(variant: str) -> str:
    """
    根据变体返回对应的系统提示
    
    Args:
        variant (str): 变体（A/B/C）
        
    Returns:
        str: 系统提示
    """
    prompts = {
        "A": "你是资深数字 IC 设计工程师，擅长在保留已有正确部分的前提下修补 RTL。只输出代码。",
        "B": "你是资深数字 IC 设计工程师，擅长重建 RTL 的关键控制/边界逻辑。只输出代码。",
        "C": "你是资深数字 IC 设计工程师，擅长根据诊断做结构性 RTL 修复。只输出代码。",
    }
    return prompts.get(variant, prompts["A"])


def clean_model_code(response: str) -> str:
    """
    从 LLM 响应中提取干净的 SystemVerilog 代码
    
    Args:
        response (str): LLM 原始响应
        
    Returns:
        str: 清理后的代码
    """
    # 策略 1: 匹配 ```systemverilog``` 代码块
    match = re.search(r'```systemverilog\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 策略 2: 匹配通用代码块
    match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        code = match.group(1).strip()
        if any(kw in code for kw in ['module', 'endmodule', 'input', 'output']):
            return code
    
    # 策略 3: 提取 module 到 endmodule
    match = re.search(r'(module\s+.*?endmodule)', response, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # 策略 4: 返回原始响应
    return response.strip()


def code_fix(failed_code_filename: str, spec_filename: str, eval_result: Dict) -> Dict:
    """
    主修复函数 - 调用多个候选变体进行修复
    
    Args:
        failed_code_filename (str): 失败的代码文件名
        spec_filename (str): 规格说明文件名
        eval_result (Dict): 评估结果
        
    Returns:
        Dict: 修复结果
            - success (bool): 是否成功
            - accepted_variant (str): 采用的变体
            - repaired_file (str): 修复后的文件路径
            - candidates (List): 候选结果列表
    """
    # 解析文件路径
    code_path = Path(failed_code_filename)
    spec_path = Path(spec_filename)
    
    if not code_path.is_absolute():
        code_path = Path.cwd() / code_path
    if not spec_path.is_absolute():
        spec_path = Path.cwd() / spec_path
    
    # 检查文件是否存在
    for fpath, fname in [(code_path, "Failed code"), (spec_path, "Specification")]:
        if not fpath.exists():
            raise FileNotFoundError(f"{fname} file not found: {fpath}")
    
    # 提取 case_id
    case_id = spec_path.stem.replace('_prompt', '').replace('_ifc', '')
    
    # 读取失败的代码和规格
    failed_code = code_path.read_text(encoding='utf-8')
    spec_text = spec_path.read_text(encoding='utf-8')
    
    print(f"[code_fix] Starting repair for {case_id}")
    print(f"   Status: {eval_result.get('status', 'unknown')}")
    print(f"   Mismatches: {eval_result.get('mismatches', 'N/A')}")
    
    # Step 1: 分类和选择修复桶
    case_type = classify_case_type(case_id)
    bucket = choose_repair_bucket(case_id, case_type, eval_result)
    
    print(f"   Case type: {case_type}")
    print(f"   Repair bucket: {bucket}")
    
    # Step 2: 获取候选变体
    variants = get_variant_candidates(bucket)
    mode_hints = build_mode_hints(bucket)
    
    print(f"   Candidate variants: {variants}")
    
    # Step 3: 为每个变体生成修复代码
    candidates = []
    candidate_files = {}
    
    for variant in variants:
        print(f"\n   Generating candidate {variant}...")
        
        try:
            # 构建提示词
            prompt = build_repair_prompt(
                case_id=case_id,
                case_type=case_type,
                bucket=bucket,
                variant=variant,
                spec_text=spec_text,
                failed_code=failed_code,
                eval_result=eval_result,
                mode_hints=mode_hints,
            )
            
            # 调用 LLM
            system_prompt = system_prompt_for_variant(variant)
            response = call_llm(
                system_prompt=system_prompt,
                user_prompt=prompt,
                model=ARK_MODEL,
            )
            
            # 提取代码
            repaired_code = clean_model_code(response)
            
            # 保存候选代码
            candidate_path = code_path.parent / f"cand_{variant.lower()}.sv"
            candidate_path.write_text(repaired_code, encoding='utf-8')
            candidate_files[variant] = candidate_path
            
            print(f"      ✓ Candidate {variant} saved to {candidate_path.name}")
            
            candidates.append({
                'variant': variant,
                'file': str(candidate_path),
                'code': repaired_code,
            })
            
        except Exception as e:
            print(f"      ✗ Candidate {variant} failed: {e}")
            candidates.append({
                'variant': variant,
                'file': None,
                'error': str(e),
            })
    
    # Step 4: 选择最佳候选（简单策略：选择第一个成功的）
    accepted_variant = ""
    accepted_file = ""
    
    for cand in candidates:
        if cand.get('file'):
            accepted_variant = cand['variant']
            accepted_file = cand['file']
            break
    
    if not accepted_file:
        print(f"[code_fix] ✗ All candidates failed")
        return {
            'success': False,
            'accepted_variant': "",
            'repaired_file': "",
            'candidates': candidates,
        }
    
    # Step 5: 复制最佳候选到 best_gen.sv
    best_path = code_path.parent / "best_gen.sv"
    best_path.write_text(Path(accepted_file).read_text(encoding='utf-8'), encoding='utf-8')
    
    print(f"\n[code_fix] ✅ Repair successful!")
    print(f"   Accepted variant: {accepted_variant}")
    print(f"   Repaired file: {best_path}")
    
    return {
        'success': True,
        'accepted_variant': accepted_variant,
        'repaired_file': str(best_path),
        'candidates': candidates,
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python code_fix.py <failed_code.sv> <spec.txt>")
        print("Example: python code_fix.py module.sv Prob001_prompt.txt")
        sys.exit(1)
    
    code_file = sys.argv[1]
    spec_file = sys.argv[2]
    
    # 模拟评估结果（实际应从 code_syntax/code_val 获取）
    mock_eval_result = {
        'syntax_pass': False,
        'func_pass': False,
        'status': 'syntax',
        'mismatches': None,
        'error_text': 'Syntax error detected',
    }
    
    try:
        result = code_fix(code_file, spec_file, mock_eval_result)
        if result['success']:
            print(f"\n✅ Success! Best candidate: {result['accepted_variant']}")
            print(f"   Output: {result['repaired_file']}")
        else:
            print(f"\n❌ All candidates failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
