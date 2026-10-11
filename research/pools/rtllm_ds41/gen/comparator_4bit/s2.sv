module bit_comparator (
    input  logic a,
    input  logic b,
    input  logic borrow_in,
    output logic diff,
    output logic borrow_out
);
    assign diff = a ^ b ^ borrow_in;
    assign borrow_out = (~a & b) | (~a & borrow_in) | (b & borrow_in);
endmodule

module comparator_4bit (
    input  logic [3:0] A,
    input  logic [3:0] B,
    output logic A_greater,
    output logic A_equal,
    output logic A_less
);

    logic [3:0] diff;
    logic borrow0, borrow1, borrow2, borrow3;

    bit_comparator u_bit0 (
        .a(A[0]),
        .b(B[0]),
        .borrow_in(1'b0),
        .diff(diff[0]),
        .borrow_out(borrow0)
    );

    bit_comparator u_bit1 (
        .a(A[1]),
        .b(B[1]),
        .borrow_in(borrow0),
        .diff(diff[1]),
        .borrow_out(borrow1)
    );

    bit_comparator u_bit2 (
        .a(A[2]),
        .b(B[2]),
        .borrow_in(borrow1),
        .diff(diff[2]),
        .borrow_out(borrow2)
    );

    bit_comparator u_bit3 (
        .a(A[3]),
        .b(B[3]),
        .borrow_in(borrow2),
        .diff(diff[3]),
        .borrow_out(borrow3)
    );

    assign A_less = borrow3;
    assign A_equal = ~|diff;
    assign A_greater = ~borrow3 & |diff;

endmodule
