# code_eval.py
"""
代码评估模块 (Code Evaluator)
================================================================================

功能:
对修复后的候选代码进行语法和功能验证，评估其质量。
支持多个候选变体的并行评估和排序。

输入:
- candidate_code_filename: 候选代码文件名
- testbench_filename: 测试平台文件名
- ref_code_filename: 参考代码文件名
- case_id: 题目 ID

输出:
- 同目录下生成 {tag}_eval.json 评估结果
- 返回评估结果字典

使用示例:
    from code_eval import code_eval
    
    result = code_eval(
        "cand_a.sv",
        "Prob001_test.sv", 
        "Prob001_ref.sv",
        "Prob001"
    )
    
    if result['func_pass']:
        print("✅ Functional verification passed")
    else:
        print(f"❌ Failed with {result['mismatches']} mismatches")
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
from config import IVERILOG, VVP, TB_TOP, run_cmd
SIM_TIMEOUT = 60


def parse_mismatch_from_log(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    从仿真日志中解析失配数量和样本总数
    
    Args:
        text (str): 仿真日志文本
        
    Returns:
        Tuple[Optional[int], Optional[int]]: (失配数，样本数)
    """
    mismatches = None
    samples = None
    match = re.search(r'Mismatches?:\s*(\d+)\s*in\s*(\d+)\s*samples', text, re.IGNORECASE)
    if match:
        return tuple(map(int, match.groups()))
    
    # 尝试匹配常见的输出格式
    # 格式 1: "Mismatches: 5 / 100"
    match = re.search(r'Mismatches?:\s*(\d+)\s*/\s*(\d+)', text, re.IGNORECASE)
    if match:
        mismatches = int(match.group(1))
        samples = int(match.group(2))
        return mismatches, samples
    
    # 格式 2: "Total mismatches: 5" 或 "Total: 5 mismatches"
    match = re.search(r'Total(?: mismatches?)?:\s*(\d+)', text, re.IGNORECASE)
    if match:
        mismatches = int(match.group(1))
    
    # 格式 3: 统计 DUT/REF 输出行数
    dut_lines = [line for line in text.split('\n') if line.startswith('DUT:')]
    ref_lines = [line for line in text.split('\n') if line.startswith('REF:')]
    samples = max(len(dut_lines), len(ref_lines))
    
    # 如果不匹配，尝试直接比较
    if mismatches is None and dut_lines and ref_lines:
        mismatches = sum(1 for d, r in zip(dut_lines, ref_lines) if d.split(':', 1)[1].strip() != r.split(':', 1)[1].strip()) + abs(len(dut_lines) - len(ref_lines))
    
    return mismatches, samples


def evaluate_candidate(
    candidate_code_filename: str,
    testbench_filename: str,
    ref_code_filename: str,
    case_id: str,
    tag: str = "cand"
) -> Dict:
    """
    评估单个候选代码
    
    Args:
        candidate_code_filename (str): 候选代码文件名
        testbench_filename (str): 测试平台文件名
        ref_code_filename (str): 参考代码文件名
        case_id (str): 题目 ID
        tag (str): 标签（用于输出文件命名）
        
    Returns:
        Dict: 评估结果
            - case_id (str)
            - rtl_file (str): RTL 文件名
            - status (str): pass/syntax/timeout/sim/unknown_sim_fail
            - syntax_pass (bool): 语法是否通过
            - func_pass (bool): 功能是否通过
            - mismatches (Optional[int]): 失配数
            - samples (Optional[int]): 样本数
            - timeout (bool): 是否超时
            - error_text (str): 错误信息
    """
    # 解析文件路径
    rtl_path = Path(candidate_code_filename).resolve()
    tb_path = Path(testbench_filename).resolve()
    ref_path = Path(ref_code_filename).resolve()
    
    for fpath, fname in [(rtl_path, "RTL code"), (tb_path, "Testbench"), (ref_path, "Reference")]:
        if not fpath.exists():
            return {
                'case_id': case_id,
                'rtl_file': rtl_path.name,
                'status': 'missing_file',
                'syntax_pass': False,
                'func_pass': False,
                'mismatches': None,
                'samples': None,
                'timeout': False,
                'error_text': f"{fname} not found: {fpath}",
            }
    
    case_dir = rtl_path.parent
    sim_output = case_dir / f"{tag}_sim.out"
    syntax_log = case_dir / f"{tag}_syntax.log"
    sim_log = case_dir / f"{tag}_sim.log"
    
    print(f"[code_eval] Evaluating {rtl_path.name}...")
    
    # Step 1: 编译仿真
    compile_cmd = [
        IVERILOG, "-g2012", "-s", TB_TOP,
        "-o", str(sim_output),
        str(tb_path), str(ref_path), str(rtl_path)
    ]
    
    print(f"   Compiling...")
    rc, out, err, to = run_cmd(compile_cmd, cwd=str(case_dir), timeout=60)
    
    # 保存语法检查日志
    syntax_log.write_text(out + "\n" + err, encoding='utf-8')
    
    # 检查编译结果
    if to or rc != 0 or not sim_output.exists():
        error_text = f"Compilation failed:\n{out}\n{err}"
        print(f"   ✗ Syntax check failed")
        return {
            'case_id': case_id,
            'rtl_file': rtl_path.name,
            'status': 'syntax',
            'syntax_pass': False,
            'func_pass': False,
            'mismatches': None,
            'samples': None,
            'timeout': to,
            'error_text': error_text[:2000],
        }
    
    print(f"   ✓ Syntax check passed")
    
    # Step 2: 运行仿真
    print(f"   Running simulation...")
    rc2, out2, err2, to2 = run_cmd([VVP, str(sim_output)], cwd=str(case_dir), timeout=SIM_TIMEOUT)
    
    # 保存仿真日志
    sim_log.write_text(out2 + "\n" + err2, encoding='utf-8')
    
    full_output = out2 + "\n" + err2
    if rc2 != 0 and not to2 and rc2 != 124:
        return dict(case_id=case_id, rtl_file=rtl_path.name, status='runtime_error',
                    syntax_pass=True, func_pass=False, mismatches=None, samples=None,
                    timeout=False, error_text=full_output[:2000])
    
    # 检查超时
    timeout = to2 or ("TIMEOUT" in full_output) or (rc2 == 124)
    if timeout:
        print(f"   ✗ Simulation timeout")
        observed_mismatches, observed_samples = parse_mismatch_from_log(full_output)
        return {
            'case_id': case_id,
            'rtl_file': rtl_path.name,
            'status': 'timeout',
            'syntax_pass': True,
            'func_pass': False,
            'mismatches': observed_mismatches,
            'samples': observed_samples,
            'timeout': True,
            'error_text': full_output[:2000],
        }
    
    print(f"   ✓ Simulation completed")
    
    # Step 3: 解析失配
    mismatches, samples = parse_mismatch_from_log(full_output)
    
    # 如果无法解析，视为未知失败
    if mismatches is None:
        print(f"   ✗ Unknown simulation failure")
        return {
            'case_id': case_id,
            'rtl_file': rtl_path.name,
            'status': 'unknown_sim_fail',
            'syntax_pass': True,
            'func_pass': False,
            'mismatches': None,
            'samples': None,
            'timeout': False,
            'error_text': full_output[:2000],
        }
    
    # Step 4: 判定结果
    if mismatches == 0 and samples is not None and samples > 0:
        print(f"   ✅ Functional verification PASSED ({samples} samples)")
        return {
            'case_id': case_id,
            'rtl_file': rtl_path.name,
            'status': 'pass',
            'syntax_pass': True,
            'func_pass': True,
            'mismatches': 0,
            'samples': samples,
            'timeout': False,
            'error_text': "",
        }
    else:
        print(f"   ❌ Functional verification FAILED ({mismatches}/{samples} mismatches)")
        return {
            'case_id': case_id,
            'rtl_file': rtl_path.name,
            'status': 'sim',
            'syntax_pass': True,
            'func_pass': False,
            'mismatches': mismatches,
            'samples': samples,
            'timeout': False,
            'error_text': full_output[:2000],
        }


def compare_results(result_a: Dict, result_b: Dict) -> int:
    """
    比较两个评估结果的优劣
    
    Args:
        result_a (Dict): 结果 A
        result_b (Dict): 结果 B
        
    Returns:
        int: -1 表示 A 更好，0 表示相同，1 表示 B 更好
    """
    # 评分规则：pass < syntax < timeout < sim
    status_order = {'pass': 0, 'sim': 1, 'timeout': 2, 'unknown_sim_fail': 3, 'syntax': 4}
    
    score_a = status_order.get(result_a.get('status', 'unknown'), 99)
    score_b = status_order.get(result_b.get('status', 'unknown'), 99)
    
    if score_a < score_b:
        return -1
    elif score_a > score_b:
        return 1
    
    # 状态相同，比较失配数
    mismatches_a = result_a.get('mismatches')
    mismatches_b = result_b.get('mismatches')
    
    if mismatches_a is None and mismatches_b is None:
        return 0
    
    if mismatches_a is None:
        return 1  # B 更好
    
    if mismatches_b is None:
        return -1  # A 更好
    
    if mismatches_a < mismatches_b:
        return -1
    elif mismatches_a > mismatches_b:
        return 1
    
    return 0


def code_eval(
    candidate_code_filename: str,
    testbench_filename: str,
    ref_code_filename: str,
    case_id: str,
    tag: str = "cand"
) -> Dict:
    """
    主评估函数
    
    Args:
        candidate_code_filename (str): 候选代码文件名
        testbench_filename (str): 测试平台文件名
        ref_code_filename (str): 参考代码文件名
        case_id (str): 题目 ID
        tag (str): 标签
        
    Returns:
        Dict: 评估结果（与 evaluate_candidate 相同）
    """
    # 调用评估函数
    result = evaluate_candidate(
        candidate_code_filename,
        testbench_filename,
        ref_code_filename,
        case_id,
        tag
    )
    
    # 保存评估结果到 JSON
    result_path = Path(candidate_code_filename).parent / f"{tag}_eval.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"[code_eval] Evaluation saved to {result_path}")
    
    return result


# 全局配置
SIM_TIMEOUT = 60  # 仿真超时时间（秒）


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python code_eval.py <candidate.sv> <testbench.sv> <reference.sv> [case_id]")
        print("Example: python code_eval.py cand_a.sv Prob001_test.sv Prob001_ref.sv Prob001")
        sys.exit(1)
    
    cand_file = sys.argv[1]
    tb_file = sys.argv[2]
    ref_file = sys.argv[3]
    case_id = sys.argv[4] if len(sys.argv) > 4 else "Unknown"
    
    try:
        result = code_eval(cand_file, tb_file, ref_file, case_id)
        
        print("\n" + "=" * 70)
        print("EVALUATION RESULT")
        print("=" * 70)
        print(f"Case ID:      {result['case_id']}")
        print(f"RTL File:     {result['rtl_file']}")
        print(f"Status:       {result['status']}")
        print(f"Syntax Pass:  {result['syntax_pass']}")
        print(f"Func Pass:    {result['func_pass']}")
        print(f"Mismatches:   {result['mismatches']}")
        print(f"Samples:      {result['samples']}")
        print(f"Timeout:      {result['timeout']}")
        print("=" * 70)
        
        if result['func_pass']:
            print("✅ PASSED")
            sys.exit(0)
        else:
            print("❌ FAILED")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
