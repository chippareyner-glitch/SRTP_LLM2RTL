module TopModule (
    input  wire clk,
    input  wire x,
    output wire z
);

    logic q_xor = 1'b0;
    logic q_and = 1'b0;
    logic q_or  = 1'b0;

    always_ff @(posedge clk) begin
        q_xor <= x ^ q_xor;
        q_and <= x & ~q_and;
        q_or  <= x | ~q_or;
    end

    assign z = ~(q_xor | q_and | q_or);

endmodule
