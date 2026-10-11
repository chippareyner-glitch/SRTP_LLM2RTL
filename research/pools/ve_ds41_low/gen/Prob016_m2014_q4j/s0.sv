module TopModule (
    input  logic [3:0] x,
    input  logic [3:0] y,
    output logic [4:0] sum
);

    logic [4:0] carry;
    logic [3:0] s;

    assign carry[0] = 1'b0;

    genvar i;
    generate
        for (i = 0; i < 4; i = i + 1) begin : fa_chain
            assign s[i]     = x[i] ^ y[i] ^ carry[i];
            assign carry[i+1] = (x[i] & y[i]) |
                                (x[i] & carry[i]) |
                                (y[i] & carry[i]);
        end
    endgenerate

    assign sum = {carry[4], s};

endmodule
