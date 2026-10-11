module TopModule (
    input  [99:0] in,
    output [99:0] out_both,
    output [99:0] out_any,
    output [99:0] out_different
);

    genvar i, j, k;

    generate
        for (i = 0; i < 99; i = i + 1) begin : gen_out_both
            assign out_both[i] = in[i] & in[i+1];
        end

        for (j = 1; j < 100; j = j + 1) begin : gen_out_any
            assign out_any[j] = in[j] | in[j-1];
        end

        for (k = 0; k < 99; k = k + 1) begin : gen_out_different
            assign out_different[k] = in[k] ^ in[k+1];
        end
    endgenerate

    assign out_both[99] = 1'b0;
    assign out_any[0] = 1'b0;
    assign out_different[99] = in[99] ^ in[0];

endmodule
