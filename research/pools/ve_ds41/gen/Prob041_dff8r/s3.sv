module TopModule (
    input  wire       clk,
    input  wire       reset,
    input  wire [7:0] d,
    output logic [7:0] q
);

    always_ff @(posedge clk) begin
        if (reset)
            q <= 8'b0;
        else
            q <= d;
    end

endmodule
