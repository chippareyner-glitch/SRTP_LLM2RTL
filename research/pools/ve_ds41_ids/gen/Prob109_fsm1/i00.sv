module TopModule (
    input  logic clk,
    input  logic areset,
    input  logic in,
    output logic out
);

    logic state;

    always_ff @(posedge clk or posedge areset) begin
        if (areset)
            state <= 1'b1;
        else if (state)
            state <= in;
        else
            state <= ~in;
    end

    assign out = state;

endmodule
