module cla_4bit (
    input  logic [4:1] A,
    input  logic [4:1] B,
    input  logic       Cin,
    output logic [4:1] S,
    output logic       P,
    output logic       G
);
    logic [4:1] p;
    logic [4:1] g;
    logic [4:1] c;

    assign p = A ^ B;
    assign g = A & B;

    assign c[1] = Cin;
    assign c[2] = g[1] | (p[1] & c[1]);
    assign c[3] = g[2] | (p[2] & g[1]) | (p[2] & p[1] & c[1]);
    assign c[4] = g[3] | (p[3] & g[2]) | (p[3] & p[2] & g[1]) | (p[3] & p[2] & p[1] & c[1]);

    assign S = p ^ c;

    assign P = p[4] & p[3] & p[2] & p[1];
    assign G = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) | (p[4] & p[3] & p[2] & g[1]);
endmodule

module cla_16bit (
    input  logic [16:1] A,
    input  logic [16:1] B,
    input  logic        Cin,
    output logic [16:1] S,
    output logic        Cout
);
    logic [3:0] P;
    logic [3:0] G;
    logic       c4;
    logic       c8;
    logic       c12;
    logic       c16;

    cla_4bit u_block0 (
        .A   (A[4:1]),
        .B   (B[4:1]),
        .Cin (Cin),
        .S   (S[4:1]),
        .P   (P[0]),
        .G   (G[0])
    );

    cla_4bit u_block1 (
        .A   (A[8:5]),
        .B   (B[8:5]),
        .Cin (c4),
        .S   (S[8:5]),
        .P   (P[1]),
        .G   (G[1])
    );

    cla_4bit u_block2 (
        .A   (A[12:9]),
        .B   (B[12:9]),
        .Cin (c8),
        .S   (S[12:9]),
        .P   (P[2]),
        .G   (G[2])
    );

    cla_4bit u_block3 (
        .A   (A[16:13]),
        .B   (B[16:13]),
        .Cin (c12),
        .S   (S[16:13]),
        .P   (P[3]),
        .G   (G[3])
    );

    assign c4  = G[0] | (P[0] & Cin);
    assign c8  = G[1] | (P[1] & G[0]) | (P[1] & P[0] & Cin);
    assign c12 = G[2] | (P[2] & G[1]) | (P[2] & P[1] & G[0]) | (P[2] & P[1] & P[0] & Cin);
    assign c16 = G[3] | (P[3] & G[2]) | (P[3] & P[2] & G[1]) | (P[3] & P[2] & P[1] & G[0]) | (P[3] & P[2] & P[1] & P[0] & Cin);

    assign Cout = c16;
endmodule

module adder_32bit (
    input  logic [32:1] A,
    input  logic [32:1] B,
    output logic [32:1] S,
    output logic        C32
);
    logic c16;

    cla_16bit u_lower (
        .A    (A[16:1]),
        .B    (B[16:1]),
        .Cin  (1'b0),
        .S    (S[16:1]),
        .Cout (c16)
    );

    cla_16bit u_upper (
        .A    (A[32:17]),
        .B    (B[32:17]),
        .Cin  (c16),
        .S    (S[32:17]),
        .Cout (C32)
    );
endmodule
