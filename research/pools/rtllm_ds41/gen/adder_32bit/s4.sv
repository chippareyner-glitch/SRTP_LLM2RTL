module cla_16bit(
    input  wire [16:1] A,
    input  wire [16:1] B,
    input  wire        Cin,
    output wire [16:1] S,
    output wire        Cout
);

    wire [16:1] p, g;
    assign p = A ^ B;
    assign g = A & B;

    // 4-bit group generate/propagate
    wire [4:1] gg, gp;

    // Group 1: bits 1-4
    assign gp[1] = p[4] & p[3] & p[2] & p[1];
    assign gg[1] = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) | (p[4] & p[3] & p[2] & g[1]);

    // Group 2: bits 5-8
    assign gp[2] = p[8] & p[7] & p[6] & p[5];
    assign gg[2] = g[8] | (p[8] & g[7]) | (p[8] & p[7] & g[6]) | (p[8] & p[7] & p[6] & g[5]);

    // Group 3: bits 9-12
    assign gp[3] = p[12] & p[11] & p[10] & p[9];
    assign gg[3] = g[12] | (p[12] & g[11]) | (p[12] & p[11] & g[10]) | (p[12] & p[11] & p[10] & g[9]);

    // Group 4: bits 13-16
    assign gp[4] = p[16] & p[15] & p[14] & p[13];
    assign gg[4] = g[16] | (p[16] & g[15]) | (p[16] & p[15] & g[14]) | (p[16] & p[15] & p[14] & g[13]);

    // Group carries
    wire [5:1] gc;
    assign gc[1] = Cin;
    assign gc[2] = gg[1] | (gp[1] & gc[1]);
    assign gc[3] = gg[2] | (gp[2] & gg[1]) | (gp[2] & gp[1] & gc[1]);
    assign gc[4] = gg[3] | (gp[3] & gg[2]) | (gp[3] & gp[2] & gg[1]) | (gp[3] & gp[2] & gp[1] & gc[1]);
    assign gc[5] = gg[4] | (gp[4] & gg[3]) | (gp[4] & gp[3] & gg[2]) |
                   (gp[4] & gp[3] & gp[2] & gg[1]) | (gp[4] & gp[3] & gp[2] & gp[1] & gc[1]);

    // Bit-wise carries
    wire [17:1] c;
    assign c[1] = gc[1];

    // Group 1
    assign c[2] = g[1] | (p[1] & c[1]);
    assign c[3] = g[2] | (p[2] & g[1]) | (p[2] & p[1] & c[1]);
    assign c[4] = g[3] | (p[3] & g[2]) | (p[3] & p[2] & g[1]) | (p[3] & p[2] & p[1] & c[1]);
    assign c[5] = gc[2];

    // Group 2
    assign c[6] = g[5] | (p[5] & c[5]);
    assign c[7] = g[6] | (p[6] & g[5]) | (p[6] & p[5] & c[5]);
    assign c[8] = g[7] | (p[7] & g[6]) | (p[7] & p[6] & g[5]) | (p[7] & p[6] & p[5] & c[5]);
    assign c[9] = gc[3];

    // Group 3
    assign c[10] = g[9] | (p[9] & c[9]);
    assign c[11] = g[10] | (p[10] & g[9]) | (p[10] & p[9] & c[9]);
    assign c[12] = g[11] | (p[11] & g[10]) | (p[11] & p[10] & g[9]) | (p[11] & p[10] & p[9] & c[9]);
    assign c[13] = gc[4];

    // Group 4
    assign c[14] = g[13] | (p[13] & c[13]);
    assign c[15] = g[14] | (p[14] & g[13]) | (p[14] & p[13] & c[13]);
    assign c[16] = g[15] | (p[15] & g[14]) | (p[15] & p[14] & g[13]) | (p[15] & p[14] & p[13] & c[13]);
    assign c[17] = gc[5];

    assign S = p ^ c[16:1];
    assign Cout = c[17];

endmodule

module adder_32bit(
    input  wire [32:1] A,
    input  wire [32:1] B,
    output wire [32:1] S,
    output wire        C32
);

    wire c16;

    cla_16bit u_low (
        .A    (A[16:1]),
        .B    (B[16:1]),
        .Cin  (1'b0),
        .S    (S[16:1]),
        .Cout (c16)
    );

    cla_16bit u_high (
        .A    (A[32:17]),
        .B    (B[32:17]),
        .Cin  (c16),
        .S    (S[32:17]),
        .Cout (C32)
    );

endmodule
