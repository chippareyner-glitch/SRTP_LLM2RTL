# enhanced_validator.py  验证器
"""
RTL代码验证器

该脚本用于验证生成的RTL代码的质量，包括语法检查和功能仿真两个阶段。
主要功能包括：
1. 语法验证：使用Icarus Verilog检查生成代码的语法正确性
2. 功能验证：通过测试平台运行仿真，验证功能正确性
3. 结果统计：生成CSV和JSON格式的验证结果汇总
4. 错误分析：生成详细的错误报告，包含错误类型和规格长度等信息
5. 报告生成：创建Excel格式的详细测试报告

支持两种验证模式：
- runs: 原始生成结果验证
- run_syntax: 语法纠错后结果验证

验证流程：
1. 用户选择验证目标目录
2. 遍历所有生成的RTL代码
3. 进行语法检查（使用iverilog）
4. 对语法正确的代码进行功能仿真（使用iverilog编译+vvp运行）
5. 解析仿真结果，判断功能是否正确
6. 生成详细的验证报告和统计数据
"""
import csv
import json
import re
import sys
from pathlib import Path
from dataclasses import asdict

import pandas as pd
from rtllm_validator import validate_rtllm

from config import (
    IVERILOG, VVP, TB_TOP,
    RUNS_DIR, DATASET_DIR,
    CaseResult,
    run_cmd,
    group_cases,
    contains_refmodule_definition,
    USE_IFC,
)

# =========================
# 路径配置
# =========================

# 语法纠错结果目录
SYNTAX_RUNS_DIR = RUNS_DIR.parent / "run_syntax"
# 语法纠错结果 CSV 文件路径
SYNTAX_RESULTS_CSV = SYNTAX_RUNS_DIR / "syntax_results.csv"
# 语法纠错汇总 JSON 文件路径
SYNTAX_SUMMARY_JSON = SYNTAX_RUNS_DIR / "syntax_summary.json"

# 闭环优化结果目录（原版本）
CLOSED_LOOP_RUNS_DIR = RUNS_DIR.parent / "runs_closed_loop"
# 闭环优化结果 CSV 文件路径
CLOSED_LOOP_RESULTS_CSV = CLOSED_LOOP_RUNS_DIR / "closed_loop_results.csv"
# 闭环优化汇总 JSON 文件路径
CLOSED_LOOP_SUMMARY_JSON = CLOSED_LOOP_RUNS_DIR / "closed_loop_summary.json"

# closed_loop_1.py 专用结果目录（增强版 v1，带详细 Mismatch 追踪）
CLOSED_LOOP_1_RUNS_DIR = RUNS_DIR.parent / "runs_closed_loop_1"
# closed_loop_1 结果 CSV 文件路径
CLOSED_LOOP_1_RESULTS_CSV = CLOSED_LOOP_1_RUNS_DIR / "closed_loop_1_results.csv"
# closed_loop_1 汇总 JSON 文件路径
CLOSED_LOOP_1_SUMMARY_JSON = CLOSED_LOOP_1_RUNS_DIR / "closed_loop_1_summary.json"

# closed_loop_1_v2.py 专用结果目录（v2.0 增强版，VCD-Aware Reviewer + 语法功能双重验证）
CLOSED_LOOP_V2_RUNS_DIR = RUNS_DIR.parent / "runs_closed_loop_v2"
# closed_loop_v2 结果 CSV 文件路径
CLOSED_LOOP_V2_RESULTS_CSV = CLOSED_LOOP_V2_RUNS_DIR / "closed_loop_v2_results.csv"
# closed_loop_v2 汇总 JSON 文件路径
CLOSED_LOOP_V2_SUMMARY_JSON = CLOSED_LOOP_V2_RUNS_DIR / "closed_loop_v2_summary.json"

# closed_loop_enhanced.py 专用结果目录（v2.0 Enhanced，智能诊断驱动）
CLOSED_LOOP_ENHANCED_RUNS_DIR = RUNS_DIR.parent / "runs_closed_loop_enhanced"
# closed_loop_enhanced 结果 CSV 文件路径
CLOSED_LOOP_ENHANCED_RESULTS_CSV = CLOSED_LOOP_ENHANCED_RUNS_DIR / "enhanced_results.csv"
# closed_loop_enhanced 汇总 JSON 文件路径
CLOSED_LOOP_ENHANCED_SUMMARY_JSON = CLOSED_LOOP_ENHANCED_RUNS_DIR / "enhanced_summary.json"

# =========================
# 目标目录配置
# =========================

TARGET_DIRS = {
    '0': {
        'name': 'runs_onlymodule',
        'path': RUNS_DIR,
        'results_csv': RUNS_DIR / "results.csv",
        'summary_json': RUNS_DIR / "summary.json",
        'error_csv': RUNS_DIR / "error_summary_with_spec_length.csv",
        'excel_report': RUNS_DIR / "results_report.xlsx",
        'prefix': ''
    },
    '1': {
        'name': 'run_syntax',
        'path': SYNTAX_RUNS_DIR,
        'results_csv': SYNTAX_RESULTS_CSV,
        'summary_json': SYNTAX_SUMMARY_JSON,
        'error_csv': SYNTAX_RUNS_DIR / "syntax_error_summary_with_spec_length.csv",
        'excel_report': SYNTAX_RUNS_DIR / "syntax_results_report.xlsx",
        'prefix': 'Syntax '
    },
    '2': {
        'name': 'runs_closed_loop',
        'path': CLOSED_LOOP_RUNS_DIR,
        'results_csv': CLOSED_LOOP_RESULTS_CSV,
        'summary_json': CLOSED_LOOP_SUMMARY_JSON,
        'error_csv': CLOSED_LOOP_RUNS_DIR / "closed_loop_error_summary_with_spec_length.csv",
        'excel_report': CLOSED_LOOP_RUNS_DIR / "closed_loop_results_report.xlsx",
        'prefix': 'Closed-Loop '
    },
    '3': {
        'name': 'runs_closed_loop_1',
        'path': CLOSED_LOOP_1_RUNS_DIR,
        'results_csv': CLOSED_LOOP_1_RESULTS_CSV,
        'summary_json': CLOSED_LOOP_1_SUMMARY_JSON,
        'error_csv': CLOSED_LOOP_1_RUNS_DIR / "closed_loop_1_error_summary_with_spec_length.csv",
        'excel_report': CLOSED_LOOP_1_RUNS_DIR / "closed_loop_1_results_report.xlsx",
        'prefix': 'Closed-Loop v1 '
    },
    '4': {
        'name': 'runs_closed_loop_v2',
        'path': CLOSED_LOOP_V2_RUNS_DIR,
        'results_csv': CLOSED_LOOP_V2_RESULTS_CSV,
        'summary_json': CLOSED_LOOP_V2_SUMMARY_JSON,
        'error_csv': CLOSED_LOOP_V2_RUNS_DIR / "closed_loop_v2_error_summary_with_spec_length.csv",
        'excel_report': CLOSED_LOOP_V2_RUNS_DIR / "closed_loop_v2_results_report.xlsx",
        'prefix': 'Closed-Loop v2 '
    },
    '5': {
        'name': 'runs_closed_loop_enhanced',
        'path': CLOSED_LOOP_ENHANCED_RUNS_DIR,
        'results_csv': CLOSED_LOOP_ENHANCED_RESULTS_CSV,
        'summary_json': CLOSED_LOOP_ENHANCED_SUMMARY_JSON,
        'error_csv': CLOSED_LOOP_ENHANCED_RUNS_DIR / "enhanced_error_summary_with_spec_length.csv",
        'excel_report': CLOSED_LOOP_ENHANCED_RUNS_DIR / "enhanced_results_report.xlsx",
        'prefix': 'Enhanced Closed-Loop '
    }
}

# =========================
# 用户交互函数
# =========================

def select_target_directory():
    """让用户通过窗口选择要验证的目标目录"""
    print("=" * 50)
    print("RTL 代码验证器")
    print("=" * 50)
    print("\n请选择包含题目子文件夹的父目录...\n")
    
    # 使用 tkinter 打开文件夹选择窗口
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        # 创建隐藏的根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.attributes('-topmost', True)  # 置顶显示
        
        # 打开文件夹选择对话框
        selected_dir = filedialog.askdirectory(
            title="选择包含题目子文件夹的父目录",
            initialdir=str(RUNS_DIR.parent),  # 默认打开 runs 目录的父目录
            mustexist=True
        )
        
        # 销毁窗口
        root.destroy()
        
        # 如果用户取消了选择
        if not selected_dir:
            print("❌ 用户取消了选择，使用默认目录")
            return '2'  # 返回默认的 runs_closed_loop
        
        selected_path = Path(selected_dir)
        print(f"\n📁 选择的目录：{selected_path.name}")
        print(f"📂 完整路径：{selected_path}")
        print("-" * 50)
        
        # 验证目录是否包含子文件夹
        subdirs = [d for d in selected_path.iterdir() if d.is_dir()]
        if subdirs:
            print(f"✅ 检测到 {len(subdirs)} 个子文件夹（题目）")
            print(f"   示例：{', '.join([d.name for d in subdirs[:3]])}")
        else:
            print("⚠️  警告：该目录下没有找到子文件夹")
        
        # 动态添加用户选择的目录到 TARGET_DIRS
        choice_key = 'custom'
        TARGET_DIRS[choice_key] = {
            'name': selected_path.name,
            'path': selected_path,
            'results_csv': selected_path / "validation_results.csv",
            'summary_json': selected_path / "validation_summary.json",
            'error_csv': selected_path / "error_summary_with_spec_length.csv",
            'excel_report': selected_path / "validation_report.xlsx",
            'prefix': f"{selected_path.name} "
        }
        
        return choice_key
        
    except ImportError:
        print("⚠️  tkinter 不可用，回退到命令行选择模式")
        # 回退到原来的命令行选择方式
        return select_target_directory_cli()
    except Exception as e:
        print(f"⚠️  打开文件夹窗口失败：{e}")
        print("回退到命令行选择模式")
        return select_target_directory_cli()


def select_target_directory_cli():
    """命令行模式的目录选择（备用方案）"""
    print("\n请选择要验证的目标目录：\n")
    
    for key, value in TARGET_DIRS.items():
        if key != 'custom':  # 不显示自定义目录
            print(f"{key}: {value['name']} - {value['prefix']}闭环优化结果")
    
    print()
    choice = input(f"请输入选项 (0-{len(TARGET_DIRS)-2}, 默认=2): ").strip()
    
    # 默认选择 runs_closed_loop
    if not choice:
        choice = '2'
    
    if choice not in TARGET_DIRS or choice == 'custom':
        print(f"❌ 无效选项：{choice}，使用默认值 2")
        choice = '2'
    
    selected = TARGET_DIRS[choice]
    print(f"\n📁 目标目录：{selected['name']}")
    print("-" * 50)
    
    return choice

# =========================
# 仿真判定：解析 mismatch
# =========================
MISMATCH_RE = re.compile(r"Mismatches:\s*(\d+)\s*in\s*(\d+)\s*samples")

def judge_pass_fail(sim_out: str, sim_err: str) -> tuple[bool, str]:
    """根据仿真输出判断功能是否通过"""
    text = (sim_out or "") + "\n" + (sim_err or "")

    if "TIMEOUT" in text:
        return False, "timeout"

    m = MISMATCH_RE.search(text)
    if not m:
        return False, "no_mismatch_summary"

    mism = int(m.group(1))
    samples = int(m.group(2))

    if samples <= 0:
        return False, "zero_samples"

    if mism == 0:
        return True, "pass"

    return False, f"mismatch={mism}"

# =========================
# 验证工具
# =========================
def syntax_check(sv_path: Path, log_path: Path) -> bool:
    """Icarus Verilog 语法检查"""
    rc, out, err, _ = run_cmd(
        [IVERILOG, "-g2012", "-tnull", str(sv_path)],
        timeout=60
    )
    log_path.write_text(out + "\n" + err, encoding="utf-8")
    return rc == 0

def compile_and_simulate(
    case_dir: Path,
    test_sv: Path,
    gen_sv: Path,
    ref_sv: Path | None,
    sim_log: Path,
):
    """
    编译并运行 SystemVerilog 仿真测试。

    该函数负责在指定目录中编译测试平台（testbench）及相关设计文件，
    并执行生成的仿真可执行文件，最后根据仿真输出判断测试是否通过。

    参数:
        case_dir (Path): 测试用例所在的工作目录路径。
        test_sv (Path): 测试平台（testbench）SystemVerilog 文件路径。
        gen_sv (Path): 待测生成的设计文件（DUT）路径。
        ref_sv (Path | None): 可选的参考模型 SystemVerilog 文件路径；若为 None，则不包含参考模型。
        sim_log (Path): 用于记录编译和仿真过程日志的文件路径。

    返回值:
        tuple[bool, str]: 包含两个元素的元组：
            - 第一个元素为布尔值，表示仿真是否成功通过；
            - 第二个元素为字符串，描述结果状态（如 "compile_failed" 或由 judge_pass_fail 返回的状态）。
    """

    print(f"Compiling case in directory: {case_dir}")
    print(f"Test file: {test_sv}")
    print(f"Generated file: {gen_sv}")
    print(f"Reference file: {ref_sv}")

    sim_out_exe = Path("sim.out")

    files = [str(test_sv.resolve())]
    if ref_sv is not None:
        files.append(str(ref_sv.resolve()))
        print(f"Adding reference file to compilation: {ref_sv}")
    files.append(str(gen_sv.resolve()))

    # 1) 编译
    cmd_compile = [
        IVERILOG, "-g2012",
        "-s", TB_TOP,
        "-o", str(sim_out_exe)
    ] + files

    print(f"Compilation command: {' '.join(cmd_compile)}")
    
    rc, out, err, _ = run_cmd(cmd_compile, cwd=case_dir, timeout=60)
    sim_log.write_text(
        "[COMPILE]\n" + out + "\n" + err + "\n",
        encoding="utf-8"
    )

    if rc != 0 or not (case_dir / sim_out_exe).exists():
        sim_log.write_text(
            sim_log.read_text(encoding="utf-8") +
            "\n[CHECK]\n" +
            f"compile_rc={rc}, sim_exists={(case_dir / sim_out_exe).exists()}\n",
            encoding="utf-8"
        )
        return False, "compile_failed"

    # 2) 仿真
    rc, out2, err2, _ = run_cmd(
        [VVP, str(sim_out_exe)],
        cwd=case_dir,
        timeout=60
    )

    sim_log.write_text(
        sim_log.read_text(encoding="utf-8") +
        "[RUN]\n" + out2 + "\n" + err2 + "\n",
        encoding="utf-8"
    )

    return judge_pass_fail(out2, err2)

def clean_obsolete_files(case_dir: Path, was_syntax_fail: bool, was_func_fail: bool):
    """
    清理过时的错误日志文件。
    
    根据当前测试结果，删除不再需要的旧错误日志文件。具体而言：
    - 如果当前语法检查已通过（即之前失败但现在成功），则删除语法错误日志；
    - 如果当前功能测试已通过（即之前失败但现在成功），则删除仿真日志。
    
    参数:
        case_dir (Path): 测试用例所在目录路径，日志文件位于此目录下。
        was_syntax_fail (bool): 表示上一次运行时是否发生语法检查失败。
        was_func_fail (bool): 表示上一次运行时是否发生功能测试失败。
        
    返回值:
        无返回值。
    """
    # 如果之前语法检查失败，现在通过了，删除语法错误日志
    if not was_syntax_fail:
        syntax_log = case_dir / "syntax.log"
        if syntax_log.exists():
            try:
                syntax_log.unlink()
            except Exception:
                pass
    
    # 如果之前功能测试失败，现在通过了，删除仿真日志
    if not was_func_fail:
        sim_log = case_dir / "sim.log"
        if sim_log.exists():
            try:
                sim_log.unlink()
            except Exception:
                pass

# =========================
# 主验证流程
# =========================
def validate_all_rtl(target_choice: str):
    """
    对指定目标目录下的所有生成的 RTL 设计进行语法检查和功能仿真验证，并生成结果汇总。

    该函数会遍历目标目录中的每个案例，执行以下步骤：
    1. 检查是否存在生成的 SystemVerilog 文件（module.sv 或 gen.sv）；
    2. 验证对应的数据集是否包含必要的规范文件（ifc/prompt）和测试平台（test）；
    3. 执行语法检查；
    4. 若语法通过，则执行功能仿真（使用数据集自带的 testbench 和参考模块 ref）；
    5. 记录验证结果到 CSV 文件，并生成 JSON 格式的汇总统计。

    参数:
        target_choice (str): 目标配置的键名，用于从全局字典 TARGET_DIRS 中获取对应的路径、结果文件名等配置信息。

    返回值:
        无（None）。函数通过副作用将结果写入文件系统。
    """
    # 根据用户选择设置目标配置
    target_config = TARGET_DIRS[target_choice]
    target_path = target_config['path']
    results_csv = target_config['results_csv']
    summary_json = target_config['summary_json']
    print_prefix = target_config['prefix']
    
    cases_in_dataset = group_cases(DATASET_DIR)
    results: list[CaseResult] = []

    print(f"Searching for generated RTL in {target_path.resolve()}")
    print(f"Using spec file: {'*_ifc.txt' if USE_IFC else '*_prompt.txt'}")

    # 确保目标目录存在
    if not target_path.exists():
        print(f"Warning: {target_path} does not exist")
        target_path.mkdir(parents=True, exist_ok=True)

    # 加载旧的验证结果（如果存在）
    old_results = {}
    if results_csv.exists():
        try:
            old_results_df = pd.read_csv(results_csv)
            for _, row in old_results_df.iterrows():
                old_results[row['case_id']] = {
                    'syntax_pass': row['syntax_pass'],
                    'func_pass': row['func_pass']
                }
        except Exception as e:
            print(f"Warning: Could not read old results: {e}")

    for case_dir in target_path.iterdir():
        if not case_dir.is_dir():
            continue

        cid = case_dir.name
        
        # 支持两种文件名：module.sv (integrated_generator) 和 gen.sv (syntax_corrector/generator)
        gen_sv = case_dir / "module.sv"
        if not gen_sv.exists():
            gen_sv = case_dir / "gen.sv"
        
        if not gen_sv.exists():
            continue

        if cid not in cases_in_dataset:
            continue

        files = cases_in_dataset[cid]
        spec_key = "ifc" if USE_IFC else "prompt"

        if spec_key not in files or "test" not in files:
            new_result = CaseResult(cid, spec_key, False, False, "", "missing_files", 0.0)
            results.append(new_result)
            continue

        print(f"Processing {cid}...")
        print(f"  Files found for {cid}: {list(files.keys())}")

        elapsed_sec = 0.0  # 未记录生成耗时，占位

        # 获取旧的验证结果
        old_result = old_results.get(cid, {})
        was_syntax_fail = not old_result.get('syntax_pass', True)
        was_func_fail = old_result.get('syntax_pass', False) and not old_result.get('func_pass', True)

        # 1) 语法检查
        syntax_log = case_dir / f"{print_prefix.lower()}syntax.log"
        ok_syntax = syntax_check(gen_sv, syntax_log)

        if not ok_syntax:
            print("  Syntax: FAIL")
            new_result = CaseResult(cid, spec_key, False, False, "", "syntax", elapsed_sec)
            results.append(new_result)
            
            # 如果之前是通过的，现在失败了，保留错误日志
            continue

        # 2) 功能仿真
        test_sv = files["test"]
        test_text = test_sv.read_text(encoding="utf-8")

        # 检查 testbench 是否包含 RefModule 定义
        need_ref = not contains_refmodule_definition(test_text)
        ref_sv = None

        print(f"  Need separate ref module: {need_ref}")
        if "ref" in files:
            print(f"  Ref file path: {files['ref']}")
        else:
            print("  No ref file found in dataset")

        # 如果需要参考模块但数据集中没有，则功能验证失败
        if need_ref and "ref" not in files:
            print("  Func: FAIL (missing ref)")
            new_result = CaseResult(cid, spec_key, True, False, "need_ref_but_missing", "sim", elapsed_sec)
            results.append(new_result)
            
            # 清理过时文件
            clean_obsolete_files(case_dir, was_syntax_fail, was_func_fail)
            continue

        # 如果需要参考模块，使用数据集中的 ref 文件
        if need_ref:
            ref_sv = files["ref"]

        sim_log = case_dir / f"{print_prefix.lower()}sim.log"
        ok_func, note = compile_and_simulate(
            case_dir, test_sv, gen_sv, ref_sv, sim_log
        )

        new_result = CaseResult(
            cid, spec_key,
            True, ok_func, note,
            "" if ok_func else "sim",
            elapsed_sec
        )
        results.append(new_result)

        # 清理过时的错误文件
        clean_obsolete_files(case_dir, was_syntax_fail, was_func_fail)
        
        status = 'PASS' if ok_func else 'FAIL'
        print(f"  Syntax: PASS, Func: {status} ({note})")

    # =========================
    # 写结果文件
    # =========================
    if results:
        target_path.mkdir(parents=True, exist_ok=True)  # 确保目录存在
        with open(results_csv, "w", newline="", encoding="utf-8") as f:
            fieldnames = list(asdict(results[0]).keys())
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for r in results:
                w.writerow(asdict(r))
    else:
        print("No results to write.")

    # =========================
    # 写汇总JSON
    # =========================
    valid_results = [r for r in results if r.error_stage != "missing_files"]
    n = len(valid_results)
    syntax_pass = sum(1 for r in valid_results if r.syntax_pass)
    func_pass = sum(1 for r in valid_results if r.func_pass)

    summary = {
        "total_cases_considered": n,
        "syntax_pass": syntax_pass,
        "syntax_pass_rate": (syntax_pass / n) if n else 0.0,
        "functional_pass": func_pass,
        "functional_pass_rate": (func_pass / n) if n else 0.0,
        "use_spec": "ifc" if USE_IFC else "prompt",
    }

    target_path.mkdir(parents=True, exist_ok=True)  # 确保目录存在
    summary_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n--- {print_prefix}Validation Summary ---")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

# =========================
# 生成错误汇总表（含 spec 长度）
# =========================
def generate_error_table_with_spec_length(target_choice: str):
    """
    根据指定的目标选择生成包含错误信息及对应规范文本长度的汇总表格。

    该函数读取指定目标的结果 CSV 文件，筛选出存在语法或功能错误的测试用例，
    并结合数据集中的规范文件（IFC 或 prompt）计算其文本长度，最终将错误信息与
    规范长度写入目标错误 CSV 文件中。

    参数:
        target_choice (str): 目标配置的键名，用于从全局字典 TARGET_DIRS 中获取对应的路径和文件配置。

    返回值:
        None: 函数无返回值。若过程中出现文件缺失、读取或写入错误，会打印警告信息并提前返回。
    """
    # 根据用户选择设置目标配置
    target_config = TARGET_DIRS[target_choice]
    target_path = target_config['path']
    results_csv = target_config['results_csv']
    error_csv = target_config['error_csv']
    
    spec_key = "ifc" if USE_IFC else "prompt"

    # 检查必需的文件是否存在
    if not results_csv.exists():
        print(f"Warning: Results file {results_csv} not found. Skipping error table generation.")
        return
        
    if not DATASET_DIR.exists():
        print(f"Warning: Dataset directory {DATASET_DIR} not found. Skipping error table generation.")
        return

    try:
        df = pd.read_csv(results_csv)
    except Exception as e:
        print(f"Warning: Could not read {results_csv}: {e}. Skipping error table generation.")
        return

    cases_in_dataset = group_cases(DATASET_DIR)

    records = []

    for _, row in df.iterrows():
        if row["syntax_pass"] and row["func_pass"]:
            continue

        if row["error_stage"] == "syntax":
            error_type = "syntax"
            error_info = "syntax_error"
        elif row["error_stage"] == "sim":
            error_type = "simulation"
            error_info = row.get("func_note", "")
        else:
            continue

        cid = row["case_id"]

        spec_length = None
        if cid in cases_in_dataset and spec_key in cases_in_dataset[cid]:
            try:
                spec_text = cases_in_dataset[cid][spec_key].read_text(encoding="utf-8")
                spec_length = len(spec_text)
            except Exception as e:
                print(f"Warning: Could not read spec file for case {cid}: {e}")

        records.append({
            "case_id": cid,
            "used_spec": spec_key,
            "spec_length": spec_length,
            "error_type": error_type,
            "error_info": error_info,
        })

    if records:  # 只有在有记录时才生成文件
        try:
            target_path.mkdir(parents=True, exist_ok=True)  # 确保目录存在
            err_df = pd.DataFrame(records)
            err_df.to_csv(error_csv, index=False, encoding="utf-8")

            print(f"\nWrote error summary table to {error_csv.resolve()}")
            print(err_df.head())
        except Exception as e:
            print(f"Warning: Could not write error summary table: {e}")
    else:
        print("\nNo errors found, skipping error summary table generation.")

def generate_excel_report(target_choice: str):
    """
    生成Excel格式的测试结果报告。

    该函数根据用户指定的目标选择，从对应的CSV结果文件中读取测试数据，
    生成包含详细测试结果、汇总统计和错误类型分布的Excel报告。
    报告包含三个工作表：'Test Results'（详细结果）、'Summary'（汇总指标）和可选的'Error Statistics'（错误统计）。

    参数:
        target_choice (str): 用户选择的目标标识符，用于从全局字典 TARGET_DIRS 中获取对应的配置信息。
                             配置需包含以下键：'path'（输出目录路径）、'results_csv'（输入CSV路径）、
                             'excel_report'（输出Excel路径）和 'prefix'（日志前缀字符串）。

    返回值:
        None: 函数无返回值。若依赖库缺失、输入文件不存在或处理过程中发生异常，
              将打印警告或错误信息并提前返回。
    """
    try:
        import openpyxl
    except ImportError:
        print("Warning: openpyxl not installed. Excel report generation will be skipped.")
        return

    # 根据用户选择设置目标配置
    target_config = TARGET_DIRS[target_choice]
    target_path = target_config['path']
    results_csv = target_config['results_csv']
    excel_report_path = target_config['excel_report']
    prefix = target_config['prefix']

    # 检查必需的文件是否存在
    if not results_csv.exists():
        print(f"Warning: Results file {results_csv} not found. Skipping Excel report generation.")
        return
    
    try:
        # 读取CSV数据
        df = pd.read_csv(results_csv)
        
        # 创建一个新的DataFrame用于Excel报告，添加一些计算列
        report_df = df.copy()
        
        # 添加通过状态列
        report_df['overall_status'] = report_df.apply(
            lambda row: 'PASS' if row['syntax_pass'] and row['func_pass'] 
                       else 'SYNTAX_FAIL' if not row['syntax_pass'] 
                       else 'FUNCTIONAL_FAIL', 
            axis=1
        )
        
        # 添加详细信息列
        report_df['details'] = report_df.apply(
            lambda row: 'Passed all checks' if row['overall_status'] == 'PASS'
                       else f"Syntax failed: {row.get('error_stage', '')}" if row['overall_status'] == 'SYNTAX_FAIL'
                       else f"Functional test failed: {row.get('func_note', '')}",
            axis=1
        )
        
        # 确保输出目录存在
        target_path.mkdir(parents=True, exist_ok=True)
        
        # 创建Excel写入器
        with pd.ExcelWriter(excel_report_path, engine='openpyxl') as writer:
            # 写入主报告sheet
            report_df.to_excel(writer, sheet_name='Test Results', index=False)
            
            # 创建汇总统计sheet
            summary_data = {
                'Metric': [
                    'Total Cases',
                    'Syntax Pass',
                    'Syntax Fail',
                    'Functional Pass',
                    'Functional Fail',
                    'Overall Pass Rate',
                    'Syntax Pass Rate',
                    'Functional Pass Rate'
                ],
                'Value': [
                    len(df),
                    len(df[df['syntax_pass'] == True]),
                    len(df[df['syntax_pass'] == False]),
                    len(df[(df['syntax_pass'] == True) & (df['func_pass'] == True)]),
                    len(df[(df['syntax_pass'] == True) & (df['func_pass'] == False)]),
                    f"{len(df[(df['syntax_pass'] == True) & (df['func_pass'] == True)]) / len(df) * 100:.2f}%" if len(df) > 0 else "0%",
                    f"{len(df[df['syntax_pass'] == True]) / len(df) * 100:.2f}%" if len(df) > 0 else "0%",
                    f"{len(df[(df['syntax_pass'] == True) & (df['func_pass'] == True)]) / len(df[df['syntax_pass'] == True]) * 100:.2f}%" if len(df[df['syntax_pass'] == True]) > 0 else "0%"
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # 按错误类型分类统计
            if 'error_stage' in df.columns:
                error_stats = df['error_stage'].value_counts().reset_index()
                error_stats.columns = ['Error Type', 'Count']
                error_stats.to_excel(writer, sheet_name='Error Statistics', index=False)
        
        print(f"\nGenerated {prefix}Excel report at: {excel_report_path.resolve()}")
        
        # 打印简要统计信息
        total = len(report_df)
        passed = len(report_df[report_df['overall_status'] == 'PASS'])
        print(f"{prefix}Excel Report - Total: {total}, Passed: {passed}, Failed: {total - passed}")
        
    except Exception as e:
        print(f"Error generating {prefix}Excel report: {e}")

def main():
    try:
        # 让用户通过窗口选择目录
        target_choice = select_target_directory()
        
        target_name = TARGET_DIRS[target_choice]['name']
        print(f"\n🚀 开始验证 '{target_name}' 目录...")
        print("-" * 50)
        
        validate_all_rtl(target_choice)
        generate_error_table_with_spec_length(target_choice)
        generate_excel_report(target_choice)
        
        print("\n" + "=" * 50)
        print(f"✅ 验证完成！结果已保存在：{TARGET_DIRS[target_choice]['path'].resolve()}")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\n用户中断了程序执行。")
        sys.exit(0)
    except Exception as e:
        print(f"验证过程中发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
