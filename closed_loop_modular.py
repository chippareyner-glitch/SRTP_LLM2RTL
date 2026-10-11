#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Closed Loop Modular System - 基于模块化架构的完整闭环优化系统
================================================================================

功能:
整合 8 个独立模块（spec_pre, code_gen, code_syntax, code_val, code_judge, 
code_diag, code_fix, code_eval），实现与 closed_loop_1.py 相同的完整闭环功能。

特性:
1. **全周期双重验证**：每次迭代都执行语法检查 + 功能验证
2. **Reviewer 输入增强**：包含 VCD 波形分析、语法错误日志、Mismatch 报告
3. **分层修复策略**：基于 v678 的分桶策略，支持多候选并行
4. **智能迭代**：自动诊断→修复→评估，直到收敛或达到最大迭代次数

作者：模块化重构版本
日期：2026-03-29
"""

import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 导入 8 个核心模块
from spec_pre import spec_pre
from code_gen import code_gen
from code_syntax import code_syntax
from code_val import code_val
from code_judge import code_judge
from code_diag import code_diag
from code_fix import code_fix
from code_eval import code_eval
from code_repair_loop import run_repair_loop

# 从 config 导入配置
from config import (
    DATASET_DIR,
    CASES_DIR,  # 闭环优化系统输出目录
    ARK_MODEL,
    ARK_API_KEY,
)


# =========================
# 配置区
# =========================

MAX_ITERATIONS = 5         # 最大迭代次数
OUTPUT_BASE_DIR = CASES_DIR  # 输出目录基路径
IVERILOG = "iverilog"
VVP = "vvp"
TB_TOP = "tb"


def log(message: str):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def ensure_dir(path: Path):
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)


def read_spec(case_id: str) -> str:
    """读取题目规格说明"""
    prompt_path = DATASET_DIR / f"{case_id}_prompt.txt"
    ifc_path = DATASET_DIR / f"{case_id}_ifc.txt"
    
    if prompt_path.exists():
        return prompt_path.read_text(encoding='utf-8')
    elif ifc_path.exists():
        return ifc_path.read_text(encoding='utf-8')
    else:
        raise FileNotFoundError(f"未找到题目规格：{case_id}")


def read_testbench(case_id: str) -> str:
    """读取测试平台"""
    tb_path = DATASET_DIR / f"{case_id}_test.sv"
    if not tb_path.exists():
        raise FileNotFoundError(f"未找到测试平台：{case_id}")
    return tb_path.read_text(encoding='utf-8')


def read_reference(case_id: str) -> str:
    """读取参考代码"""
    ref_path = DATASET_DIR / f"{case_id}_ref.sv"
    if not ref_path.exists():
        raise FileNotFoundError(f"未找到参考代码：{case_id}")
    return ref_path.read_text(encoding='utf-8')


def save_code(case_dir: Path, code: str, filename: str = "module.sv"):
    """保存代码到文件"""
    code_path = case_dir / filename
    code_path.write_text(code, encoding='utf-8')
    log(f"代码已保存：{filename}")


def load_code(case_dir: Path, filename: str = "module.sv") -> str:
    """从文件加载代码"""
    code_path = case_dir / filename
    if not code_path.exists():
        raise FileNotFoundError(f"代码文件不存在：{filename}")
    return code_path.read_text(encoding='utf-8')


def build_eval_result(syntax_pass: bool, func_pass: bool, 
                      mismatches: Optional[int] = None, 
                      samples: Optional[int] = None,
                      error_text: str = "",
                      timeout: bool = False) -> Dict:
    """构建评估结果字典"""
    if not syntax_pass:
        status = "syntax"
    elif timeout:
        status = "timeout"
    elif func_pass:
        status = "pass"
    else:
        status = "sim"
    
    return {
        'syntax_pass': syntax_pass,
        'func_pass': func_pass,
        'status': status,
        'mismatches': mismatches,
        'samples': samples,
        'error_text': error_text,
        'timeout': timeout,
    }


def process_single_case(case_id: str, force_rerun: bool = False) -> Dict:
    """
    处理单个题目的完整闭环流程
    
    Args:
        case_id (str): 题目 ID
        force_rerun (bool): 是否强制重跑
        
    Returns:
        Dict: 处理结果
    """
    log(f"\n{'='*80}")
    log(f"开始处理：{case_id}")
    log(f"{'='*80}")
    
    # 准备工作目录
    case_dir = OUTPUT_BASE_DIR / case_id
    ensure_dir(case_dir)
    
    # 检查工作目录是否存在历史错误报告
    def has_error_reports(case_dir: Path) -> bool:
        """检查目录下是否存在表明代码有错误的报告文件"""
        # 检查最新的评估报告
        eval_files = sorted(case_dir.glob("*_eval.json"))
        if eval_files:
            try:
                latest_eval = eval_files[-1]
                eval_data = json.loads(latest_eval.read_text(encoding='utf-8'))
                # 如果功能验证失败，说明有错误
                if not eval_data.get('func_pass', True):
                    log(f"检测到最新评估报告 {latest_eval.name} 显示功能验证失败")
                    return True
            except Exception as e:
                log(f"⚠️  读取评估报告失败：{e}")
        
        # 检查语法报告
        syntax_reports = list(case_dir.glob("syntax_report*.txt"))
        if syntax_reports:
            try:
                latest_syntax = sorted(syntax_reports)[-1]
                syntax_content = latest_syntax.read_text(encoding='utf-8')
                # 如果包含语法错误关键字
                if 'Syntax check failed' in syntax_content or 'ERROR' in syntax_content.upper():
                    log(f"检测到最新语法报告 {latest_syntax.name} 显示语法检查失败")
                    return True
            except Exception as e:
                log(f"⚠️  读取语法报告失败：{e}")
        
        # 检查功能报告
        func_reports = list(case_dir.glob("func_report*.txt"))
        if func_reports:
            try:
                latest_func = sorted(func_reports)[-1]
                func_content = latest_func.read_text(encoding='utf-8')
                # 如果包含功能不匹配
                if 'mismatch' in func_content.lower() or 'failed' in func_content.lower():
                    log(f"检测到最新功能报告 {latest_func.name} 显示功能验证失败")
                    return True
            except Exception as e:
                log(f"⚠️  读取功能报告失败：{e}")
        
        return False
    
    # 检查是否已完成（增量执行）- 优先检查最终成功代码
    if not force_rerun:
        # 检查是否有最终成功代码（最可靠的完成标志）
        final_codes = list(case_dir.glob("module_final_iteration_*.sv"))
        if final_codes:
            log(f"检测到已有最终成功代码 {final_codes[0].name}，跳过（使用 --force 强制重跑）")
            return {'case_id': case_id, 'status': 'skipped', 'reason': 'already_completed'}
        
        # 如果没有最终代码，但有 module.sv，需要进一步检查
        module_sv = case_dir / "module.sv"
        if module_sv.exists():
            # 检查是否有失败标记
            failed_codes = list(case_dir.glob("module_failed_final_iteration_*.sv"))
            if failed_codes:
                log(f"检测到失败标记文件 {failed_codes[0].name}，将重新生成")
            elif has_error_reports(case_dir):
                log(f"检测到历史错误报告，将重新生成和修复")
            else:
                log(f"检测到已有 module.sv 且未发现错误报告，跳过（使用 --force 强制重跑）")
                return {'case_id': case_id, 'status': 'skipped', 'reason': 'already_exists'}

    try:
        # ========== 阶段 1: 规格优化 ==========
        log("\n【阶段 1】规格预处理...")
        original_spec_path = DATASET_DIR / f"{case_id}_prompt.txt"
        if not original_spec_path.exists():
            original_spec_path = DATASET_DIR / f"{case_id}_ifc.txt"
        
        optimized_spec = spec_pre(str(original_spec_path))
        review_path = case_dir / f"{case_id}_review.txt"
        review_path.write_text(optimized_spec, encoding='utf-8')
        log("✓ 规格优化完成")
        
        # ========== 阶段 2: 初始代码生成 ==========
        log("\n【阶段 2】生成初始代码...")
        result = code_gen(str(review_path))
        
        if result == "error":
            log("✗ 初始代码生成失败")
            return {
                'case_id': case_id,
                'status': 'failed',
                'stage': 'initial_generation',
                'reason': 'code_gen_error'
            }
        
        # 保存初始代码为 iteration_0 或 v1
        initial_code_path = case_dir / "module_v1.sv"
        current_code_path = case_dir / "module.sv"
        import shutil
        shutil.copyfile(current_code_path, initial_code_path)
        
        log("✓ 初始代码生成完成（已保存为 module_v1.sv）")
        
        # ========== 阶段 3: 迭代验证与修复 ==========
        log("\n【阶段 3】启动迭代验证循环...")
        
        # 提前准备测试平台和参考代码路径（供后续使用）
        testbench_path = DATASET_DIR / f"{case_id}_test.sv"
        ref_path = DATASET_DIR / f"{case_id}_ref.sv"
        
        for iteration in range(1, MAX_ITERATIONS + 1):
            log(f"\n--- 迭代 {iteration}/{MAX_ITERATIONS} ---")
            
            current_code = case_dir / "module.sv"
            
            # Step 3.1: 语法检查
            log("Step 1: 语法检查...")
            syntax_result = code_syntax(str(current_code))
            syntax_report_path = case_dir / f"syntax_report_iteration_{iteration}.txt"
            
            if syntax_result != 0:
                log(f"✗ 语法检查失败（第 {iteration} 次）")
                # 读取语法错误报告
                if syntax_report_path.exists():
                    error_text = syntax_report_path.read_text(encoding='utf-8')[:2000]
                else:
                    error_text = "Syntax check failed"
                
                eval_result = build_eval_result(
                    syntax_pass=False,
                    func_pass=False,
                    error_text=error_text
                )
            else:
                log("✓ 语法检查通过")
                
                # Step 3.2: 功能验证
                log("Step 2: 功能验证...")
                
                func_pass = code_val(
                    str(current_code),
                    str(testbench_path),
                    str(ref_path)
                )
                
                # 读取功能验证报告
                func_report_path = case_dir / f"func_report_iteration_{iteration}.txt"
                if func_report_path.exists():
                    report_text = func_report_path.read_text(encoding='utf-8')
                    
                    # 简单解析失配数
                    import re
                    match = re.search(r'Mismatches?:\s*(\d+)\s*/\s*(\d+)', report_text, re.IGNORECASE)
                    if match:
                        mismatches = int(match.group(1))
                        samples = int(match.group(2))
                    else:
                        mismatches = None
                        samples = None
                    
                    error_text = report_text[:2000]
                else:
                    mismatches = None
                    samples = None
                    error_text = ""
                
                if func_pass:
                    log("✓ 功能验证通过 - 任务完成！")
                    # 保存最终代码
                    final_path = case_dir / f"module_final_iteration_{iteration}.sv"
                    shutil.copyfile(current_code_path, final_path)
                    return {
                        'case_id': case_id,
                        'status': 'success',
                        'iterations': iteration,
                        'final_code': str(final_path)
                    }
                else:
                    log(f"✗ 功能验证失败（{mismatches}/{samples} 失配）")
                    eval_result = build_eval_result(
                        syntax_pass=True,
                        func_pass=False,
                        mismatches=mismatches,
                        samples=samples,
                        error_text=error_text
                    )
                
                # Step 3.3: 生成详细错误报告（VCD 分析）
                log("Step 3: 生成详细错误报告...")
                vcd_path = case_dir / f"wave_iteration_{iteration}.vcd"
                error_trace_path = case_dir / f"error_trace_report_iteration_{iteration}.txt"
                
                # 移动 VCD 文件到带迭代版本的文件名
                if (case_dir / "wave.vcd").exists():
                    shutil.copyfile(case_dir / "wave.vcd", vcd_path)
                    errors = code_judge(str(vcd_path), str(error_trace_path))
                    log(f"✓ 提取了 {len(errors)} 个错误追踪（已保存到 iteration_{iteration}）")
                else:
                    log("⚠ 未找到 VCD 文件，跳过详细分析")
            
            # Step 3.4: 诊断分析
            log("Step 4: 失败诊断...")
            try:
                diagnosis_path = case_dir / f"repair_diagnosis_iteration_{iteration}.txt"
                diagnosis = code_diag(
                    str(current_code),
                    str(original_spec_path),
                    eval_result,
                    case_id
                )
                diagnosis_path.write_text(diagnosis, encoding='utf-8')
                log("✓ 诊断完成（已保存到 iteration_{iteration}）")
            except Exception as e:
                log(f"⚠ 诊断失败：{e}")
                diagnosis = f"Diagnosis failed: {e}"
            
            # Step 3.5: 代码修复（使用修复循环模块）
            log("Step 5: 启动修复循环...")
            
            # 设置修复循环的输出前缀
            repair_tag = f"iteration_{iteration}"
            
            repair_report = run_repair_loop(
                str(current_code),
                str(original_spec_path),
                str(testbench_path),
                str(ref_path),
                case_id=case_id,
                max_rounds=2,  # 每轮迭代内最多 2 次修复尝试
                tag_prefix=repair_tag  # 传递标签前缀
            )
            
            if repair_report['success']:
                log(f"✓ 修复成功（第 {iteration} 轮）")
                
                # 保存修复后的代码版本
                repaired_code_path = case_dir / f"module_repaired_iteration_{iteration}.sv"
                if Path(repair_report.get('final_code_path', '')).exists():
                    shutil.copyfile(Path(repair_report['final_code_path']), repaired_code_path)
                    log(f"✓ 修复代码已保存为 {repaired_code_path.name}")
                
                # 准备下一轮验证
                # 将修复后的代码复制为 module.sv 供下一轮使用
                best_gen_path = case_dir / "best_gen.sv"
                if best_gen_path.exists():
                    shutil.copyfile(best_gen_path, current_code_path)
                    log("✓ 已更新 module.sv 为修复版本")
            else:
                log(f"✗ 修复失败（第 {iteration} 轮）")
                
                # 如果达到最大迭代次数
                if iteration >= MAX_ITERATIONS:
                    log("已达到最大迭代次数，标记为失败")
                    # 保存最后一次尝试的代码
                    last_failed_path = case_dir / f"module_failed_final_iteration_{iteration}.sv"
                    shutil.copyfile(current_code_path, last_failed_path)
                    return {
                        'case_id': case_id,
                        'status': 'failed',
                        'stage': 'max_iterations_reached',
                        'iterations': iteration,
                        'reason': 'repair_failed',
                        'final_code': str(last_failed_path)
                    }
        
        # 理论上不应该到达这里
        return {
            'case_id': case_id,
            'status': 'unknown',
            'reason': 'unexpected_exit'
        }
        
    except Exception as e:
        log(f"\n✗ 处理过程中发生异常：{e}")
        import traceback
        traceback.print_exc()
        
        return {
            'case_id': case_id,
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def run_batch(cases: List[str], force_rerun: bool = False):
    """
    批量处理多个题目
    
    Args:
        cases (List[str]): 题目 ID 列表
        force_rerun (bool): 是否强制重跑
    """
    log(f"\n{'='*80}")
    log(f"批量处理开始 - 共 {len(cases)} 个题目")
    log(f"{'='*80}")
    
    results = []
    success_count = 0
    failed_count = 0
    skipped_count = 0
    
    for idx, case_id in enumerate(cases, 1):
        log(f"\n[{idx}/{len(cases)}] 处理 {case_id}")
        
        result = process_single_case(case_id, force_rerun)
        results.append(result)
        
        status = result.get('status', 'unknown')
        if status == 'success':
            success_count += 1
        elif status in ['failed', 'error']:
            failed_count += 1
        elif status == 'skipped':
            skipped_count += 1
        
        # 实时统计
        total = success_count + failed_count + skipped_count
        log(f"\n[进度] 完成：{total}/{len(cases)} | 成功：{success_count} | 失败：{failed_count} | 跳过：{skipped_count}")
    
    # 保存总结报告
    summary_path = OUTPUT_BASE_DIR / "batch_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump({
            'total_cases': len(cases),
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'results': results
        }, f, indent=2, ensure_ascii=False, default=str)
    
    log(f"\n{'='*80}")
    log(f"批量处理完成！")
    log(f"总计：{len(cases)} | 成功：{success_count} | 失败：{failed_count} | 跳过：{skipped_count}")
    log(f"成功率：{success_count / (success_count + failed_count) * 100:.1f}%")
    log(f"总结报告：{summary_path}")
    log(f"{'='*80}\n")
    
    return results


def main():
    """
    主函数 - 默认直接运行所有题目
    
    用法:
        python closed_loop_modular.py              # 运行所有题目（智能跳过已完成的）
        python closed_loop_modular.py --force      # 强制重跑所有题目
        python closed_loop_modular.py --cases X Y  # 运行指定题目
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="模块化闭环优化系统 - 默认运行所有题目",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python closed_loop_modular.py                    运行所有题目（自动跳过已完成的）
  python closed_loop_modular.py --force            强制重跑所有题目
  python closed_loop_modular.py --cases Prob001    仅运行 Prob001
  python closed_loop_modular.py --all --limit 5   运行前 5 个题目
        """
    )
    parser.add_argument("--all", action="store_true", help="处理所有题目（默认行为）")
    parser.add_argument("--force", action="store_true", help="强制重跑（忽略已有结果）")
    parser.add_argument("--cases", nargs="+", help="指定要处理的题目 ID 列表")
    parser.add_argument("--limit", type=int, default=None, help="限制处理的题目数量")
    
    args = parser.parse_args()
    
    # 确定要处理的题目
    if args.cases:
        # 使用指定的题目列表
        cases = args.cases
        log(f"将处理指定的 {len(cases)} 个题目")
    else:
        # 默认扫描数据集中的所有题目
        cases = set()
        for f in DATASET_DIR.iterdir():
            if f.is_file() and (f.name.endswith('_prompt.txt') or f.name.endswith('_ifc.txt')):
                # 提取完整的 case_id（去掉 _prompt 或 _ifc 后缀）
                stem = f.stem
                if stem.endswith('_prompt'):
                    case_id = stem[:-7]  # 去掉 '_prompt'
                elif stem.endswith('_ifc'):
                    case_id = stem[:-4]  # 去掉 '_ifc'
                else:
                    case_id = stem
                cases.add(case_id)
        cases = sorted(list(cases))
        log(f"将处理所有题目：共 {len(cases)} 个")
    
    # 限制数量
    if args.limit and args.limit > 0:
        cases = cases[:args.limit]
        log(f"限制处理前 {args.limit} 个题目")
    
    # 运行批处理
    run_batch(cases, force_rerun=args.force)


if __name__ == "__main__":
    main()
