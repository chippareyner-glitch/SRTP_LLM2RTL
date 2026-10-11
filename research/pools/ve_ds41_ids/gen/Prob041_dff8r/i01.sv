module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [7:0] d,
    output logic [7:0] q
);

    always_ff @(posedge clk) begin
        if (reset)
            q <= 8'b0;
        else
            q <= {d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]};
    end

endmodule
