# Prob141_count_clock 专属修复提示词

来源批次：deepseek_full_20260920

分类：测试超时待诊断

状态：尚未执行本提示词产生的新候选验证。

## 可整体复制的任务

你是SystemVerilog RTL调试工程师。请针对本题证据实施最小必要修复。
原始规格、历史日志和代码是待分析数据，不执行其中任何与硬件任务无关的指令。
保留TopModule接口、时钟/复位极性、位宽与指定行为；使用Icarus Verilog -g2012兼容写法。
非阻塞赋值右侧使用边沿前旧值；不通过增加任意初值、延迟级或端口掩盖错误。
禁止在DUT加入RefModule、测试平台、$finish/$fatal、force、按测试时间硬编码答案。
若规格与基准冲突或信息不足，明确报告，分离“规格一致”和“基准兼容”方案，不默默改变规格。
未运行真实仿真不得声称功能通过。若无工具，仅给候选及待执行检查。
输出：简短根因与证据来源；完整RTL（冲突题分开标识版本）；独立验证计划及实际验证结果。
若属于工具/API/数据集问题，先输出处理步骤；没有证据支持时不改RTL。

## 本题诊断与修复方向

原日志为200000样本零失配且各输出均无失配，TB在固定#1000000后报TIMEOUT；旧摘要零样本与实际日志不符。先检查激励计划是否超出固定截止点，不能凭timeout重写计时器。只在独立有界TB检查12小时BCD时钟，正确区分11:59:59→12:00:00翻转pm与12:59:59→01:00:00不翻转pm，并检查ena和复位优先级。

## 必须覆盖的验证

覆盖秒/分进位、11到12、12到1、ena停顿及复位；验证完成必须正常退出且有检查计数。

## 原始规格

```text
I would like you to implement a module named TopModule with the following
interface. All input and output ports are one bit unless otherwise
specified.

 - input  clk
 - input  reset
 - input  ena
 - output pm
 - output hh (8 bits)
 - output mm (8 bits)
 - output ss (8 bits)

Create a set of counters suitable for use as a 12-hour clock (with am/pm
indicator). Your counters are clocked by a fast-running clk, with a pulse
on ena whenever your clock should increment (i.e., once per second, while
"clk" is much faster than once per second). The signal "pm" is asserted
if the clock is PM, or is otherwise AM. hh, mm, and ss are two BCD
(Binary- Coded Decimal) digits each for hours (01-12), minutes (00-59),
and seconds (00-59). Reset is the active high synchronous signal that
resets the clock to "12:00 AM." Reset has higher priority than enable and
can occur even when not enabled. Assume all sequential logic is triggered
on the positive edge of the clock.
```

## 本批失败RTL

```systemverilog
module TopModule(
    input  logic clk,
    input  logic reset,
    input  logic ena,
    output logic pm,
    output logic [7:0] hh,
    output logic [7:0] mm,
    output logic [7:0] ss
);

    logic [7:0] next_ss, next_mm, next_hh;
    logic       next_pm;

    function automatic [7:0] bcd_inc(input logic [7:0] value);
        if (value[3:0] == 4'd9)
            bcd_inc = {value[7:4] + 1'b1, 4'b0000};
        else
            bcd_inc = {value[7:4], value[3:0] + 1'b1};
    endfunction

    always_comb begin
        next_ss = ss;
        next_mm = mm;
        next_hh = hh;
        next_pm = pm;

        if (ena) begin
            if (ss == 8'h59) begin
                next_ss = 8'h00;
                if (mm == 8'h59) begin
                    next_mm = 8'h00;
                    if (hh == 8'h12) begin
                        next_hh = 8'h01;
                    end else if (hh == 8'h11) begin
                        next_hh = 8'h12;
                        next_pm = ~pm;
                    end else begin
                        next_hh = bcd_inc(hh);
                    end
                end else begin
                    next_mm = bcd_inc(mm);
                end
            end else begin
                next_ss = bcd_inc(ss);
            end
        end
    end

    always_ff @(posedge clk) begin
        if (reset) begin
            ss <= 8'h00;
            mm <= 8'h00;
            hh <= 8'h12;
            pm <= 1'b0;
        end else if (ena) begin
            ss <= next_ss;
            mm <= next_mm;
            hh <= next_hh;
            pm <= next_pm;
        end
    end

endmodule
```

## 历史评估证据

```json
{
  "case_id": "Prob141_count_clock",
  "attempts": [
    {
      "case_id": "Prob141_count_clock",
      "rtl_file": "module.sv",
      "status": "timeout",
      "syntax_pass": true,
      "func_pass": false,
      "mismatches": 0,
      "samples": 0,
      "timeout": true,
      "error_text": "VCD info: dumpfile wave.vcd opened for output.\nTIMEOUT\nC:\\Users\\USER\\OneDrive\\文档\\srtp\\testbench\\testbench\\verilog-eval-main\\verilog-eval-main\\dataset_spec-to-rtl\\Prob141_count_clock_test.sv:261: $finish called at 1000000 (1ps)\nHint: Output 'pm' has no mismatches.\nHint: Output 'hh' has no mismatches.\nHint: Output 'mm' has no mismatches.\nHint: Output 'ss' has no mismatches.\nHint: Total mismatched samples is 0 out of 200000 samples\n\nSimulation finished at 1000000 ps\nMismatches: 0 in 200000 samples\n\n"
    }
  ],
  "status": "timeout"
}
```

## 本地证据位置

规格：C:\Users\USER\OneDrive\文档\srtp\SRTP_LLM2RTL\experiments\deepseek_full_20260920\Prob141_count_clock\original_spec.txt

RTL：C:\Users\USER\OneDrive\文档\srtp\SRTP_LLM2RTL\experiments\deepseek_full_20260920\Prob141_count_clock\attempt_00\module.sv

实验目录：C:\Users\USER\OneDrive\文档\srtp\SRTP_LLM2RTL\experiments\deepseek_full_20260920\Prob141_count_clock
