module TopModule (
    input  clk,
    input  a,
    input  b,
    output q,
    output state
);

    reg state_reg;
    wire d;

    assign d = (a & b) | (state_reg & (a | b));
    assign q = a ^ b ^ state_reg;
    assign state = state_reg;

    always @(posedge clk) begin
        state_reg <= d;
    end

endmodule
