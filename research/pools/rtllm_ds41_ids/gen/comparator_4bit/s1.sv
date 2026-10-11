module comparator_4bit (
    input  wire [3:0] A,
    input  wire [3:0] B,
    output wire A_greater,
    output wire A_equal,
    output wire A_less
);

    wire [4:0] sub_result;
    wire borrow;
    wire [3:0] diff;

    // 5-bit subtraction: {1'b0, A} - {1'b0, B}
    // MSB of sub_result is the borrow (1 if A < B)
    assign sub_result = {1'b0, A} - {1'b0, B};
    assign borrow = sub_result[4];
    assign diff   = sub_result[3:0];

    assign A_less    = borrow;
    assign A_equal   = ~borrow & (diff == 4'b0000);
    assign A_greater = ~borrow & (diff != 4'b0000);

endmodule
