module TopModule (
    input  logic clk,
    input  logic d,
    output q
);
    logic q_pos, q_neg;

    always @(posedge clk) q_pos <= d;
    always @(negedge clk) q_neg <= d;

    assign q = clk ? q_pos : q_neg;
endmodule
