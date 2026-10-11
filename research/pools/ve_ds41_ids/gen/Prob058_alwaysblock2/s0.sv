module TopModule (
    input  clk,
    input  a,
    input  b,
    output out_assign,
    output out_always_comb,
    output out_always_ff
);

    // XOR using continuous assignment
    assign out_assign = a ^ b;

    // XOR using combinational always block
    always_comb begin
        out_always_comb = a ^ b;
    end

    // XOR using clocked always block (flip-flop, delayed by one cycle)
    always_ff @(posedge clk) begin
        out_always_ff <= a ^ b;
    end

endmodule
