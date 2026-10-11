module TopModule (
    input  logic [1:4] x,
    output logic f
);
    assign f = (~x[1] & x[3]) | (x[2] & x[4]);
endmodule
