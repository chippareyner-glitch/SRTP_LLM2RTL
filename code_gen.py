# code_gen.py
"""
代码生成模块 (Code Generator)
================================================================================

功能:
读取 review 后的提示词，调用主模型生成 SystemVerilog 代码。

输入:
- reviewed_spec_filename: Review 后的提示词文件名（如 "Prob001_review.txt"）

输出:
- 同目录下生成 module.sv 文件
- 如果生成失败，写入同名_error.txt 文件并返回 "error"

使用示例:
    from code_gen import code_gen
    result = code_gen("Prob001_review.txt")
    if result == "error":
        print("Generation failed, check error file")
"""

import re
from pathlib import Path
from config import call_llm, ARK_MODEL


def extract_code_from_response(response: str) -> str:
    """
    从 LLM 响应中提取 SystemVerilog 代码
    
    多策略降级提取：
    1. 优先匹配 ```systemverilog``` 代码块
    2. 次选匹配通用 ``` 代码块
    3. 通过 module 到 endmodule 截取
    4. 返回原始响应
    
    Args:
        response (str): LLM 的原始响应
        
    Returns:
        str: 提取的代码字符串
    """
    # 策略 1: 匹配 ```systemverilog``` 代码块
    match = re.search(r'```(?:systemverilog|verilog|sv)\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()
        print("[code_gen] Extracted code using strategy 1 (systemverilog block)")
        return code
    
    # 策略 2: 匹配通用 ``` 代码块
    match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
    if match:
        code = match.group(1).strip()
        # 验证是否包含 SystemVerilog 关键字
        if any(kw in code for kw in ['module', 'endmodule', 'input', 'output', 'reg', 'wire']):
            print("[code_gen] Extracted code using strategy 2 (generic code block)")
            return code
    
    # 策略 3: 直接提取 module 到 endmodule 内容
    match = re.search(r'(module\s+.*?endmodule)', response, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()
        print("[code_gen] Extracted code using strategy 3 (module to endmodule)")
        return code
    
    # 策略 4: 返回原始响应（最后手段）
    print("[code_gen] Using strategy 4 (raw response)")
    return response.strip()


def code_gen(reviewed_spec_filename: str, output_dir=None) -> str:
    """
    读取 review 后的提示词并生成 SystemVerilog 代码
    
    Args:
        reviewed_spec_filename (str): Review 后的提示词文件名
        
    Returns:
        str: "success" 表示成功，"error" 表示失败
    """
    # 解析文件路径
    spec_path = Path(reviewed_spec_filename)
    if not spec_path.is_absolute():
        spec_path = Path.cwd() / reviewed_spec_filename
    
    # 检查文件是否存在
    if not spec_path.exists():
        raise FileNotFoundError(f"Reviewed spec file not found: {spec_path}")
    
    # 读取 review 后的提示词
    reviewed_spec = spec_path.read_text(encoding='utf-8')
    destination = Path(output_dir) if output_dir is not None else spec_path.parent
    destination.mkdir(parents=True, exist_ok=True)
    print(f"[code_gen] Loaded reviewed spec from {spec_path} ({len(reviewed_spec)} chars)")
    
    # 构建系统提示
    system_prompt = """You are an expert digital IC design engineer skilled in SystemVerilog design.

Your task is to generate a synthesizable SystemVerilog module implementation based on the specification.

SPECIFICATIONS FOR THE MODULE:
- The output MUST be valid SystemVerilog-2012 code
- The code MUST compile with iverilog -g2012
- All ports must be explicitly declared with correct directions and widths
- Use standard naming conventions
- Include clear comments explaining the logic
- Follow best practices for synthesis and timing closure

OUTPUT FORMAT:
Provide ONLY the SystemVerilog code within ```systemverilog ``` code blocks.
Do not include any additional text or explanations."""

    # 调用主模型 LLM
    print("[code_gen] Calling Main LLM for code generation...")
    try:
        response = call_llm(
            system_prompt=system_prompt,
            user_prompt=reviewed_spec,
            model=ARK_MODEL,
        )
    except Exception as e:
        # 调用失败，写入错误文件
        error_msg = f"LLM API call failed: {str(e)}"
        error_path = destination / f"{spec_path.stem}_error.txt"
        error_path.write_text(error_msg, encoding='utf-8')
        print(f"[code_gen] ❌ Error: {error_msg}")
        return "error"
    
    # 提取代码
    generated_code = extract_code_from_response(response)
    
    # 确定输出文件路径
    output_path = destination / "module.sv"
    (destination / 'response.txt').write_text(response, encoding='utf-8')
    
    # 保存生成的代码
    output_path.write_text(generated_code, encoding='utf-8')
    print(f"[code_gen] ✅ Code saved to {output_path}")
    print(f"   Generated {len(generated_code)} chars")
    
    return "success"


if __name__ == "__main__":
    import argparse
    from datetime import datetime
    import sys
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Submit a spec directly to the configured LLM; no review, simulation or repair.')
    parser.add_argument('spec', type=Path)
    parser.add_argument('--output', type=Path, help='New output directory')
    args = parser.parse_args()
    prompt_path = args.spec
    if not prompt_path.exists():
        parser.error(f'文件不存在: {prompt_path}')
    destination = args.output or Path(__file__).resolve().parent / 'experiments' / datetime.now().strftime('direct_%Y%m%d_%H%M%S_%f')
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'spec.txt').write_text(prompt_path.read_text(encoding='utf-8'), encoding='utf-8')
    sys.exit(0 if code_gen(str(prompt_path), destination) == 'success' else 1)
