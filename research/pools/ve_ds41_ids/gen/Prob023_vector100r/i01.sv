module TopModule (
    input  clk,
    input  [99:0] in,
    output reg [99:0] out
);

    always_ff @(posedge clk) begin
        for (int i = 0; i < 100; i++) begin
            out[i] <= in[99-i];
        end
    end

endmodule
