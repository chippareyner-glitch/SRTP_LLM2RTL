module pe (
    input  wire        clk,
    input  wire        rst,
    input  wire [31:0] a,
    input  wire [31:0] b,
    output reg  [31:0] c
);

    // Partial sum register / accumulator.
    // a and b are unsigned 32-bit operands; a*b is an unsigned 64-bit product.
    // The accumulated value in c is truncated to 32 bits.
    always @(posedge clk or posedge rst) begin
        if (rst)
            c <= 32'd0;
        else
            c <= c + (a * b);
    end

endmodule
