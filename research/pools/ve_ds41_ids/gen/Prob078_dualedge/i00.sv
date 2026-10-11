module TopModule (
    input  clk,
    input  d,
    output logic q
);

    logic q_pos;
    logic q_neg;

    initial begin
        q_pos = 1'b0;
        q_neg = 1'b0;
    end

    always @(posedge clk) begin
        q_pos <= d;
    end

    always @(negedge clk) begin
        q_neg <= d;
    end

    assign q = clk ? q_pos : q_neg;

endmodule
