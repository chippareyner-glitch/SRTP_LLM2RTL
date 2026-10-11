module TopModule (
    input  [3:0] x,
    output       f
);

    // x[3] = MSB (K-map variable x[1])
    // x[2] =     (K-map variable x[2])
    // x[1] =     (K-map variable x[3])
    // x[0] = LSB (K-map variable x[4])
    assign f = (~x[3] &  x[1]) |
               ( x[3] &  x[2] & ~x[1]);

endmodule
