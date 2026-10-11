module TopModule (
    input  logic clk,
    input  logic d,
    output logic q
);
    logic q_pos = 1'b0, q_neg = 1'b0;

    always @(posedge clk) q_pos <= d;
    always @(negedge clk) q_neg <= d;

    assign q = clk ? q_pos : q_neg;
endmodule
