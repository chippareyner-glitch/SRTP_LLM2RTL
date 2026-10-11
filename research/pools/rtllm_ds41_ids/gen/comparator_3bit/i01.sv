module comparator_3bit (
    input  wire [2:0] A,
    input  wire [2:0] B,
    output wire       A_greater,
    output wire       A_equal,
    output wire       A_less
);

    // Treat A and B as 3-bit two's-complement signed values:
    //   100 = -4, 101 = -3, 110 = -2, 111 = -1,
    //   000 =  0, 001 =  1, 010 =  2, 011 =  3
    wire A_sign = A[2];
    wire B_sign = B[2];

    // Sign bits differ -> the positive operand is greater.
    wire sign_diff = A_sign ^ B_sign;

    // Same sign -> two's-complement ordering matches unsigned ordering
    // of the lower magnitude bits.
    wire mag_gt = (A[1:0] > B[1:0]);
    wire mag_lt = (A[1:0] < B[1:0]);

    assign A_greater = sign_diff ? ~A_sign : mag_gt;
    assign A_less    = sign_diff ?  A_sign : mag_lt;
    assign A_equal   = (A == B);

endmodule
