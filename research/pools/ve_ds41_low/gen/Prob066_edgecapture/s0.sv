module TopModule(
    input  clk,
    input  reset,
    input  [31:0] in,
    output reg [31:0] out
);

    reg [31:0] prev;

    always @(posedge clk) begin
        if (reset) begin
            out  <= 32'b0;
            prev <= 32'b0;
        end else begin
            prev <= in;
            out  <= out | (prev & ~in);
        end
    end

endmodule
