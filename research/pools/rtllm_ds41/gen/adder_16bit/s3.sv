module adder_8bit (
    input  [7:0] a,
    input  [7:0] b,
    input        cin,
    output [7:0] y,
    output       co
);
    wire [8:0] sum;

    assign sum = a + b + cin;
    assign y   = sum[7:0];
    assign co  = sum[8];
endmodule

module adder_16bit (
    input  [15:0] a,
    input  [15:0] b,
    input         Cin,
    output [15:0] y,
    output        Co
);
    wire c_mid;

    adder_8bit u_adder_low (
        .a   (a[7:0]),
        .b   (b[7:0]),
        .cin (Cin),
        .y   (y[7:0]),
        .co  (c_mid)
    );

    adder_8bit u_adder_high (
        .a   (a[15:8]),
        .b   (b[15:8]),
        .cin (c_mid),
        .y   (y[15:8]),
        .co  (Co)
    );
endmodule
