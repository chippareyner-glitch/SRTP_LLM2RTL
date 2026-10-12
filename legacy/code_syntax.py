# code_syntax.py
"""
语法验证模块 (Code Syntax Checker)
================================================================================

功能:
使用 Icarus Verilog 对生成的 SystemVerilog 代码进行语法检查。

输入:
- code_filename: 代码文件名（如 "module.sv"）

输出:
- 同目录下生成 syntax_report.txt 文件
- 返回 0 表示语法通过，1 表示语法失败

使用示例:
    from code_syntax import code_syntax
    result = code_syntax("module.sv")
    if result == 0:
        print("Syntax check passed")
    else:
        print("Syntax check failed")
"""

import sys as _sys, pathlib as _pathlib  # legacy/ 下的模块依赖项目根目录的 config 等模块
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from pathlib import Path
from config import IVERILOG, run_cmd


def code_syntax(code_filename: str) -> int:
    """
    对 SystemVerilog 代码进行语法检查
    
    Args:
        code_filename (str): 代码文件名
        
    Returns:
        int: 0 表示语法通过，1 表示语法失败
    """
    # 解析文件路径
    code_path = Path(code_filename)
    if not code_path.is_absolute():
        code_path = Path.cwd() / code_filename
    
    # 检查文件是否存在
    if not code_path.exists():
        raise FileNotFoundError(f"Code file not found: {code_path}")
    
    # 确定报告文件路径
    report_path = code_path.parent / "syntax_report.txt"
    
    print(f"[code_syntax] Running syntax check on {code_path}...")
    print(f"   Using Icarus Verilog: {IVERILOG}")
    
    # 运行 Icarus Verilog 语法检查
    # -g2012: 启用 SystemVerilog-2012 标准
    # -t null: 不生成任何输出文件，仅检查语法
    rc, stdout, stderr, _ = run_cmd(
        [IVERILOG, "-g2012", "-t", "null", str(code_path)],
        timeout=60
    )
    
    # 构建报告内容
    report_lines = [
        "=" * 70,
        "SYSTEMVERILOG SYNTAX CHECK REPORT",
        "=" * 70,
        "",
        f"File: {code_path.name}",
        f"Path: {code_path.absolute()}",
        "",
        "-" * 70,
        "CHECK RESULT",
        "-" * 70,
        ""
    ]
    
    if rc == 0:
        report_lines.append("✅ SYNTAX CHECK PASSED")
        report_lines.append("")
        report_lines.append("No syntax errors detected.")
        report_lines.append("")
        report_lines.append("The code is syntactically correct and should compile successfully.")
        print(f"[code_syntax] ✅ Syntax check PASSED")
    else:
        report_lines.append("❌ SYNTAX CHECK FAILED")
        report_lines.append("")
        report_lines.append("Syntax errors detected:")
        report_lines.append("")
        
        if stdout:
            report_lines.append("Standard Output:")
            report_lines.append(stdout)
            report_lines.append("")
        
        if stderr:
            report_lines.append("Standard Error:")
            report_lines.append(stderr)
            report_lines.append("")
        
        report_lines.append("-" * 70)
        report_lines.append("COMMON FIXES:")
        report_lines.append("-" * 70)
        report_lines.append("1. Check module port declarations (input/output/inout)")
        report_lines.append("2. Verify signal types (wire vs reg)")
        report_lines.append("3. Ensure all begin/end pairs are matched")
        report_lines.append("4. Check for missing semicolons at end of statements")
        report_lines.append("5. Verify case/endcase or if/endif pairs")
        report_lines.append("6. Confirm module ends with 'endmodule'")
        
        print(f"[code_syntax] ❌ Syntax check FAILED")
    
    report_lines.append("")
    report_lines.append("=" * 70)
    
    # 写入报告文件
    report_content = "\n".join(report_lines)
    report_path.write_text(report_content, encoding='utf-8')
    print(f"[code_syntax] Report saved to {report_path}")
    
    # 返回结果：0 表示通过，1 表示失败
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python code_syntax.py <code_filename>")
        print("Example: python code_syntax.py module.sv")
        sys.exit(1)
    
    code_file = sys.argv[1]
    try:
        result = code_syntax(code_file)
        if result == 0:
            print(f"\n✅ Syntax check PASSED (return code: 0)")
        else:
            print(f"\n❌ Syntax check FAILED (return code: 1)")
            print(f"   Check syntax_report.txt for details")
        sys.exit(result)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
