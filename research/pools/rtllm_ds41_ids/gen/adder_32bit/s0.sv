module cla_4bit (
    input  logic [4:1] A,
    input  logic [4:1] B,
    input  logic       Cin,
    output logic [4:1] S,
    output logic       Cout,
    output logic       Pg,
    output logic       Gg
);

    logic [4:1] p, g;
    logic       c1, c2, c3, c4, c5;

    assign p = A ^ B;
    assign g = A & B;

    assign c1 = Cin;
    assign c2 = g[1] | (p[1] & c1);
    assign c3 = g[2] | (p[2] & g[1]) | (p[2] & p[1] & c1);
    assign c4 = g[3] | (p[3] & g[2]) | (p[3] & p[2] & g[1]) | (p[3] & p[2] & p[1] & c1);
    assign c5 = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) |
                (p[4] & p[3] & p[2] & g[1]) | (p[4] & p[3] & p[2] & p[1] & c1);

    assign S[1] = p[1] ^ c1;
    assign S[2] = p[2] ^ c2;
    assign S[3] = p[3] ^ c3;
    assign S[4] = p[4] ^ c4;

    assign Cout = c5;
    assign Pg = p[4] & p[3] & p[2] & p[1];
    assign Gg = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) | (p[4] & p[3] & p[2] & g[1]);

endmodule

module cla_16bit (
    input  logic [16:1] A,
    input  logic [16:1] B,
    input  logic        Cin,
    output logic [16:1] S,
    output logic        Cout,
    output logic        Pg,
    output logic        Gg
);

    logic P0, G0, P1, G1, P2, G2, P3, G3;
    logic C4, C8, C12, C16;

    assign C4  = G0 | (P0 & Cin);
    assign C8  = G1 | (P1 & G0) | (P1 & P0 & Cin);
    assign C12 = G2 | (P2 & G1) | (P2 & P1 & G0) | (P2 & P1 & P0 & Cin);

    assign Pg = P3 & P2 & P1 & P0;
    assign Gg = G3 | (P3 & G2) | (P3 & P2 & G1) | (P3 & P2 & P1 & G0);
    assign C16 = Gg | (Pg & Cin);
    assign Cout = C16;

    cla_4bit U0 (
        .A    (A[4:1]),
        .B    (B[4:1]),
        .Cin  (Cin),
        .S    (S[4:1]),
        .Cout (),
        .Pg   (P0),
        .Gg   (G0)
    );

    cla_4bit U1 (
        .A    (A[8:5]),
        .B    (B[8:5]),
        .Cin  (C4),
        .S    (S[8:5]),
        .Cout (),
        .Pg   (P1),
        .Gg   (G1)
    );

    cla_4bit U2 (
        .A    (A[12:9]),
        .B    (B[12:9]),
        .Cin  (C8),
        .S    (S[12:9]),
        .Cout (),
        .Pg   (P2),
        .Gg   (G2)
    );

    cla_4bit U3 (
        .A    (A[16:13]),
        .B    (B[16:13]),
        .Cin  (C12),
        .S    (S[16:13]),
        .Cout (),
        .Pg   (P3),
        .Gg   (G3)
    );

endmodule

module adder_32bit (
    input  logic [32:1] A,
    input  logic [32:1] B,
    output logic [32:1] S,
    output logic        C32
);

    logic C16;
    logic P_high, G_high;

    cla_16bit U_LOW (
        .A    (A[16:1]),
        .B    (B[16:1]),
        .Cin  (1'b0),
        .S    (S[16:1]),
        .Cout (C16),
        .Pg   (),
        .Gg   ()
    );

    cla_16bit U_HIGH (
        .A    (A[32:17]),
        .B    (B[32:17]),
        .Cin  (C16),
        .S    (S[32:17]),
        .Cout (),
        .Pg   (P_high),
        .Gg   (G_high)
    );

    assign C32 = G_high | (P_high & C16);

endmodule
