module comparator_3bit (
    input  wire [2:0] A,
    input  wire [2:0] B,
    output wire       A_greater,
    output wire       A_equal,
    output wire       A_less
);

    // Treat A and B as unsigned 3-bit values (000 = 0 .. 111 = 7)
    assign A_greater = (A > B);
    assign A_equal   = (A == B);
    assign A_less    = (A < B);

endmodule
