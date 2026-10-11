module multi_8bit (
    input  logic [7:0]  A,
    input  logic [7:0]  B,
    output logic [15:0] product
);

    logic [15:0] sum;
    integer      i;

    always_comb begin
        sum = 16'd0;

        for (i = 0; i < 8; i = i + 1) begin
            if (B[i]) begin
                sum = sum + ({8'b0, A} << i);
            end
        end

        product = sum;
    end

endmodule
