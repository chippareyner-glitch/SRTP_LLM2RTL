module TopModule(
    input  clk,
    input  j,
    input  k,
    output Q
);

    reg q;

    always @(posedge clk) begin
        q <= (j & ~k) | (~k & q) | (j & ~q);
    end

    assign Q = q;

endmodule
