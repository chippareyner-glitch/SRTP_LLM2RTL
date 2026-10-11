module TopModule (
    input  logic       clk,
    input  logic       reset,
    input  logic [7:0] d,
    output logic [7:0] q
);

    initial q = 8'h34;

    always_ff @(negedge clk) begin
        if (reset)
            q <= 8'h34;
        else
            q <= d;
    end

endmodule
