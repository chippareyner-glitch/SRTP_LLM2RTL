module pe (
    input  logic               clk,
    input  logic               rst,
    input  logic signed [31:0] a,
    input  logic signed [31:0] b,
    output logic signed [31:0] c
);

    // Signed 64-bit product of the two signed 32-bit operands
    logic signed [63:0] product;

    assign product = a * b;

    // Accumulator register: asynchronous active-high reset,
    // synchronous accumulation on the rising edge of clk.
    // Low 32 bits of the signed product are accumulated into c.
    always_ff @(posedge clk or posedge rst) begin
        if (rst)
            c <= 32'sd0;
        else
            c <= c + product[31:0];
    end

endmodule
