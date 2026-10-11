module multi_8bit (
    input  logic [7:0]  A,
    input  logic [7:0]  B,
    output logic [15:0] product
);

    logic [15:0] temp;
    logic [15:0] shifted_A;
    integer i;

    always_comb begin
        temp      = 16'd0;
        shifted_A = {8'd0, A};

        for (i = 0; i < 8; i = i + 1) begin
            if (B[i])
                temp = temp + shifted_A;

            shifted_A = shifted_A << 1;
        end

        product = temp;
    end

endmodule
