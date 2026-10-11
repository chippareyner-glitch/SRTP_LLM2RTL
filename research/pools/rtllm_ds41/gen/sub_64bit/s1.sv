module sub_64bit (
    input  logic [63:0] A,
    input  logic [63:0] B,
    output logic [63:0] result,
    output logic        overflow
);

    // 64-bit binary subtraction: result = A - B
    assign result = A - B;

    // Overflow detection for signed subtraction:
    // Overflow can only occur when the operands have different sign bits.
    //  - Positive overflow: A positive, B negative (result should be positive),
    //    but the result comes out negative.
    //  - Negative overflow: A negative, B positive (result should be negative),
    //    but the result comes out positive.
    assign overflow = (A[63] ^ B[63]) & (result[63] ^ A[63]);

endmodule
