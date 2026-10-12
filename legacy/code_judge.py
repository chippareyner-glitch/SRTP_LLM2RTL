# code_judge.py
"""
错误判定模块 (Error Judge)
================================================================================

功能:
根据功能验证的结果，解析 VCD 波形文件，生成详细的错误报告。
包含每个错误点前 2 个时钟周期的完整状态信息。

输入:
- vcd_filename: VCD 波形文件名（如 "wave.vcd"）
- output_filename: 输出报告文件名（可选，默认 "error_trace_report.txt"）

输出:
- 同目录下生成 error_trace_report.txt 文件
- 返回错误追踪列表（空列表表示无错误）

使用示例:
    from code_judge import code_judge
    errors = code_judge("wave.vcd")
    if errors:
        print(f"Found {len(errors)} errors")
    else:
        print("No errors found or VCD parsing failed")
"""

import sys as _sys, pathlib as _pathlib  # legacy/ 下的模块依赖项目根目录的 config 等模块
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
import re
import json
from pathlib import Path
from typing import List, Dict


def parse_vcd_waveform_fast(vcd_path: Path, max_errors: int = 50) -> List[Dict]:
    """
    快速解析 VCD 文件，仅提取前 N 个错误点及其上下文（避免加载整个大文件）
    
    Args:
        vcd_path (Path): VCD 文件路径
        max_errors (int): 最大错误数
        
    Returns:
        List[Dict]: 错误追踪列表（转换为时间线格式）
    """
    if not vcd_path.exists():
        print(f"[code_judge] VCD file not found: {vcd_path}")
        return []
    
    error_traces = []
    current_time = None
    last_values = {'x': 0, 'y': 0, 'z_ref': 0, 'z_dut': 0, 'tb_mismatch': 0}
    recent_states = []  # 保留最近几个状态用于上下文
    
    signal_map = {
        '!': 'clk', 
        '"': 'tb_mismatch', 
        '#': 'x', 
        '$': 'y', 
        '%': 'z_ref', 
        '&': 'z_dut'
    }
    
    print(f"[Fast Parse] Scanning VCD for first {max_errors} errors...")
    
    with open(vcd_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # 匹配时间戳
            time_match = re.match(r'#(\d+)', line)
            if time_match:
                # 保存新时间点前检查是否错误
                if current_time is not None and len(recent_states) > 0:
                    last_state = recent_states[-1]
                    if last_state.get('tb_mismatch') == 1 and len(error_traces) < max_errors:
                        # 发现错误，保存轨迹
                        context = recent_states[-3:] if len(recent_states) >= 3 else recent_states
                        
                        error_trace = {
                            'error_time': last_state['time'],
                            'input_x': last_state.get('x', 0),
                            'input_y': last_state.get('y', 0),
                            'expected_output': last_state.get('z_ref', 0),
                            'actual_output': last_state.get('z_dut', 0),
                            'mismatch': True,
                            'context': context  # context 已经是正确的字典列表
                        }
                        error_traces.append(error_trace)
                
                current_time = int(time_match.group(1))
                # 每 10000 个时间点打印进度
                if current_time % 10000 == 0 and current_time > 0:
                    print(f"   Processed {current_time} ps, found {len(error_traces)} errors so far...")
                continue
            
            # 匹配信号值
            if current_time is not None and line:
                match = re.match(r'(b[01xXzZ]+|[01xXzZ])([!#$%&"])', line)
                if match:
                    value_str, sig = match.groups()
                    name = signal_map.get(sig, sig)
                    
                    if name in ['x', 'y', 'z_ref', 'z_dut', 'tb_mismatch']:
                        # 解析值
                        if value_str.startswith('b'):
                            if any(c in value_str.lower() for c in ['x', 'z']):
                                parsed_value = None
                            else:
                                try:
                                    parsed_value = int(value_str[1:], 2)
                                except:
                                    parsed_value = None
                        else:
                            parsed_value = int(value_str) if value_str in '01' else None
                        
                        if parsed_value is not None:
                            last_values[name] = parsed_value
                        
                        # 如果是 tb_mismatch 且为 1，触发错误记录
                        if name == 'tb_mismatch' and parsed_value == 1:
                            state = {
                                'time': current_time,
                                'x': last_values.get('x', 0),
                                'y': last_values.get('y', 0),
                                'z_ref': last_values.get('z_ref', 0),
                                'z_dut': last_values.get('z_dut', 0),
                                'tb_mismatch': 1
                            }
                            recent_states.append(state)
                            # 保持最近 5 个状态
                            if len(recent_states) > 5:
                                recent_states.pop(0)
            
            # 限制处理的行数，避免超时（前 200 万行）
            if line_num > 2000000:
                print(f"   Reached line limit ({line_num}), stopping early...")
                break
    
    # 处理最后一个时间点
    if len(recent_states) > 0 and len(error_traces) < max_errors:
        last_state = recent_states[-1]
        if last_state.get('tb_mismatch') == 1:
            context = recent_states[-3:] if len(recent_states) >= 3 else recent_states
            error_trace = {
                'error_time': last_state['time'],
                'input_x': last_state.get('x', 0),
                'input_y': last_state.get('y', 0),
                'expected_output': last_state.get('z_ref', 0),
                'actual_output': last_state.get('z_dut', 0),
                'mismatch': True,
                'context': context
            }
            error_traces.append(error_trace)
    
    print(f"   ✅ Found {len(error_traces)} errors in VCD")
    
    # 将错误轨迹转换为时间线格式
    timeline = []
    seen_times = set()
    for trace in error_traces:
        context = trace.get('context', [])
        for ctx_entry in context:
            if ctx_entry['time'] not in seen_times:
                seen_times.add(ctx_entry['time'])
                timeline.append({
                    'time': ctx_entry['time'],
                    'x': ctx_entry.get('x', 0),
                    'y': ctx_entry.get('y', 0),
                    'z_ref': ctx_entry.get('z_ref', 0),
                    'z_dut': ctx_entry.get('z_dut', 0),
                    'tb_mismatch': ctx_entry.get('tb_mismatch', 0)
                })
    
    # 按时间排序
    timeline.sort(key=lambda x: x['time'])
    return timeline


def parse_vcd_waveform(vcd_path: Path) -> List[Dict]:
    """
    解析 VCD 文件，提取时间点信号值（完整版，适用于小文件）
    
    Args:
        vcd_path (Path): VCD 文件路径
        
    Returns:
        List[Dict]: 时间线数据列表
    """
    if not vcd_path.exists():
        print(f"[code_judge] VCD file not found: {vcd_path}")
        return []
    
    # 检查文件大小
    file_size_mb = vcd_path.stat().st_size / (1024 * 1024)
    print(f"[code_judge] Parsing VCD waveform from {vcd_path} ({file_size_mb:.1f} MB)...")
    
    # 如果文件太大，使用快速解析
    if file_size_mb > 10:  # 大于 10MB 使用快速模式
        print(f"   File too large, using fast parsing mode...")
        timeline = parse_vcd_waveform_fast(vcd_path, max_errors=50)
        print(f"   Extracted {len(timeline)} timepoints from fast parse")
        return timeline
    
    timeline = []
    current_time = None
    
    # Icarus Verilog VCD 格式信号映射
    signal_map = {
        '!': 'clk', 
        '"': 'tb_mismatch', 
        '#': 'x', 
        '$': 'y', 
        '%': 'z_ref', 
        '&': 'z_dut'
    }
    
    with open(vcd_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # 匹配时间戳 #<number>
            time_match = re.match(r'#(\d+)', line)
            if time_match:
                current_time = int(time_match.group(1))
                continue
            
            # 匹配信号值变化
            if current_time is not None and line:
                # 支持单比特和多比特值
                match = re.match(r'(b[01xXzZ]+|[01xXzZ])([!#$%&"])', line)
                if match:
                    value_str, sig = match.groups()
                    name = signal_map.get(sig, sig)
                    
                    # 只关心我们需要的信号
                    if name in ['x', 'y', 'z_ref', 'z_dut', 'tb_mismatch']:
                        # 查找或创建当前时间点的条目
                        entry = next((e for e in timeline if e['time'] == current_time), None)
                        if not entry:
                            entry = {
                                'time': current_time, 
                                'x': None, 
                                'y': None, 
                                'z_ref': None, 
                                'z_dut': None, 
                                'tb_mismatch': None
                            }
                            timeline.append(entry)
                        
                        # 处理值：单比特直接转换，多比特转整数
                        if value_str.startswith('b'):
                            if any(c in value_str.lower() for c in ['x', 'z']):
                                parsed_value = None
                            else:
                                try:
                                    parsed_value = int(value_str[1:], 2)
                                except:
                                    parsed_value = None
                        else:
                            parsed_value = int(value_str) if value_str in '01' else None
                        
                        entry[name] = parsed_value
    
    # 填充缺失值（使用前向填充）
    last = {'x': 0, 'y': 0, 'z_ref': 0, 'z_dut': 0, 'tb_mismatch': 0}
    filled = []
    for entry in timeline:
        row = {'time': entry['time']}
        for sig in ['x', 'y', 'z_ref', 'z_dut', 'tb_mismatch']:
            if entry[sig] is not None:
                last[sig] = entry[sig]
            row[sig] = last[sig]
        filled.append(row)
    
    print(f"   Parsed {len(timeline)} time points, {len(filled)} after filling")
    return filled


def extract_error_traces(timeline: List[Dict], max_errors: int = 15) -> List[Dict]:
    """
    提取前 N 个出错点及其前 2 个状态
    
    Args:
        timeline (List[Dict]): 时间线数据
        max_errors (int): 最大错误数
        
    Returns:
        List[Dict]: 错误追踪列表
    """
    error_traces = []
    error_count = 0
    
    for i, entry in enumerate(timeline):
        # 检测不匹配的两种方法
        is_mismatch = (entry.get('tb_mismatch') == 1) or \
                      (entry.get('z_ref') is not None and entry.get('z_dut') is not None and 
                       entry['z_ref'] != entry['z_dut'])
        
        if is_mismatch and error_count < max_errors:
            error_count += 1
            
            # 获取前 2 个状态
            prev_states = []
            for j in range(max(0, i - 2), i):
                prev = timeline[j]
                prev_match = (prev.get('z_ref') == prev.get('z_dut')) if (prev.get('z_ref') is not None and prev.get('z_dut') is not None) else True
                prev_states.append({
                    'time': prev['time'], 
                    'x': prev['x'], 
                    'y': prev['y'],
                    'z_ref': prev['z_ref'], 
                    'z_dut': prev['z_dut'],
                    'match': prev_match
                })
            
            # 构建错误记录
            error_trace = {
                'error_index': error_count,
                'error_time': entry['time'],
                'error_input_x': entry['x'],
                'error_input_y': entry['y'],
                'ref_output': entry['z_ref'],
                'dut_output': entry['z_dut'],
                'previous_states': prev_states,
                'state_sequence': f"t={entry['time']}: ({entry['x']},{entry['y']})→{entry['z_dut']} (expected {entry['z_ref']})"
            }
            
            error_traces.append(error_trace)
    
    return error_traces


def code_judge(vcd_filename: str, output_filename: str = "error_trace_report.txt") -> List[Dict]:
    """
    解析 VCD 波形并生成详细错误报告
    
    Args:
        vcd_filename (str): VCD 波形文件名
        output_filename (str): 输出报告文件名
        
    Returns:
        List[Dict]: 错误追踪列表，空列表表示无错误或解析失败
    """
    # 解析文件路径
    vcd_path = Path(vcd_filename)
    if not vcd_path.is_absolute():
        vcd_path = Path.cwd() / vcd_filename
    
    # 检查文件是否存在
    if not vcd_path.exists():
        print(f"[code_judge] VCD file not found: {vcd_path}")
        return []
    
    # 确定输出目录和报告路径
    output_dir = vcd_path.parent
    report_path = output_dir / output_filename
    json_path = output_dir / "error_trace_data.json"
    
    print(f"[code_judge] Starting error analysis...")
    
    # Step 1: 解析 VCD 波形
    timeline = parse_vcd_waveform(vcd_path)
    
    if not timeline:
        report_content = """ERROR TRACE REPORT
================================================================================

⚠️  NO DATA AVAILABLE

VCD waveform parsing failed or returned empty data.
Possible causes:
1. VCD file is empty or corrupted
2. No mismatch events occurred during simulation
3. VCD format is incompatible with parser

Please check the simulation output and VCD file manually.
"""
        report_path.write_text(report_content, encoding='utf-8')
        print(f"[code_judge] ⚠️  VCD parsing returned empty data")
        return []
    
    # Step 2: 提取错误追踪
    error_traces = extract_error_traces(timeline, max_errors=15)
    
    # Step 3: 生成详细报告
    report_lines = [
        "=" * 80,
        "DETAILED ERROR TRACE REPORT",
        "=" * 80,
        "",
        f"VCD File: {vcd_path.name}",
        f"Total Time Points Analyzed: {len(timeline)}",
        f"Errors Found: {len(error_traces)}",
        ""
    ]
    
    if error_traces:
        report_lines.extend([
            f"First Error: t={error_traces[0]['error_time']} ps",
            f"Last Error: t={error_traces[-1]['error_time']} ps",
            "",
            "-" * 80,
            "ERROR DETAILS (First 15)",
            "-" * 80,
            ""
        ])
        
        for trace in error_traces:
            report_lines.extend([
                f"ERROR #{trace['error_index']} @ {trace['error_time']} ps",
                f"  Input: x={trace['error_input_x']}, y={trace['error_input_y']}",
                f"  Expected Output: {trace['ref_output']}",
                f"  Actual Output:   {trace['dut_output']}",
                f"  State Sequence: {trace['state_sequence']}",
                ""
            ])
            
            # 添加前 2 个状态的详细信息
            if trace['previous_states']:
                report_lines.append("  Previous States:")
                for idx, state in enumerate(trace['previous_states'], 1):
                    status = "✓ MATCH" if state['match'] else "✗ MISMATCH"
                    report_lines.append(
                        f"    [{idx}] t={state['time']} ps: "
                        f"input=({state['x']},{state['y']}), "
                        f"output={state['z_dut']} (expected {state['z_ref']}) {status}"
                    )
                report_lines.append("")
            
            report_lines.append("-" * 80)
            report_lines.append("")
        
        # 添加分析总结
        report_lines.extend([
            "=" * 80,
            "ANALYSIS SUMMARY",
            "=" * 80,
            "",
            f"Total Errors: {len(error_traces)}",
            "",
            "Common Patterns to Check:",
            "1. Timing violations (setup/hold time)",
            "2. Incorrect state transitions",
            "3. Off-by-one errors in counters",
            "4. Missing edge cases in combinational logic",
            "5. Incorrect reset or initialization behavior",
            ""
        ])
        
        print(f"[code_judge] ✅ Found {len(error_traces)} errors")
    else:
        report_lines.extend([
            "",
            "✅ NO ERRORS DETECTED",
            "",
            "All outputs match between DUT and Reference model.",
            "The design appears to be functionally correct."
        ])
        print(f"[code_judge] ✅ No errors detected")
    
    report_lines.extend(["", "=" * 80])
    
    # 写入文本报告
    report_content = "\n".join(report_lines)
    report_path.write_text(report_content, encoding='utf-8')
    print(f"[code_judge] Report saved to {report_path}")
    
    # 保存 JSON 数据
    try:
        json_data = {
            'vcd_file': str(vcd_path),
            'total_time_points': len(timeline),
            'error_count': len(error_traces),
            'error_traces': error_traces,
            'timeline_sample': timeline[:100]  # 保存前 100 个时间点用于调试
        }
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        print(f"[code_judge] JSON data saved to {json_path}")
    except Exception as e:
        print(f"[code_judge] ⚠️  Warning: Could not save JSON data: {e}")
    
    return error_traces


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code_judge.py <vcd_file> [output_report_name]")
        print("Example: python code_judge.py wave.vcd")
        sys.exit(1)
    
    vcd_file = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else "error_trace_report.txt"
    
    try:
        errors = code_judge(vcd_file, output_name)
        if errors:
            print(f"\n✅ Found {len(errors)} errors")
            print(f"   Detailed report saved to: {output_name}")
            sys.exit(1)  # 有错误，返回非零退出码
        else:
            print(f"\n✅ No errors found")
            sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
