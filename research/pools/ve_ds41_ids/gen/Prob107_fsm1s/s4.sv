module TopModule (
    input  clk,
    input  reset,
    input  in,
    output out
);

    reg state;

    always @(posedge clk) begin
        if (reset)
            state <= 1'b1; // B
        else
            state <= ~(state ^ in);
    end

    assign out = state;

endmodule
