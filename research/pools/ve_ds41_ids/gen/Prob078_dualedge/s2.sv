module TopModule (
    input  clk,
    input  d,
    output logic q
);

    logic p, n;

    always_ff @(posedge clk) begin
        p <= d ^ n;
    end

    always_ff @(negedge clk) begin
        n <= d ^ p;
    end

    assign q = p ^ n;

endmodule
