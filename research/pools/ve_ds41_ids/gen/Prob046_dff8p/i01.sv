module TopModule (
    input clk,
    input reset,
    input [7:0] d,
    output logic [0:7] q
);

    always_ff @(negedge clk) begin
        if (reset)
            q <= 8'h34;
        else
            q <= {d[7], d[6], d[5], d[4], d[3], d[2], d[1], d[0]};
    end

endmodule
