module TopModule (
    input  clk,
    input  areset,
    input  x,
    output z
);

    reg stateA;
    reg stateB;

    always @(posedge clk or posedge areset) begin
        if (areset) begin
            stateA <= 1'b1;
            stateB <= 1'b0;
        end else begin
            if (stateA) begin
                if (x) begin
                    stateA <= 1'b0;
                    stateB <= 1'b1;
                end else begin
                    stateA <= 1'b1;
                    stateB <= 1'b0;
                end
            end else if (stateB) begin
                stateA <= 1'b0;
                stateB <= 1'b1;
            end else begin
                stateA <= 1'b1;
                stateB <= 1'b0;
            end
        end
    end

    assign z = (stateA & x) | (stateB & ~x);

endmodule
