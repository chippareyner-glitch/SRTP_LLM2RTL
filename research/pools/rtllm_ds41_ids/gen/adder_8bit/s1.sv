// -----------------------------------------------------------------------------
// Full adder: 1-bit combinational adder with carry-in / carry-out
//   sum  = a ^ b ^ cin
//   cout = (a & b) | (cin & (a ^ b))
// -----------------------------------------------------------------------------
module full_adder (
    input  logic a,
    input  logic b,
    input  logic cin,
    output logic sum,
    output logic cout
);
    assign sum  = a ^ b ^ cin;
    assign cout = (a & b) | (cin & (a ^ b));
endmodule


// -----------------------------------------------------------------------------
// 8-bit ripple-carry adder built from eight bit-level full adders.
// Purely combinational logic.
// -----------------------------------------------------------------------------
module adder_8bit (
    input  logic [7:0] a,     // 8-bit input operand A
    input  logic [7:0] b,     // 8-bit input operand B
    input  logic       cin,   // Carry-in
    output logic [7:0] sum,   // 8-bit sum
    output logic       cout   // Carry-out
);

    logic [7:0] c;  // internal carry chain

    // Bit 0: least significant bit, uses external carry-in
    full_adder fa0 (
        .a    (a[0]),
        .b    (b[0]),
        .cin  (cin),
        .sum  (sum[0]),
        .cout (c[0])
    );

    // Bit 1
    full_adder fa1 (
        .a    (a[1]),
        .b    (b[1]),
        .cin  (c[0]),
        .sum  (sum[1]),
        .cout (c[1])
    );

    // Bit 2
    full_adder fa2 (
        .a    (a[2]),
        .b    (b[2]),
        .cin  (c[1]),
        .sum  (sum[2]),
        .cout (c[2])
    );

    // Bit 3
    full_adder fa3 (
        .a    (a[3]),
        .b    (b[3]),
        .cin  (c[2]),
        .sum  (sum[3]),
        .cout (c[3])
    );

    // Bit 4
    full_adder fa4 (
        .a    (a[4]),
        .b    (b[4]),
        .cin  (c[3]),
        .sum  (sum[4]),
        .cout (c[4])
    );

    // Bit 5
    full_adder fa5 (
        .a    (a[5]),
        .b    (b[5]),
        .cin  (c[4]),
        .sum  (sum[5]),
        .cout (c[5])
    );

    // Bit 6
    full_adder fa6 (
        .a    (a[6]),
        .b    (b[6]),
        .cin  (c[5]),
        .sum  (sum[6]),
        .cout (c[6])
    );

    // Bit 7: most significant bit
    full_adder fa7 (
        .a    (a[7]),
        .b    (b[7]),
        .cin  (c[6]),
        .sum  (sum[7]),
        .cout (c[7])
    );

    // Final carry-out of the 8-bit addition
    assign cout = c[7];

endmodule
