module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [31:0] in,
    output logic [31:0] out
);

    logic [31:0] prev;

    always_ff @(posedge clk) begin
        if (reset) begin
            out <= 32'd0;
        end else begin
            out <= out | (~in & prev);
        end
        prev <= in;
    end

endmodule
