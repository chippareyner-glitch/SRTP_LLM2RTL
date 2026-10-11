module TopModule (
    input  logic [3:0] a,
    input  logic [3:0] b,
    input  logic [3:0] c,
    input  logic [3:0] d,
    input  logic [3:0] e,
    output logic [3:0] q
);

    assign q = (c == 4'd0) ? b :
               (c == 4'd1) ? e :
               (c == 4'd2) ? a :
               (c == 4'd3) ? d :
               4'hF;

endmodule
