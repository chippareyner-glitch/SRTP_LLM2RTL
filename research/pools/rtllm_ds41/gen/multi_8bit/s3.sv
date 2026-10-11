module multi_8bit (
    input  logic [7:0]  A,
    input  logic [7:0]  B,
    output logic [15:0] product
);

    logic [15:0] shifted;
    logic [15:0] temp;
    integer i;

    always_comb begin
        temp = 16'd0;
        shifted = {8'b0, A};

        for (i = 0; i < 8; i = i + 1) begin
            if (B[i]) begin
                temp = temp + shifted;
            end
            shifted = shifted << 1;
        end

        product = temp;
    end

endmodule
