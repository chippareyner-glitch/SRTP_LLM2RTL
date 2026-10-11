module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    logic stateA;
    logic stateB;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            stateA <= 1'b1;
            stateB <= 1'b0;
        end else begin
            stateA <= stateA & ~x;
            stateB <= (stateA & x) | stateB;
        end
    end

    assign z = (stateA & x) | (stateB & ~x);

endmodule
