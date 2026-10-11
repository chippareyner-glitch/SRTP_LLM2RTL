module sub_64bit (
    input  logic [63:0] A,
    input  logic [63:0] B,
    output logic [63:0] result,
    output logic        overflow
);

    logic [63:0] diff;

    always_comb begin
        diff = A - B;

        // Overflow occurs when A and B have opposite signs and the
        // result's sign differs from A's sign.
        overflow = (A[63] ^ B[63]) & (A[63] ^ diff[63]);

        result = diff;
    end

endmodule
