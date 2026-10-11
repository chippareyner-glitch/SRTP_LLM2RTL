module TopModule (
    input  logic [2:0] in,
    output logic [0:1] out
);

    logic [1:0] count;
    assign count = in[0] + in[1] + in[2];
    assign out[0] = count[1];
    assign out[1] = count[0];

endmodule
