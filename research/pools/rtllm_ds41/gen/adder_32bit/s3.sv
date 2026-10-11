module cla_4bit (
    input  logic [4:1] A,
    input  logic [4:1] B,
    input  logic       cin,
    output wire  [4:1] S,
    output wire        cout,
    output wire        pg,
    output wire        gg
);
    wire [4:1] p;
    wire [4:1] g;
    wire c1, c2, c3, c4;

    assign p = A ^ B;
    assign g = A & B;

    assign c1 = cin;
    assign c2 = g[1] | (p[1] & c1);
    assign c3 = g[2] | (p[2] & g[1]) | (p[2] & p[1] & c1);
    assign c4 = g[3] | (p[3] & g[2]) | (p[3] & p[2] & g[1]) | (p[3] & p[2] & p[1] & c1);

    assign cout = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) | (p[4] & p[3] & p[2] & g[1]) | (p[4] & p[3] & p[2] & p[1] & c1);

    assign pg = p[4] & p[3] & p[2] & p[1];
    assign gg = g[4] | (p[4] & g[3]) | (p[4] & p[3] & g[2]) | (p[4] & p[3] & p[2] & g[1]);

    assign S[1] = p[1] ^ c1;
    assign S[2] = p[2] ^ c2;
    assign S[3] = p[3] ^ c3;
    assign S[4] = p[4] ^ c4;
endmodule

module cla_16 (
    input  logic [16:1] A,
    input  logic [16:1] B,
    input  logic        cin,
    output wire  [16:1] S,
    output wire         cout
);
    wire [4:1] S0, S1, S2, S3;
    wire       pg0, pg1, pg2, pg3;
    wire       gg0, gg1, gg2, gg3;
    wire       c1, c2, c3;
    wire       cout0, cout1, cout2, cout3;

    cla_4bit u0 (
        .A   (A[4:1]),
        .B   (B[4:1]),
        .cin (cin),
        .S   (S0),
        .cout(cout0),
        .pg  (pg0),
        .gg  (gg0)
    );

    cla_4bit u1 (
        .A   (A[8:5]),
        .B   (B[8:5]),
        .cin (c1),
        .S   (S1),
        .cout(cout1),
        .pg  (pg1),
        .gg  (gg1)
    );

    cla_4bit u2 (
        .A   (A[12:9]),
        .B   (B[12:9]),
        .cin (c2),
        .S   (S2),
        .cout(cout2),
        .pg  (pg2),
        .gg  (gg2)
    );

    cla_4bit u3 (
        .A   (A[16:13]),
        .B   (B[16:13]),
        .cin (c3),
        .S   (S3),
        .cout(cout3),
        .pg  (pg3),
        .gg  (gg3)
    );

    assign c1 = gg0 | (pg0 & cin);
    assign c2 = gg1 | (pg1 & gg0) | (pg1 & pg0 & cin);
    assign c3 = gg2 | (pg2 & gg1) | (pg2 & pg1 & gg0) | (pg2 & pg1 & pg0 & cin);
    assign cout = gg3 | (pg3 & gg2) | (pg3 & pg2 & gg1) | (pg3 & pg2 & pg1 & gg0) | (pg3 & pg2 & pg1 & pg0 & cin);

    assign S[4:1]   = S0;
    assign S[8:5]   = S1;
    assign S[12:9]  = S2;
    assign S[16:13] = S3;
endmodule

module adder_32bit (
    input  logic [32:1] A,
    input  logic [32:1] B,
    output wire  [32:1] S,
    output wire         C32
);
    wire c16;

    cla_16 u_low (
        .A   (A[16:1]),
        .B   (B[16:1]),
        .cin (1'b0),
        .S   (S[16:1]),
        .cout(c16)
    );

    cla_16 u_high (
        .A   (A[32:17]),
        .B   (B[32:17]),
        .cin (c16),
        .S   (S[32:17]),
        .cout(C32)
    );
endmodule
