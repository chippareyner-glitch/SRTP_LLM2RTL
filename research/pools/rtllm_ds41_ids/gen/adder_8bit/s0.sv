module full_adder (
    input  logic a,
    input  logic b,
    input  logic cin,
    output logic sum,
    output logic cout
);
    assign {cout, sum} = a + b + cin;
endmodule

module adder_8bit (
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic       cin,
    output logic [7:0] sum,
    output logic       cout
);
    logic [8:0] carry;

    assign carry[0] = cin;

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_full_adders
            full_adder fa_inst (
                .a    (a[i]),
                .b    (b[i]),
                .cin  (carry[i]),
                .sum  (sum[i]),
                .cout (carry[i + 1])
            );
        end
    endgenerate

    assign cout = carry[8];
endmodule
