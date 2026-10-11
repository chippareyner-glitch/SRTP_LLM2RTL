module TopModule (
    input  clk,
    input  reset,
    output logic [3:0] q
);

    always_ff @(posedge clk) begin
        if (reset)
            q <= 4'b0000;
        else
            q <= q + 1'b1;
    end

endmodule
