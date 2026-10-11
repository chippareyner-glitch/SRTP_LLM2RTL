module TopModule (
    input  [0:3] x,
    output       f
);

    assign f = (~x[1] & ~x[3]) |
               (~x[0] &  x[2]) |
               ( x[1] &  x[2] & x[3]);

endmodule
