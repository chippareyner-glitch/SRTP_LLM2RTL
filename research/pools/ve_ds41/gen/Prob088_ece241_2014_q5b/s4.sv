module TopModule (
    input  clk,
    input  areset,
    input  x,
    output logic z
);

    logic A, B;

    always_ff @(posedge clk or posedge areset) begin
        if (areset) begin
            A <= 1'b1;
            B <= 1'b0;
        end else begin
            A <= A & ~x;
            B <= B | (A & x);
        end
    end

    assign z = (A & x) | (B & ~x);

endmodule
