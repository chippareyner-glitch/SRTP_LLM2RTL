# code_diag.py
"""
代码诊断模块 (Code Diagnostician)
================================================================================

功能:
分析失败原因并生成详细的诊断报告，为修复提供精准指导。
基于闭环仿真 v678 的诊断逻辑，支持多维度错误分析。

输入:
- failed_code_filename: 失败的代码文件名
- spec_filename: 规格说明文件名
- eval_result: 评估结果字典
- case_id: 题目 ID

输出:
- 同目录下生成 repair_diagnosis.txt 诊断报告
- 返回诊断文本

使用示例:
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
    print(f"Diagnosis report saved. Key issues identified.")
"""

import sys as _sys, pathlib as _pathlib  # legacy/ 下的模块依赖项目根目录的 config 等模块
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
import re
from pathlib import Path
from typing import Dict, List, Optional
from config import ARK_MODEL, ARK_API_KEY, call_reviewer_llm


def extract_tb_port_info(case_id: str, dataset_dir: Optional[Path] = None) -> str:
    """
    从测试平台中提取端口信息
    
    Args:
        case_id (str): 题目 ID
        dataset_dir (Optional[Path]): 数据集目录
        
    Returns:
        str: 端口名列表
    """
    if dataset_dir is None:
        from config import DATASET_DIR
        dataset_dir = DATASET_DIR
    
    tb_path = dataset_dir / f"{case_id}_test.sv"
    if not tb_path.exists():
        return ""
    
    tb_text = tb_path.read_text(encoding='utf-8')
    
    # 查找 TopModule 实例化
    match = re.search(r'TopModule\s+\w+\s*\((.*?)\)\s*;', tb_text, re.DOTALL)
    if not match:
        return ""
    
    port_block = match.group(1)
    ports = re.findall(r'\.\s*([A-Za-z_][A-Za-z0-9_$]*)\s*\(', port_block)
    
    if not ports:
        return ""
    
    return "TopModule 在 testbench 中出现的端口名（仅供接口对齐参考）：\n- " + "\n- ".join(ports)


def analyze_failure_pattern(eval_result: Dict, failed_code: str) -> List[str]:
    """
    分析失败模式
    
    Args:
        eval_result (Dict): 评估结果
        failed_code (str): 失败的代码
        
    Returns:
        List[str]: 失败模式列表
    """
    patterns = []
    
    status = eval_result.get('status', 'unknown')
    mismatches = eval_result.get('mismatches')
    samples = eval_result.get('samples')
    
    # 语法失败模式
    if status == "syntax":
        error_text = eval_result.get('error_text', '')
        
        if "extra data" in error_text.lower():
            patterns.append("LLM 响应包含额外解释文本，需要清理代码块标记")
        
        if "endmodule" in error_text.lower():
            patterns.append("缺少 endmodule 结束符")
        
        if "syntax" in error_text.lower() or "parse" in error_text.lower():
            patterns.append("SystemVerilog 语法错误")
    
    # 功能失败模式
    elif status == "sim":
        if mismatches is not None and samples is not None:
            mismatch_rate = mismatches / max(samples, 1)
            
            if mismatch_rate < 0.05:
                patterns.append("小残差（<5%），可能是边界/初值/首拍问题")
            elif mismatch_rate < 0.3:
                patterns.append("中等失配（5%-30%），可能是部分逻辑错误")
            else:
                patterns.append("高比例失配（>30%），可能是整体结构或核心逻辑错误")
        
        # 检查是否有时序相关问题
        error_text = eval_result.get('error_text', '')
        if any(kw in error_text.lower() for kw in ["timing", "setup", "hold", "clock"]):
            patterns.append("可能涉及时序违例")
    
    # 超时模式
    elif status == "timeout":
        patterns.append("仿真超时，可能存在死循环或长延时路径")
    
    # 代码特征分析
    if "always @(*)" in failed_code and "posedge" not in failed_code:
        patterns.append("纯组合逻辑设计")
    
    if "always @(posedge" in failed_code:
        patterns.append("时序逻辑设计")
    
    if "case" in failed_code:
        patterns.append("使用 case 语句")
    
    if "for" in failed_code:
        patterns.append("使用 for 循环")
    
    return patterns


def build_diagnosis_prompt(
    case_id: str,
    case_type: str,
    bucket: str,
    spec_text: str,
    failed_code: str,
    eval_result: Dict,
    failure_patterns: List[str],
    tb_port_info: str,
) -> str:
    """
    构建诊断提示词
    
    Args:
        case_id (str): 题目 ID
        case_type (str): 题目类型
        bucket (str): 修复桶
        spec_text (str): 规格说明
        failed_code (str): 失败的代码
        eval_result (Dict): 评估结果
        failure_patterns (List[str]): 失败模式列表
        tb_port_info (str): TB 端口信息
        
    Returns:
        str: 诊断提示词
    """
    status = eval_result.get('status', 'unknown')
    mismatches = eval_result.get('mismatches', 'N/A')
    samples = eval_result.get('samples', 'N/A')
    error_text = eval_result.get('error_text', 'Unknown error')[:1500]
    
    return f"""你是 RTL 根因分析助手。不要写代码，只输出精简诊断（300 字以内）。

【CASE 信息】
Case ID: {case_id}
Type: {case_type}
Repair Bucket: {bucket}
Status: {status}
Mismatches: {mismatches}/{samples}

【失败模式】
""" + "\n".join(f"- {p}" for p in failure_patterns) + f"""

【规格说明】
{spec_text[:1500]}

【当前代码】
{failed_code[:1000]}

【TB 端口信息】
{tb_port_info}

【错误日志】
{error_text}

【你的任务】
请分析：
1. 最可能的根本原因（Root Cause）
2. 应该优先修复的 Top 3 问题
3. 推荐的修复策略（小修小补 vs 结构性重写）

用简洁的条目式回答，不要写代码。"""


def code_diag(
    failed_code_filename: str,
    spec_filename: str,
    eval_result: Dict,
    case_id: Optional[str] = None,
) -> str:
    """
    主诊断函数
    
    Args:
        failed_code_filename (str): 失败的代码文件名
        spec_filename (str): 规格说明文件名
        eval_result (Dict): 评估结果
        case_id (Optional[str]): 题目 ID（可选，可从 spec 文件名提取）
        
    Returns:
        str: 诊断报告文本
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
    if case_id is None:
        case_id = spec_path.stem.replace('_prompt', '').replace('_ifc', '')
    
    # 读取失败的代码和规格
    failed_code = code_path.read_text(encoding='utf-8')
    spec_text = spec_path.read_text(encoding='utf-8')
    
    print(f"[code_diag] Analyzing failure for {case_id}...")
    
    # Step 1: 分类
    case_type = classify_case_type(case_id)
    bucket = choose_repair_bucket(case_id, case_type, eval_result)
    
    print(f"   Case type: {case_type}")
    print(f"   Repair bucket: {bucket}")
    
    # Step 2: 分析失败模式
    failure_patterns = analyze_failure_pattern(eval_result, failed_code)
    
    print(f"   Failure patterns identified: {len(failure_patterns)}")
    for pattern in failure_patterns:
        print(f"      - {pattern}")
    
    # Step 3: 提取 TB 端口信息
    tb_port_info = extract_tb_port_info(case_id)
    
    if tb_port_info:
        print(f"   Extracted {tb_port_info.count('-') - 1} ports from testbench")
    
    # Step 4: 调用 LLM 进行诊断
    print(f"\n   Calling Reviewer LLM for diagnosis...")
    
    try:
        prompt = build_diagnosis_prompt(
            case_id=case_id,
            case_type=case_type,
            bucket=bucket,
            spec_text=spec_text,
            failed_code=failed_code,
            eval_result=eval_result,
            failure_patterns=failure_patterns,
            tb_port_info=tb_port_info,
        )
        
        system_prompt = "你是数字电路 RTL 调试专家，擅长从失败案例中定位根本原因。只输出诊断，不写代码。"
        
        diagnosis = call_reviewer_llm(
            system_prompt=system_prompt,
            user_prompt=prompt,
            model=ARK_MODEL,
        )
        
        # 限制诊断报告长度
        diagnosis = diagnosis[:2000]
        
    except Exception as e:
        print(f"   ⚠️  LLM diagnosis failed: {e}")
        diagnosis = f"LLM diagnosis failed: {str(e)}\n\nFallback to pattern-based analysis:\n" + "\n".join(f"- {p}" for p in failure_patterns)
    
    # Step 5: 保存诊断报告
    diagnosis_path = code_path.parent / "repair_diagnosis.txt"
    diagnosis_path.write_text(diagnosis, encoding='utf-8')
    
    print(f"\n[code_diag] ✅ Diagnosis report saved to {diagnosis_path}")
    print(f"   Report length: {len(diagnosis)} chars")
    
    return diagnosis


# =========================
# 辅助函数（从 code_fix 复用）
# =========================

def classify_case_type(case_id: str) -> str:
    """根据 case_id 分类题目类型"""
    cid = case_id.lower()
    
    if any(kw in cid for kw in ["edge", "edgedetect", "edgecapture", "pedge", "anyedge"]):
        return "edge"
    
    if any(kw in cid for kw in ["shift", "lfsr", "shiftcount", "count_clock", "fancytimer"]):
        return "shift_lfsr"
    
    if any(kw in cid for kw in ["fsm", "serial", "ps2", "lemmings", "timer"]):
        return "fsm"
    
    if any(kw in cid for kw in ["mux", "circuit", "kmap", "always_if", "always_case", "bugs_mux2"]):
        return "mux_comb"
    
    if any(kw in cid for kw in ["dff", "muxdff", "q4d"]):
        return "seq_basic"
    
    return "default"


def choose_repair_bucket(case_id: str, case_type: str, eval_result: Dict) -> str:
    """选择修复桶"""
    from code_fix import (
        SMALL_INITIAL_PATCH, SMALL_LOGIC_PATCH, COMPILE_ONLY,
        TIMEOUT_REWRITE, SEMANTICS_STRONG
    )
    
    status = eval_result.get('status', 'unknown')
    mismatches = eval_result.get('mismatches')
    
    if case_id in SMALL_INITIAL_PATCH:
        return "small_initial_patch"
    
    if case_id in SMALL_LOGIC_PATCH:
        return "small_logic_patch"
    
    if case_id in COMPILE_ONLY or status == "syntax":
        return "compile_only_fix"
    
    if case_id in TIMEOUT_REWRITE or status == "timeout":
        return "timeout_rewrite"
    
    if case_id in SEMANTICS_STRONG:
        return "semantics_fix"
    
    if mismatches is not None and mismatches <= 3:
        return "boundary_patch"
    
    if mismatches is not None and mismatches <= 20:
        return "targeted_logic_fix"
    
    if case_type in {"edge", "fsm", "shift_lfsr"}:
        return "semantics_fix"
    
    return "structure_rewrite"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python code_diag.py <failed_code.sv> <spec.txt> [case_id]")
        print("Example: python code_diag.py module.sv Prob001_prompt.txt Prob001")
        sys.exit(1)
    
    code_file = sys.argv[1]
    spec_file = sys.argv[2]
    case_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    # 模拟评估结果
    mock_eval_result = {
        'syntax_pass': False,
        'func_pass': False,
        'status': 'syntax',
        'mismatches': None,
        'samples': None,
        'error_text': 'Syntax error detected',
    }
    
    try:
        diagnosis = code_diag(code_file, spec_file, mock_eval_result, case_id)
        print("\n" + "=" * 70)
        print("DIAGNOSIS REPORT")
        print("=" * 70)
        print(diagnosis[:1000])  # 只显示前 1000 字符
        print("=" * 70)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
