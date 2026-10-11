# code_repair_loop.py
"""
代码修复循环模块 (Code Repair Loop)
================================================================================

功能:
整合语法检查、功能验证、诊断、修复和评估，实现完整的闭环修复流程。
基于闭环仿真 v678 的分层修复策略。

输入:
- failed_code_filename: 失败的代码文件名
- spec_filename: 规格说明文件名
- testbench_filename: 测试平台文件名
- ref_code_filename: 参考代码文件名
- max_rounds: 最大修复轮次（默认 3）

输出:
- 同目录下生成完整的过程文件和最终修复结果
- 返回修复总结报告

使用示例:
    from code_repair_loop import run_repair_loop
    
    report = run_repair_loop(
        "module.sv",
        "Prob001_prompt.txt",
        "Prob001_test.sv",
        "Prob001_ref.sv",
        max_rounds=3
    )
    
    if report['success']:
        print(f"✅ Repair successful in round {report['completed_round']}")
    else:
        print(f"❌ Repair failed after {report['completed_round']} rounds")
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from code_syntax import code_syntax
from code_val import code_val
from code_diag import code_diag
from code_fix import code_fix
from code_eval import code_eval


def run_single_repair_round(
    round_num: int,
    failed_code_path: Path,
    spec_path: Path,
    tb_path: Path,
    ref_path: Path,
    case_id: str,
    prev_eval_result: Dict,
    tag_prefix: str = "cand"
) -> Dict:
    """
    运行单轮修复
    
    Args:
        round_num (int): 轮次编号
        failed_code_path (Path): 失败代码路径
        spec_path (Path): 规格路径
        tb_path (Path): TB 路径
        ref_path (Path): 参考代码路径
        case_id (str): 题目 ID
        prev_eval_result (Dict): 上一轮的评估结果
        tag_prefix (str): 文件标签前缀
        
    Returns:
        Dict: 本轮修复结果
    """
    print(f"\n{'='*80}")
    print(f"[Round {round_num}] Starting repair cycle...")
    print(f"{'='*80}")
    
    result = {
        'round': round_num,
        'diagnosis': None,
        'repair_candidates': [],
        'best_candidate': None,
        'eval_results': [],
        'success': False,
    }
    
    # Step 1: 诊断分析
    print(f"\n[Step 1] Running failure diagnosis...")
    try:
        diagnosis = code_diag(
            str(failed_code_path),
            str(spec_path),
            prev_eval_result,
            case_id
        )
        result['diagnosis'] = diagnosis
        print(f"   ✓ Diagnosis completed")
    except Exception as e:
        print(f"   ✗ Diagnosis failed: {e}")
        result['diagnosis'] = f"Diagnosis failed: {e}"
    
    # Step 2: 调用修复模块生成候选
    print(f"\n[Step 2] Generating repair candidates...")
    try:
        repair_result = code_fix(
            str(failed_code_path),
            str(spec_path),
            prev_eval_result
        )
        
        result['repair_candidates'] = repair_result.get('candidates', [])
        
        if repair_result['success']:
            print(f"   ✓ Generated {len(result['repair_candidates'])} candidates")
        else:
            print(f"   ✗ All candidates failed to generate")
            
    except Exception as e:
        print(f"   ✗ Repair generation failed: {e}")
        return result
    
    # Step 3: 评估每个候选
    print(f"\n[Step 3] Evaluating candidates...")
    for cand in result['repair_candidates']:
        if not cand.get('file'):
            continue
        
        cand_path = Path(cand['file'])
        variant = cand.get('variant', 'unknown')
        
        print(f"\n   Evaluating candidate {variant}...")
        
        try:
            # 使用自定义标签前缀
            eval_tag = f"{tag_prefix}_round_{round_num}_{variant.lower()}"
            eval_result = code_eval(
                str(cand_path),
                str(tb_path),
                str(ref_path),
                case_id,
                tag=eval_tag
            )
            
            result['eval_results'].append(eval_result)
            
            if eval_result.get('func_pass'):
                print(f"      ✅ Candidate {variant} PASSED!")
                result['best_candidate'] = cand
                result['success'] = True
                break
            else:
                mismatches = eval_result.get('mismatches', 'N/A')
                samples = eval_result.get('samples', 'N/A')
                print(f"      ❌ Candidate {variant} failed ({mismatches}/{samples} mismatches)")
                
        except Exception as e:
            print(f"      ✗ Evaluation failed: {e}")
            result['eval_results'].append({
                'variant': variant,
                'error': str(e),
                'func_pass': False,
            })
    
    # Step 4: 选择最佳候选
    if not result['success'] and result['eval_results']:
        # 优先选择语法通过但功能失败的候选
        valid_results = [r for r in result['eval_results'] if r.get('syntax_pass')]
        
        if valid_results:
            # 有语法通过的候选，选择失配最少的
            best_failed = min(valid_results, key=lambda x: x.get('mismatches', 999))
            result['best_candidate'] = next(
                (c for c in result['repair_candidates'] 
                 if c.get('variant') == best_failed.get('rtl_file', '').replace('cand_', '').replace('.sv', '')),
                None
            )
            print(f"\n   Selected best failed candidate (syntax passed) for next round: {result['best_candidate']}")
        else:
            # 所有候选都语法失败，选择第一个作为下一轮的基础
            # 这种情况需要 LLM 重新生成，因为语法都有问题
            result['best_candidate'] = result['repair_candidates'][0]
            print(f"\n   ⚠️  All candidates have syntax errors, selecting first candidate for regeneration: {result['best_candidate']['variant']}")

    print(f"\n[Round {round_num}] Completed: {'✅ SUCCESS' if result['success'] else '❌ FAILED'}")
    
    return result


def run_repair_loop(
    failed_code_filename: str,
    spec_filename: str,
    testbench_filename: str,
    ref_code_filename: str,
    case_id: Optional[str] = None,
    max_rounds: int = 3,
    tag_prefix: str = "cand"
) -> Dict:
    """
    运行完整的修复循环
    
    Args:
        failed_code_filename (str): 失败的代码文件名
        spec_filename (str): 规格说明文件名
        testbench_filename (str): 测试平台文件名
        ref_code_filename (str): 参考代码文件名
        case_id (Optional[str]): 题目 ID
        max_rounds (int): 最大修复轮次
        tag_prefix (str): 文件标签前缀（用于区分不同迭代）
        
    Returns:
        Dict: 修复总结报告
    """
    # 解析文件路径
    code_path = Path(failed_code_filename)
    spec_path = Path(spec_filename)
    tb_path = Path(testbench_filename)
    ref_path = Path(ref_code_filename)
    
    for fpath, fname in [(code_path, "Failed code"), (spec_path, "Specification"),
                          (tb_path, "Testbench"), (ref_path, "Reference")]:
        if not fpath.exists():
            raise FileNotFoundError(f"{fname} file not found: {fpath}")
    
    # 提取 case_id
    if case_id is None:
        case_id = spec_path.stem.replace('_prompt', '').replace('_ifc', '')
    
    print(f"{'='*80}")
    print(f"CLOSED-LOOP REPAIR SYSTEM")
    print(f"{'='*80}")
    print(f"Case ID: {case_id}")
    print(f"Max Rounds: {max_rounds}")
    print(f"Working Directory: {code_path.parent}")
    print(f"{'='*80}")
    
    # 初始化
    summary = {
        'case_id': case_id,
        'max_rounds': max_rounds,
        'completed_rounds': 0,
        'success': False,
        'round_results': [],
        'final_code': None,
    }
    
    current_code_path = code_path
    prev_eval_result = {
        'syntax_pass': False,
        'func_pass': False,
        'status': 'unknown',
        'mismatches': None,
        'samples': None,
        'error_text': 'Initial failure',
    }
    
    # 主循环
    for round_num in range(1, max_rounds + 1):
        print(f"\n\n{'='*80}")
        print(f"STARTING REPAIR ROUND {round_num}/{max_rounds}")
        print(f"{'='*80}")
        
        # 运行单轮修复（传入标签前缀）
        round_result = run_single_repair_round(
            round_num=round_num,
            failed_code_path=current_code_path,
            spec_path=spec_path,
            tb_path=tb_path,
            ref_path=ref_path,
            case_id=case_id,
            prev_eval_result=prev_eval_result,
            tag_prefix=tag_prefix
        )
        
        summary['round_results'].append(round_result)
        summary['completed_rounds'] = round_num
        
        # 检查是否成功
        if round_result['success']:
            print(f"\n{'='*80}")
            print(f"✅ REPAIR SUCCESSFUL in Round {round_num}!")
            print(f"{'='*80}")
            
            summary['success'] = True
            summary['final_code'] = round_result['best_candidate']
            
            # 复制最佳代码到 module.sv
            if round_result['best_candidate'] and round_result['best_candidate'].get('file'):
                final_path = code_path.parent / "module.sv"
                best_cand_path = Path(round_result['best_candidate']['file'])
                final_path.write_text(best_cand_path.read_text(encoding='utf-8'), encoding='utf-8')
                summary['final_code_path'] = str(final_path)
                print(f"Final code saved to: {final_path}")
            
            break
        
        # 准备下一轮
        if round_result['best_candidate'] and round_result['best_candidate'].get('file'):
            current_code_path = Path(round_result['best_candidate']['file'])
            
            # 更新评估结果为当前最佳失败候选的结果
            if round_result['eval_results']:
                prev_eval_result = round_result['eval_results'][0]
        else:
            print(f"\n⚠️  No valid candidate for next round, stopping...")
            break
    
    # 生成总结报告
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Case ID: {case_id}")
    print(f"Total Rounds: {summary['completed_rounds']}/{max_rounds}")
    print(f"Result: {'✅ SUCCESS' if summary['success'] else '❌ FAILED'}")
    
    if summary['success']:
        print(f"Accepted Variant: {summary['final_code'].get('variant', 'N/A')}")
        print(f"Final Code: {summary.get('final_code_path', 'N/A')}")
    else:
        print(f"All {summary['completed_rounds']} rounds failed to produce a working solution.")
    
    # 保存总结报告（带标签前缀）
    summary_path = code_path.parent / f"{tag_prefix}_repair_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\nSummary saved to: {summary_path}")
    print(f"{'='*80}\n")
    
    return summary


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 5:
        print("Usage: python code_repair_loop.py <failed_code.sv> <spec.txt> <testbench.sv> <reference.sv> [case_id]")
        print("Example: python code_repair_loop.py module.sv Prob001_prompt.txt Prob001_test.sv Prob001_ref.sv Prob001")
        sys.exit(1)
    
    code_file = sys.argv[1]
    spec_file = sys.argv[2]
    tb_file = sys.argv[3]
    ref_file = sys.argv[4]
    case_id = sys.argv[5] if len(sys.argv) > 5 else None
    
    try:
        report = run_repair_loop(code_file, spec_file, tb_file, ref_file, case_id)
        
        if report['success']:
            print(f"\n✅ Repair completed successfully!")
            sys.exit(0)
        else:
            print(f"\n❌ Repair failed after all rounds")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
