module TopModule (
    input  logic        clk,
    input  logic        reset,
    input  logic [31:0] in,
    output logic [31:0] out
);

    logic [31:0] prev;

    always_ff @(posedge clk) begin
        // Remember this cycle's input to compare against next cycle.
        // This must also happen on the reset cycle so that a 1->0
        // transition spanning the reset boundary is captured
        // (see Example 1: in=d82c07cd during reset, then 0 => out=d82c07cd).
        prev <= in;

        if (reset) begin
            out <= 32'd0;
        end else begin
            // Sticky capture of every bit that fell from 1 to 0.
            out <= out | (prev & ~in);
        end
    end

endmodule
