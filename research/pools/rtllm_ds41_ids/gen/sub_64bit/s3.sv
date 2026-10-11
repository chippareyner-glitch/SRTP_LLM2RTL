module sub_64bit (
    input  logic [63:0] A,
    input  logic [63:0] B,
    output logic [63:0] result,
    output logic        overflow
);

    logic [63:0] diff;

    // 64-bit binary subtraction
    assign diff   = A - B;
    assign result = diff;

    // Signed overflow detection:
    // Overflow occurs only when operands have different sign bits and
    // the sign of the result differs from the sign of A.
    //  - Positive overflow: A positive, B negative, result negative
    //  - Negative overflow: A negative, B positive, result positive
    assign overflow = (A[63] != B[63]) && (diff[63] != A[63]);

endmodule
