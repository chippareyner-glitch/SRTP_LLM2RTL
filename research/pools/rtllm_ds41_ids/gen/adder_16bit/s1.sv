module adder_8bit (
    input  logic [7:0] a,
    input  logic [7:0] b,
    input  logic       Cin,
    output logic [7:0] y,
    output logic       Co
);

    logic [8:0] sum;

    assign sum = a + b + Cin;
    assign y   = sum[7:0];
    assign Co  = sum[8];

endmodule

module adder_16bit (
    input  logic [15:0] a,
    input  logic [15:0] b,
    input  logic        Cin,
    output logic [15:0] y,
    output logic        Co
);

    logic carry_mid;

    adder_8bit u_adder_low (
        .a   (a[7:0]),
        .b   (b[7:0]),
        .Cin (Cin),
        .y   (y[7:0]),
        .Co  (carry_mid)
    );

    adder_8bit u_adder_high (
        .a   (a[15:8]),
        .b   (b[15:8]),
        .Cin (carry_mid),
        .y   (y[15:8]),
        .Co  (Co)
    );

endmodule
