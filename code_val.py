# code_val.py
"""
功能验证模块 (Code Functional Validator)
================================================================================

功能:
使用 Icarus Verilog 对生成的 SystemVerilog 代码进行功能验证，
比对 DUT（Design Under Test）和 REF（Reference Model）的输出。

输入:
- code_filename: 待验证的代码文件名（如 "module.sv"）
- testbench_filename: 测试平台文件名（如 "Prob001_test.sv"）
- ref_code_filename: 参考代码文件名（如 "Prob001_ref.sv"）

输出:
- 同目录下生成 func_report.txt 文件
- 返回 True 表示功能通过，False 表示功能失败

使用示例:
    from code_val import code_val
    result = code_val("module.sv", "Prob001_test.sv", "Prob001_ref.sv")
    if result:
        print("Functional verification passed")
    else:
        print("Functional verification failed")
"""

from pathlib import Path
from config import IVERILOG, VVP, run_cmd


def code_val(code_filename: str, testbench_filename: str, ref_code_filename: str) -> bool:
    """
    对 SystemVerilog 代码进行功能验证
    
    Args:
        code_filename (str): 待验证的代码文件名
        testbench_filename (str): 测试平台文件名
        ref_code_filename (str): 参考代码文件名
        
    Returns:
        bool: True 表示功能通过，False 表示功能失败
    """
    from code_eval import evaluate_candidate
    import json
    code_path = Path(code_filename).resolve()
    result = evaluate_candidate(str(code_path), testbench_filename, ref_code_filename, code_path.parent.name, tag="functional")
    report = "FUNCTIONAL VERIFICATION REPORT\n" + json.dumps(result, ensure_ascii=False, indent=2)
    (code_path.parent / "func_report.txt").write_text(report, encoding="utf-8")
    return bool(result["func_pass"])


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python code_val.py <code.sv> <testbench.sv> <reference.sv>")
        print("Example: python code_val.py module.sv Prob001_test.sv Prob001_ref.sv")
        sys.exit(1)
    
    code_file = sys.argv[1]
    tb_file = sys.argv[2]
    ref_file = sys.argv[3]
    
    try:
        result = code_val(code_file, tb_file, ref_file)
        if result:
            print(f"\n✅ Functional verification PASSED")
            sys.exit(0)
        else:
            print(f"\n❌ Functional verification FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
