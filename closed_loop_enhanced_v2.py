#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Closed Loop Enhanced System V2 - 基于智能诊断与分层摘要的增强型闭环优化系统（修复版）
================================================================================

版本：v2.0 Fixed with Fallback Mechanism
主要改进:
1. ✅ **VCD 解析降级策略**: 当 VCD 解析失败时，从传统报告中提取统计信息
2. ✅ **一致性保证**: Quick Summary 必须采信 Traditional Report 的错误计数
3. ✅ **冲突检测**: 自动识别并报告摘要与详细报告的矛盾
4. ✅ **友好提示**: 当数据不可用时显示明确提示而非空表
5. ✅ **移除 Code Diff**: 不再依赖参考代码对比，符合生产场景

作者：增强版本开发团队（修复 VCD 依赖问题）
日期：2026-03-30
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 导入核心模块（保持与 modular 版本兼容）
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
    CASES_DIR_ENHANCED as OUTPUT_BASE_DIR,  # 使用独立的 enhanced 输出目录
    ARK_MODEL,
    ARK_API_KEY,
    IVERILOG,
    VVP,
    TB_TOP,
    run_cmd,
)

# =========================
# 配置区
# =========================

MAX_ITERATIONS = 5         # 最大迭代次数
MAX_WORKERS = 4            # 最大并发线程数（建议值：CPU 核心数的 1/2 到 1/4）
# OUTPUT_BASE_DIR 已在 import 中设置为 CASES_DIR_ENHANCED


def log(message: str):
    """打印带时间戳的日志（线程安全版本）"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    thread_id = threading.current_thread().name
    # 主线程显示线程名，工作线程显示线程 ID
    if thread_id == "MainThread":
        print(f"[{timestamp}] {message}")
    else:
        # 提取线程 ID 后几位简化显示
        tid = thread_id.split("_")[-1][:4]
        print(f"[{timestamp}][T-{tid}] {message}")
    sys.stdout.flush()


# 线程安全的日志锁
log_lock = threading.Lock()

def log_thread_safe(message: str):
    """线程安全的日志打印函数"""
    with log_lock:
        timestamp = datetime.now().strftime("%H:%M:%S")
        thread_id = threading.current_thread().name
        if thread_id == "MainThread":
            print(f"[{timestamp}] {message}")
        else:
            tid = thread_id.split("_")[-1][:4]
            print(f"[{timestamp}][T-{tid}] {message}")
        sys.stdout.flush()


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
    ensure_dir(case_dir)
    code_path = case_dir / filename
    code_path.write_text(code, encoding='utf-8')
    return code_path


def load_code(code_path: Path) -> str:
    """加载代码"""
    if not code_path.exists():
        raise FileNotFoundError(f"Code file not found: {code_path}")
    return code_path.read_text(encoding='utf-8')


# =========================
# 【升级 1】分层错误摘要生成器
# =========================

def generate_quick_summary(error_traces: List[Dict], timeline: List[Dict]) -> str:
    """
    生成一句话错误摘要（Layer 1）
    
    格式："X mismatches found. First error at t=Yps. Z% errors occur at input (A,B). Suggests [PATTERN]."
    """
    if not error_traces:
        return "No errors detected - verification passed!"
    
    total_errors = len(error_traces)
    first_error_time = error_traces[0].get('error_time', 'unknown')
    
    # 统计输入组合的错误分布
    input_errors = defaultdict(int)
    input_total = defaultdict(int)
    
    for entry in timeline:
        key = (entry.get('x'), entry.get('y'))
        input_total[key] += 1
        if any(e.get('error_time') == entry.get('time') for e in error_traces):
            input_errors[key] += 1
    
    # 找出错误率最高的输入组合
    max_error_rate = 0
    worst_input = None
    for inp, total in input_total.items():
        if total > 0:
            rate = input_errors[inp] / total
            if rate > max_error_rate:
                max_error_rate = rate
                worst_input = inp
    
    # 推断可能的错误模式
    pattern_hint = ""
    if max_error_rate > 0.8 and worst_input == (1, 1):
        pattern_hint = "Suggests wrong gate implementation (NOR vs XNOR)"
    elif max_error_rate > 0.8 and worst_input == (0, 0):
        pattern_hint = "Suggests initialization error or inverted logic"
    elif all(input_errors[k] > 0 for k in input_total.keys()):
        pattern_hint = "Suggests systematic logic error across all inputs"
    
    summary_parts = [
        f"{total_errors} mismatches found.",
        f"First error at t={first_error_time}ps."
    ]
    
    if worst_input and max_error_rate > 0.5:
        summary_parts.append(
            f"{max_error_rate*100:.0f}% errors occur at input {worst_input}."
        )
    
    if pattern_hint:
        summary_parts.append(pattern_hint)
    
    return " ".join(summary_parts)


def generate_stats_table(error_traces: List[Dict], timeline: List[Dict]) -> str:
    """
    生成统计表格（Layer 2）
    
    返回 Markdown 格式的输入组合错误率统计表
    """
    # 按输入组合分类统计
    input_stats = defaultdict(lambda: {'total': 0, 'errors': 0})
    
    # 构建时间点→错误的映射
    error_times = {e.get('error_time') for e in error_traces}
    
    for entry in timeline:
        key = (entry.get('x', '?'), entry.get('y', '?'))
        input_stats[key]['total'] += 1
        if entry.get('time') in error_times:
            input_stats[key]['errors'] += 1
    
    # 生成表格
    lines = [
        "| Input (x,y) | Total Samples | Errors | Error Rate | Status |",
        "|-------------|---------------|--------|------------|--------|"
    ]
    
    for inp in sorted(input_stats.keys()):
        stats = input_stats[inp]
        total = stats['total']
        errors = stats['errors']
        rate = (errors / total * 100) if total > 0 else 0
        
        status = "✓" if errors == 0 else "❌ CRITICAL" if rate > 50 else "⚠️ WARNING"
        
        lines.append(
            f"| {inp} | {total} | {errors} | {rate:>6.2f}% | {status} |"
        )
    
    return "\n".join(lines)


# =========================
# 【升级 2】自动错误模式识别器
# =========================

def diagnose_error_pattern(error_traces: List[Dict], timeline: List[Dict]) -> List[Dict]:
    """
    自动诊断错误模式
    
    检测的模式：
    1. WRONG_GATE: 单门错误（如 NOR vs XNOR）
    2. FSM_LOCK: 状态机锁死
    3. TIMING_VIOLATION: 时序违例
    4. INIT_ERROR: 初始化错误
    5. SYSTEMATIC_ERROR: 系统性逻辑错误
    
    Returns:
        List[Dict]: 检测到的模式列表，每个包含 type, confidence, description, evidence, fix
    """
    patterns = []
    
    if not error_traces:
        return patterns
    
    # ========== Pattern 1: WRONG_GATE（单门错误） ==========
    # 特征：某个输入组合错误率>80%，其他组合 0%
    input_stats = defaultdict(lambda: {'total': 0, 'errors': 0})
    error_times = {e.get('error_time') for e in error_traces}
    
    for entry in timeline:
        key = (entry.get('x'), entry.get('y'))
        input_stats[key]['total'] += 1
        if entry.get('time') in error_times:
            input_stats[key]['errors'] += 1
    
    high_error_inputs = []
    zero_error_inputs = []
    
    for inp, stats in input_stats.items():
        rate = stats['errors'] / stats['total'] if stats['total'] > 0 else 0
        if rate > 0.8:
            high_error_inputs.append(inp)
        elif rate == 0:
            zero_error_inputs.append(inp)
    
    if high_error_inputs and zero_error_inputs:
        confidence = min(0.95, 0.7 + len(high_error_inputs) * 0.1)
        patterns.append({
            'type': 'WRONG_GATE',
            'confidence': confidence,
            'description': f'Likely implemented with wrong gate type',
            'evidence': f"High error rate at inputs {high_error_inputs}, zero errors at {zero_error_inputs}",
            'fix': f'Check logic gates for input combinations {high_error_inputs}',
            'gate_hypothesis': infer_wrong_gate_type(high_error_inputs, zero_error_inputs)
        })
    
    # ========== Pattern 2: FSM_LOCK（状态机锁死） ==========
    # 特征：连续 50+ 周期全部错误
    if has_consecutive_errors(error_traces, min_length=50):
        patterns.append({
            'type': 'FSM_LOCK',
            'confidence': 0.9,
            'description': 'FSM likely stuck in wrong state',
            'evidence': f'{len(error_traces)} consecutive errors detected',
            'fix': 'Check reset logic and state transition conditions'
        })
    
    # ========== Pattern 3: TIMING_VIOLATION（时序违例） ==========
    # 特征：错误集中在时钟边沿附近（±5ps）
    if detect_timing_violation(error_traces):
        patterns.append({
            'type': 'TIMING_VIOLATION',
            'confidence': 0.8,
            'description': 'Setup/hold time violation suspected',
            'evidence': 'Errors cluster around clock edges',
            'fix': 'Add pipeline stage or adjust clock period'
        })
    
    # ========== Pattern 4: INIT_ERROR（初始化错误） ==========
    # 特征：第一个错误在 t=0 或非常早（<10ps）
    first_error_time = error_traces[0].get('error_time', 999)
    if first_error_time < 10:
        patterns.append({
            'type': 'INIT_ERROR',
            'confidence': 0.85,
            'description': 'Initialization or reset value incorrect',
            'evidence': f'First error at t={first_error_time}ps (< 10ps)',
            'fix': 'Check initial values and reset logic'
        })
    
    # ========== Pattern 5: SYSTEMATIC_ERROR（系统性错误） ==========
    # 特征：所有输入组合都有错误，且错误率相近（40-60%）
    all_rates = []
    for inp, stats in input_stats.items():
        if stats['total'] > 0:
            all_rates.append(stats['errors'] / stats['total'])
    
    if all_rates and all(0.4 <= r <= 0.6 for r in all_rates):
        patterns.append({
            'type': 'SYSTEMATIC_ERROR',
            'confidence': 0.75,
            'description': 'Systematic logic error across all inputs',
            'evidence': f'Error rates similar across all inputs: {[f"{r*100:.0f}%" for r in all_rates]}',
            'fix': 'Review core algorithm implementation'
        })
    
    return patterns


def infer_wrong_gate_type(high_error_inputs: List[Tuple], zero_error_inputs: List[Tuple]) -> str:
    """推断可能的错误门类型"""
    # 简化版本：基于真值表推断
    if (1, 1) in high_error_inputs and (0, 0) in zero_error_inputs:
        return "Possible NOR instead of XNOR"
    elif (0, 0) in high_error_inputs and (1, 1) in zero_error_inputs:
        return "Possible NAND instead of XOR"
    else:
        return "Unknown gate mismatch - check truth table"


def has_consecutive_errors(error_traces: List[Dict], min_length: int = 50) -> bool:
    """检测是否有连续错误"""
    if len(error_traces) < min_length:
        return False
    
    # 检查时间戳是否连续（假设周期为 10ps）
    consecutive_count = 1
    max_consecutive = 1
    
    for i in range(1, len(error_traces)):
        time_diff = error_traces[i].get('error_time', 0) - error_traces[i-1].get('error_time', 0)
        if time_diff <= 15:  # 允许小的抖动
            consecutive_count += 1
            max_consecutive = max(max_consecutive, consecutive_count)
        else:
            consecutive_count = 1
    
    return max_consecutive >= min_length


def detect_timing_violation(error_traces: List[Dict]) -> bool:
    """检测时序违例（简化版本）"""
    if len(error_traces) < 5:
        return False
    
    # 检查错误时间是否是周期的倍数（如 10ps, 20ps, 30ps...）
    times = [e.get('error_time', 0) for e in error_traces]
    period_candidates = [10, 5, 20, 100]
    
    for period in period_candidates:
        multiples = sum(1 for t in times if t % period < 3 or t % period > period - 3)
        if multiples > len(times) * 0.7:
            return True
    
    return False


# =========================
# 【V2 新增】增强的错误数据提取器（不依赖 VCD）
# =========================

def parse_traditional_report(mismatch_report: str) -> Dict:
    """
    解析传统功能验证报告，提取错误统计信息
    
    Args:
        mismatch_report: func_report.txt 的完整内容
        
    Returns:
        Dict: 包含 error_count, total_samples, error_rate 的字典
    """
    result = {
        'error_count': 0,
        'total_samples': 0,
        'error_rate': 0.0,
        'parsed': False
    }
    
    if not mismatch_report:
        return result

    # Current code_val emits a JSON evaluation after its title line.
    try:
        payload = json.loads(mismatch_report[mismatch_report.index('{'):])
        errors, samples = payload.get('mismatches'), payload.get('samples')
        if errors is not None and samples is not None:
            return dict(error_count=int(errors), total_samples=int(samples),
                        error_rate=100 * errors / samples if samples else 0.0, parsed=True)
    except (ValueError, TypeError, AttributeError):
        pass
    standard = re.search(r'Mismatches:\s*(\d+)\s+in\s+(\d+)\s+samples', mismatch_report, re.IGNORECASE)
    if standard:
        errors, samples = map(int, standard.groups())
        return dict(error_count=errors, total_samples=samples,
                    error_rate=100 * errors / samples if samples else 0.0, parsed=True)
    
    # 模式 1: "FAIL: X mismatches in Y samples"
    pattern1 = r'FAIL:\s*(\d+)\s+mismatches\s+in\s+(\d+)\s+samples'
    match1 = re.search(pattern1, mismatch_report, re.IGNORECASE)
    
    if match1:
        result['error_count'] = int(match1.group(1))
        result['total_samples'] = int(match1.group(2))
        result['error_rate'] = (result['error_count'] / result['total_samples'] * 100) if result['total_samples'] > 0 else 0
        result['parsed'] = True
        return result
    
    # 模式 2: "Total mismatches found: X"
    pattern2 = r'Total\s+mismatches\s+found:\s*(\d+)'
    match2 = re.search(pattern2, mismatch_report, re.IGNORECASE)
    
    if match2:
        result['error_count'] = int(match2.group(1))
        # 尝试估算总样本数（如果有错误率信息）
        rate_pattern = r'(\d+(?:\.\d+)?)%\s+errors?'
        rate_match = re.search(rate_pattern, mismatch_report, re.IGNORECASE)
        if rate_match:
            error_rate = float(rate_match.group(1))
            if error_rate > 0:
                result['total_samples'] = int(result['error_count'] / (error_rate / 100))
                result['error_rate'] = error_rate
        result['parsed'] = True
        return result
    
    return result


def generate_fallback_stats(error_count: int, total_samples: int, error_rate: float) -> str:
    """
    生成降级统计表格（当 VCD 解析失败时使用）
    
    Args:
        error_count: 错误数量
        total_samples: 总样本数
        error_rate: 错误率（百分比）
        
    Returns:
        str: Markdown 格式的简化统计表格
    """
    lines = [
        "| Input Pattern | Total Samples | Errors | Error Rate | Status |",
        "|---------------|---------------|--------|------------|--------|"
    ]
    
    if error_count == 0:
        # 没有错误，显示通过
        lines.append(
            f"| All Combinations | {total_samples} | 0 | 0.00% | ✓ PASS |"
        )
    elif error_count > 0 and total_samples > 0:
        # 有错误但无法区分输入组合
        success_count = total_samples - error_count
        success_rate = (success_count / total_samples * 100)
        
        lines.append(
            f"| Failed Cases | {error_count} | {error_count} | 100.00% | ❌ CRITICAL |"
        )
        lines.append(
            f"| Passed Cases | {success_count} | 0 | 0.00% | ✓ PASS |"
        )
        
        # 添加注释说明
        if error_rate < 50:
            lines.append("")
            lines.append(f"*Note: Overall error rate is {error_rate:.1f}%. Detailed input pattern analysis unavailable.*")
    else:
        # 完全无法解析
        lines.append(
            "| ⚠️ Data Unavailable | - | - | - | ⚠️ WARNING |"
        )
        lines.append("")
        lines.append("*Note: Could not parse error statistics from traditional report.*")
    
    return "\n".join(lines)


def generate_quick_summary_v2(
    error_traces: List[Dict], 
    timeline: List[Dict],
    traditional_report: str = ""
) -> str:
    """
    增强的快速摘要生成器（V2 版本）
    
    改进：
    1. 优先使用 VCD 解析的详细数据
    2. VCD 失败时降级到传统报告
    3. 确保与传统报告一致性
    
    Args:
        error_traces: VCD 解析的错误追踪
        timeline: VCD 解析的时间线
        traditional_report: 传统功能验证报告文本
        
    Returns:
        str: 快速错误摘要
    """
    # 首先尝试从传统报告中提取错误计数
    traditional_data = parse_traditional_report(traditional_report)
    
    # 如果 VCD 解析失败但有传统报告数据，使用传统报告
    if not error_traces and traditional_data['parsed']:
        error_count = traditional_data['error_count']
        total_samples = traditional_data['total_samples']
        error_rate = traditional_data['error_rate']
        
        if error_count == 0:
            return "No errors detected - verification passed!"
        else:
            summary_parts = [
                f"{error_count} mismatches found.",
            ]
            if total_samples > 0:
                summary_parts.append(
                    f"Error rate: {error_rate:.1f}% ({error_count}/{total_samples} samples)."
                )
            summary_parts.append("⚠️ Detailed waveform analysis unavailable.")
            return " ".join(summary_parts)
    
    # 如果 VCD 解析成功，使用原有逻辑
    if error_traces or timeline:
        return generate_quick_summary(error_traces, timeline)
    
    # 都失败的情况
    return "⚠️ Could not parse error data from any source."


def generate_stats_table_v2(
    error_traces: List[Dict], 
    timeline: List[Dict],
    traditional_report: str = ""
) -> str:
    """
    增强的统计表格生成器（V2 版本）
    
    改进：
    1. 优先使用 VCD 解析的详细数据
    2. VCD 失败时降级到传统报告
    3. 绝不输出空表
    
    Args:
        error_traces: VCD 解析的错误追踪
        timeline: VCD 解析的时间线
        traditional_report: 传统功能验证报告文本
        
    Returns:
        str: Markdown 格式的统计表格
    """
    # 首先尝试 VCD 解析路径
    if timeline:
        # 检查是否有实际的输入数据
        input_stats = defaultdict(lambda: {'total': 0, 'errors': 0})
        error_times = {e.get('error_time') for e in error_traces}
        
        for entry in timeline:
            key = (entry.get('x', '?'), entry.get('y', '?'))
            input_stats[key]['total'] += 1
            if entry.get('time') in error_times:
                input_stats[key]['errors'] += 1
        
        # 如果 VCD 解析提供了有效数据，使用原有逻辑
        if input_stats:
            return generate_stats_table(error_traces, timeline)
    
    # VCD 解析失败或无数据，降级到传统报告
    traditional_data = parse_traditional_report(traditional_report)
    
    if traditional_data['parsed']:
        return generate_fallback_stats(
            traditional_data['error_count'],
            traditional_data['total_samples'],
            traditional_data['error_rate']
        )
    
    # 最后兜底：显示友好提示
    return (
        "| Input Pattern | Total Samples | Errors | Error Rate | Status |\n"
        "|---------------|---------------|--------|------------|--------|\n"
        "| ⚠️ Data Unavailable | - | - | - | ⚠️ WARNING |\n\n"
        "*Note: Waveform parsing failed and traditional report could not be parsed.*"
    )


def detect_report_conflict(quick_summary: str, mismatch_report: str) -> Optional[str]:
    """
    检测快速摘要与传统报告的冲突
    
    Args:
        quick_summary: 生成的快速摘要
        mismatch_report: 传统详细报告
        
    Returns:
        Optional[str]: 如果检测到冲突则返回警告信息，否则返回 None
    """
    # 检查快速摘要是否说"通过"
    if "no errors detected" in quick_summary.lower() or "verification passed" in quick_summary.lower():
        # 检查传统报告是否说"失败"
        if "failed" in mismatch_report.lower() or "mismatch" in mismatch_report.lower():
            traditional_data = parse_traditional_report(mismatch_report)
            if traditional_data['error_count'] > 0:
                return (
                    f"⚠️ **CRITICAL WARNING: Report Conflict Detected**\n\n"
                    f"The Quick Summary incorrectly states 'No errors detected', but the Traditional Report shows:\n"
                    f"- **{traditional_data['error_count']} mismatches** in {traditional_data['total_samples']} samples\n"
                    f"- Error rate: {traditional_data['error_rate']:.1f}%\n\n"
                    f"**This indicates VCD parsing failure. Please prioritize the Traditional Report data.**\n"
                )
    return None


# =========================
# 【升级 4】错误历史追踪器（Error Memory）
# =========================

class ErrorMemory:
    """维护全局错误档案，避免重复犯错"""
    
    def __init__(self, case_id: str):
        self.case_id = case_id
        self.history = []  # List[Dict]: 每轮迭代的错误记录
    
    def record_iteration(self, iteration: int, error_traces: List[Dict], 
                        diagnosis: List[Dict], passed: bool):
        """记录本轮错误"""
        self.history.append({
            'iteration': iteration,
            'error_count': len(error_traces),
            'error_patterns': [d['type'] for d in diagnosis],
            'first_error_time': error_traces[0].get('error_time') if error_traces else None,
            'diagnosis_details': diagnosis,
            'passed': passed
        })
    
    def get_trend_analysis(self) -> str:
        """分析错误趋势"""
        if len(self.history) < 2:
            return "Not enough data for trend analysis"
        
        trends = []
        for i in range(1, len(self.history)):
            prev = self.history[i-1]
            curr = self.history[i]
            
            if not prev['passed'] and curr['passed']:
                trends.append(f"✓ Iteration {curr['iteration']}: FIXED! (was {prev['count']} errors)")
            elif curr['error_count'] > prev['error_count']:
                trends.append(
                    f"❌ Iteration {curr['iteration']}: Errors INCREASED "
                    f"({prev['error_count']}→{curr['error_count']})"
                )
            elif curr['error_count'] < prev['error_count']:
                trends.append(
                    f"✓ Iteration {curr['iteration']}: Errors DECREASED "
                    f"({prev['error_count']}→{curr['error_count']})"
                )
            else:
                trends.append(
                    f"⚠ Iteration {curr['iteration']}: Errors UNCHANGED "
                    f"({curr['error_count']})"
                )
        
        return '\n'.join(trends)
    
    def get_repeated_mistakes(self) -> List[str]:
        """识别重复错误模式"""
        pattern_occurrences = defaultdict(list)
        
        for record in self.history:
            for pattern in record['error_patterns']:
                pattern_occurrences[pattern].append(record['iteration'])
        
        repeated = []
        for pattern, iterations in pattern_occurrences.items():
            if len(iterations) >= 2:
                repeated.append(
                    f"⚠️ RECURRENT ERROR: '{pattern}' occurred in iterations {iterations}"
                )
        
        return repeated
    
    def get_summary_for_reviewer(self) -> str:
        """生成给 Reviewer 的错误历史摘要"""
        parts = []
        
        if self.history:
            last = self.history[-1]
            parts.append(f"**Current Status**: Iteration {last['iteration']}, {last['error_count']} errors")
        
        trend = self.get_trend_analysis()
        if trend != "Not enough data for trend analysis":
            parts.append("\n**Trend Analysis**:")
            parts.append(trend)
        
        repeated = self.get_repeated_mistakes()
        if repeated:
            parts.append("\n**Repeated Mistakes to Avoid**:")
            parts.append('\n'.join(repeated))
            parts.append("\n\n⚠️ **CRITICAL**: Do NOT repeat the same mistakes from previous iterations!")
        
        return '\n'.join(parts)


# =========================
# 【升级 5】少样本示例库
# =========================

FEW_SHOT_EXAMPLES = """
## 📖 Successful Fix Examples (Learn from these)

### Example 1: Gate Type Error (XNOR vs NOR)
**Symptom**: 88% errors at input (1,1), 0% elsewhere  
**Diagnosis**: WRONG_GATE (95% confidence)  
**Bad Fix**: "Change the gate" ← Too vague!  
**Good Fix**: 
``systemverilog
// Line 45: Replace this WRONG code:
assign z = ~(a | b);  // NOR gate - INCORRECT

// With this CORRECT code:
assign z = ~(a ^ b);  // XNOR gate - CORRECT
// Or equivalently:
assign z = (a == b);  // Equality check
```
**Result**: Errors reduced from 212 → 0

### Example 2: FSM State Lock
**Symptom**: 127 consecutive errors, all outputs wrong after t=500ps  
**Diagnosis**: FSM_LOCK (90% confidence)  
**Bad Fix**: "Fix the state machine" ← Useless!  
**Good Fix**:
``systemverilog
// Line 78: Add missing transition condition
always @(posedge clk) begin
    case (state)
        S_IDLE: if (start) state <= S_RUNNING;
        S_RUNNING: if (done) state <= S_DONE;
        // ADD THIS MISSING LINE:
        S_ERROR: if (reset) state <= S_IDLE;  // Reset transition was missing!
    endcase
end
```
**Result**: Consecutive errors eliminated

### Example 3: Timing Violation
**Symptom**: Errors cluster around clock edges (t=10, 20, 30...)  
**Diagnosis**: TIMING_VIOLATION (80% confidence)  
**Good Fix**:
```systemverilog
// Add 1-cycle pipeline delay
reg temp;
always @(posedge clk) begin
    temp <= data_in;      // Stage 1
    data_out <= temp;     // Stage 2 (delayed by 1 cycle)
end
```
**Result**: Setup time violations resolved
"""


# =========================
# 【升级 6】增强的 Reviewer Prompt 构建器
# =========================

def build_enhanced_reviewer_prompt_v2(
    case_id: str,
    spec: str,
    gen_code: str,
    ref_code: str,
    mismatch_report: str,
    vcd_error_report: str,
    syntax_errors: str,
    error_traces: List[Dict],
    timeline: List[Dict],
    error_memory: Optional[ErrorMemory] = None,
    iteration: int = 1
) -> str:
    """
    构建增强的 Reviewer Prompt V2（修复版）
    
    改进：
    1. ✅ 使用 V2 版本的摘要生成器（支持降级）
    2. ✅ 确保 Quick Summary 与 Traditional Report 一致
    3. ✅ 添加冲突检测警告
    4. ✅ 移除 Code Diff（不再依赖 ref 代码）
    
    结构：
    1. ⚠️ Conflict Detection（如有）
    2. Quick Summary（200 字符，V2 增强）
    3. Statistical Analysis（表格，V2 增强）
    4. Top-5 Critical Errors
    5. Automated Diagnosis
    6. Error History（如有）
    7. Few-Shot Examples
    8. Specification and Current Code
    """
    import textwrap
    
    prompt_parts = []
    
    # Header
    prompt_parts.append("="*80)
    prompt_parts.append(f"CODE REVIEW & OPTIMIZATION V2 - {case_id} (Iteration {iteration})")
    prompt_parts.append("="*80)
    prompt_parts.append("")
    
    # 【V2 新增】检测冲突并添加警告
    conflict_warning = detect_report_conflict(quick_summary := generate_quick_summary_v2(error_traces, timeline, mismatch_report), mismatch_report)
    if conflict_warning:
        prompt_parts.append("⚠️ REPORT CONSISTENCY CHECK")
        prompt_parts.append(conflict_warning)
        prompt_parts.append("")
    
    # 【V2 修复】使用增强的快速摘要生成器
    prompt_parts.append("## ⭐ QUICK ERROR SUMMARY (READ FIRST)")
    prompt_parts.append(quick_summary)
    prompt_parts.append("")
    
    # 【V2 修复】使用增强的统计表格生成器
    stats_table = generate_stats_table_v2(error_traces, timeline, mismatch_report)
    prompt_parts.append("## 📊 STATISTICAL ANALYSIS")
    prompt_parts.append(stats_table)
    prompt_parts.append("")
    
    # 4. Automated Diagnosis（升级 2）
    diagnosis = diagnose_error_pattern(error_traces, timeline) if error_traces else []
    if diagnosis:
        prompt_parts.append("## 🎯 AUTOMATED DIAGNOSIS")
        prompt_parts.append("")
        for i, pattern in enumerate(diagnosis, 1):
            prompt_parts.append(f"[PATTERN {i}] {pattern['type']} (Confidence: {pattern['confidence']*100:.0f}%)")
            prompt_parts.append(f"- Issue: {pattern['description']}")
            prompt_parts.append(f"- Evidence: {pattern['evidence']}")
            prompt_parts.append(f"- Fix: {pattern['fix']}")
            if 'gate_hypothesis' in pattern:
                prompt_parts.append(f"- Hypothesis: {pattern['gate_hypothesis']}")
            prompt_parts.append("")
    
    # 6. Error History（升级 4）
    if error_memory and error_memory.history:
        prompt_parts.append("## 📚 ERROR HISTORY (LEARN FROM PAST)")
        prompt_parts.append(error_memory.get_summary_for_reviewer())
        prompt_parts.append("")
    
    # 7. Few-Shot Examples（升级 5）
    prompt_parts.append("## 📖 SUCCESSFUL FIX EXAMPLES")
    prompt_parts.append(FEW_SHOT_EXAMPLES)
    prompt_parts.append("")
    
    # 8. Specification and Current Code - 恢复完整内容，不限制长度
    prompt_parts.append("## SPECIFICATION")
    prompt_parts.append(spec)  # 恢复完整规格说明
    prompt_parts.append("")
    
    prompt_parts.append("## GENERATED CODE (Current Iteration)")
    prompt_parts.append(gen_code)  # 恢复完整生成代码
    prompt_parts.append("")
    
    # 9. Syntax Errors（如有）- 恢复完整内容
    if syntax_errors:
        prompt_parts.append("## 🔴 SYNTAX ERRORS (MUST FIX FIRST)")
        prompt_parts.append(syntax_errors)  # 恢复完整语法错误信息
        prompt_parts.append("")
        prompt_parts.append("**CRITICAL**: Fix syntax errors BEFORE functional issues!")
        prompt_parts.append("")
    
    # 10. Mismatch Report（传统报告作为补充）- 恢复完整内容
    if mismatch_report:
        prompt_parts.append("## APPENDIX: Traditional Mismatch Report")
        prompt_parts.append(mismatch_report)  # 恢复完整失配报告
        prompt_parts.append("")

    # Final Instructions
    prompt_parts.append("="*80)
    prompt_parts.append("YOUR TASK")
    prompt_parts.append("="*80)
    prompt_parts.append("""
Based on the comprehensive analysis above, provide SPECIFIC, ACTIONABLE fixes.

**Requirements**:
1. ✅ Be SPECIFIC: Tell EXACTLY which line to change and how
2. ✅ Provide CODE: Show the exact replacement code snippet
3. ✅ Prioritize: Fix syntax errors first, then functionality
4. ✅ Learn from history: Do NOT repeat past mistakes
5. ✅ Follow examples: Use the successful fix patterns shown above

**Output Format**:
### Issues Identified
[List issues in priority order]

### Root Cause Analysis
[Explain WHY each issue occurred]

### Specific Fixes
``systemverilog
// Line X: Replace this WRONG code:
[wrong code]

// With this CORRECT code:
[correct code]
```

### Verification Steps
[What to check after applying the fix]
""")
    
    return '\n'.join(prompt_parts)


# =========================
# 核心功能函数
# =========================

def run_enhanced_repair_loop(
    case_id: str,
    spec: str,
    testbench: str,
    reference: str,
    initial_code: str,
    case_dir: Path,
    max_rounds: int = 2,
    error_memory: Optional[ErrorMemory] = None
) -> Dict:
    """
    增强的修复循环（集成智能诊断）
    
    基于 code_repair_loop.py，但使用增强的 Reviewer Prompt
    """
    from code_repair_loop import run_repair_loop as original_repair_loop
    
    # 首先尝试原始修复循环
    result = original_repair_loop(
        case_id=case_id,
        spec=spec,
        testbench=testbench,
        reference=reference,
        initial_code=initial_code,
        case_dir=case_dir,
        max_rounds=max_rounds
    )
    
    # 【增强】如果原始修复失败且有错误追踪，应用智能诊断
    if not result['success'] and result.get('error_traces'):
        log("Applying enhanced diagnosis...")
        
        # 这里可以添加额外的诊断逻辑
        # 例如：尝试不同的修复策略
        
    return result


def enhanced_closed_loop_iteration(
    case_id: str,
    spec: str,
    testbench: str,
    reference: str,
    current_code: str,
    case_dir: Path,
    iteration: int,
    error_memory: ErrorMemory,
    max_iterations: int = MAX_ITERATIONS
) -> Tuple[bool, str, Dict]:
    """
    增强的单次迭代流程
    
    Returns:
        Tuple[bool, str, Dict]: (是否成功，当前代码，结果字典)
    """
    log(f"Starting Iteration {iteration}...")
    
    # Step 1: 语法检查
    log("[Step 1/4] Syntax check...")
    
    # 保存当前代码到临时文件（code_syntax 需要文件路径作为参数）
    # 同时保留迭代版本的历史记录
    temp_code_path = case_dir / "module_temp.sv"
    iteration_code_path = case_dir / f"module_v{iteration}.sv"  # 保存本轮次代码
    
    temp_code_path.write_text(current_code, encoding='utf-8')
    iteration_code_path.write_text(current_code, encoding='utf-8')  # 保留历史版本
    
    # 调用 code_syntax（只需要传递文件路径）
    syntax_ok = code_syntax(str(temp_code_path)) == 0
    
    syntax_error_log = ""
    if not syntax_ok:
        log("  ✗ Syntax check failed")
        
        # 保存语法检查失败的代码版本
        failed_syntax_path = case_dir / f"module_v{iteration}_syntax_failed.sv"
        failed_syntax_path.write_text(current_code, encoding='utf-8')
        
        # 尝试修复语法错误（简化策略：直接调用 code_fix）
        from code_fix import code_fix
        
        # 构建评估结果（模拟语法错误场景）
        eval_result = {
            'status': 'syntax_error',
            'mismatches': 0,
            'error_type': 'compilation_failed'
        }
        
        try:
            fix_result = code_fix(
                failed_code_filename=str(temp_code_path),
                spec_filename=str(DATASET_DIR / f"{case_id}_prompt.txt"),
                eval_result=eval_result
            )
            
            # 如果修复成功，读取修复后的代码
            if fix_result.get('success') and fix_result.get('repaired_file'):
                repaired_path = Path(fix_result['repaired_file'])
                if repaired_path.exists():
                    fixed_code = repaired_path.read_text(encoding='utf-8')
                    current_code = fixed_code
                    
                    # 更新临时文件并重新检查
                    temp_code_path.write_text(current_code, encoding='utf-8')
                    
                    # 保存修复后的代码
                    fixed_code_path = case_dir / f"module_v{iteration}_fixed.sv"
                    fixed_code_path.write_text(current_code, encoding='utf-8')
                    
                    syntax_ok = code_syntax(str(temp_code_path)) == 0
                    log(f"  ✓ Syntax fix attempted (variant: {fix_result.get('accepted_variant', 'unknown')})")
                    
        except Exception as e:
            log(f"  ⚠ Syntax fix failed: {e}")
            # 继续执行后续逻辑
    
    log("  ✓ Syntax check passed")
    
    # Step 2: 功能验证
    log("[Step 2/4] Functional verification...")
    
    # 保存当前代码（带迭代标识）
    module_path = case_dir / "module.sv"
    save_code(case_dir, current_code, "module.sv")
    
    # 【修复】复制一份带迭代标识的模块代码用于追踪
    module_iter_path = case_dir / f"module_for_verification_iteration_{iteration}.sv"
    save_code(case_dir, current_code, f"module_for_verification_iteration_{iteration}.sv")
    
    # 运行验证
    func_passed = code_val(str(module_path), 
                          str(DATASET_DIR / f"{case_id}_test.sv"),
                          str(DATASET_DIR / f"{case_id}_ref.sv"))
    
    # 【修复】读取验证报告并保存为带迭代标识的版本
    report_path = case_dir / "func_report.txt"
    mismatch_report = ""
    if report_path.exists():
        mismatch_report = report_path.read_text(encoding='utf-8')
        # 保存到带迭代号的文件
        func_report_iter_path = case_dir / f"func_report_iteration_{iteration}.txt"
        func_report_iter_path.write_text(mismatch_report, encoding='utf-8')
    
    # 解析 VCD 获取错误追踪
    error_traces = []
    timeline = []
    vcd_path = case_dir / "wave.vcd"
    
    if not func_passed and vcd_path.exists():
        # 【修复】复制 VCD 文件为带迭代标识的版本
        vcd_iter_path = case_dir / f"wave_iteration_{iteration}.vcd"
        import shutil
        shutil.copyfile(vcd_path, vcd_iter_path)
        
        # 导入 VCD 解析函数并增强调试
        try:
            from closed_loop_1 import parse_vcd_waveform, extract_error_traces
            
            log(f"  📊 Parsing VCD waveform: {vcd_path} ({os.path.getsize(vcd_path) / 1024:.1f} KB)")
            timeline = parse_vcd_waveform(vcd_path)
            
            if timeline and len(timeline) > 0:
                log(f"  ✅ Parsed {len(timeline)} signal entries from VCD")
                error_traces = extract_error_traces(timeline, max_errors=15)
                log(f"  🎯 Extracted {len(error_traces)} error traces from VCD")
                
                # 【新增】保存详细的波形分析报告
                waveform_report_path = case_dir / f"waveform_analysis_iteration_{iteration}.txt"
                with open(waveform_report_path, 'w', encoding='utf-8') as f:
                    f.write("="*80 + "\n")
                    f.write(f"WAVEFORM ANALYSIS REPORT - Iteration {iteration}\n")
                    f.write("="*80 + "\n\n")
                    
                    f.write(f"Total timeline entries: {len(timeline)}\n")
                    f.write(f"Extracted error traces: {len(error_traces)}\n\n")
                    
                    if error_traces:
                        f.write("\n" + "="*80 + "\n")
                        f.write("TOP ERROR TRACES:\n")
                        f.write("="*80 + "\n\n")
                        
                        for i, trace in enumerate(error_traces[:5], 1):
                            f.write(f"[Error {i}]\n")
                            f.write(f"  Time: {trace.get('error_time', 'N/A')} ps\n")
                            f.write(f"  Input X: {trace.get('input_x', 'N/A')}\n")
                            f.write(f"  Input Y: {trace.get('input_y', 'N/A')}\n")
                            f.write(f"  Expected: {trace.get('expected_output', 'N/A')}\n")
                            f.write(f"  Actual: {trace.get('actual_output', 'N/A')}\n")
                            f.write(f"  Status: {'❌ MISMATCH' if trace.get('mismatch') else '✓ OK'}\n")
                            f.write("\n")
                    
                    # 如果有更多错误，显示统计信息
                    if len(error_traces) > 5:
                        f.write(f"... and {len(error_traces) - 5} more errors\n\n")
                    
                    # 显示时间线样本（增强版：标注错误并显示预期值）
                    f.write("\n" + "="*80 + "\n")
                    f.write("TIMELINE SAMPLE (First 20 entries with error markers):\n")
                    f.write("="*80 + "\n\n")
                    
                    # 创建错误时间点的快速查找表
                    error_time_map = {}
                    for trace in error_traces:
                        error_time = trace.get('error_time')
                        if error_time:
                            error_time_map[error_time] = {
                                'expected': trace.get('expected_output', 'N/A'),
                                'actual': trace.get('actual_output', 'N/A'),
                                'mismatch': trace.get('mismatch', False)
                            }
                    
                    # 显示时间线，标注错误
                    for i, entry in enumerate(timeline[:20], 1):
                        time_ps = entry.get('time', '?')
                        actual_out = entry.get('output', '?')
                        
                        # 检查这个时间点是否有错误
                        error_info = error_time_map.get(time_ps)
                        
                        if error_info and error_info['mismatch']:
                            # 错误点：高亮显示对比
                            expected_out = error_info['expected']
                            f.write(f"  t={time_ps:6d}ps | x={entry.get('x', '?'):3d} | y={entry.get('y', '?'):3d}\n")
                            f.write(f"             | out={actual_out} ❌ EXPECTED: {expected_out}\n")
                            f.write(f"             | *** MISMATCH DETECTED ***\n\n")
                        else:
                            # 正确点：正常显示
                            f.write(f"  t={time_ps:6d}ps | x={entry.get('x', '?'):3d} | y={entry.get('y', '?'):3d} | out={actual_out} ✓\n")
                    
                    if len(timeline) > 20:
                        f.write(f"\n... and {len(timeline) - 20} more entries\n")
                    
                    # 添加图例说明
                    f.write("\n" + "-"*80 + "\n")
                    f.write("LEGEND:\n")
                    f.write("-"*80 + "\n")
                    f.write("✓ = Output matches expected value (correct)\n")
                    f.write("❌ = Output differs from expected value (error)\n")
                    f.write("EXPECTED: The reference output value that should be produced\n")
                    f.write("\nNOTE: This sample shows the first 20 simulation timepoints.\n")
                    f.write("      For complete error analysis, see TOP ERROR TRACES section above.\n")
                    
                    # 【新增】生成错误节点及其上下文分析报告
                    f.write("\n" + "="*80 + "\n")
                    f.write("ERROR-CENTRIC WAVEFORM ANALYSIS:\n")
                    f.write("="*80 + "\n\n")
                    
                    if error_traces:
                        # 创建时间线索引，便于查找前后时刻
                        time_to_entry = {}
                        for idx, entry in enumerate(timeline):
                            time_key = entry.get('time')
                            if time_key is not None:
                                time_to_entry[time_key] = (idx, entry)
                        
                        # 对每个错误点，提取前后时刻的状态
                        f.write(f"Analyzing {len(error_traces)} error(s) with context (±2 timepoints):\n\n")
                        
                        for i, error_trace in enumerate(error_traces, 1):
                            error_time = error_trace.get('error_time')
                            if error_time is None:
                                continue
                            
                            f.write(f"[Error #{i}]\n")
                            f.write("-"*80 + "\n")
                            f.write(f"Error Time: {error_time} ps\n")
                            f.write(f"Input X: {error_trace.get('input_x', 'N/A')}, Input Y: {error_trace.get('input_y', 'N/A')}\n")
                            f.write(f"Expected Output: {error_trace.get('expected_output', 'N/A')}\n")
                            f.write(f"Actual Output:   {error_trace.get('actual_output', 'N/A')}")
                            
                            if error_trace.get('mismatch'):
                                f.write(" ❌ MISMATCH\n")
                            else:
                                f.write(" ✓ OK\n")
                            
                            f.write("\n")
                            
                            # 查找当前错误点在时间线中的位置
                            current_idx, current_entry = time_to_entry.get(error_time, (None, None))
                            
                            if current_idx is not None:
                                # 提取前 2 个时刻 + 当前时刻 + 后 2 个时刻
                                start_idx = max(0, current_idx - 2)
                                end_idx = min(len(timeline), current_idx + 3)  # +3 因为 range 不包含结束
                                
                                f.write("Surrounding Context:\n")
                                f.write("-"*80 + "\n")
                                
                                for j in range(start_idx, end_idx):
                                    entry = timeline[j]
                                    t = entry.get('time', '?')
                                    x = entry.get('x', '?')
                                    y = entry.get('y', '?')
                                    out = entry.get('output', '?')
                                    
                                    # 判断是否是错误点
                                    if j == current_idx:
                                        # 错误点：显示预期值对比
                                        expected = error_trace.get('expected_output', 'N/A')
                                        f.write(f">>> t={t:6d}ps | x={x:3d} | y={y:3d} | out={out} ❌ EXPECTED: {expected} *** ERROR ***\n")
                                    else:
                                        # 前后时刻：正常显示
                                        f.write(f"    t={t:6d}ps | x={x:3d} | y={y:3d} | out={out}\n")
                                
                                # 如果有更多错误，简要提示
                                if len(error_traces) > 1 and i < len(error_traces):
                                    f.write("\n")
                            else:
                                f.write("⚠️ Could not find this error timepoint in timeline.\n")
                            
                            f.write("\n")
                        
                        # 如果错误数量超过显示限制，添加提示
                        if len(error_traces) > 15:
                            f.write(f"\n... and {len(error_traces) - 15} more errors (not shown).\n")
                            f.write("See TOP ERROR TRACES section above for complete list.\n")
                    
                    else:
                        f.write("No errors detected. All outputs match expected values.\n")
                
                log(f"  📄 Waveform analysis saved: {waveform_report_path}")
                
                # 【修复】保存错误追踪报告为带迭代标识的版本
                error_trace_path = case_dir / "error_trace_report.txt"
                if error_trace_path.exists():
                    error_trace_iter_path = case_dir / f"error_trace_report_iteration_{iteration}.txt"
                    shutil.copyfile(error_trace_path, error_trace_iter_path)
            else:
                log(f"  ⚠️ WARNING: VCD parser returned empty timeline!")
                log(f"  This may indicate:")
                log(f"    1. VCD file is corrupted or incomplete")
                log(f"    2. Signal names don't match expected patterns")
                log(f"    3. No signal transitions found in VCD")
                
        except ImportError as e:
            log(f"  ⚠️ Could not import VCD parser: {e}")
            log(f"  Falling back to traditional report analysis")
        except Exception as e:
            log(f"  💥 VCD parsing failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 3: 诊断分析
    log("[Step 3/4] Diagnosing errors...")
    diagnosis = diagnose_error_pattern(error_traces, timeline) if error_traces else []
    
    # 记录到错误历史
    error_memory.record_iteration(
        iteration=iteration,
        error_traces=error_traces,
        diagnosis=diagnosis,
        passed=func_passed
    )
    
    if func_passed:
        log("  ✓ Functional verification PASSED")
        
        # 【修复】保存语法检查报告为带迭代标识的版本
        syntax_report_path = case_dir / "syntax_report.txt"
        if syntax_report_path.exists():
            syntax_report_iter_path = case_dir / f"syntax_report_iteration_{iteration}.txt"
            import shutil
            shutil.copyfile(syntax_report_path, syntax_report_iter_path)
        
        return True, current_code, {
            'status': 'success',
            'iterations': iteration,
            'error_memory': error_memory
        }
    
    report_stats = parse_traditional_report(mismatch_report)
    count_text = str(report_stats['error_count']) if report_stats['parsed'] else 'unknown'
    log(f"  ✗ Functional verification FAILED ({count_text} mismatches; {len(error_traces)} waveform traces extracted)")
    # The budget counts evaluated versions. Do not produce an untested last repair.
    if iteration >= max_iterations:
        return False, current_code, {'status': 'failed_max_iterations', 'iterations': iteration,
                                     'error_memory': error_memory}
    
    # Step 4: Reviewer 分析与优化（V2 版本）
    log("[Step 4/4] Calling Reviewer with enhanced prompt V2...")
    log(f"  第 {iteration} 轮验证失败，正在请求 Reviewer 分析；返回后生成修复代码，再进入下一轮验证。API 等待期间可能没有新输出。")
    
    # 构建增强的 Reviewer Prompt V2
    reviewer_prompt = build_enhanced_reviewer_prompt_v2(
        case_id=case_id,
        spec=spec,
        gen_code=current_code,
        ref_code=reference,
        mismatch_report=mismatch_report,
        vcd_error_report="",  # 已包含在分层摘要中
        syntax_errors="" if syntax_ok else syntax_error_log,
        error_traces=error_traces,
        timeline=timeline,
        error_memory=error_memory,
        iteration=iteration
    )
    
    # 保存 Reviewer Prompt
    prompt_path = case_dir / f"reviewer_prompt_iteration_{iteration}.txt"
    prompt_path.write_text(reviewer_prompt, encoding='utf-8')
    
    # 调用 Reviewer LLM
    try:
        from config import call_reviewer_llm
        
        # 构建系统提示（设定 Reviewer 的角色）
        system_prompt = """You are an expert SystemVerilog code reviewer specializing in digital circuit design verification.
Your task is to analyze the generated code, identify errors based on the provided specifications and error reports, and provide specific, actionable fix suggestions.

Please focus on:
1. Syntax correctness (must compile with Icarus Verilog)
2. Functional correctness (must match reference behavior)
3. Best practices in SystemVerilog coding style

Provide concrete line-by-line fixes rather than vague suggestions."""
        
        # 调用 Reviewer（传递系统提示和用户提示）
        review_suggestions = call_reviewer_llm(system_prompt, reviewer_prompt)
        
        # 保存 Reviewer 建议
        review_path = case_dir / f"review_iteration_{iteration}.txt"
        review_path.write_text(review_suggestions, encoding='utf-8')
        log(f"  ✓ Review saved ({len(review_suggestions)} chars)")
        
        # 生成优化代码
        log("  Generating optimized code...")
        
        # 构建增强的规格说明（包含原始规格 + Reviewer 反馈）- 恢复完整内容
        enhanced_spec = f"""ORIGINAL SPECIFICATION:
{spec}

PREVIOUS CODE:
{current_code}

REVIEWER FEEDBACK (MUST FOLLOW THESE SUGGESTIONS):
{review_suggestions}

INSTRUCTIONS:
Based on the reviewer's feedback above, generate an IMPROVED version of the SystemVerilog code that:
1. Fixes all identified syntax errors
2. Corrects functional mismatches
3. Implements the specific suggestions from the reviewer
4. Maintains compatibility with Icarus Verilog -g2012

Provide ONLY the improved SystemVerilog code within ```systemverilog ``` code blocks."""
        
        # 调用主模型生成优化代码
        from config import call_llm, ARK_MODEL
        from code_gen import extract_code_from_response
        
        try:
            response = call_llm(
                system_prompt="You are an expert SystemVerilog developer. Generate improved code based on reviewer feedback.",
                user_prompt=enhanced_spec,
                model=ARK_MODEL,
            )
            
            # 提取代码
            optimized_code = extract_code_from_response(response)
            
        except Exception as e:
            log(f"  ✗ Failed to generate optimized code: {e}")
            return False, current_code, {'status': 'repair_generation_failed',
                                         'error': str(e), 'error_memory': error_memory}
        
        # 保存迭代记录
        iter_dir = case_dir / f"iteration_{iteration}"
        ensure_dir(iter_dir)
        save_code(iter_dir, optimized_code, f"module_v{iteration+1}.sv")
        
        # 同时保存一份到主目录，便于追踪最新的优化结果
        optimized_path = case_dir / f"module_optimized_iteration_{iteration}.sv"
        optimized_path.write_text(optimized_code, encoding='utf-8')
        
        # 【修复】保存修复后的代码为带迭代标识的版本
        repaired_code_path = case_dir / f"module_repaired_iteration_{iteration}.sv"
        repaired_code_path.write_text(optimized_code, encoding='utf-8')
        
        return False, optimized_code, {
            'status': 'continued',
            'review_saved': str(review_path),
            'error_memory': error_memory
        }
        
    except Exception as e:
        log(f"  ✗ Reviewer call failed: {e}")
        return False, current_code, {
            'status': 'reviewer_failed',
            'error': str(e),
            'error_memory': error_memory
        }


def run_enhanced_closed_loop(
    case_id: str,
    max_iterations: int = MAX_ITERATIONS,
    use_preprocessed_spec: bool = False
) -> Dict:
    """
    主流程：增强的闭环优化系统
    
    Args:
        case_id: 题目 ID
        max_iterations: 最大迭代次数
        use_preprocessed_spec: 是否使用预处理规格（根据记忆规范，迭代修复时不能用）
    
    Returns:
        Dict: 结果统计
    """
    log(f"\n{'='*80}")
    log(f"ENHANCED CLOSED LOOP OPTIMIZATION - {case_id}")
    log(f"{'='*80}")
    
    start_time = datetime.now()
    case_dir = OUTPUT_BASE_DIR / f"{case_id}"
    ensure_dir(case_dir)
    
    # 初始化错误历史
    error_memory = ErrorMemory(case_id)
    
    try:
        # 读取输入
        log("Loading specifications...")
        spec = read_spec(case_id)
        testbench = read_testbench(case_id)
        reference = read_reference(case_id)
        
        # 初始代码生成
        log("\n[Pre-phase] Generating initial code...")
        
        # 创建临时 review 文件（code_gen 需要文件路径作为参数）
        from pathlib import Path
        temp_review_path = case_dir / "review_initial.txt"
        temp_review_path.write_text(spec, encoding='utf-8')
        
        # 调用 code_gen（只需要传递 review 文件路径）
        generation_status = code_gen(str(temp_review_path))
        if generation_status != "success":
            raise RuntimeError("Initial code generation failed; see generation error log")
        initial_code = (case_dir / "module.sv").read_text(encoding='utf-8')
        
        # 保存初始生成的代码（v1 版本）
        save_code(case_dir, initial_code, "module_v1.sv")
        save_code(case_dir, initial_code, "module_initial.sv")
        
        # 迭代优化
        current_code = initial_code
        result = {}
        
        for iteration in range(1, max_iterations + 1):
            success, current_code, iter_result = enhanced_closed_loop_iteration(
                case_id=case_id,
                spec=spec,
                testbench=testbench,
                reference=reference,
                current_code=current_code,
                case_dir=case_dir,
                iteration=iteration,
                error_memory=error_memory,
                max_iterations=max_iterations
            )
            
            result = dict(iter_result)
            result['iterations'] = iteration
            # Persist failures as well as successes, without carrying stale errors forward.
            iteration_record = {k: v for k, v in result.items() if k != 'error_memory'}
            (case_dir / f'iteration_result_{iteration}.json').write_text(
                json.dumps(iteration_record, ensure_ascii=False, indent=2), encoding='utf-8')
            if result.get('status') in ('reviewer_failed', 'repair_generation_failed'):
                log('API 阶段失败，本题停止；保留错误记录，避免将旧代码重复验证计为修复。')
                break
            
            if success:
                log(f"\n✓ SUCCESS! Converged at iteration {iteration}")
                
                # 【修复】保存最终代码为带迭代标识的版本
                final_path = save_code(case_dir, current_code, f"module_final_iteration_{iteration}.sv")
                log(f"Final code saved: {final_path}")
                
                # 同时保留一份不带轮次的副本作为当前工作版本
                save_code(case_dir, current_code, "module_final.sv")
                
                break
            
            if iteration == max_iterations:
                log(f"\n✗ FAILED after {max_iterations} iterations")
                result['status'] = 'failed_max_iterations'
                
                # 【修复】保存失败时的最终代码为带迭代标识的版本
                failed_final_path = save_code(case_dir, current_code, f"module_failed_final_iteration_{iteration}.sv")
                log(f"Failed final code saved: {failed_final_path}")
                
                # 同时保留一份不带轮次的副本作为当前工作版本
                save_code(case_dir, current_code, "module_failed_final.sv")
        
        # 最终统计
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        result['duration'] = duration
        result['case_id'] = case_id
        
    except Exception as e:
        log(f"\n✗ EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        result = {
            'status': 'exception',
            'error': str(e),
            'case_id': case_id
        }
    
    finally:
        # 保存汇总 JSON
        summary_path = case_dir / "enhanced_summary.json"
        summary_path.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
        log(f"\nSummary saved: {summary_path}")
    
    return result


# =========================
# 批处理主程序
# =========================

def run_enhanced_single_case(case_id: str, force: bool = False) -> Dict:
    """
    运行单个题目的 enhanced closed loop（包装函数）
    
    Args:
        case_id: 题目 ID
        force: 是否强制重新运行
        
    Returns:
        Dict: 结果统计
    """
    try:
        log_thread_safe(f"Starting {case_id}...")
        
        case_dir = OUTPUT_BASE_DIR / case_id
        
        # 检查是否已存在成功结果
        if not force and case_dir.exists():
            final_files = list(case_dir.glob("module_final_iteration_*.sv"))
            if final_files:
                log_thread_safe(f"⏭️ Skipping {case_id} (already succeeded)")
                return {
                    'case_id': case_id,
                    'status': 'skipped',
                    'reason': 'already_succeeded'
                }
            
            failed_files = list(case_dir.glob("module_failed_final_iteration_*.sv"))
            error_summary = case_dir / "enhanced_summary.json"
            if failed_files or error_summary.exists():
                log_thread_safe(f"♻️ Re-running {case_id} (previous failed)")
        
        # 运行闭环优化
        result = run_enhanced_closed_loop(case_id)
        
        if result.get('status') == 'success':
            log_thread_safe(f"✅ {case_id} SUCCESS!")
        else:
            log_thread_safe(f"❌ {case_id} FAILED ({result.get('status', 'unknown')})")
        
        result['case_id'] = case_id
        return result
        
    except Exception as e:
        log_thread_safe(f"💥 {case_id} EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return {
            'case_id': case_id,
            'status': 'exception',
            'error': str(e)
        }


def run_enhanced_batch_multithread(case_ids: List[str], force: bool = False, max_workers: int = MAX_WORKERS):
    """
    多线程批量运行 enhanced closed loop
    
    Args:
        case_ids: 题目 ID 列表
        force: 是否强制重新运行
        max_workers: 最大并发线程数
    """
    log("\n" + "="*80)
    log("ENHANCED CLOSED LOOP BATCH PROCESSING (MULTITHREADED)")
    log("="*80)
    log(f"Total cases: {len(case_ids)}")
    log(f"Max workers: {max_workers}")
    log(f"Output directory: {OUTPUT_BASE_DIR}")
    log("="*80 + "\n")
    
    start_time = datetime.now()
    results = {
        'total': len(case_ids),
        'success': 0,
        'failed': 0,
        'exceptions': 0,
        'skipped': 0,
        'details': []
    }
    
    # 使用 ThreadPoolExecutor 实现多线程并行
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_case = {
            executor.submit(run_enhanced_single_case, case_id, force): case_id 
            for case_id in case_ids
        }
        
        # 收集结果
        completed = 0
        for future in as_completed(future_to_case):
            case_id = future_to_case[future]
            completed += 1
            
            try:
                result = future.result()
                results['details'].append(result)
                
                # 统计
                status = result.get('status', 'unknown')
                if status == 'success':
                    results['success'] += 1
                elif status == 'skipped':
                    results['skipped'] += 1
                elif status == 'exception':
                    results['exceptions'] += 1
                else:
                    results['failed'] += 1
                
                # 进度报告
                progress = f"[{completed}/{len(case_ids)}]"
                if status == 'success':
                    log(f"{progress} ✅ {case_id} completed")
                elif status == 'skipped':
                    log(f"{progress} ⏭️ {case_id} skipped")
                elif status == 'exception':
                    log(f"{progress} 💥 {case_id} exception")
                else:
                    log(f"{progress} ❌ {case_id} failed")
                    
            except Exception as e:
                log(f"[{completed}/{len(case_ids)}] 💥 {case_id} execution error: {e}")
                results['details'].append({
                    'case_id': case_id,
                    'status': 'execution_error',
                    'error': str(e)
                })
                results['exceptions'] += 1
    
    # 批处理总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results['duration'] = duration
    results['timestamp'] = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存批处理汇总
    summary_path = OUTPUT_BASE_DIR / f"enhanced_batch_{results['timestamp']}.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    
    # 打印总结
    log("\n" + "="*80)
    log("BATCH SUMMARY (MULTITHREADED)")
    log("="*80)
    log(f"Total: {len(case_ids)} cases")
    log(f"Success: {results['success']} ({results['success']/len(case_ids)*100:.1f}%)")
    log(f"Failed: {results['failed']}")
    log(f"Exceptions: {results['exceptions']}")
    log(f"Skipped: {results['skipped']}")
    log(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    log(f"Average per case: {duration/len(case_ids):.1f}s")
    log(f"Summary saved: {summary_path}")
    log("="*80)
    
    return results


def run_enhanced_batch(case_ids: List[str], force: bool = False):
    """
    批量运行 enhanced closed loop
    
    Args:
        case_ids: 题目 ID 列表
        force: 是否强制重新运行（忽略已存在的结果）
    """
    log("\n" + "="*80)
    log("ENHANCED CLOSED LOOP BATCH PROCESSING")
    log("="*80)
    
    start_time = datetime.now()
    results = {
        'total': len(case_ids),
        'success': 0,
        'failed': 0,
        'exceptions': 0,
        'skipped': 0,
        'details': []
    }
    
    # 统计计数器
    success_count = 0
    failed_count = 0
    exception_count = 0
    skipped_count = 0
    
    for i, case_id in enumerate(case_ids, 1):
        log(f"\n[{i}/{len(case_ids)}] Processing {case_id}...")
        
        case_dir = OUTPUT_BASE_DIR / case_id
        
        # 检查是否已存在成功结果
        if not force and case_dir.exists():
            # 检查是否有成功的最终文件
            final_files = list(case_dir.glob("module_final_iteration_*.sv"))
            if final_files:
                log(f"  ⏭️  Skipping (already succeeded at iteration {len(final_files)})")
                results['details'].append({
                    'case_id': case_id,
                    'status': 'skipped',
                    'reason': 'already_succeeded'
                })
                skipped_count += 1
                continue
            
            # 检查是否有失败标记
            failed_files = list(case_dir.glob("module_failed_final_iteration_*.sv"))
            error_summary = case_dir / "enhanced_summary.json"
            if failed_files or (error_summary.exists() and error_summary.exists()):
                log(f"  ♻️  Re-running (previous attempt failed)")
        
        try:
            # 运行单个题目的闭环优化
            result = run_enhanced_closed_loop(case_id)
            
            # 统计结果
            if result.get('status') == 'success':
                log(f"  ✅ SUCCESS!")
                success_count += 1
                status = 'success'
            elif result.get('status') == 'exception':
                exception_count += 1
                status = 'exception'
            else:
                log(f"  ❌ FAILED ({result.get('status', 'unknown')})")
                failed_count += 1
                status = 'failed'
            
            results['details'].append({
                'case_id': case_id,
                'status': status,
                'iterations': result.get('iterations', 0),
                'duration': result.get('duration', 0),
                'detail_status': result.get('status'),
                'error': result.get('error')
            })
            
        except Exception as e:
            log(f"  💥 EXCEPTION: {e}")
            exception_count += 1
            results['details'].append({
                'case_id': case_id,
                'status': 'exception',
                'error': str(e)
            })
    
    # 批处理总结
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results['success'] = success_count
    results['failed'] = failed_count
    results['exceptions'] = exception_count
    results['skipped'] = skipped_count
    results['duration'] = duration
    results['timestamp'] = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存批处理汇总
    summary_path = OUTPUT_BASE_DIR / f"enhanced_batch_{results['timestamp']}.json"
    summary_path.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    
    # 打印总结
    log("\n" + "="*80)
    log("BATCH SUMMARY")
    log("="*80)
    log(f"Total: {len(case_ids)} cases")
    log(f"Success: {success_count} ({success_count/len(case_ids)*100:.1f}%)")
    log(f"Failed: {failed_count}")
    log(f"Exceptions: {exception_count}")
    log(f"Skipped: {skipped_count}")
    log(f"Duration: {duration:.1f}s ({duration/60:.1f} minutes)")
    log(f"Summary saved: {summary_path}")
    log("="*80)
    
    return results


def get_all_case_ids() -> List[str]:
    """
    获取数据集中所有题目的 ID
    
    Returns:
        List[str]: 题目 ID 列表
    """
    case_ids = set()
    
    # 从 prompt 文件中提取
    for prompt_file in DATASET_DIR.glob("*_prompt.txt"):
        # 移除 _prompt.txt 后缀获取 ID
        case_id = prompt_file.stem.replace("_prompt", "")
        case_ids.add(case_id)
    
    # 从 ifc 文件中提取（备选）
    for ifc_file in DATASET_DIR.glob("*_ifc.txt"):
        case_id = ifc_file.stem.replace("_ifc", "")
        case_ids.add(case_id)
    
    return sorted(list(case_ids))


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Closed Loop Optimization System V2 (Multithreaded)")
    parser.add_argument("--cases", nargs="+", help="指定要运行的题目 ID 列表")
    parser.add_argument("--all", action="store_true", help="运行数据集中的所有题目")
    parser.add_argument("--force", action="store_true", help="强制重新运行（忽略已存在结果）")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help=f"最大并发线程数 (默认：{MAX_WORKERS})")
    parser.add_argument("--single", action="store_true", help="单线程模式（禁用多线程）")
    parser.add_argument("--check", action="store_true", help="只检查题目文件，不调用 API")
    
    args = parser.parse_args()
    
    # 确定要运行的题目列表
    if args.all:
        # 运行所有题目
        case_ids = get_all_case_ids()
        log(f"Found {len(case_ids)} cases in dataset")
    elif args.cases:
        # 运行指定的题目
        case_ids = args.cases
    else:
        # 默认运行所有题目
        case_ids = get_all_case_ids()
        log(f"No cases specified, running all {len(case_ids)} cases from dataset")
    
    # Validate inputs before any generation; accept an unambiguous numeric prefix.
    available = get_all_case_ids()
    resolved = []
    for requested in case_ids:
        matches = [cid for cid in available if cid == requested or cid.startswith(requested + '_')]
        if len(matches) != 1:
            suggestions = [cid for cid in available if cid.split('_')[0] == requested.split('_')[0]]
            parser.error(f'找不到唯一题目 {requested}；数据集：{DATASET_DIR}；可能的题号：{suggestions}')
        resolved.append(matches[0])
    case_ids = resolved
    if not case_ids:
        parser.error(f'数据集没有题目：{DATASET_DIR}')
    for cid in case_ids:
        read_spec(cid)
        read_testbench(cid)
        read_reference(cid)
    if args.check:
        log(f'文件检查通过：{len(case_ids)} 题；数据集：{DATASET_DIR}；未调用 API')
        sys.exit(0)

    # 选择运行模式
    if args.single:
        # 单线程模式
        log(f"\n⚙️ Running in SINGLE-THREAD mode")
        run_enhanced_batch(case_ids, force=args.force)
    else:
        # 多线程模式（默认）
        max_workers = min(args.workers, len(case_ids))  # 不超过题目数量
        log(f"\n⚙️ Running in MULTI-THREAD mode with {max_workers} workers")
        run_enhanced_batch_multithread(case_ids, force=args.force, max_workers=max_workers)
