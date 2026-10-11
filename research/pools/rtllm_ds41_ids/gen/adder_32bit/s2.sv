module cla_4 (
    input  [4:1] A,
    input  [4:1] B,
    input        cin,
    output [4:1] S,
    output       P,
    output       G
);
    wire [4:1] p, g;
    wire [4:1] c;

    assign p = A ^ B;
    assign g = A & B;

    assign c[1] = cin;
    assign c[2] = g[1] | (p[1] & c[1]);
    assign c[3] = g[2] | (p[2] & g[1]) | (p[2] & p[1] & c[1]);
    assign c[4] = g[3] | (p[3] & g[2]) | (p[3] & p[2] & g[1]) | (p[3] & p[2] & p[1] & c[1]);

    assign S = p ^ c;

    assign P = p[4] & p[3] & p[2] & p[1];
    assign G = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) | (p[4] & p[3] & p[2] & g[1]);
endmodule

module cla_16 (
    input  [16:1] A,
    input  [16:1] B,
    input         cin,
    output [16:1] S,
    output        cout
);
    wire c1, c5, c9, c13;
    wire P0, G0, P1, G1, P2, G2, P3, G3;

    assign c1 = cin;

    assign c5  = G0 | (P0 & c1);
    assign c9  = G1 | (P1 & G0) | (P1 & P0 & c1);
    assign c13 = G2 | (P2 & G1) | (P2 & P1 & G0) | (P2 & P1 & P0 & c1);
    assign cout = G3 | (P3 & c13);

    cla_4 block0 (
        .A(A[4:1]),
        .B(B[4:1]),
        .cin(c1),
        .S(S[4:1]),
        .P(P0),
        .G(G0)
    );

    cla_4 block1 (
        .A(A[8:5]),
        .B(B[8:5]),
        .cin(c5),
        .S(S[8:5]),
        .P(P1),
        .G(G1)
    );

    cla_4 block2 (
        .A(A[12:9]),
        .B(B[12:9]),
        .cin(c9),
        .S(S[12:9]),
        .P(P2),
        .G(G2)
    );

    cla_4 block3 (
        .A(A[16:13]),
        .B(B[16:13]),
        .cin(c13),
        .S(S[16:13]),
        .P(P3),
        .G(G3)
    );
endmodule

module adder_32bit (
    input  [32:1] A,
    input  [32:1] B,
    output [32:1] S,
    output        C32
);
    wire c16;

    cla_16 lower (
        .A(A[16:1]),
        .B(B[16:1]),
        .cin(1'b0),
        .S(S[16:1]),
        .cout(c16)
    );

    cla_16 upper (
        .A(A[32:17]),
        .B(B[32:17]),
        .cin(c16),
        .S(S[32:17]),
        .cout(C32)
    );
endmodule
