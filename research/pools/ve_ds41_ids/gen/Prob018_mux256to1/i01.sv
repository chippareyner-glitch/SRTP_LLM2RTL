module TopModule (
    input  [0:255] in,
    input  [7:0]   sel,
    output         out
);

    assign out = in[sel];

endmodule
