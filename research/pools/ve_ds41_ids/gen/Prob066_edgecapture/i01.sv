module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [31:0] in,
    output logic [31:0] out
);

    logic [31:0] prev;

    always_ff @(posedge clk) begin
        prev <= in;

        if (reset)
            out <= 32'b0;
        else
            out <= out | (prev & ~in);
    end

endmodule
