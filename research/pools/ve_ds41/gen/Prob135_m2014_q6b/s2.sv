module TopModule (
    input  logic [2:0] y,
    input  logic       w,
    output logic       Y1
);

    assign Y1 = (~y[1] & y[0]) | (w & ~y[0] & (y[2] ^ y[1]));

endmodule
