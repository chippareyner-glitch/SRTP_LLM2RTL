module TopModule (
    input  logic clk,
    input  logic d,
    output logic q
);

    logic q_pos;
    logic q_neg;

    always_ff @(posedge clk) begin
        q_pos <= d;
    end

    always_ff @(negedge clk) begin
        q_neg <= d;
    end

    assign q = clk ? q_pos : q_neg;

endmodule
