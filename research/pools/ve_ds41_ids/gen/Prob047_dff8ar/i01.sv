module TopModule (
    input  clk,
    input  areset,
    input  [7:0] d,
    output logic [7:0] q
);

    always_ff @(posedge clk) begin
        if (areset)
            q <= 8'b0;
        else
            q <= d;
    end

endmodule
