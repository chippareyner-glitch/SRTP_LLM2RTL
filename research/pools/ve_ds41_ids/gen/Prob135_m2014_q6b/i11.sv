module TopModule (
    input  [3:1] y,
    input  w,
    output Y1
);
    assign Y1 = (~y[3] & ~(w ^ y[2] ^ y[1])) | (w & y[3] & ~y[2]);
endmodule
