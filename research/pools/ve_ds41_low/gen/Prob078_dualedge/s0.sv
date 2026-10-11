module TopModule (
    input  clk,
    input  d,
    output q
);

    reg p, n;

    always @(posedge clk) begin
        p <= d ^ n;
    end

    always @(negedge clk) begin
        n <= d ^ p;
    end

    assign q = p ^ n;

endmodule
