module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [31:0] in,
    output logic [31:0] out
);

    logic [31:0] prev_in;

    always_ff @(posedge clk) begin
        if (reset) begin
            out     <= '0;
            prev_in <= '0;
        end else begin
            out     <= out | (prev_in & ~in);
            prev_in <= in;
        end
    end

endmodule
