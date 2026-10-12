# spec_pre.py
"""
规格预处理模块 (Specification Preprocessor)
================================================================================

功能:
读取原始问题提示词，调用 Reviewer 模型生成优化后的提示词，
增强规格说明的清晰度和完整性。

输入:
- prompt_filename: 原始提示词文件名（如 "Prob001_prompt.txt"）

输出:
- 同目录下生成原文件名+_review.txt 文件
- 返回优化后的提示词内容字符串

使用示例:
    from spec_pre import spec_pre
    optimized_spec = spec_pre("Prob001_prompt.txt")
"""

import sys as _sys, pathlib as _pathlib  # legacy/ 下的模块依赖项目根目录的 config 等模块
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from pathlib import Path
from config import call_reviewer_llm, DEFAULT_REVIEW_GUIDANCE


def spec_pre(prompt_filename: str) -> str:
    """
    读取原始提示词并通过 Reviewer 模型生成优化版本
    
    Args:
        prompt_filename (str): 原始提示词文件名
        
    Returns:
        str: 优化后的提示词内容
        
    Raises:
        FileNotFoundError: 输入文件不存在
        Exception: Reviewer 调用失败
    """
    # 解析文件路径
    prompt_path = Path(prompt_filename)
    if not prompt_path.is_absolute():
        # 如果是相对路径，默认在当前工作目录查找
        prompt_path = Path.cwd() / prompt_filename
    
    # 检查文件是否存在
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    # 读取原始提示词
    original_spec = prompt_path.read_text(encoding='utf-8')
    print(f"[spec_pre] Loaded original spec from {prompt_path} ({len(original_spec)} chars)")
    
    # 构建 Reviewer 系统提示
    system_prompt = """You are an expert specification analyzer for digital IC design.

Your task is to review and enhance the problem specification for SystemVerilog code generation.

Focus on:
1. **Clarity**: Identify and clarify ambiguous requirements
2. **Completeness**: Detect missing specifications (timing, reset behavior, edge cases)
3. **Consistency**: Check for contradictory or conflicting requirements
4. **Testability**: Ensure the spec can be verified through simulation
5. **Hardware Constraints**: Add critical constraints for synthesis-friendly design

Output a detailed review report that will guide the code generation process."""

    # 构建 Reviewer 用户提示
    user_prompt = f"""Please analyze this specification and provide comprehensive guidance for RTL implementation:

{original_spec}

Provide your analysis in the following structure:
1. Specification Summary
2. Ambiguity Analysis
3. Missing Critical Details
4. Edge Cases & Boundary Conditions
5. Functional Correctness Prediction
6. Actionable Guidance for RTL Generation"""

    # 调用 Reviewer LLM
    print("[spec_pre] Calling Reviewer LLM...")
    review_response = call_reviewer_llm(system_prompt, user_prompt)
    
    # 构建优化后的提示词（原始规格 + Reviewer 建议）
    optimized_spec = f"""[ORIGINAL SPECIFICATION]
{original_spec}

[EXPERT REVIEW AND OPTIMIZATION GUIDANCE]
{review_response}

[GENERATION REQUIREMENTS]
Based on the specification and review above, please generate a complete, synthesizable SystemVerilog module implementation that:
1. Strictly follows the original specification
2. Incorporates all expert review suggestions
3. Handles all identified edge cases and boundary conditions
4. Uses proper coding practices for synthesis and timing closure"""

    # 确定输出文件路径
    output_path = prompt_path.with_name(f"{prompt_path.stem}_review.txt")
    
    # 保存优化后的提示词
    output_path.write_text(optimized_spec, encoding='utf-8')
    print(f"[spec_pre] Optimized spec saved to {output_path}")
    
    return optimized_spec


if __name__ == "__main__":
    import sys
    from pathlib import Path

    # ==============================================
    # 自动填入你的数据集路径，直接点运行就能用
    # ==============================================
    default_file = r"C:\Users\USER\OneDrive\文档\srtp\SRTP_LLM2RTL\dataset_spec-to-rtl_gcc\Prob001_prompt.txt"

    if len(sys.argv) < 2:
        print("⚠️ 未传入参数，自动使用默认数据集文件")
        sys.argv.append(default_file)

    prompt_path = Path(sys.argv[1])
    if not prompt_path.exists():
        print(f"❌ 文件不存在: {prompt_path}")
        sys.exit(1)

    print(f"✅ 正在处理: {prompt_path}")
    # 下面保持你原来的业务代码不变
