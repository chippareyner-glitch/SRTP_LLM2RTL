module TopModule (
    input  clk,
    input  d,
    input  r,
    output reg q
);

    always @(negedge clk) begin
        if (r)
            q <= 1'b0;
        else
            q <= d;
    end

endmodule
