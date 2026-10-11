module TopModule (
    input  wire [3:0] x,
    input  wire [3:0] y,
    output wire [4:0] sum
);

    wire [4:0] carry;

    assign carry[0] = 1'b0;

    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : full_adder_gen
            wire s;
            wire c;

            assign s = x[i] ^ y[i] ^ carry[i];
            assign c = (x[i] & y[i]) | (x[i] & carry[i]) | (y[i] & carry[i]);

            assign sum[i]   = s;
            assign carry[i+1] = c;
        end
    endgenerate

    assign sum[4] = carry[4];

endmodule
