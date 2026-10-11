module sub_64bit (
    input  logic [63:0] A,
    input  logic [63:0] B,
    output logic [63:0] result,
    output logic        overflow
);

    // 64-bit binary subtraction (A - B)
    assign result = A - B;

    // Overflow detection:
    //  - Positive overflow: A is non-negative, B is negative, but result is negative
    //  - Negative overflow: A is negative, B is non-negative, but result is non-negative
    // Equivalently: operands have different signs and the result sign differs from A's sign.
    assign overflow = (A[63] ^ B[63]) & (A[63] ^ result[63]);

endmodule
