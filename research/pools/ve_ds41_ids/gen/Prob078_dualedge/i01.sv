module TopModule (
    input  clk,
    input  d,
    output q
);

    logic q1, q2;

    always_ff @(posedge clk) begin
        q1 <= d;
    end

    always_ff @(negedge clk) begin
        q2 <= d;
    end

    assign q = clk ? q1 : q2;

endmodule
