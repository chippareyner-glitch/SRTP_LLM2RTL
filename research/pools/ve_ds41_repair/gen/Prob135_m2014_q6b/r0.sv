module TopModule (
    input  logic [3:1] y,
    input  logic w,
    output logic Y1
);

    assign Y1 = y[3] ? w : ~(y[2] ^ y[1] ^ w);

endmodule
