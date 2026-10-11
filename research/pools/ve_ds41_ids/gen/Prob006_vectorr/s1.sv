module TopModule (
    input  logic [7:0] in,
    output logic [7:0] out
);

    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : g_reverse
            assign out[i] = in[7 - i];
        end
    endgenerate

endmodule
